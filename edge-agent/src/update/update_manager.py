"""
Update Manager - OTA update checking and application.

Checks for updates from backend and applies config patches.
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
import yaml

from config.settings import Settings


logger = logging.getLogger(__name__)


@dataclass
class UpdateInfo:
    """Available update information."""
    version: str
    download_url: Optional[str]
    config_patch: Optional[Dict[str, Any]]
    checksum: Optional[str]
    is_required: bool
    release_notes: Optional[str] = None


@dataclass
class UpdateCheckResult:
    """Result of update check."""
    update_available: bool
    current_version: str
    latest_version: Optional[str]
    update_info: Optional[UpdateInfo] = None
    is_required: bool = False


class UpdateManager:
    """
    OTA update checking and application.
    
    Features:
    - Periodic update checks
    - Config-only patch updates
    - Version comparison
    - Update reporting to backend
    """
    
    CURRENT_VERSION = "1.0.0"
    
    def __init__(self, settings: Settings, device_id: Optional[str] = None):
        self.settings = settings
        self.config = settings.update
        self.base_url = settings.backend_url.rstrip("/")
        self.device_id = device_id
        
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._last_check: Optional[datetime] = None
        self._pending_update: Optional[UpdateInfo] = None
        
        # Config file path
        self.config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0),
                headers={"Content-Type": "application/json"}
            )
        return self._client
        
    async def check_for_updates(self) -> UpdateCheckResult:
        """
        Check for available updates from backend.
        
        Returns:
            UpdateCheckResult with update information
        """
        if not self.config.enabled:
            return UpdateCheckResult(
                update_available=False,
                current_version=self.CURRENT_VERSION,
                latest_version=None
            )
            
        try:
            client = await self._get_client()
            
            response = await client.get(
                "/api/update/check",
                params={
                    "currentVersion": self.CURRENT_VERSION,
                    "tenantId": self.settings.tenant_id
                }
            )
            
            self._last_check = datetime.now(timezone.utc)
            
            if response.status_code == 200:
                data = response.json()
                
                update_available = data.get("updateAvailable", False)
                latest_version = data.get("latestVersion")
                is_required = data.get("isRequired", False)
                
                update_info = None
                if update_available and data.get("update"):
                    update_data = data["update"]
                    
                    # Parse config patch if present
                    config_patch = None
                    if update_data.get("configPatch"):
                        try:
                            config_patch = json.loads(update_data["configPatch"])
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse config patch JSON")
                    
                    update_info = UpdateInfo(
                        version=update_data["version"],
                        download_url=update_data.get("downloadUrl"),
                        config_patch=config_patch,
                        checksum=update_data.get("checksum"),
                        is_required=update_data.get("isRequired", False),
                        release_notes=data.get("releaseNotes")
                    )
                    
                    self._pending_update = update_info
                    
                logger.info(
                    f"Update check: current={self.CURRENT_VERSION}, "
                    f"latest={latest_version}, available={update_available}"
                )
                
                return UpdateCheckResult(
                    update_available=update_available,
                    current_version=self.CURRENT_VERSION,
                    latest_version=latest_version,
                    update_info=update_info,
                    is_required=is_required
                )
            else:
                logger.warning(f"Update check failed: {response.status_code}")
                return UpdateCheckResult(
                    update_available=False,
                    current_version=self.CURRENT_VERSION,
                    latest_version=None
                )
                
        except Exception as e:
            logger.error(f"Update check error: {e}")
            return UpdateCheckResult(
                update_available=False,
                current_version=self.CURRENT_VERSION,
                latest_version=None
            )
            
    async def apply_config_update(self, config_patch: Dict[str, Any]) -> bool:
        """
        Apply config-only update.
        
        Args:
            config_patch: Dictionary of config changes to apply
            
        Returns:
            True if applied successfully
        """
        try:
            # Load current config
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    current_config = yaml.safe_load(f) or {}
            else:
                current_config = {}
                
            # Apply patch (deep merge)
            updated_config = self._deep_merge(current_config, config_patch)
            
            # Backup current config
            backup_path = self.config_path.with_suffix(".yaml.bak")
            if self.config_path.exists():
                with open(backup_path, "w", encoding="utf-8") as f:
                    yaml.dump(current_config, f, default_flow_style=False)
                    
            # Write updated config
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(updated_config, f, default_flow_style=False)
                
            logger.info("Config update applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply config update: {e}")
            return False
            
    def _deep_merge(self, base: Dict, patch: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in patch.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
        
    async def apply_pending_update(self) -> bool:
        """
        Apply pending update if available.
        
        Returns:
            True if update was applied (may require restart)
        """
        if self._pending_update is None:
            logger.info("No pending update to apply")
            return False
            
        update = self._pending_update
        success = False
        
        # Apply config patch if available
        if update.config_patch:
            success = await self.apply_config_update(update.config_patch)
            
        # Report update result
        await self._report_update(
            from_version=self.CURRENT_VERSION,
            to_version=update.version,
            success=success
        )
        
        if success:
            self._pending_update = None
            logger.info(f"Update to {update.version} applied. Restart recommended.")
            
        return success
        
    async def _report_update(
        self, 
        from_version: str, 
        to_version: str, 
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Report update result to backend."""
        if not self.device_id:
            return
            
        try:
            client = await self._get_client()
            
            await client.post(
                "/api/update/report",
                json={
                    "deviceId": self.device_id,
                    "fromVersion": from_version,
                    "toVersion": to_version,
                    "success": success,
                    "errorMessage": error_message
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to report update: {e}")
            
    async def start_background_check(self, interval: Optional[int] = None) -> None:
        """
        Start background update checking loop.
        
        Args:
            interval: Check interval in seconds
        """
        if not self.config.enabled:
            logger.info("Update checking disabled")
            return
            
        check_interval = interval or self.config.check_interval_seconds
        self._running = True
        
        logger.info(f"Starting update check loop (interval: {check_interval}s)")
        
        while self._running:
            try:
                await asyncio.sleep(check_interval)
                
                if self._running:
                    result = await self.check_for_updates()
                    
                    # Auto-apply if enabled and not required
                    if result.update_available and self.config.auto_apply:
                        if result.update_info and result.update_info.config_patch:
                            await self.apply_pending_update()
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Update check loop error: {e}")
                
    async def stop(self) -> None:
        """Stop update checking and close client."""
        self._running = False
        
        if self._client:
            await self._client.aclose()
            self._client = None
            
        logger.info("Update manager stopped")
        
    @property
    def last_check(self) -> Optional[datetime]:
        """Get timestamp of last update check."""
        return self._last_check
        
    @property
    def has_pending_update(self) -> bool:
        """Check if there's a pending update."""
        return self._pending_update is not None
        
    @property
    def pending_version(self) -> Optional[str]:
        """Get pending update version."""
        return self._pending_update.version if self._pending_update else None
