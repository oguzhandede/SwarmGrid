"""
SwarmGrid Edge Agent - Main Entry Point

RTSP kameralardan feature extraction yaparak backend'e telemetri gönderir.
Zone polygon desteği, device provisioning ve OTA update içerir.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional, List

import uvicorn

from config.settings import Settings
from ingestion.rtsp_client import RTSPClient
from features.feature_builder import FeatureBuilder, TelemetryPayload
from transport.backend_client import BackendClient
from transport.zone_sync_client import ZoneSyncClient
from zones.zone_manager import ZoneManager, Zone
from provisioning.device_provisioning import DeviceProvisioning
from update.update_manager import UpdateManager
from api.health import create_app
from api.stream_server import StreamServer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeAgent:
    """Main Edge Agent orchestrator with full feature support."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.running = False
        
        # Core components
        self.rtsp_client = RTSPClient(settings)
        self.feature_builder = FeatureBuilder(settings)
        self.backend_client = BackendClient(settings)
        self.stream_server = StreamServer(fps=settings.fps)
        
        # Zone management
        self.zone_manager = ZoneManager()
        self.zone_sync_client: Optional[ZoneSyncClient] = None
        
        # Device provisioning
        self.device_provisioning = DeviceProvisioning(settings)
        
        # Update manager (initialized after provisioning)
        self.update_manager: Optional[UpdateManager] = None
        
        # Active zone for processing
        self._active_zone: Optional[Zone] = None
        self._zone_mask = None
        
    async def _initialize(self) -> bool:
        """Initialize all components before starting."""
        logger.info("Initializing Edge Agent components...")
        
        # Step 1: Device Provisioning
        if self.settings.device_provisioning.enabled:
            logger.info("Starting device provisioning...")
            result = await self.device_provisioning.ensure_registered()
            
            if not result.success:
                logger.error(f"Device provisioning failed: {result.message}")
                # Continue anyway for development
            else:
                logger.info(f"Device registered: {result.device_id}")
                
        # Step 2: Initialize Update Manager
        self.update_manager = UpdateManager(
            self.settings, 
            self.device_provisioning.device_id
        )
        
        # Step 3: Check for updates
        if self.settings.update.enabled:
            update_result = await self.update_manager.check_for_updates()
            if update_result.update_available:
                logger.info(f"Update available: {update_result.latest_version}")
                if update_result.is_required:
                    logger.warning("Required update pending!")
                    
        # Step 4: Initialize Zone Sync
        self.zone_sync_client = ZoneSyncClient(
            self.settings,
            self.zone_manager
        )
        
        # Step 5: Sync zones from backend
        if self.settings.zone_sync.enabled:
            logger.info("Syncing zones from backend...")
            zones = await self.zone_sync_client.sync_zones()
            logger.info(f"Synced {len(zones)} zones")
            
            # Set active zone if available
            if zones:
                self._active_zone = zones[0]
                self._update_zone_mask()
                
        return True
        
    def _update_zone_mask(self) -> None:
        """Update zone mask for feature extraction."""
        if self._active_zone is None:
            self._zone_mask = None
            return
            
        frame_shape = (self.settings.frame_height, self.settings.frame_width)
        self._zone_mask = self._active_zone.get_mask(frame_shape)
        logger.info(f"Zone mask updated for: {self._active_zone.zone_id}")
        
    async def start(self):
        """Start the edge agent processing loop."""
        self.running = True
        logger.info(f"Starting Edge Agent for camera: {self.settings.camera_id}")
        
        # Initialize components
        if not await self._initialize():
            logger.error("Initialization failed")
            return
            
        # Connect to RTSP stream
        if not await self.rtsp_client.connect():
            logger.error("Failed to connect to RTSP stream")
            return
            
        logger.info("Connected to RTSP stream")
        
        # Start background tasks
        background_tasks = []
        
        # Heartbeat loop
        if self.settings.device_provisioning.enabled:
            background_tasks.append(
                asyncio.create_task(self.device_provisioning.start_heartbeat_loop())
            )
            
        # Zone sync loop
        if self.settings.zone_sync.enabled and self.zone_sync_client:
            background_tasks.append(
                asyncio.create_task(self.zone_sync_client.start_background_sync())
            )
            
        # Update check loop
        if self.settings.update.enabled and self.update_manager:
            background_tasks.append(
                asyncio.create_task(self.update_manager.start_background_check())
            )
        
        # Main processing loop with exponential backoff
        consecutive_errors = 0
        max_backoff = 60  # Maximum backoff in seconds
        base_backoff = 1  # Base backoff in seconds
        
        while self.running:
            try:
                # Get frame from camera
                frame = await self.rtsp_client.get_frame()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process each zone (or full frame if no zones)
                await self._process_frame(frame)
                
                # Reset error counter on success
                consecutive_errors = 0
                    
            except (ConnectionError, TimeoutError, OSError) as e:
                # Network/connection errors - use exponential backoff
                consecutive_errors += 1
                backoff_time = min(base_backoff * (2 ** consecutive_errors), max_backoff)
                logger.warning(f"Connection error (attempt {consecutive_errors}): {e}. Retrying in {backoff_time}s...")
                await asyncio.sleep(backoff_time)
                
                # Try to reconnect after several failures
                if consecutive_errors >= 3:
                    logger.info("Attempting to reconnect to RTSP stream...")
                    await self.rtsp_client.disconnect()
                    if await self.rtsp_client.connect():
                        logger.info("Reconnected successfully")
                        consecutive_errors = 0
                    else:
                        logger.error("Reconnection failed")
                        
            except ValueError as e:
                # Data processing errors - log and continue
                logger.error(f"Data processing error: {e}")
                await asyncio.sleep(0.5)
                
            except Exception as e:
                # Unexpected errors - log full traceback
                logger.exception(f"Unexpected processing error: {e}")
                consecutive_errors += 1
                await asyncio.sleep(min(base_backoff * consecutive_errors, max_backoff))
                
        # Cancel background tasks
        for task in background_tasks:
            task.cancel()
            
    async def _process_frame(self, frame) -> None:
        """Process a single frame, optionally with zone filtering."""
        zones_to_process = self.zone_manager.get_all_zones()
        
        if not zones_to_process:
            # No zones defined, process full frame
            await self._extract_and_send(frame, None, self.settings.zone_id)
        else:
            # Process each zone
            for zone in zones_to_process:
                frame_shape = (frame.shape[0], frame.shape[1])
                zone_mask = zone.get_mask(frame_shape)
                await self._extract_and_send(frame, zone_mask, zone.zone_id)
                
    async def _extract_and_send(
        self, 
        frame, 
        zone_mask, 
        zone_id: str
    ) -> None:
        """Extract features and send telemetry."""
        # Extract features with zone mask
        features = self.feature_builder.extract(frame, zone_mask)
        
        # Update stream server with frame and metrics
        metrics = {}
        if features:
            # Override zone_id if processing specific zone
            if zone_id != self.settings.zone_id:
                features = TelemetryPayload(
                    tenant_id=features.tenant_id,
                    site_id=features.site_id,
                    camera_id=features.camera_id,
                    zone_id=zone_id,
                    timestamp=features.timestamp,
                    density=features.density,
                    avg_speed=features.avg_speed,
                    speed_variance=features.speed_variance,
                    flow_entropy=features.flow_entropy,
                    alignment=features.alignment,
                    bottleneck_index=features.bottleneck_index
                )
            
            metrics = {
                'density': features.density,
                'flow_entropy': features.flow_entropy,
                'avg_speed': features.avg_speed,
                'zone_id': zone_id,
                'risk_level': 'Kritik' if features.density > 0.75 else (
                    'Dikkat' if features.density > 0.5 else 'Normal'
                )
            }
            
            # Send to backend
            await self.backend_client.send_telemetry(features)
            
        # Update stream server (for first/main zone only)
        if zone_id == self.settings.zone_id or not self.zone_manager.get_all_zones():
            self.stream_server.update_frame(frame, metrics)
                
    async def stop(self):
        """Stop the edge agent gracefully."""
        logger.info("Stopping Edge Agent...")
        self.running = False
        
        # Stop components
        self.stream_server.stop()
        await self.rtsp_client.disconnect()
        await self.backend_client.close()
        
        if self.zone_sync_client:
            await self.zone_sync_client.stop()
            
        if self.device_provisioning:
            await self.device_provisioning.stop()
            
        if self.update_manager:
            await self.update_manager.stop()
            
        logger.info("Edge Agent stopped")


async def main():
    """Main entry point."""
    # Load settings
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    settings = Settings.from_yaml(config_path)
    
    # Create agent
    agent = EdgeAgent(settings)
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(agent.stop()))
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    # Start API server in background
    api_app = create_app(agent)
    api_config = uvicorn.Config(
        api_app, 
        host=settings.api_host, 
        port=settings.api_port,
        log_level="warning"
    )
    api_server = uvicorn.Server(api_config)
    
    # Run both agent and API server
    await asyncio.gather(
        agent.start(),
        api_server.serve()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        sys.exit(0)
