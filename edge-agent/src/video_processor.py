"""
Video Processor - Standalone script for processing video files.

This script is called by the backend to process uploaded video files.
It sends progress updates and telemetry to the backend.

Usage:
    python video_processor.py <video_path> <source_id> <zone_id>
"""

import asyncio
import sys
import logging
from pathlib import Path

import httpx
import cv2

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from ingestion.video_file_client import VideoFileClient
from features.feature_builder import FeatureBuilder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_video(video_path: str, source_id: str, zone_id: str):
    """
    Process a video file and send telemetry to backend.
    
    Args:
        video_path: Path to the video file
        source_id: Source ID for progress tracking
        zone_id: Zone ID for telemetry
    """
    # Load settings
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    settings = Settings.from_yaml(config_path)
    
    # Override zone_id from argument
    settings.zone_id = zone_id
    
    # Initialize components
    video_client = VideoFileClient(video_path, settings)
    feature_builder = FeatureBuilder(settings)
    
    backend_url = settings.backend_url
    
    logger.info(f"Starting video processing: {video_path}")
    logger.info(f"Source ID: {source_id}, Zone ID: {zone_id}")
    
    # Connect to video file
    if not await video_client.connect():
        await report_error(backend_url, source_id, "Failed to open video file")
        return
        
    async with httpx.AsyncClient() as client:
        last_progress = -1
        frame_count = 0
        
        while True:
            # Get next frame
            frame = await video_client.get_frame()
            
            if frame is None:
                if video_client.is_complete:
                    break
                await asyncio.sleep(0.01)
                continue
                
            frame_count += 1
            
            # Extract features
            features = feature_builder.extract(frame)
            
            if features:
                # Send telemetry to backend
                try:
                    await client.post(
                        f"{backend_url}/api/telemetry/ingest",
                        json=[features.to_dict()],
                        timeout=5.0
                    )
                except Exception as e:
                    logger.warning(f"Telemetry send failed: {e}")
            
            # Report progress every 5%
            current_progress = int(video_client.progress)
            if current_progress != last_progress and current_progress % 5 == 0:
                await report_progress(backend_url, source_id, current_progress)
                last_progress = current_progress
                logger.info(f"Progress: {current_progress}%")
    
    # Mark as complete
    await report_complete(backend_url, source_id)
    logger.info(f"Video processing complete. Frames processed: {frame_count}")
    
    # Cleanup
    await video_client.disconnect()


async def report_progress(backend_url: str, source_id: str, progress: float):
    """Report progress to backend."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{backend_url}/api/source/{source_id}/progress",
                json={
                    "sourceId": source_id,
                    "status": 1,  # Processing
                    "progress": progress,
                    "message": f"Processing: {progress}%"
                },
                timeout=5.0
            )
    except Exception as e:
        logger.warning(f"Progress report failed: {e}")


async def report_complete(backend_url: str, source_id: str):
    """Report completion to backend."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{backend_url}/api/source/{source_id}/progress",
                json={
                    "sourceId": source_id,
                    "status": 2,  # Completed
                    "progress": 100,
                    "message": "Processing complete"
                },
                timeout=5.0
            )
    except Exception as e:
        logger.warning(f"Completion report failed: {e}")


async def report_error(backend_url: str, source_id: str, error_message: str):
    """Report error to backend."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{backend_url}/api/source/{source_id}/progress",
                json={
                    "sourceId": source_id,
                    "status": 3,  # Error
                    "progress": 0,
                    "message": error_message
                },
                timeout=5.0
            )
    except Exception as e:
        logger.warning(f"Error report failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python video_processor.py <video_path> <source_id> <zone_id>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    source_id = sys.argv[2]
    zone_id = sys.argv[3]
    
    asyncio.run(process_video(video_path, source_id, zone_id))
