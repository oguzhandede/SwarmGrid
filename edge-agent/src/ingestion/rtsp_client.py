"""
RTSP Client for video stream ingestion.
"""

import asyncio
import logging
from typing import Optional

import cv2
import numpy as np

from config.settings import Settings


logger = logging.getLogger(__name__)


class RTSPClient:
    """
    RTSP stream client with frame rate control.
    
    Handles connection, reconnection, and frame extraction
    from RTSP camera streams.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cap: Optional[cv2.VideoCapture] = None
        self.connected = False
        self._frame_interval = 1.0 / settings.fps
        self._last_frame_time = 0.0
        
    async def connect(self) -> bool:
        """
        Connect to RTSP stream.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            # Run blocking OpenCV operation in thread pool
            loop = asyncio.get_event_loop()
            self.cap = await loop.run_in_executor(
                None,
                self._create_capture
            )
            
            if self.cap is not None and self.cap.isOpened():
                self.connected = True
                logger.info(f"Connected to: {self.settings.rtsp_url}")
                return True
            else:
                logger.error(f"Failed to open stream: {self.settings.rtsp_url}")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
            
    def _create_capture(self) -> cv2.VideoCapture:
        """Create OpenCV VideoCapture object."""
        rtsp_url = self.settings.rtsp_url
        
        # Check if rtsp_url is a device index (integer or numeric string)
        if isinstance(rtsp_url, int) or (isinstance(rtsp_url, str) and rtsp_url.isdigit()):
            device_index = int(rtsp_url)
            logger.info(f"Opening webcam device: {device_index}")
            cap = cv2.VideoCapture(device_index)
        else:
            logger.info(f"Opening stream URL: {rtsp_url}")
            cap = cv2.VideoCapture(rtsp_url)
        
        # Set capture properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.frame_height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
        
        return cap
        
    async def get_frame(self) -> Optional[np.ndarray]:
        """
        Get next frame from stream with FPS control.
        
        Returns:
            Frame as numpy array, or None if not available.
        """
        if not self.connected or self.cap is None:
            return None
            
        # FPS control
        current_time = asyncio.get_event_loop().time()
        if current_time - self._last_frame_time < self._frame_interval:
            return None
            
        try:
            # Run blocking read in thread pool
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(
                None,
                self.cap.read
            )
            
            if ret and frame is not None:
                self._last_frame_time = current_time
                
                # Resize if needed
                if frame.shape[1] != self.settings.frame_width or \
                   frame.shape[0] != self.settings.frame_height:
                    frame = cv2.resize(
                        frame,
                        (self.settings.frame_width, self.settings.frame_height)
                    )
                    
                return frame
            else:
                logger.warning("Failed to read frame, attempting reconnect...")
                await self._reconnect()
                return None
                
        except Exception as e:
            logger.error(f"Frame read error: {e}")
            return None
            
    async def _reconnect(self) -> None:
        """Attempt to reconnect to stream."""
        self.connected = False
        if self.cap is not None:
            self.cap.release()
            
        await asyncio.sleep(1)
        await self.connect()
        
    async def disconnect(self) -> None:
        """Disconnect from stream."""
        self.connected = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info("Disconnected from RTSP stream")
