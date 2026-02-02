"""
Density estimation module.

Provides motion-based density estimation as a proxy for person count.
"""

import logging
from typing import Optional

import cv2
import numpy as np

from config.settings import Settings


logger = logging.getLogger(__name__)


class DensityEstimator:
    """
    Estimate crowd density from video frames.
    
    Uses motion-based analysis as a proxy for density.
    For more accurate results, use ONNX person detection model.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
        
    def estimate(self, frame: np.ndarray, zone_mask: Optional[np.ndarray] = None) -> float:
        """
        Estimate density from frame using motion analysis.
        
        Args:
            frame: Input frame (BGR color)
            zone_mask: Optional binary mask for zone-specific analysis
            
        Returns:
            Density score (0-1)
        """
        try:
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Clean up mask with morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Apply zone mask if provided
            if zone_mask is not None:
                if zone_mask.shape != fg_mask.shape:
                    zone_mask = cv2.resize(zone_mask, (fg_mask.shape[1], fg_mask.shape[0]))
                fg_mask = cv2.bitwise_and(fg_mask, zone_mask)
                total_pixels = np.count_nonzero(zone_mask)
            else:
                total_pixels = fg_mask.size
            
            if total_pixels == 0:
                return 0.0
            
            # Calculate motion pixels ratio
            motion_pixels = np.count_nonzero(fg_mask)
            
            # Normalize to 0-1 range
            # Typical motion coverage is 0-30%, so we scale accordingly
            density = min(1.0, motion_pixels / (total_pixels * 0.3))
            
            return float(density)
            
        except Exception as e:
            logger.error(f"Density estimation error: {e}")
            return 0.0
            
    def reset(self) -> None:
        """Reset the background model."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )


def compute_bottleneck_index(
    magnitude: np.ndarray,
    zone_mask: Optional[np.ndarray] = None,
    threshold: float = 0.5
) -> float:
    """
    Compute bottleneck index from flow magnitude.
    
    Identifies areas where flow is concentrated (potential bottlenecks).
    
    Args:
        magnitude: Flow magnitude array
        zone_mask: Optional binary mask for zone-specific analysis
        threshold: Threshold for significant flow
        
    Returns:
        Bottleneck index (0-1)
    """
    # Apply zone mask if provided
    if zone_mask is not None:
        if zone_mask.shape != magnitude.shape:
            zone_mask = cv2.resize(zone_mask, (magnitude.shape[1], magnitude.shape[0]))
        magnitude = np.where(zone_mask > 0, magnitude, 0)
    
    # Normalize magnitude
    if magnitude.max() > 0:
        norm_mag = magnitude / magnitude.max()
    else:
        return 0.0
        
    # Find high-flow regions
    high_flow_mask = norm_mag > threshold
    high_flow_ratio = np.mean(high_flow_mask)
    
    # Find spatial concentration
    # If all high-flow pixels are in one area = high bottleneck
    if np.count_nonzero(high_flow_mask) == 0:
        return 0.0
        
    # Use contour analysis to find clustering
    high_flow_uint8 = (high_flow_mask * 255).astype(np.uint8)
    contours, _ = cv2.findContours(
        high_flow_uint8,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    if len(contours) == 0:
        return 0.0
        
    # Ratio of largest contour area to total high-flow area
    largest_contour_area = max(cv2.contourArea(c) for c in contours)
    total_high_flow_area = np.count_nonzero(high_flow_mask)
    
    concentration = largest_contour_area / (total_high_flow_area + 1)
    
    # Combine with flow ratio
    bottleneck_index = concentration * high_flow_ratio
    
    return float(min(1.0, bottleneck_index))
