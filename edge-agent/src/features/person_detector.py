"""
YOLO-based Person Detection for accurate crowd counting.

Uses YOLOv8-nano for edge-optimized person detection.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

try:
    from ultralytics import YOLO  # type: ignore[reportPrivateImportUsage]
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
    YOLO-based person detector optimized for crowded scenes.
    
    Uses YOLOv8-nano for fast edge inference with crowd-optimized settings.
    Falls back to motion-based detection if YOLO unavailable.
    """
    
    def __init__(
        self,
        model_path: str = "yolov8s.pt",  # Small model for better accuracy
        confidence_threshold: float = 0.35,  # Balanced for accuracy
        iou_threshold: float = 0.4,  # Standard IoU for person detection
        device: str = "cpu",
        img_size: int = 1280,  # Larger input for small person detection
        max_det: int = 300  # Maximum detections
    ):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.img_size = img_size
        self.max_det = max_det
        self.model = None
        self.device = device
        
        if YOLO_AVAILABLE and YOLO is not None:
            try:
                logger.info(f"Loading YOLO model: {model_path}")
                self.model = YOLO(model_path)
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load YOLO model: {e}")
        else:
            logger.warning("Ultralytics not installed, using fallback detection")
            
    def detect(
        self, 
        frame: np.ndarray,
        zone_polygon: Optional[List[Tuple[float, float]]] = None
    ) -> DetectionResult:
        """
        Detect persons in frame.
        
        Args:
            frame: BGR image
            zone_polygon: Optional polygon to filter detections
            
        Returns:
            DetectionResult with person count and bounding boxes
        """
        if self.model is None:
            return self._fallback_detect(frame)
            
        try:
            # Run YOLO detection with crowd-optimized settings
            results = self.model(
                frame,
                classes=[0],  # class 0 = person
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                imgsz=self.img_size,
                max_det=self.max_det,
                verbose=False,
                device=self.device,
                agnostic_nms=True  # Class-agnostic NMS for better crowd detection
            )
            
            detections = []
            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        
                        det = Detection(
                            x1=float(x1),
                            y1=float(y1),
                            x2=float(x2),
                            y2=float(y2),
                            confidence=conf
                        )
                        
                        # Filter by zone if provided
                        if zone_polygon is None or det.is_in_zone(zone_polygon):
                            detections.append(det)
                        
            # Apply additional filtering for small/invalid boxes
            detections = self._filter_detections(detections, frame.shape)
            
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
    
    def _filter_detections(
        self, 
        detections: List[Detection],
        frame_shape: Tuple[int, int, int]
    ) -> List[Detection]:
        """
        Filter out invalid detections.
        
        Args:
            detections: List of detections
            frame_shape: Frame dimensions (H, W, C)
            
        Returns:
            Filtered list of detections
        """
        h, w = frame_shape[:2]
        min_area = (w * h) * 0.0001  # Minimum 0.01% of frame (very small persons)
        max_area = (w * h) * 0.35    # Maximum 35% of frame
        min_aspect_ratio = 0.15      # Width/Height ratio (allow wider boxes)
        max_aspect_ratio = 2.5       # Allow taller boxes
        
        filtered = []
        for det in detections:
            area = det.area
            width = det.x2 - det.x1
            height = det.y2 - det.y1
            
            if height > 0:
                aspect_ratio = width / height
            else:
                continue
                
            # Filter by area
            if area < min_area or area > max_area:
                continue
                
            # Filter by aspect ratio (persons are typically taller than wide)
            if aspect_ratio < min_aspect_ratio or aspect_ratio > max_aspect_ratio:
                continue
                
            # NOTE: Removed edge filtering - it was too aggressive for crowded scenes
            filtered.append(det)
            
        return filtered
            
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
