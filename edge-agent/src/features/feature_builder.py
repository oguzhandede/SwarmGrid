"""
Feature Builder - Aggregates all features into telemetry payload.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from config.settings import Settings
from features.optical_flow import OpticalFlowExtractor, compute_flow_entropy, compute_alignment
from features.density import DensityEstimator, compute_bottleneck_index


logger = logging.getLogger(__name__)


@dataclass
class TelemetryPayload:
    """Telemetry data structure matching backend schema."""
    tenant_id: str
    site_id: str
    camera_id: str
    zone_id: str
    timestamp: str
    density: float
    avg_speed: float
    speed_variance: float
    flow_entropy: float
    alignment: float
    bottleneck_index: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization with camelCase keys."""
        return {
            "tenantId": self.tenant_id,
            "siteId": self.site_id,
            "cameraId": self.camera_id,
            "zoneId": self.zone_id,
            "timestamp": self.timestamp,
            "density": self.density,
            "avgSpeed": self.avg_speed,
            "speedVariance": self.speed_variance,
            "flowEntropy": self.flow_entropy,
            "alignment": self.alignment,
            "bottleneckIndex": self.bottleneck_index
        }


class FeatureBuilder:
    """
    Extracts and aggregates features from video frames.
    
    Produces telemetry payloads ready for backend transmission.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.optical_flow = OpticalFlowExtractor(settings)
        self.density_estimator = DensityEstimator(settings)
        
    def extract(self, frame: np.ndarray, zone_mask: Optional[np.ndarray] = None) -> Optional[TelemetryPayload]:
        """
        Extract all features from a frame.
        
        Args:
            frame: Input frame (BGR color)
            zone_mask: Optional binary mask (255 = zone area) for zone-specific analysis
            
        Returns:
            TelemetryPayload if features extracted successfully, None otherwise
        """
        try:
            # Get optical flow
            flow_result = self.optical_flow.compute(frame)
            
            if flow_result is None:
                # First frame, no flow yet
                return None
                
            magnitude, angle = flow_result
            
            # Apply zone mask if provided
            if zone_mask is not None:
                # Ensure mask is same size as flow output
                if zone_mask.shape != magnitude.shape:
                    import cv2
                    zone_mask = cv2.resize(zone_mask, (magnitude.shape[1], magnitude.shape[0]))
                
                # Mask the flow data
                mask_bool = zone_mask > 0
                magnitude = np.where(mask_bool, magnitude, 0)
                angle = np.where(mask_bool, angle, 0)
            
            # Compute features
            density = self.density_estimator.estimate(frame, zone_mask)
            avg_speed = float(np.mean(magnitude[magnitude > 0]) if np.any(magnitude > 0) else 0)
            speed_variance = float(np.var(magnitude[magnitude > 0]) if np.any(magnitude > 0) else 0)
            flow_entropy = compute_flow_entropy(angle, zone_mask)
            alignment = compute_alignment(angle, zone_mask)
            bottleneck_index = compute_bottleneck_index(magnitude, zone_mask)
            
            # Build payload
            payload = TelemetryPayload(
                tenant_id=self.settings.tenant_id,
                site_id=self.settings.site_id,
                camera_id=self.settings.camera_id,
                zone_id=self.settings.zone_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                density=round(density, 4),
                avg_speed=round(avg_speed, 4),
                speed_variance=round(speed_variance, 4),
                flow_entropy=round(flow_entropy, 4),
                alignment=round(alignment, 4),
                bottleneck_index=round(bottleneck_index, 4)
            )
            
            logger.debug(f"Features extracted: density={density:.2f}, entropy={flow_entropy:.2f}")
            
            return payload
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
            
    def reset(self) -> None:
        """Reset all feature extractors."""
        self.optical_flow.reset()
        self.density_estimator.reset()
