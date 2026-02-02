"""
Video File Client for processing local video files.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

import cv2
import numpy as np

from config.settings import Settings


logger = logging.getLogger(__name__)


class VideoFileClient:
    """
    Video file client for processing local video files.
    
    Processes video frame by frame with progress tracking
    and automatic completion detection.
    """
    
    def __init__(self, file_path: str, settings: Settings):
        self.file_path = file_path
        self.settings = settings
        self.cap: Optional[cv2.VideoCapture] = None
        self.connected = False
        
        # Progress tracking
        self.total_frames = 0
        self.current_frame = 0
        self._frame_interval = 1.0 / settings.fps
        self._last_frame_time = 0.0
        
    async def connect(self) -> bool:
        """
        Open video file for processing.
        
        Returns:
            True if file opened successfully, False otherwise.
        """
        try:
            if not Path(self.file_path).exists():
                logger.error(f"Video file not found: {self.file_path}")
                return False
                
            # Run blocking OpenCV operation in thread pool
            loop = asyncio.get_event_loop()
            self.cap = await loop.run_in_executor(
                None,
                self._create_capture
            )
            
            if self.cap is not None and self.cap.isOpened():
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.current_frame = 0
                self.connected = True
                logger.info(f"Video file opened: {self.file_path} ({self.total_frames} frames)")
                return True
            else:
                logger.error(f"Failed to open video file: {self.file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Video file error: {e}")
            return False
            
    def _create_capture(self) -> cv2.VideoCapture:
        """Create OpenCV VideoCapture object."""
        cap = cv2.VideoCapture(self.file_path)
        return cap
        
    async def get_frame(self) -> Optional[np.ndarray]:
        """
        Get next frame from video file with FPS control.
        
        Returns:
            Frame as numpy array, or None if video ended or not available.
        """
        if not self.connected or self.cap is None:
            return None
            
        # Check if video ended
        if self.current_frame >= self.total_frames:
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
                self.current_frame += 1
                
                # Resize if needed
                if frame.shape[1] != self.settings.frame_width or \
                   frame.shape[0] != self.settings.frame_height:
                    frame = cv2.resize(
                        frame,
                        (self.settings.frame_width, self.settings.frame_height)
                    )
                    
                return frame
            else:
                # Video ended
                logger.info("Video processing complete")
                return None
                
        except Exception as e:
            logger.error(f"Frame read error: {e}")
            return None
            
    @property
    def progress(self) -> float:
        """Return processing progress 0-100."""
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100
        
    @property
    def is_complete(self) -> bool:
        """Check if video processing is complete."""
        return self.current_frame >= self.total_frames and self.total_frames > 0
        
    async def disconnect(self) -> None:
        """Close video file."""
        self.connected = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info("Video file closed")
