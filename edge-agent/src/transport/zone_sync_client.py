"""
Zone Sync Client - Fetches zone definitions from backend.

Syncs zone polygons and thresholds from the Core Backend to enable
zone-aware feature extraction.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any

import httpx

from config.settings import Settings
from zones.zone_manager import Zone, ZoneManager


logger = logging.getLogger(__name__)


@dataclass
class ZoneSyncConfig:
    """Zone sync configuration."""
    enabled: bool = True
    sync_interval_seconds: int = 60
    retry_attempts: int = 3
    timeout_seconds: int = 10


class ZoneSyncClient:
    """
    Backend'den zone tanımlarını çeker ve ZoneManager'a yükler.
    
    Features:
    - Periyodik sync (default: 60 saniye)
    - Başlangıçta otomatik sync
    - Backend bağlantı hatalarında retry
    - Zone değişiklik algılama
    """
    
    def __init__(
        self, 
        settings: Settings, 
        zone_manager: ZoneManager,
        config: Optional[ZoneSyncConfig] = None
    ):
        self.settings = settings
        self.zone_manager = zone_manager
        self.config = config or ZoneSyncConfig()
        self.base_url = settings.backend_url.rstrip("/")
        
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._last_sync_hash: Optional[str] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers={
                    "Content-Type": "application/json",
                    "X-Camera-Id": self.settings.camera_id
                }
            )
        return self._client
        
    async def sync_zones(self) -> List[Zone]:
        """
        Fetch zones from backend and update ZoneManager.
        
        Returns:
            List of synced Zone objects
        """
        if not self.config.enabled:
            logger.debug("Zone sync disabled")
            return []
            
        try:
            client = await self._get_client()
            
            # Fetch zones for this camera
            for attempt in range(self.config.retry_attempts):
                try:
                    response = await client.get(
                        f"/api/zone/by-camera/{self.settings.camera_id}"
                    )
                    
                    if response.status_code == 200:
                        zones_data = response.json()
                        return self._process_zones(zones_data)
                    elif response.status_code == 404:
                        logger.info(f"No zones found for camera {self.settings.camera_id}")
                        return []
                    else:
                        logger.warning(f"Zone sync failed: {response.status_code}")
                        
                except httpx.TimeoutException:
                    logger.warning(f"Zone sync timeout, attempt {attempt + 1}")
                    await asyncio.sleep(2 ** attempt)
                except httpx.ConnectError:
                    logger.warning(f"Zone sync connection error, attempt {attempt + 1}")
                    await asyncio.sleep(2 ** attempt)
                    
            logger.error(f"Zone sync failed after {self.config.retry_attempts} attempts")
            return []
            
        except Exception as e:
            logger.error(f"Zone sync error: {e}")
            return []
            
    def _process_zones(self, zones_data: List[Dict[str, Any]]) -> List[Zone]:
        """Process zone data from backend and update ZoneManager."""
        synced_zones = []
        
        for zone_data in zones_data:
            try:
                # Parse polygon points
                polygon_points = []
                if zone_data.get("polygon"):
                    for point in zone_data["polygon"]:
                        x = int(point.get("x", 0))
                        y = int(point.get("y", 0))
                        polygon_points.append((x, y))
                
                # Create Zone object
                zone = Zone(
                    zone_id=zone_data.get("zoneId", ""),
                    name=zone_data.get("name", ""),
                    polygon=polygon_points,
                    max_capacity=zone_data.get("maxCapacity", 100),
                    yellow_threshold=zone_data.get("yellowThreshold", 0.5),
                    red_threshold=zone_data.get("redThreshold", 0.75),
                    zone_type=self._determine_zone_type(zone_data)
                )
                
                # Add to manager
                self.zone_manager.add_zone(zone)
                synced_zones.append(zone)
                
            except Exception as e:
                logger.error(f"Error processing zone {zone_data.get('zoneId')}: {e}")
                
        logger.info(f"Synced {len(synced_zones)} zones from backend")
        return synced_zones
        
    def _determine_zone_type(self, zone_data: Dict[str, Any]) -> str:
        """Determine zone type from backend data."""
        name = zone_data.get("name", "").lower()
        description = zone_data.get("description", "").lower() if zone_data.get("description") else ""
        
        if "çıkış" in name or "exit" in name or "çıkış" in description:
            return "exit"
        elif "giriş" in name or "entrance" in name or "giriş" in description:
            return "entrance"
        elif "darboğaz" in name or "bottleneck" in name or "dar" in description:
            return "bottleneck"
        else:
            return "general"
            
    async def start_background_sync(self, interval: Optional[int] = None) -> None:
        """
        Start background zone synchronization.
        
        Args:
            interval: Sync interval in seconds (default: from config)
        """
        if not self.config.enabled:
            logger.info("Zone sync disabled, skipping background sync")
            return
            
        sync_interval = interval or self.config.sync_interval_seconds
        self._running = True
        
        logger.info(f"Starting background zone sync (interval: {sync_interval}s)")
        
        while self._running:
            try:
                await asyncio.sleep(sync_interval)
                if self._running:
                    await self.sync_zones()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background sync error: {e}")
                
    async def stop(self) -> None:
        """Stop background sync and close client."""
        self._running = False
        
        if self._client:
            await self._client.aclose()
            self._client = None
            
        logger.info("Zone sync client stopped")
        
    async def get_zone_for_point(self, x: float, y: float) -> Optional[Zone]:
        """
        Get the zone containing a specific point.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Zone containing the point, or None
        """
        for zone in self.zone_manager.get_all_zones():
            if zone.contains_point(x, y):
                return zone
        return None
