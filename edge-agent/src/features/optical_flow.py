"""
Optical Flow feature extraction.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from config.settings import Settings


logger = logging.getLogger(__name__)


class OpticalFlowExtractor:
    """
    Extract optical flow features from consecutive frames.
    
    Uses Farneback dense optical flow by default.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = settings.optical_flow
        self.prev_gray: Optional[np.ndarray] = None
        
    def compute(self, frame: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Compute optical flow between current and previous frame.
        
        Args:
            frame: Current frame (BGR color)
            
        Returns:
            Tuple of (magnitude, angle) arrays, or None if first frame
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return None
            
        try:
            # Compute dense optical flow
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray,
                gray,
                None,
                pyr_scale=self.config.pyr_scale,
                levels=self.config.levels,
                winsize=self.config.winsize,
                iterations=self.config.iterations,
                poly_n=self.config.poly_n,
                poly_sigma=self.config.poly_sigma,
                flags=0
            )
            
            # Update previous frame
            self.prev_gray = gray
            
            # Convert to polar coordinates (magnitude, angle)
            magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            return magnitude, angle
            
        except Exception as e:
            logger.error(f"Optical flow computation error: {e}")
            self.prev_gray = gray
            return None
            
    def reset(self) -> None:
        """Reset the previous frame buffer."""
        self.prev_gray = None


def compute_flow_entropy(angle: np.ndarray, zone_mask: Optional[np.ndarray] = None, bins: int = 36) -> float:
    """
    Compute flow entropy from angle distribution.
    
    High entropy = chaotic movement (risk indicator)
    Low entropy = aligned movement
    
    Args:
        angle: Flow angle array in radians
        zone_mask: Optional binary mask for zone-specific analysis
        bins: Number of histogram bins
        
    Returns:
        Entropy value (0-1 normalized)
    """
    # Apply zone mask if provided
    if zone_mask is not None:
        mask_bool = zone_mask > 0
        if mask_bool.shape != angle.shape:
            mask_bool = cv2.resize(zone_mask, (angle.shape[1], angle.shape[0])) > 0
        angles_deg = np.degrees(angle[mask_bool].flatten())
    else:
        angles_deg = np.degrees(angle.flatten())
    
    if len(angles_deg) == 0:
        return 0.0
    
    # Create histogram
    hist, _ = np.histogram(angles_deg, bins=bins, range=(0, 360))
    
    # Normalize to probability distribution
    hist = hist.astype(float)
    hist = hist / (hist.sum() + 1e-10)
    
    # Compute entropy
    entropy = -np.sum(hist * np.log2(hist + 1e-10))
    
    # Normalize to 0-1 range (max entropy = log2(bins))
    max_entropy = np.log2(bins)
    normalized_entropy = entropy / max_entropy
    
    return float(normalized_entropy)


def compute_alignment(angle: np.ndarray, zone_mask: Optional[np.ndarray] = None) -> float:
    """
    Compute flow alignment score.
    
    High alignment = people moving in same direction
    Low alignment = scattered movement (risk indicator)
    
    Args:
        angle: Flow angle array in radians
        zone_mask: Optional binary mask for zone-specific analysis
        
    Returns:
        Alignment value (0-1)
    """
    # Apply zone mask if provided
    if zone_mask is not None:
        mask_bool = zone_mask > 0
        if mask_bool.shape != angle.shape:
            mask_bool = cv2.resize(zone_mask, (angle.shape[1], angle.shape[0])) > 0
        masked_angle = angle[mask_bool]
    else:
        masked_angle = angle.flatten()
    
    if len(masked_angle) == 0:
        return 0.0
    
    # Use circular mean to find dominant direction
    sin_sum = np.sin(masked_angle).mean()
    cos_sum = np.cos(masked_angle).mean()
    
    # Resultant length (R) indicates alignment
    # R = 1 means perfect alignment, R = 0 means uniform distribution
    alignment = np.sqrt(sin_sum**2 + cos_sum**2)
    
    return float(alignment)
