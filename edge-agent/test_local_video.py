"""
Test Edge Agent with local video file.
"""

import sys
import time
import cv2
import numpy as np


def test_feature_extraction(video_path: str, num_frames: int = 30):
    """Test feature extraction from local video."""
    print(f"\n📹 Opening video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Cannot open video file")
        return False
    
    # Get video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 Video info: {width}x{height}, {fps:.1f} FPS, {total_frames} frames")
    print(f"\n🔬 Extracting features from {num_frames} frames...\n")
    
    prev_gray = None
    frame_count = 0
    results = []
    
    while frame_count < num_frames + 1:
        ret, frame = cap.read()
        if not ret:
            print("📼 End of video")
            break
            
        # Resize for processing
        frame = cv2.resize(frame, (640, 480))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if prev_gray is not None:
            # Calculate optical flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            
            # Extract features
            magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            avg_speed = float(np.mean(magnitude))
            speed_variance = float(np.var(magnitude))
            
            # Flow entropy (chaos indicator)
            angles_deg = np.degrees(angle.flatten())
            hist, _ = np.histogram(angles_deg, bins=36, range=(0, 360))
            hist = hist.astype(float) / (hist.sum() + 1e-10)
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            flow_entropy = entropy / np.log2(36)
            
            # Alignment (direction coherence)
            sin_sum = np.sin(angle).mean()
            cos_sum = np.cos(angle).mean()
            alignment = np.sqrt(sin_sum**2 + cos_sum**2)
            
            # Density (motion area)
            motion_threshold = 0.5
            motion_pixels = np.count_nonzero(magnitude > motion_threshold)
            density = min(1.0, motion_pixels / (magnitude.size * 0.3))
            
            # Bottleneck (concentrated flow)
            high_flow = magnitude > np.percentile(magnitude, 75)
            bottleneck = np.count_nonzero(high_flow) / magnitude.size
            
            result = {
                'density': density,
                'speed': avg_speed,
                'entropy': flow_entropy,
                'alignment': alignment,
                'bottleneck': bottleneck
            }
            results.append(result)
            
            # Risk calculation (simple V1)
            risk_score = (
                density * 0.35 +
                flow_entropy * 0.25 +
                (1 - alignment) * 0.20 +
                bottleneck * 0.20
            )
            
            risk_level = "🟢 Green" if risk_score < 0.5 else "🟡 Yellow" if risk_score < 0.75 else "🔴 Red"
            
            print(f"Frame {frame_count:3d}: density={density:.2f} | speed={avg_speed:.2f} | entropy={flow_entropy:.2f} | align={alignment:.2f} | RISK={risk_score:.2f} {risk_level}")
            
        prev_gray = gray
        frame_count += 1
        
    cap.release()
    
    if results:
        print("\n" + "=" * 70)
        print("📈 SUMMARY")
        print("=" * 70)
        
        avg_density = np.mean([r['density'] for r in results])
        avg_entropy = np.mean([r['entropy'] for r in results])
        avg_alignment = np.mean([r['alignment'] for r in results])
        max_density = np.max([r['density'] for r in results])
        
        avg_risk = avg_density * 0.35 + avg_entropy * 0.25 + (1 - avg_alignment) * 0.20
        
        print(f"  Average Density:   {avg_density:.3f}")
        print(f"  Max Density:       {max_density:.3f}")
        print(f"  Average Entropy:   {avg_entropy:.3f}")
        print(f"  Average Alignment: {avg_alignment:.3f}")
        print(f"  Overall Risk:      {avg_risk:.3f}")
        
        if avg_risk < 0.3:
            print("\n  Status: 🟢 LOW RISK - Normal crowd behavior")
        elif avg_risk < 0.5:
            print("\n  Status: 🟡 MODERATE - Some congestion detected")
        else:
            print("\n  Status: 🔴 HIGH RISK - Dense/chaotic movement detected")
            
        print("=" * 70)
        return True
    
    return False


if __name__ == "__main__":
    video_path = r"e:\Oguz\SwarmGrid\20260105_0016_New Video_simple_compose_01ke5dwdzrfrtvvchjzsg53cp1.mp4"
    
    print("=" * 70)
    print("🎥 SwarmGrid Edge Agent - Local Video Test")
    print("=" * 70)
    
    success = test_feature_extraction(video_path, num_frames=50)
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed")
    
    sys.exit(0 if success else 1)
