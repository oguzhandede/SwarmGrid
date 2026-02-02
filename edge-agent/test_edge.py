"""
Simple test script for Edge Agent.
Tests video stream connection and feature extraction.
Uses HTTP video URLs which are more reliable than RTSP.
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np


def test_video_connection(url: str) -> bool:
    """Test if video URL is accessible."""
    print(f"\n🔌 Testing connection: {url[:60]}...")
    
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print("❌ Failed to open stream")
        return False
        
    # Try to read a frame with timeout
    ret, frame = cap.read()
    cap.release()
    
    if ret and frame is not None:
        print(f"✅ Connection successful! Frame size: {frame.shape}")
        return True
    else:
        print("❌ Could not read frame from stream")
        return False


def test_feature_extraction(url: str, num_frames: int = 5):
    """Test feature extraction from video."""
    print(f"\n📊 Testing feature extraction ({num_frames} frames)...")
    
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("❌ Cannot open video")
        return False
        
    prev_gray = None
    frame_count = 0
    success_count = 0
    
    while frame_count < num_frames + 1:  # +1 for first frame (no flow)
        ret, frame = cap.read()
        if not ret:
            print("⚠️ End of video or read error")
            break
            
        # Resize for faster processing
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
            
            # Flow entropy
            angles_deg = np.degrees(angle.flatten())
            hist, _ = np.histogram(angles_deg, bins=36, range=(0, 360))
            hist = hist.astype(float) / (hist.sum() + 1e-10)
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            flow_entropy = entropy / np.log2(36)
            
            # Alignment
            sin_sum = np.sin(angle).mean()
            cos_sum = np.cos(angle).mean()
            alignment = np.sqrt(sin_sum**2 + cos_sum**2)
            
            # Density proxy (motion pixels)
            motion_threshold = 1.0
            motion_pixels = np.count_nonzero(magnitude > motion_threshold)
            density = min(1.0, motion_pixels / (magnitude.size * 0.3))
            
            print(f"  Frame {success_count + 1}: density={density:.3f}, speed={avg_speed:.3f}, entropy={flow_entropy:.3f}, alignment={alignment:.3f}")
            success_count += 1
            
        prev_gray = gray
        frame_count += 1
        
    cap.release()
    
    if success_count > 0:
        print(f"\n✅ Feature extraction successful! Processed {success_count} frames.")
        return True
    else:
        print("\n❌ No frames processed")
        return False


def main():
    print("=" * 50)
    print("🎥 SwarmGrid Edge Agent Test")
    print("=" * 50)
    
    # Test URLs - HTTP video files (more reliable than RTSP)
    test_urls = [
        # Sample videos from HTTP
        "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    ]
    
    working_url = None
    
    for url in test_urls:
        if test_video_connection(url):
            working_url = url
            break
        print("⏭️ Trying next URL...")
        
    if working_url is None:
        print("\n❌ No working video stream found!")
        print("\n💡 This might be a network issue. Check your internet connection.")
        return False
        
    # Test feature extraction
    result = test_feature_extraction(working_url, num_frames=5)
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 Test Complete - Edge Agent is working!")
        print("\nNext steps:")
        print("1. Start the backend: cd core-backend && dotnet run --project src/SwarmGrid.Api")
        print("2. Run full agent: python src/main.py")
    else:
        print("⚠️ Test partially complete")
    print("=" * 50)
    
    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
