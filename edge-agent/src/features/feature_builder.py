"""
Feature Builder - Aggregates all features into telemetry payload.

Combines YOLO person detection with optical flow analysis.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, List, Tuple

import cv2
import numpy as np

from config.settings import Settings
from features.optical_flow import OpticalFlowExtractor, compute_flow_entropy, compute_alignment
from features.density import DensityEstimator, compute_bottleneck_index
from features.person_detector import PersonDetector, DetectionResult


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
    person_count: int = 0  # Actual person count from YOLO
    
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
            "bottleneckIndex": self.bottleneck_index,
            "personCount": self.person_count
        }


class FeatureBuilder:
    """
    Extracts and aggregates features from video frames.
    
    Combines YOLO-based person detection with optical flow analysis
    to produce accurate telemetry payloads.
    """
    
    def __init__(self, settings: Settings, zone_capacity: int = 100):
        self.settings = settings
        self.zone_capacity = zone_capacity  # Maximum expected persons in zone
        self.optical_flow = OpticalFlowExtractor(settings)
        self.density_estimator = DensityEstimator(settings)
        self.person_detector = PersonDetector(
            model_path="yolov8s.pt",  # Small model for better accuracy
            confidence_threshold=0.35,  # Balanced for accuracy
            iou_threshold=0.4,
            device="cpu",
            img_size=1280,
            max_det=300
        )
        self._last_person_count = 0
        self._person_count_smoothing = 0.3  # Exponential smoothing factor
        
    def extract(
        self, 
        frame: np.ndarray, 
        zone_mask: Optional[np.ndarray] = None,
        zone_polygon: Optional[List[Tuple[float, float]]] = None,
        zone_capacity: Optional[int] = None
    ) -> Optional[TelemetryPayload]:
        """
        Extract all features from a frame.
        
        Args:
            frame: Input frame (BGR color)
            zone_mask: Optional binary mask (255 = zone area) for zone-specific analysis
            zone_polygon: Optional polygon coordinates for person filtering
            zone_capacity: Optional zone-specific capacity (overrides default)
            
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
                    zone_mask = cv2.resize(zone_mask, (magnitude.shape[1], magnitude.shape[0]))
                
                # Mask the flow data
                mask_bool = zone_mask > 0
                magnitude = np.where(mask_bool, magnitude, 0)
                angle = np.where(mask_bool, angle, 0)
            
            # Person detection with YOLO
            detection_result = self.person_detector.detect(frame, zone_polygon)
            person_count = detection_result.person_count
            
            # Apply smoothing to reduce jitter
            smoothed_count = int(
                self._person_count_smoothing * person_count + 
                (1 - self._person_count_smoothing) * self._last_person_count
            )
            self._last_person_count = smoothed_count
            
            # Calculate density from person count
            capacity = zone_capacity or self.zone_capacity
            count_based_density = min(1.0, smoothed_count / capacity)
            
            # Motion-based density as backup/supplement
            motion_density = self.density_estimator.estimate(frame, zone_mask)
            
            # Combine densities (prefer person count when detections are reliable)
            if person_count > 0:
                # Use count-based density primarily, motion as correction
                density = count_based_density * 0.8 + motion_density * 0.2
            else:
                # Fall back to motion-based when no detections
                density = motion_density
            
            # Other features
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
                bottleneck_index=round(bottleneck_index, 4),
                person_count=smoothed_count
            )
            
            logger.debug(
                f"Features: persons={smoothed_count}, density={density:.2f}, "
                f"entropy={flow_entropy:.2f}"
            )
            
            return payload
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
            
    def reset(self) -> None:
        """Reset all feature extractors."""
        self.optical_flow.reset()
        self.density_estimator.reset()
        self._last_person_count = 0
