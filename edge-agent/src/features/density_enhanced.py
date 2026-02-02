"""
Enhanced Density Estimation with Background Subtraction.

Combines motion-based and stationary crowd detection.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DensityResult:
    """Density estimation result."""
    motion_density: float       # Moving objects density
    stationary_density: float   # Stationary objects density  
    total_density: float        # Combined density
    motion_mask: np.ndarray     # Binary mask of motion
    foreground_mask: np.ndarray # All detected foreground


class EnhancedDensityEstimator:
    """
    Advanced density estimation using background subtraction.
    
    Detects both moving and stationary crowds.
    """
    
    def __init__(
        self,
        history: int = 500,
        var_threshold: float = 16,
        learning_rate: float = 0.005,
        stationary_threshold: int = 30  # frames to consider stationary
    ):
        # Background subtractor for motion
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=True
        )
        
        # Long-term background for stationary detection
        self.long_term_bg = cv2.createBackgroundSubtractorMOG2(
            history=history * 3,
            varThreshold=var_threshold * 2,
            detectShadows=False
        )
        
        self.learning_rate = learning_rate
        self.stationary_threshold = stationary_threshold
        self.stationary_buffer = None
        self.frame_count = 0
        
        # Morphological kernels
        self.kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        
    def estimate(self, frame: np.ndarray) -> DensityResult:
        """
        Estimate density from frame.
        
        Args:
            frame: BGR input image
            
        Returns:
            DensityResult with motion and stationary densities
        """
        self.frame_count += 1
        
        # Apply background subtraction (motion detection)
        fg_mask = self.bg_subtractor.apply(frame, learningRate=self.learning_rate)
        
        # Remove shadows (gray pixels = 127)
        motion_mask = np.where(fg_mask == 255, 255, 0).astype(np.uint8)
        
        # Clean up motion mask
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, self.kernel_small)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, self.kernel_large)
        
        # Long-term background for stationary detection
        long_term_fg = self.long_term_bg.apply(frame, learningRate=0.001)
        long_term_mask = np.where(long_term_fg == 255, 255, 0).astype(np.uint8)
        
        # Stationary = in long-term foreground but not moving
        stationary_mask = cv2.bitwise_and(long_term_mask, cv2.bitwise_not(motion_mask))
        stationary_mask = cv2.morphologyEx(stationary_mask, cv2.MORPH_CLOSE, self.kernel_large)
        
        # Calculate densities
        total_pixels = frame.shape[0] * frame.shape[1]
        
        motion_pixels = np.count_nonzero(motion_mask)
        motion_density = min(1.0, motion_pixels / (total_pixels * 0.3))
        
        stationary_pixels = np.count_nonzero(stationary_mask)
        stationary_density = min(1.0, stationary_pixels / (total_pixels * 0.3))
        
        # Combined foreground
        foreground_mask = cv2.bitwise_or(motion_mask, stationary_mask)
        
        # Total density (weighted)
        total_density = min(1.0, motion_density * 0.6 + stationary_density * 0.4)
        
        return DensityResult(
            motion_density=round(motion_density, 4),
            stationary_density=round(stationary_density, 4),
            total_density=round(total_density, 4),
            motion_mask=motion_mask,
            foreground_mask=foreground_mask
        )
        
    def reset(self) -> None:
        """Reset background models."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        self.long_term_bg = cv2.createBackgroundSubtractorMOG2(
            history=1500,
            varThreshold=32,
            detectShadows=False
        )
        self.frame_count = 0


def compute_bottleneck_index(
    magnitude: np.ndarray,
    threshold: float = 0.5
) -> float:
    """
    Compute bottleneck index from flow magnitude.
    
    Identifies areas where flow is concentrated (potential bottlenecks).
    
    Args:
        magnitude: Flow magnitude array
        threshold: Threshold for significant flow
        
    Returns:
        Bottleneck index (0-1)
    """
    # Normalize magnitude
    if magnitude.max() > 0:
        norm_mag = magnitude / magnitude.max()
    else:
        return 0.0
        
    # Find high-flow regions
    high_flow_mask = norm_mag > threshold
    high_flow_ratio = np.mean(high_flow_mask)
    
    # Find spatial concentration
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


# Test function
def test_density():
    """Quick test of density estimator."""
    estimator = EnhancedDensityEstimator()
    
    # Create test frames
    for i in range(10):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = estimator.estimate(frame)
        print(f"Frame {i}: motion={result.motion_density:.2f}, stationary={result.stationary_density:.2f}")
        

if __name__ == "__main__":
    test_density()
