"""
Configuration management for Edge Agent.
"""

import os
from pathlib import Path
from typing import Any, Callable, TypeVar

import yaml
from pydantic import BaseModel, Field


T = TypeVar("T")


def _apply_env_override(
    data: dict, key_path: list[str], env_var: str, cast: Callable[[str], T] = str
) -> None:
    value = os.getenv(env_var)
    if value is None or value == "":
        return
    try:
        parsed: Any = cast(value)
    except (TypeError, ValueError):
        parsed = value
    target = data
    for key in key_path[:-1]:
        if key not in target or not isinstance(target[key], dict):
            target[key] = {}
        target = target[key]
    target[key_path[-1]] = parsed


class OpticalFlowConfig(BaseModel):
    """Optical flow algorithm configuration."""
    method: str = "farneback"
    pyr_scale: float = 0.5
    levels: int = 3
    winsize: int = 15
    iterations: int = 3
    poly_n: int = 5
    poly_sigma: float = 1.2


class TelemetryConfig(BaseModel):
    """Telemetry transmission configuration."""
    send_interval_seconds: int = 1
    batch_size: int = 5
    retry_attempts: int = 3
    timeout_seconds: int = 5


class ApiConfig(BaseModel):
    """Local API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"


class ZoneSyncConfig(BaseModel):
    """Zone sync configuration."""
    enabled: bool = True
    sync_interval_seconds: int = 60
    retry_attempts: int = 3
    timeout_seconds: int = 10


class DeviceProvisioningConfig(BaseModel):
    """Device provisioning configuration."""
    enabled: bool = True
    heartbeat_interval_seconds: int = 60
    device_store_path: str = "config/device.json"


class UpdateConfig(BaseModel):
    """OTA update configuration."""
    enabled: bool = True
    check_interval_seconds: int = 3600  # 1 hour
    auto_apply: bool = False  # Require manual approval for updates


class Settings(BaseModel):
    """Main settings class for Edge Agent."""
    
    # Connection
    rtsp_url: str = Field(default="rtsp://localhost:554/stream")
    backend_url: str = Field(default="http://localhost:5000")
    
    # Identification
    tenant_id: str = Field(default="demo")
    site_id: str = Field(default="site-01")
    camera_id: str = Field(default="cam-01")
    zone_id: str = Field(default="zone-01")
    
    # Processing
    fps: int = Field(default=5, ge=1, le=30)
    frame_width: int = Field(default=640)
    frame_height: int = Field(default=480)
    
    # Sub-configurations
    optical_flow: OpticalFlowConfig = Field(default_factory=OpticalFlowConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    zone_sync: ZoneSyncConfig = Field(default_factory=ZoneSyncConfig)
    device_provisioning: DeviceProvisioningConfig = Field(default_factory=DeviceProvisioningConfig)
    update: UpdateConfig = Field(default_factory=UpdateConfig)
    
    @property
    def api_host(self) -> str:
        return self.api.host
    
    @property
    def api_port(self) -> int:
        return self.api.port
    
    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from YAML file."""
        data = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            data = {}

        _apply_env_override(data, ["rtsp_url"], "RTSP_URL")
        _apply_env_override(data, ["backend_url"], "BACKEND_URL")
        _apply_env_override(data, ["tenant_id"], "TENANT_ID")
        _apply_env_override(data, ["site_id"], "SITE_ID")
        _apply_env_override(data, ["camera_id"], "CAMERA_ID")
        _apply_env_override(data, ["zone_id"], "ZONE_ID")
        _apply_env_override(data, ["fps"], "FPS", int)
        _apply_env_override(data, ["frame_width"], "FRAME_WIDTH", int)
        _apply_env_override(data, ["frame_height"], "FRAME_HEIGHT", int)
        _apply_env_override(data, ["api", "port"], "API_PORT", int)
        _apply_env_override(data, ["logging", "level"], "LOG_LEVEL")

        return cls(**data)
    
    def to_yaml(self, path: Path) -> None:
        """Save settings to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
