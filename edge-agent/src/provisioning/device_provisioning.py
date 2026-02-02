"""
Device Provisioning - Edge agent registration and authentication.

Handles device registration, token validation, and heartbeat.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

import httpx

from config.settings import Settings
from provisioning.device_store import DeviceStore, DeviceCredentials


logger = logging.getLogger(__name__)


@dataclass
class ProvisioningResult:
    """Result of provisioning operation."""
    success: bool
    message: str
    device_id: Optional[str] = None


class DeviceProvisioning:
    """
    Device registration and authentication manager.
    
    Flow:
    1. Check for existing credentials in device store
    2. If not exists, generate new device_id and secret
    3. Register with backend
    4. Store credentials locally
    5. Add auth headers to all requests
    6. Send periodic heartbeats
    """
    
    VERSION = "1.0.0"  # Current agent version
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = settings.device_provisioning
        self.base_url = settings.backend_url.rstrip("/")
        
        # Initialize device store
        store_path = Path(settings.device_provisioning.device_store_path)
        if not store_path.is_absolute():
            store_path = Path(__file__).parent.parent.parent / store_path
        self.device_store = DeviceStore(store_path)
        
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._credentials: Optional[DeviceCredentials] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(10.0),
                headers={"Content-Type": "application/json"}
            )
        return self._client
        
    async def ensure_registered(self) -> ProvisioningResult:
        """
        Ensure device is registered with backend.
        
        Returns:
            ProvisioningResult with success status
        """
        if not self.config.enabled:
            logger.info("Device provisioning disabled")
            return ProvisioningResult(True, "Provisioning disabled")
            
        # Try to load existing credentials
        self._credentials = self.device_store.load()
        
        if self._credentials is not None and self._credentials.registered:
            # Validate existing credentials
            if await self.validate_token():
                logger.info(f"Device validated: {self._credentials.device_id[:8]}...")
                return ProvisioningResult(
                    True, 
                    "Device already registered",
                    self._credentials.device_id
                )
            else:
                logger.warning("Existing credentials invalid, re-registering...")
                
        # Generate new credentials if needed
        if self._credentials is None:
            device_id = DeviceStore.generate_device_id()
            device_secret = DeviceStore.generate_device_secret()
            
            self._credentials = DeviceCredentials(
                device_id=device_id,
                device_secret=device_secret,
                tenant_id=self.settings.tenant_id,
                site_id=self.settings.site_id,
                registered=False
            )
            
        # Register with backend
        return await self._register_device()
        
    async def _register_device(self) -> ProvisioningResult:
        """Register device with backend."""
        if self._credentials is None:
            return ProvisioningResult(False, "No credentials available")
            
        try:
            client = await self._get_client()
            
            response = await client.post(
                "/api/device/register",
                json={
                    "deviceId": self._credentials.device_id,
                    "deviceSecret": self._credentials.device_secret,
                    "tenantId": self._credentials.tenant_id,
                    "siteId": self._credentials.site_id,
                    "cameraId": self.settings.camera_id,
                    "name": f"Edge Agent - {self.settings.camera_id}",
                    "agentVersion": self.VERSION
                }
            )
            
            if response.status_code in (200, 201):
                # Registration successful
                self._credentials.registered = True
                self._credentials.registered_at = datetime.now(timezone.utc).isoformat()
                
                # Save credentials
                self.device_store.save(self._credentials)
                
                logger.info(f"Device registered: {self._credentials.device_id}")
                return ProvisioningResult(
                    True,
                    "Device registered successfully",
                    self._credentials.device_id
                )
            else:
                error_msg = response.text
                logger.error(f"Registration failed: {response.status_code} - {error_msg}")
                return ProvisioningResult(False, f"Registration failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return ProvisioningResult(False, f"Registration error: {e}")
            
    async def validate_token(self) -> bool:
        """
        Validate current device token with backend.
        
        Returns:
            True if token is valid
        """
        if self._credentials is None:
            return False
            
        try:
            client = await self._get_client()
            
            response = await client.post(
                "/api/device/validate",
                json={
                    "deviceId": self._credentials.device_id,
                    "deviceSecret": self._credentials.device_secret
                }
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
            
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to backend.
        
        Returns:
            True if heartbeat was successful
        """
        if self._credentials is None:
            return False
            
        try:
            client = await self._get_client()
            
            response = await client.post(
                "/api/device/heartbeat",
                json={
                    "deviceId": self._credentials.device_id,
                    "deviceSecret": self._credentials.device_secret,
                    "agentVersion": self.VERSION
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for updates
                if data.get("updateAvailable"):
                    logger.info("Update available from backend")
                    
                return True
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
            
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of auth headers
        """
        if self._credentials is None:
            return {}
            
        return {
            "X-Device-Id": self._credentials.device_id,
            "X-Device-Secret": self._credentials.device_secret
        }
        
    async def start_heartbeat_loop(self, interval: Optional[int] = None) -> None:
        """
        Start background heartbeat loop.
        
        Args:
            interval: Heartbeat interval in seconds
        """
        if not self.config.enabled:
            return
            
        heartbeat_interval = interval or self.config.heartbeat_interval_seconds
        self._running = True
        
        logger.info(f"Starting heartbeat loop (interval: {heartbeat_interval}s)")
        
        while self._running:
            try:
                await asyncio.sleep(heartbeat_interval)
                if self._running:
                    await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                
    async def stop(self) -> None:
        """Stop heartbeat loop and close client."""
        self._running = False
        
        if self._client:
            await self._client.aclose()
            self._client = None
            
        logger.info("Device provisioning stopped")
        
    @property
    def device_id(self) -> Optional[str]:
        """Get current device ID."""
        return self._credentials.device_id if self._credentials else None
        
    @property
    def is_registered(self) -> bool:
        """Check if device is registered."""
        return self._credentials is not None and self._credentials.registered
