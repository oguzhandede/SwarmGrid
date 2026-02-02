"""
Zone Manager - Define and manage analysis zones.

Supports polygon zones with custom thresholds.
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Zone:
    """Definition of an analysis zone."""
    zone_id: str
    name: str
    polygon: List[Tuple[int, int]]  # List of (x, y) points
    max_capacity: int = 100
    yellow_threshold: float = 0.5
    red_threshold: float = 0.75
    zone_type: str = "general"  # general, exit, entrance, bottleneck
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside zone polygon."""
        n = len(self.polygon)
        if n < 3:
            return False
            
        inside = False
        j = n - 1
        
        for i in range(n):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
            
        return inside
        
    def get_mask(self, shape: Tuple[int, int]) -> np.ndarray:
        """Create binary mask for zone."""
        import cv2
        mask = np.zeros(shape, dtype=np.uint8)
        pts = np.array(self.polygon, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        return mask
        
    def to_dict(self) -> dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> "Zone":
        # Convert polygon points from lists to tuples
        if "polygon" in data and data["polygon"]:
            data["polygon"] = [tuple(p) for p in data["polygon"]]
        return cls(**data)


@dataclass  
class ZoneAnalysis:
    """Analysis results for a single zone."""
    zone_id: str
    zone_name: str
    person_count: int = 0
    density: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "Green"
    suggested_actions: List[str] = field(default_factory=list)


class ZoneManager:
    """
    Manages multiple analysis zones.
    
    Handles zone loading, saving, and per-zone analysis.
    """
    
    def __init__(self, zones_file: Optional[Path] = None):
        self.zones: Dict[str, Zone] = {}
        self.zones_file = zones_file
        
        if zones_file and zones_file.exists():
            self.load_zones(zones_file)
            
    def add_zone(self, zone: Zone) -> None:
        """Add a zone."""
        self.zones[zone.zone_id] = zone
        logger.info(f"Added zone: {zone.zone_id} ({zone.name})")
        
    def remove_zone(self, zone_id: str) -> None:
        """Remove a zone."""
        if zone_id in self.zones:
            del self.zones[zone_id]
            logger.info(f"Removed zone: {zone_id}")
            
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Get zone by ID."""
        return self.zones.get(zone_id)
        
    def get_all_zones(self) -> List[Zone]:
        """Get all zones."""
        return list(self.zones.values())
        
    def analyze_zones(
        self,
        person_count: int,
        detections: list,
        frame_shape: Tuple[int, int]
    ) -> List[ZoneAnalysis]:
        """
        Analyze all zones for current frame.
        
        Args:
            person_count: Total person count
            detections: List of Detection objects
            frame_shape: (height, width) of frame
            
        Returns:
            List of ZoneAnalysis results
        """
        results = []
        
        for zone in self.zones.values():
            # Count persons in zone
            zone_count = 0
            for det in detections:
                cx, cy = det.center
                if zone.contains_point(cx, cy):
                    zone_count += 1
                    
            # Calculate zone density
            zone_mask = zone.get_mask(frame_shape)
            zone_area = np.count_nonzero(zone_mask)
            
            if zone_area > 0:
                # Density based on capacity
                density = zone_count / zone.max_capacity
            else:
                density = 0.0
                
            # Calculate risk
            risk_score = min(1.0, density)
            
            if risk_score >= zone.red_threshold:
                risk_level = "Red"
            elif risk_score >= zone.yellow_threshold:
                risk_level = "Yellow"
            else:
                risk_level = "Green"
                
            # Generate actions
            actions = self._generate_actions(zone, zone_count, risk_level)
            
            results.append(ZoneAnalysis(
                zone_id=zone.zone_id,
                zone_name=zone.name,
                person_count=zone_count,
                density=round(density, 4),
                risk_score=round(risk_score, 4),
                risk_level=risk_level,
                suggested_actions=actions
            ))
            
        return results
        
    def _generate_actions(self, zone: Zone, count: int, level: str) -> List[str]:
        """Generate suggested actions for zone."""
        actions = []
        
        if level == "Green":
            return actions
            
        if zone.zone_type == "exit":
            actions.append(f"{zone.name}: Alternatif çıkışları göster")
            if level == "Red":
                actions.append(f"{zone.name}: Güvenlik yönlendir")
                
        elif zone.zone_type == "entrance":
            actions.append(f"{zone.name}: Giriş akışını yavaşlat")
            
        elif zone.zone_type == "bottleneck":
            actions.append(f"{zone.name}: Dar boğaz - bariyer aç")
            
        else:
            if level == "Yellow":
                actions.append(f"{zone.name}: Yoğunluk artıyor, izleniyor")
            if level == "Red":
                actions.append(f"{zone.name}: Kritik yoğunluk!")
                actions.append(f"{zone.name}: Acil müdahale ekibi")
                
        return actions
        
    def save_zones(self, path: Optional[Path] = None) -> None:
        """Save zones to JSON file."""
        save_path = path or self.zones_file
        if save_path is None:
            logger.warning("No save path specified")
            return
            
        data = {
            "zones": [z.to_dict() for z in self.zones.values()]
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(self.zones)} zones to {save_path}")
        
    def load_zones(self, path: Path) -> None:
        """Load zones from JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for zone_data in data.get("zones", []):
                zone = Zone.from_dict(zone_data)
                self.zones[zone.zone_id] = zone
                
            logger.info(f"Loaded {len(self.zones)} zones from {path}")
            
        except Exception as e:
            logger.error(f"Failed to load zones: {e}")


# Default zones example
def create_default_zones() -> ZoneManager:
    """Create default zone configuration."""
    manager = ZoneManager()
    
    # Example zones (would be configured per-camera)
    manager.add_zone(Zone(
        zone_id="zone-1",
        name="Ana Çıkış",
        polygon=[(100, 100), (300, 100), (300, 400), (100, 400)],
        max_capacity=50,
        zone_type="exit"
    ))
    
    manager.add_zone(Zone(
        zone_id="zone-2", 
        name="Food Court",
        polygon=[(350, 100), (600, 100), (600, 400), (350, 400)],
        max_capacity=100,
        zone_type="general"
    ))
    
    return manager
