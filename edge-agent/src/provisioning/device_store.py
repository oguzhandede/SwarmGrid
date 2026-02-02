"""
Device Store - Secure storage for device credentials.

Stores device ID and secret in a local JSON file.
"""

import json
import logging
import secrets
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import uuid


logger = logging.getLogger(__name__)


@dataclass
class DeviceCredentials:
    """Device authentication credentials."""
    device_id: str
    device_secret: str
    tenant_id: str
    site_id: str
    registered: bool = False
    registered_at: Optional[str] = None


class DeviceStore:
    """
    Secure storage for device credentials.
    
    Stores device_id and device_secret in a local JSON file.
    The file should be protected and excluded from version control.
    """
    
    def __init__(self, store_path: Path):
        self.store_path = store_path
        self._credentials: Optional[DeviceCredentials] = None
        
    def load(self) -> Optional[DeviceCredentials]:
        """
        Load credentials from store.
        
        Returns:
            DeviceCredentials if exists, None otherwise
        """
        if self._credentials is not None:
            return self._credentials
            
        if not self.store_path.exists():
            logger.debug(f"Device store not found: {self.store_path}")
            return None
            
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._credentials = DeviceCredentials(**data)
            logger.info(f"Loaded device credentials: {self._credentials.device_id[:8]}...")
            return self._credentials
            
        except Exception as e:
            logger.error(f"Failed to load device credentials: {e}")
            return None
            
    def save(self, credentials: DeviceCredentials) -> bool:
        """
        Save credentials to store.
        
        Args:
            credentials: Device credentials to save
            
        Returns:
            True if saved successfully
        """
        try:
            # Ensure parent directory exists
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(asdict(credentials), f, indent=2)
                
            self._credentials = credentials
            logger.info(f"Saved device credentials: {credentials.device_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save device credentials: {e}")
            return False
            
    def clear(self) -> bool:
        """
        Clear stored credentials.
        
        Returns:
            True if cleared successfully
        """
        try:
            if self.store_path.exists():
                self.store_path.unlink()
                
            self._credentials = None
            logger.info("Device credentials cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear device credentials: {e}")
            return False
            
    def exists(self) -> bool:
        """Check if credentials exist."""
        return self.store_path.exists()
        
    @staticmethod
    def generate_device_id() -> str:
        """Generate a unique device ID."""
        return f"edge-{uuid.uuid4().hex[:12]}"
        
    @staticmethod
    def generate_device_secret() -> str:
        """Generate a secure device secret."""
        return secrets.token_urlsafe(32)
