#!/usr/bin/env python3
"""
Test Sprocket Detection
Interactive tool to test and tune sprocket detection parameters.
"""

import sys
import cv2
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sprocket_detector import SprocketDetector


def test_sprocket_detection(video_path, frame_number=0):
    """
    Test sprocket detection on a single frame with visualization.

    Args:
        video_path: Path to input video
        frame_number: Which frame to test (default: 0)
    """
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return

    # Seek to frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"Error: Could not read frame {frame_number}")
        return

    print(f"Testing frame {frame_number}")
    print(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
    print("\nAdjust parameters and press keys:")
    print("  t/T: Decrease/Increase threshold")
    print("  a/A: Decrease/Increase min area")
    print("  s/S: Decrease/Increase max area")
    print("  r/R: Decrease/Increase right detection boundary")
    print("  q: Quit")
    print("  Space: Print current parameters")

    # Initial parameters
    threshold = 50
    min_area = 50
    max_area = 5000
    detection_right = 0.15

    while True:
        # Create detector with current parameters
        detector = SprocketDetector(
            min_hole_area=min_area,
            max_hole_area=max_area,
            detection_region=(0.0, detection_right),
            threshold_value=threshold
        )

        # Detect holes
        holes = detector.detect_sprocket_holes(frame)

        # Create visualization
        vis_frame = detector.visualize_detection(frame, holes)

        # Add parameter text
        text_y = 30
        cv2.putText(vis_frame, f"Threshold: {threshold}", (10, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        text_y += 30
        cv2.putText(vis_frame, f"Min Area: {min_area}", (10, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        text_y += 30
        cv2.putText(vis_frame, f"Max Area: {max_area}", (10, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        text_y += 30
        cv2.putText(vis_frame, f"Detection Right: {detection_right:.2f}", (10, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        text_y += 30
        cv2.putText(vis_frame, f"Holes Found: {len(holes)}", (10, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show
        cv2.imshow('Sprocket Detection Test', vis_frame)

        # Handle keys
        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('t'):
            threshold = max(10, threshold - 5)
        elif key == ord('T'):
            threshold = min(200, threshold + 5)
        elif key == ord('a'):
            min_area = max(10, min_area - 10)
        elif key == ord('A'):
            min_area = min(1000, min_area + 10)
        elif key == ord('s'):
            max_area = max(100, max_area - 100)
        elif key == ord('S'):
            max_area = min(20000, max_area + 100)
        elif key == ord('r'):
            detection_right = max(0.05, detection_right - 0.01)
        elif key == ord('R'):
            detection_right = min(0.5, detection_right + 0.01)
        elif key == ord(' '):
            print(f"\nCurrent parameters:")
            print(f"  --threshold {threshold}")
            print(f"  --min-area {min_area}")
            print(f"  --max-area {max_area}")
            print(f"  --detection-right {detection_right:.2f}")

    cv2.destroyAllWindows()
    print("\nFinal parameters:")
    print(f"  --threshold {threshold}")
    print(f"  --min-area {min_area}")
    print(f"  --max-area {max_area}")
    print(f"  --detection-right {detection_right:.2f}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_sprocket_detection.py <video_file> [frame_number]")
        sys.exit(1)

    video_path = sys.argv[1]
    frame_number = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    test_sprocket_detection(video_path, frame_number)
