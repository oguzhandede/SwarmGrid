"""
Video-based Edge Agent for Integration Testing.

Reads from video file and sends telemetry to backend.
"""

import asyncio
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

import cv2
import numpy as np
import httpx

# Setup path - add src directory
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Try imports with fallback
try:
    from features.person_detector import PersonDetector, YOLO_AVAILABLE
except ImportError:
    PersonDetector = None
    YOLO_AVAILABLE = False

try:
    from features.density_enhanced import EnhancedDensityEstimator
except ImportError:
    EnhancedDensityEstimator = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoEdgeAgent:
    """Edge Agent that processes video and sends telemetry to backend."""
    
    def __init__(
        self,
        video_path: str,
        backend_url: str = "http://localhost:5000",
        tenant_id: str = "demo",
        site_id: str = "site-01",
        camera_id: str = "cam-01",
        zone_id: str = "zone-01",
        fps: int = 5
    ):
        self.video_path = video_path
        self.backend_url = backend_url.rstrip("/")
        self.tenant_id = tenant_id
        self.site_id = site_id
        self.camera_id = camera_id
        self.zone_id = zone_id
        self.target_fps = fps
        
        # Components
        self.person_detector = PersonDetector() if PersonDetector and YOLO_AVAILABLE else None
        self.density_estimator = EnhancedDensityEstimator() if EnhancedDensityEstimator else None
        
        # State
        self.prev_gray = None
        self.running = False
        self.telemetry_buffer = []
        
    async def run(self, max_frames: int = 100):
        """Run the video analysis and send telemetry."""
        logger.info(f"Starting Video Edge Agent")
        logger.info(f"  Video: {self.video_path}")
        logger.info(f"  Backend: {self.backend_url}")
        logger.info(f"  YOLO: {'Enabled' if self.person_detector else 'Disabled'}")
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error("Cannot open video file")
            return
            
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_skip = max(1, int(video_fps / self.target_fps))
        
        logger.info(f"  Video FPS: {video_fps:.1f}, Processing every {frame_skip} frames")
        
        self.running = True
        frame_count = 0
        processed_count = 0
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while self.running and processed_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    logger.info("End of video")
                    break
                    
                frame_count += 1
                
                # Skip frames for FPS control
                if frame_count % frame_skip != 0:
                    continue
                    
                # Process frame
                telemetry = self._process_frame(frame)
                
                if telemetry:
                    self.telemetry_buffer.append(telemetry)
                    processed_count += 1
                    
                    # Send batch every 5 frames
                    if len(self.telemetry_buffer) >= 5:
                        await self._send_telemetry(client)
                        
                    # Log progress
                    if processed_count % 10 == 0:
                        logger.info(f"Processed {processed_count} frames, Risk: {telemetry['risk_score']:.2f}")
                        
                # Small delay to control rate
                await asyncio.sleep(0.1)
                
            # Send remaining buffer
            if self.telemetry_buffer:
                await self._send_telemetry(client)
                
        cap.release()
        logger.info(f"Completed: {processed_count} frames processed")
        
    def _process_frame(self, frame: np.ndarray) -> dict:
        """Process single frame and extract features."""
        frame_resized = cv2.resize(frame, (640, 480))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        # Person detection
        person_count = 0
        if self.person_detector:
            det_result = self.person_detector.detect(frame_resized)
            person_count = det_result.person_count
            
        # Density estimation
        motion_density = 0.0
        stationary_density = 0.0
        total_density = 0.0
        if self.density_estimator:
            density_result = self.density_estimator.estimate(frame_resized)
            motion_density = float(density_result.motion_density)
            stationary_density = float(density_result.stationary_density)
            total_density = float(density_result.total_density)
        
        # Optical flow
        flow_entropy = 0.0
        alignment = 1.0
        avg_speed = 0.0
        speed_variance = 0.0
        bottleneck_index = 0.0
        
        if self.prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            avg_speed = float(np.mean(magnitude))
            speed_variance = float(np.var(magnitude))
            
            # Entropy
            angles_deg = np.degrees(angle.flatten())
            hist, _ = np.histogram(angles_deg, bins=36, range=(0, 360))
            hist = hist.astype(float) / (hist.sum() + 1e-10)
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            flow_entropy = float(entropy / np.log2(36))
            
            # Alignment
            sin_sum = float(np.sin(angle).mean())
            cos_sum = float(np.cos(angle).mean())
            alignment = float(np.sqrt(sin_sum**2 + cos_sum**2))
            
            # Bottleneck
            high_flow = magnitude > np.percentile(magnitude, 75) if magnitude.max() > 0 else magnitude > 0
            bottleneck_index = float(np.count_nonzero(high_flow) / magnitude.size)
            
        self.prev_gray = gray
        
        # Combined density
        density = total_density
        
        # Add person count factor
        person_factor = min(1.0, person_count / 20)
        density = max(density, person_factor)
        
        # Calculate risk
        risk_score = (
            density * 0.30 +
            person_factor * 0.25 +
            flow_entropy * 0.20 +
            (1 - alignment) * 0.15 +
            bottleneck_index * 0.10
        )
        
        return {
            "tenantId": self.tenant_id,
            "siteId": self.site_id,
            "cameraId": self.camera_id,
            "zoneId": self.zone_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "density": round(density, 4),
            "avgSpeed": round(avg_speed, 4),
            "speedVariance": round(speed_variance, 4),
            "flowEntropy": round(flow_entropy, 4),
            "alignment": round(alignment, 4),
            "bottleneckIndex": round(bottleneck_index, 4),
            "personCount": person_count,
            "risk_score": round(risk_score, 4)
        }
        
    async def _send_telemetry(self, client: httpx.AsyncClient):
        """Send buffered telemetry to backend."""
        if not self.telemetry_buffer:
            return
            
        payload = self.telemetry_buffer.copy()
        self.telemetry_buffer.clear()
        
        try:
            response = await client.post(
                f"{self.backend_url}/api/telemetry/ingest",
                json=payload
            )
            
            if response.status_code == 200:
                logger.debug(f"Sent {len(payload)} telemetry records")
            else:
                logger.warning(f"Backend returned {response.status_code}: {response.text[:100]}")
                
        except httpx.ConnectError:
            logger.warning("Cannot connect to backend - is it running?")
        except Exception as e:
            logger.error(f"Send error: {e}")


async def main():
    video_path = r"e:\Oguz\SwarmGrid\20260105_0016_New Video_simple_compose_01ke5dwdzrfrtvvchjzsg53cp1.mp4"
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
    agent = VideoEdgeAgent(
        video_path=video_path,
        backend_url="http://localhost:5000",
        tenant_id="demo",
        site_id="avm-istanbul",
        camera_id="cam-foodcourt",
        zone_id="foodcourt-exit"
    )
    
    print("=" * 60)
    print("🚀 SwarmGrid Video Edge Agent")
    print("=" * 60)
    print(f"Video: {video_path}")
    print(f"Backend: http://localhost:5000")
    print("=" * 60)
    print("\n⚠️  Make sure backend is running:")
    print("    cd core-backend && dotnet run --project src/SwarmGrid.Api\n")
    
    await agent.run(max_frames=100)


if __name__ == "__main__":
    asyncio.run(main())
