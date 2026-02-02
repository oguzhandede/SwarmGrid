"""
Interactive Zone Drawing Tool.

Allows drawing polygon zones on video frames using mouse.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np

from zones.zone_manager import Zone, ZoneManager

logger = logging.getLogger(__name__)


class ZoneDrawer:
    """
    Interactive tool for drawing zones on video frames.
    
    Usage:
        drawer = ZoneDrawer()
        zones = drawer.draw_zones(video_path, output_path)
    """
    
    def __init__(self):
        self.current_polygon: List[Tuple[int, int]] = []
        self.zones: List[Zone] = []
        self.drawing = False
        self.frame = None
        self.display_frame = None
        self.zone_counter = 0
        
        # Colors for different zone types
        self.colors = {
            "general": (0, 255, 0),    # Green
            "exit": (0, 165, 255),     # Orange
            "entrance": (255, 255, 0), # Cyan
            "bottleneck": (0, 0, 255)  # Red
        }
        self.current_type = "general"
        
    def _mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for polygon drawing."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Add point to polygon
            self.current_polygon.append((x, y))
            self._update_display()
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Complete polygon
            if len(self.current_polygon) >= 3:
                self._complete_zone()
                
        elif event == cv2.EVENT_MOUSEMOVE:
            # Show preview line while drawing
            if self.current_polygon:
                self._update_display()
                if self.display_frame is not None:
                    cv2.line(
                        self.display_frame,
                        self.current_polygon[-1],
                        (x, y),
                        self.colors[self.current_type],
                        1
                    )
                    
    def _update_display(self):
        """Update display frame with current drawings."""
        self.display_frame = self.frame.copy()
        
        # Draw existing zones
        for zone in self.zones:
            pts = np.array(zone.polygon, dtype=np.int32)
            color = self.colors.get(zone.zone_type, (0, 255, 0))
            cv2.polylines(self.display_frame, [pts], True, color, 2)
            cv2.fillPoly(self.display_frame, [pts], (*color[:3], 50))
            
            # Draw zone name
            centroid = np.mean(pts, axis=0).astype(int)
            cv2.putText(
                self.display_frame,
                zone.name,
                tuple(centroid),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
            
        # Draw current polygon in progress
        if self.current_polygon:
            pts = np.array(self.current_polygon, dtype=np.int32)
            cv2.polylines(
                self.display_frame, [pts], False,
                self.colors[self.current_type], 2
            )
            for pt in self.current_polygon:
                cv2.circle(self.display_frame, pt, 5, (255, 255, 255), -1)
                
        # Draw instructions
        self._draw_instructions()
        
    def _draw_instructions(self):
        """Draw usage instructions on frame."""
        instructions = [
            "Zone Drawing Tool",
            "-------------------",
            "Left Click: Add point",
            "Right Click: Complete zone",
            "1-4: Change zone type",
            "Z: Undo last point",
            "C: Clear current",
            "S: Save and exit",
            "Q: Quit without saving",
            f"Current type: {self.current_type}"
        ]
        
        y = 30
        for text in instructions:
            cv2.putText(
                self.display_frame,
                text,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            y += 20
            
    def _complete_zone(self):
        """Complete current zone and add to list."""
        self.zone_counter += 1
        
        # Get zone name from user (console input)
        zone_name = f"Zone {self.zone_counter}"
        
        zone = Zone(
            zone_id=f"zone-{self.zone_counter}",
            name=zone_name,
            polygon=self.current_polygon.copy(),
            zone_type=self.current_type,
            max_capacity=50
        )
        
        self.zones.append(zone)
        self.current_polygon = []
        self._update_display()
        
        logger.info(f"Zone created: {zone.name} ({zone.zone_type})")
        
    def draw_zones(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        start_frame: int = 0
    ) -> List[Zone]:
        """
        Open video and draw zones interactively.
        
        Args:
            video_path: Path to video file
            output_path: Path to save zones JSON
            start_frame: Frame to display for drawing
            
        Returns:
            List of drawn zones
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return []
            
        # Seek to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        ret, self.frame = cap.read()
        cap.release()
        
        if not ret:
            logger.error("Cannot read frame")
            return []
            
        # Setup window
        window_name = "Zone Drawer - SwarmGrid"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self._mouse_callback)
        
        self._update_display()
        
        print("\n🎯 Zone Drawing Tool")
        print("=" * 40)
        print("Left click to add polygon points")
        print("Right click to complete zone")
        print("Press 1-4 to change zone type:")
        print("  1: General, 2: Exit, 3: Entrance, 4: Bottleneck")
        print("Press S to save, Q to quit")
        print("=" * 40 + "\n")
        
        while True:
            cv2.imshow(window_name, self.display_frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                # Quit without saving
                break
                
            elif key == ord('s'):
                # Save and exit
                if output_path:
                    self._save_zones(output_path)
                break
                
            elif key == ord('z'):
                # Undo last point
                if self.current_polygon:
                    self.current_polygon.pop()
                    self._update_display()
                    
            elif key == ord('c'):
                # Clear current polygon
                self.current_polygon = []
                self._update_display()
                
            elif key == ord('1'):
                self.current_type = "general"
                self._update_display()
                
            elif key == ord('2'):
                self.current_type = "exit"
                self._update_display()
                
            elif key == ord('3'):
                self.current_type = "entrance"
                self._update_display()
                
            elif key == ord('4'):
                self.current_type = "bottleneck"
                self._update_display()
                
        cv2.destroyAllWindows()
        return self.zones
        
    def _save_zones(self, path: str):
        """Save zones to JSON file."""
        manager = ZoneManager()
        for zone in self.zones:
            manager.add_zone(zone)
        manager.save_zones(Path(path))
        print(f"\n✅ Saved {len(self.zones)} zones to {path}")


def main():
    """Run zone drawer tool."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python zone_drawer.py <video_path> [output_json]")
        print("Example: python zone_drawer.py video.mp4 zones.json")
        sys.exit(1)
        
    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "zones.json"
    
    drawer = ZoneDrawer()
    zones = drawer.draw_zones(video_path, output_path)
    
    print(f"\nCreated {len(zones)} zones:")
    for z in zones:
        print(f"  - {z.name} ({z.zone_type}): {len(z.polygon)} points")


if __name__ == "__main__":
    main()
