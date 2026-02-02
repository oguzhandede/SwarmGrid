"""
Stream Server - MJPEG video stream with detection overlay.

Provides HTTP endpoint for live video streaming with
visual overlays showing detection results.
"""

import asyncio
import logging
import time
from typing import Optional, AsyncGenerator
from io import BytesIO

import cv2
import numpy as np
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse


logger = logging.getLogger(__name__)


class StreamServer:
    """
    MJPEG stream server with detection overlay rendering.
    
    Provides real-time video stream with:
    - Density heatmap overlay
    - Motion flow visualization
    - Risk level indicators
    """
    
    def __init__(self, fps: int = 10):
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.current_frame: Optional[np.ndarray] = None
        self.current_metrics: dict = {}
        self.running = False
        self._lock = asyncio.Lock()
        
    def update_frame(self, frame: np.ndarray, metrics: dict = None):
        """
        Update the current frame and metrics.
        
        Args:
            frame: BGR frame from video source
            metrics: Detection metrics (density, flow, etc.)
        """
        self.current_frame = frame.copy()
        if metrics:
            self.current_metrics = metrics
            
    def render_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Render detection overlay on frame.
        
        Args:
            frame: Original BGR frame
            
        Returns:
            Frame with overlay rendered
        """
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        metrics = self.current_metrics
        
        # Get metrics
        density = metrics.get('density', 0)
        flow_entropy = metrics.get('flow_entropy', 0)
        avg_speed = metrics.get('avg_speed', 0)
        risk_level = metrics.get('risk_level', 'Normal')
        
        # Density heatmap overlay (semi-transparent)
        if density > 0:
            # Create color based on density (green -> yellow -> red)
            if density < 0.5:
                color = (0, int(255 * (1 - density * 2)), int(255 * density * 2))  # Green to Yellow
            else:
                color = (0, int(255 * (1 - (density - 0.5) * 2)), 255)  # Yellow to Red
            
            # Draw density indicator bar at bottom
            bar_height = 20
            bar_width = int(w * density)
            cv2.rectangle(overlay, (0, h - bar_height), (bar_width, h), color, -1)
            
        # Add alpha blending
        alpha = 0.3
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Draw info panel at top
        panel_height = 60
        cv2.rectangle(frame, (0, 0), (w, panel_height), (0, 0, 0), -1)
        
        # Risk level indicator
        risk_colors = {
            'Normal': (0, 255, 0),    # Green
            'Dikkat': (0, 255, 255),  # Yellow
            'Kritik': (0, 0, 255)     # Red
        }
        risk_color = risk_colors.get(risk_level, (128, 128, 128))
        
        # Draw risk indicator circle
        cv2.circle(frame, (30, 30), 15, risk_color, -1)
        cv2.circle(frame, (30, 30), 15, (255, 255, 255), 2)
        
        # Draw text labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_color = (255, 255, 255)
        
        cv2.putText(frame, f"Density: {density*100:.1f}%", (60, 20), font, font_scale, font_color, 1)
        cv2.putText(frame, f"Entropy: {flow_entropy:.2f}", (60, 40), font, font_scale, font_color, 1)
        cv2.putText(frame, f"Speed: {avg_speed:.2f}", (200, 20), font, font_scale, font_color, 1)
        cv2.putText(frame, f"Status: {risk_level}", (200, 40), font, font_scale, font_color, 1)
        
        # Timestamp
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (w - 80, 20), font, font_scale, font_color, 1)
        
        return frame
        
    def frame_to_jpeg(self, frame: np.ndarray) -> bytes:
        """Convert frame to JPEG bytes."""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()
        
    async def generate_frames(self) -> AsyncGenerator[bytes, None]:
        """
        Generate MJPEG frames for streaming.
        
        Yields:
            MJPEG frame bytes with boundary
        """
        self.running = True
        
        while self.running:
            start_time = time.time()
            
            if self.current_frame is not None:
                # Render overlay
                frame_with_overlay = self.render_overlay(self.current_frame)
                
                # Convert to JPEG
                jpeg_bytes = self.frame_to_jpeg(frame_with_overlay)
                
                # Yield as MJPEG frame
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
                )
            else:
                # Generate placeholder frame
                placeholder = self.generate_placeholder()
                jpeg_bytes = self.frame_to_jpeg(placeholder)
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
                )
            
            # FPS control
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_interval - elapsed)
            await asyncio.sleep(sleep_time)
            
    def generate_placeholder(self) -> np.ndarray:
        """Generate placeholder frame when no video source."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (30, 30, 30)  # Dark gray
        
        # Add "Waiting for stream..." text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Video bekleniyor..."
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        x = (640 - text_size[0]) // 2
        y = (480 + text_size[1]) // 2
        cv2.putText(frame, text, (x, y), font, 1, (100, 100, 100), 2)
        
        return frame
        
    def stop(self):
        """Stop the stream generator."""
        self.running = False


def add_stream_routes(app: FastAPI, stream_server: StreamServer):
    """Add stream routes to FastAPI app."""
    
    @app.get("/stream")
    async def video_stream():
        """MJPEG video stream endpoint."""
        return StreamingResponse(
            stream_server.generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
        
    @app.get("/stream/snapshot")
    async def stream_snapshot():
        """Get single frame snapshot."""
        if stream_server.current_frame is not None:
            frame = stream_server.render_overlay(stream_server.current_frame)
            jpeg_bytes = stream_server.frame_to_jpeg(frame)
            return Response(content=jpeg_bytes, media_type="image/jpeg")
        else:
            placeholder = stream_server.generate_placeholder()
            jpeg_bytes = stream_server.frame_to_jpeg(placeholder)
            return Response(content=jpeg_bytes, media_type="image/jpeg")
