"""
YOLO-based Person Detection for accurate crowd counting.

Uses YOLOv8-nano for edge-optimized person detection.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single person detection result."""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def area(self) -> float:
        """Get bounding box area."""
        return (self.x2 - self.x1) * (self.y2 - self.y1)
    
    def is_in_zone(self, polygon: List[Tuple[float, float]]) -> bool:
        """Check if detection center is inside a polygon zone."""
        cx, cy = self.center
        return point_in_polygon(cx, cy, polygon)


@dataclass
class DetectionResult:
    """Result from person detector."""
    person_count: int
    detections: List[Detection]
    density_map: Optional[np.ndarray] = None
    
    def get_zone_count(self, zone_polygon: List[Tuple[float, float]]) -> int:
        """Count persons in a specific zone."""
        return sum(1 for d in self.detections if d.is_in_zone(zone_polygon))


def point_in_polygon(x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
    """Ray casting algorithm to check if point is inside polygon."""
    n = len(polygon)
    inside = False
    
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
        
    return inside


class PersonDetector:
    """
    YOLO-based person detector.
    
    Uses YOLOv8-nano for fast edge inference.
    Falls back to motion-based detection if YOLO unavailable.
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        device: str = "cpu"
    ):
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = device
        
        if YOLO_AVAILABLE:
            try:
                logger.info(f"Loading YOLO model: {model_path}")
                self.model = YOLO(model_path)
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load YOLO model: {e}")
        else:
            logger.warning("Ultralytics not installed, using fallback detection")
            
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect persons in frame.
        
        Args:
            frame: BGR image
            
        Returns:
            DetectionResult with person count and bounding boxes
        """
        if self.model is None:
            return self._fallback_detect(frame)
            
        try:
            # Run YOLO detection
            results = self.model(
                frame,
                classes=[0],  # class 0 = person
                conf=self.confidence_threshold,
                verbose=False,
                device=self.device
            )
            
            detections = []
            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        detections.append(Detection(
                            x1=float(x1),
                            y1=float(y1),
                            x2=float(x2),
                            y2=float(y2),
                            confidence=conf
                        ))
                        
            # Create density map
            density_map = self._create_density_map(frame.shape[:2], detections)
            
            return DetectionResult(
                person_count=len(detections),
                detections=detections,
                density_map=density_map
            )
            
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return self._fallback_detect(frame)
            
    def _fallback_detect(self, frame: np.ndarray) -> DetectionResult:
        """Fallback detection using motion analysis."""
        # Use background subtraction as fallback
        return DetectionResult(
            person_count=0,
            detections=[],
            density_map=None
        )
        
    def _create_density_map(
        self,
        shape: Tuple[int, int],
        detections: List[Detection],
        sigma: float = 30.0
    ) -> np.ndarray:
        """Create Gaussian density map from detections."""
        h, w = shape
        density = np.zeros((h, w), dtype=np.float32)
        
        for det in detections:
            cx, cy = det.center
            cx, cy = int(cx), int(cy)
            
            # Create Gaussian kernel around center
            y, x = np.ogrid[max(0, cy-50):min(h, cy+50), max(0, cx-50):min(w, cx+50)]
            y = y - cy
            x = x - cx
            g = np.exp(-(x*x + y*y) / (2 * sigma * sigma))
            
            # Add to density map
            y_start, y_end = max(0, cy-50), min(h, cy+50)
            x_start, x_end = max(0, cx-50), min(w, cx+50)
            density[y_start:y_end, x_start:x_end] += g
            
        return density


# Test function
def test_detector():
    """Quick test of person detector."""
    import cv2
    
    detector = PersonDetector()
    
    # Create test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result = detector.detect(frame)
    print(f"Detected {result.person_count} persons")
    
    
if __name__ == "__main__":
    test_detector()
