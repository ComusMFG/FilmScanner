"""
Sprocket Hole Detection Module
Detects 8mm film sprocket holes in video frames to identify frame boundaries.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class SprocketDetector:
    """Detects sprocket holes in 8mm film frames."""

    def __init__(self,
                 min_hole_area: int = 50,
                 max_hole_area: int = 5000,
                 detection_region: Optional[Tuple[float, float]] = None,
                 threshold_value: int = 50):
        """
        Initialize the sprocket detector.

        Args:
            min_hole_area: Minimum area in pixels for a valid sprocket hole
            max_hole_area: Maximum area in pixels for a valid sprocket hole
            detection_region: (left_ratio, right_ratio) defining the horizontal region to search
                             e.g., (0.0, 0.15) searches the left 15% of the frame
            threshold_value: Threshold for binary conversion (sprocket holes are typically dark)
        """
        self.min_hole_area = min_hole_area
        self.max_hole_area = max_hole_area
        self.detection_region = detection_region or (0.0, 0.15)  # Default to left edge
        self.threshold_value = threshold_value

    def detect_sprocket_holes(self, frame: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect sprocket holes in a frame.

        Args:
            frame: Input frame (BGR or grayscale)

        Returns:
            List of (x, y) coordinates of detected sprocket hole centers
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()

        # Extract detection region
        height, width = gray.shape
        left_x = int(width * self.detection_region[0])
        right_x = int(width * self.detection_region[1])
        roi = gray[:, left_x:right_x]

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(roi, (5, 5), 0)

        # Threshold to find dark regions (sprocket holes)
        _, binary = cv2.threshold(blurred, self.threshold_value, 255, cv2.THRESH_BINARY_INV)

        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area and extract centers
        holes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_hole_area <= area <= self.max_hole_area:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"]) + left_x
                    cy = int(M["m01"] / M["m00"])
                    holes.append((cx, cy))

        # Sort by y-coordinate (top to bottom)
        holes.sort(key=lambda h: h[1])

        return holes

    def get_sprocket_spacing(self, holes: List[Tuple[int, int]]) -> Optional[float]:
        """
        Calculate the average vertical spacing between sprocket holes.

        Args:
            holes: List of sprocket hole centers

        Returns:
            Average spacing in pixels, or None if insufficient holes
        """
        if len(holes) < 2:
            return None

        spacings = []
        for i in range(len(holes) - 1):
            spacing = holes[i + 1][1] - holes[i][1]
            spacings.append(spacing)

        # Use median to be robust against outliers
        return float(np.median(spacings))

    def visualize_detection(self, frame: np.ndarray, holes: List[Tuple[int, int]]) -> np.ndarray:
        """
        Create a visualization of detected sprocket holes.

        Args:
            frame: Input frame
            holes: List of detected hole centers

        Returns:
            Frame with visualized detections
        """
        vis_frame = frame.copy()

        # Draw detection region
        height, width = frame.shape[:2]
        left_x = int(width * self.detection_region[0])
        right_x = int(width * self.detection_region[1])
        cv2.rectangle(vis_frame, (left_x, 0), (right_x, height), (255, 255, 0), 2)

        # Draw detected holes
        for x, y in holes:
            cv2.circle(vis_frame, (x, y), 10, (0, 255, 0), 2)
            cv2.circle(vis_frame, (x, y), 2, (0, 0, 255), -1)

        return vis_frame
