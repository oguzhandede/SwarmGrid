"""
Health and status endpoints for Edge Agent.

Includes version info, device status, zone info, and update endpoints.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List

from fastapi import FastAPI
from pydantic import BaseModel


if TYPE_CHECKING:
    from main import EdgeAgent


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    camera_id: str
    zone_id: str
    connected: bool


class StatusResponse(BaseModel):
    """Detailed status response."""
    status: str
    timestamp: str
    camera_id: str
    zone_id: str
    tenant_id: str
    site_id: str
    rtsp_connected: bool
    backend_url: str
    fps_target: int
    # New fields
    agent_version: str
    device_id: Optional[str]
    device_registered: bool
    zones_synced: int
    update_available: bool
    last_update_check: Optional[str]


class VersionResponse(BaseModel):
    """Agent version information."""
    version: str
    device_id: Optional[str]
    device_registered: bool
    update_available: bool
    pending_version: Optional[str]
    last_update_check: Optional[str]


class ZoneInfoResponse(BaseModel):
    """Zone information."""
    zone_id: str
    name: str
    zone_type: str
    max_capacity: int
    yellow_threshold: float
    red_threshold: float
    polygon_points: int


def create_app(agent: "EdgeAgent") -> FastAPI:
    """
    Create FastAPI app for health and status endpoints.
    
    Args:
        agent: Edge Agent instance for status queries
        
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="SwarmGrid Edge Agent",
        description="Local health, configuration, and update API",
        version="1.0.0"
    )
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Basic health check endpoint."""
        return HealthResponse(
            status="healthy" if agent.running else "stopped",
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id=agent.settings.camera_id,
            zone_id=agent.settings.zone_id,
            connected=agent.rtsp_client.connected
        )
        
    @app.get("/status", response_model=StatusResponse)
    async def get_status():
        """Detailed status endpoint."""
        # Get update info
        update_available = False
        last_update_check = None
        
        if agent.update_manager:
            update_available = agent.update_manager.has_pending_update
            if agent.update_manager.last_check:
                last_update_check = agent.update_manager.last_check.isoformat()
        
        return StatusResponse(
            status="running" if agent.running else "stopped",
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id=agent.settings.camera_id,
            zone_id=agent.settings.zone_id,
            tenant_id=agent.settings.tenant_id,
            site_id=agent.settings.site_id,
            rtsp_connected=agent.rtsp_client.connected,
            backend_url=agent.settings.backend_url,
            fps_target=agent.settings.fps,
            # New fields
            agent_version="1.0.0",
            device_id=agent.device_provisioning.device_id if agent.device_provisioning else None,
            device_registered=agent.device_provisioning.is_registered if agent.device_provisioning else False,
            zones_synced=len(agent.zone_manager.get_all_zones()),
            update_available=update_available,
            last_update_check=last_update_check
        )
    
    @app.get("/version", response_model=VersionResponse)
    async def get_version():
        """Get agent version and update status."""
        update_available = False
        pending_version = None
        last_update_check = None
        
        if agent.update_manager:
            update_available = agent.update_manager.has_pending_update
            pending_version = agent.update_manager.pending_version
            if agent.update_manager.last_check:
                last_update_check = agent.update_manager.last_check.isoformat()
        
        return VersionResponse(
            version="1.0.0",
            device_id=agent.device_provisioning.device_id if agent.device_provisioning else None,
            device_registered=agent.device_provisioning.is_registered if agent.device_provisioning else False,
            update_available=update_available,
            pending_version=pending_version,
            last_update_check=last_update_check
        )
    
    @app.get("/zones", response_model=List[ZoneInfoResponse])
    async def list_zones():
        """List synced zones."""
        zones = agent.zone_manager.get_all_zones()
        return [
            ZoneInfoResponse(
                zone_id=z.zone_id,
                name=z.name,
                zone_type=z.zone_type,
                max_capacity=z.max_capacity,
                yellow_threshold=z.yellow_threshold,
                red_threshold=z.red_threshold,
                polygon_points=len(z.polygon)
            )
            for z in zones
        ]
    
    @app.post("/zones/sync")
    async def sync_zones():
        """Manually trigger zone sync."""
        if agent.zone_sync_client:
            zones = await agent.zone_sync_client.sync_zones()
            return {"synced": len(zones), "zones": [z.zone_id for z in zones]}
        return {"error": "Zone sync not available"}
    
    @app.post("/update/check")
    async def check_update():
        """Manually trigger update check."""
        if agent.update_manager:
            result = await agent.update_manager.check_for_updates()
            return {
                "current_version": result.current_version,
                "latest_version": result.latest_version,
                "update_available": result.update_available,
                "is_required": result.is_required
            }
        return {"error": "Update manager not available"}
    
    @app.post("/update/apply")
    async def apply_update():
        """Apply pending update."""
        if agent.update_manager and agent.update_manager.has_pending_update:
            success = await agent.update_manager.apply_pending_update()
            return {
                "applied": success,
                "message": "Update applied. Restart recommended." if success else "Update failed"
            }
        return {"error": "No pending update"}
        
    @app.post("/reset")
    async def reset_features():
        """Reset feature extraction state."""
        agent.feature_builder.reset()
        return {"message": "Feature extractors reset"}
    
    # Add stream routes if stream server is available
    if hasattr(agent, 'stream_server'):
        from api.stream_server import add_stream_routes
        add_stream_routes(app, agent.stream_server)
        
    return app
