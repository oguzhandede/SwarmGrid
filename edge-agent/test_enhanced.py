"""
Enhanced Edge Agent Test - All Features Combined.

Tests:
- YOLO Person Detection
- Background Subtraction (stationary + motion)
- Zone-based Analysis
- Optical Flow
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Check imports
try:
    from features.person_detector import PersonDetector, YOLO_AVAILABLE
    PERSON_DETECTOR_OK = True
except ImportError as e:
    print(f"⚠️ Person detector not available: {e}")
    PERSON_DETECTOR_OK = False
    YOLO_AVAILABLE = False

try:
    from features.density_enhanced import EnhancedDensityEstimator
    DENSITY_OK = True
except ImportError as e:
    print(f"⚠️ Enhanced density not available: {e}")
    DENSITY_OK = False

try:
    from zones.zone_manager import Zone, ZoneManager
    ZONES_OK = True
except ImportError as e:
    print(f"⚠️ Zone manager not available: {e}")
    ZONES_OK = False


def analyze_video_enhanced(video_path: str, num_frames: int = 50, show_video: bool = False):
    """
    Analyze video with all enhanced features.
    """
    print("=" * 70)
    print("🎥 SwarmGrid Enhanced Edge Agent Test")
    print("=" * 70)
    
    # Status check
    print("\n📦 Module Status:")
    print(f"  • YOLO Detection: {'✅ Available' if YOLO_AVAILABLE else '❌ Not installed'}")
    print(f"  • Person Detector: {'✅ OK' if PERSON_DETECTOR_OK else '❌ Error'}")
    print(f"  • Enhanced Density: {'✅ OK' if DENSITY_OK else '❌ Error'}")
    print(f"  • Zone Manager: {'✅ OK' if ZONES_OK else '❌ Error'}")
    
    # Open video
    print(f"\n📹 Opening: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Cannot open video")
        return False
        
    # Video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📊 Video: {width}x{height}, {fps:.1f} FPS, {total_frames} frames")
    
    # Initialize components
    person_detector = PersonDetector() if PERSON_DETECTOR_OK else None
    density_estimator = EnhancedDensityEstimator() if DENSITY_OK else None
    
    # Create sample zones (would normally be loaded from file)
    zone_manager = None
    if ZONES_OK:
        zone_manager = ZoneManager()
        # Create zones based on frame size
        zone_manager.add_zone(Zone(
            zone_id="zone-left",
            name="Sol Alan",
            polygon=[(0, 0), (width//2, 0), (width//2, height), (0, height)],
            max_capacity=30,
            zone_type="general"
        ))
        zone_manager.add_zone(Zone(
            zone_id="zone-right",
            name="Sağ Alan",
            polygon=[(width//2, 0), (width, 0), (width, height), (width//2, height)],
            max_capacity=30,
            zone_type="exit"
        ))
    
    # Optical flow
    prev_gray = None
    
    # Results storage
    results = {
        'person_counts': [],
        'motion_densities': [],
        'stationary_densities': [],
        'flow_entropies': [],
        'risk_scores': []
    }
    
    print(f"\n🔬 Analyzing {min(num_frames, total_frames)} frames...\n")
    
    frame_count = 0
    start_time = time.time()
    
    while frame_count < num_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_resized = cv2.resize(frame, (640, 480))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        # 1. Person Detection (YOLO)
        person_count = 0
        detections = []
        if person_detector:
            det_result = person_detector.detect(frame_resized)
            person_count = det_result.person_count
            detections = det_result.detections
            
        # 2. Background Subtraction
        motion_density = 0.0
        stationary_density = 0.0
        if density_estimator:
            density_result = density_estimator.estimate(frame_resized)
            motion_density = density_result.motion_density
            stationary_density = density_result.stationary_density
            
        # 3. Optical Flow
        flow_entropy = 0.0
        alignment = 1.0
        avg_speed = 0.0
        
        if prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            avg_speed = float(np.mean(magnitude))
            
            # Entropy
            angles_deg = np.degrees(angle.flatten())
            hist, _ = np.histogram(angles_deg, bins=36, range=(0, 360))
            hist = hist.astype(float) / (hist.sum() + 1e-10)
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            flow_entropy = entropy / np.log2(36)
            
            # Alignment
            sin_sum = np.sin(angle).mean()
            cos_sum = np.cos(angle).mean()
            alignment = np.sqrt(sin_sum**2 + cos_sum**2)
            
        prev_gray = gray
        
        # 4. Zone Analysis
        zone_results = []
        if zone_manager and detections:
            zone_results = zone_manager.analyze_zones(
                person_count, detections, frame_resized.shape[:2]
            )
        
        # 5. Combined Risk Score
        # Weight: person count > motion > entropy > stationary
        person_factor = min(1.0, person_count / 20)  # Normalize to 20 people
        
        risk_score = (
            person_factor * 0.30 +
            motion_density * 0.25 +
            flow_entropy * 0.20 +
            (1 - alignment) * 0.15 +
            stationary_density * 0.10
        )
        
        risk_level = "🟢" if risk_score < 0.5 else "🟡" if risk_score < 0.75 else "🔴"
        
        # Store results
        results['person_counts'].append(person_count)
        results['motion_densities'].append(motion_density)
        results['stationary_densities'].append(stationary_density)
        results['flow_entropies'].append(flow_entropy)
        results['risk_scores'].append(risk_score)
        
        # Print every 5th frame
        if frame_count % 5 == 0:
            zone_info = ""
            if zone_results:
                zone_info = f" | zones: {', '.join(f'{z.zone_name}:{z.person_count}p' for z in zone_results)}"
            print(f"Frame {frame_count:3d}: 👥{person_count:2d} | motion={motion_density:.2f} | stat={stationary_density:.2f} | entropy={flow_entropy:.2f} | RISK={risk_score:.2f} {risk_level}{zone_info}")
        
        # Show video if requested
        if show_video:
            # Draw detections
            display = frame_resized.copy()
            for det in detections:
                cv2.rectangle(display, 
                    (int(det.x1), int(det.y1)), 
                    (int(det.x2), int(det.y2)),
                    (0, 255, 0), 2)
                    
            # Draw zones
            if zone_manager:
                for zone in zone_manager.get_all_zones():
                    pts = np.array(zone.polygon, dtype=np.int32)
                    # Scale to 640x480
                    pts[:, 0] = pts[:, 0] * 640 // width
                    pts[:, 1] = pts[:, 1] * 480 // height
                    color = (0, 255, 0) if zone.zone_type == "general" else (0, 165, 255)
                    cv2.polylines(display, [pts], True, color, 2)
                    
            cv2.putText(display, f"Persons: {person_count} | Risk: {risk_score:.2f}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("SwarmGrid Analysis", display)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        frame_count += 1
        
    cap.release()
    if show_video:
        cv2.destroyAllWindows()
        
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("📈 ANALYSIS SUMMARY")
    print("=" * 70)
    
    if results['person_counts']:
        avg_persons = np.mean(results['person_counts'])
        max_persons = np.max(results['person_counts'])
        avg_motion = np.mean(results['motion_densities'])
        avg_stationary = np.mean(results['stationary_densities'])
        avg_entropy = np.mean(results['flow_entropies'])
        avg_risk = np.mean(results['risk_scores'])
        max_risk = np.max(results['risk_scores'])
        
        print(f"\n  Person Detection:")
        print(f"    Average Count: {avg_persons:.1f}")
        print(f"    Maximum Count: {max_persons}")
        
        print(f"\n  Density Analysis:")
        print(f"    Motion Density: {avg_motion:.3f}")
        print(f"    Stationary Density: {avg_stationary:.3f}")
        
        print(f"\n  Flow Analysis:")
        print(f"    Average Entropy: {avg_entropy:.3f}")
        
        print(f"\n  Risk Assessment:")
        print(f"    Average Risk: {avg_risk:.3f}")
        print(f"    Maximum Risk: {max_risk:.3f}")
        
        if avg_risk < 0.3:
            status = "🟢 LOW RISK - Normal activity"
        elif avg_risk < 0.5:
            status = "🟡 MODERATE - Some congestion"
        elif avg_risk < 0.75:
            status = "🟠 ELEVATED - High activity"
        else:
            status = "🔴 CRITICAL - Dense crowd detected"
            
        print(f"\n  Overall Status: {status}")
        
    print(f"\n  Performance: {frame_count} frames in {elapsed:.1f}s ({frame_count/elapsed:.1f} FPS)")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    # Default to the user's video
    video_path = r"e:\Oguz\SwarmGrid\20260105_0016_New Video_simple_compose_01ke5dwdzrfrtvvchjzsg53cp1.mp4"
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
    show_video = "--show" in sys.argv
    
    success = analyze_video_enhanced(video_path, num_frames=50, show_video=show_video)
    sys.exit(0 if success else 1)
