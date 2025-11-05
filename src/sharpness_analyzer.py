"""
Sharpness Analysis Module
Calculates image sharpness metrics to identify the best-focused frame.
"""

import cv2
import numpy as np
from typing import Optional


class SharpnessAnalyzer:
    """Analyzes image sharpness using multiple metrics."""

    @staticmethod
    def calculate_laplacian_variance(frame: np.ndarray,
                                     roi: Optional[tuple] = None) -> float:
        """
        Calculate Laplacian variance as a sharpness metric.
        Higher values indicate sharper images.

        Args:
            frame: Input frame (BGR or grayscale)
            roi: Optional region of interest as (x, y, w, h)

        Returns:
            Laplacian variance (sharpness score)
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Extract ROI if specified
        if roi:
            x, y, w, h = roi
            gray = gray[y:y+h, x:x+w]

        # Calculate Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)

        # Return variance
        return float(laplacian.var())

    @staticmethod
    def calculate_gradient_magnitude(frame: np.ndarray,
                                     roi: Optional[tuple] = None) -> float:
        """
        Calculate mean gradient magnitude as a sharpness metric.

        Args:
            frame: Input frame (BGR or grayscale)
            roi: Optional region of interest as (x, y, w, h)

        Returns:
            Mean gradient magnitude
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Extract ROI if specified
        if roi:
            x, y, w, h = roi
            gray = gray[y:y+h, x:x+w]

        # Calculate gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate magnitude
        magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Return mean magnitude
        return float(magnitude.mean())

    @staticmethod
    def calculate_tenengrad(frame: np.ndarray,
                           roi: Optional[tuple] = None,
                           threshold: float = 0.0) -> float:
        """
        Calculate Tenengrad focus measure (Sobel-based).

        Args:
            frame: Input frame (BGR or grayscale)
            roi: Optional region of interest as (x, y, w, h)
            threshold: Threshold for gradient values to consider

        Returns:
            Tenengrad score
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Extract ROI if specified
        if roi:
            x, y, w, h = roi
            gray = gray[y:y+h, x:x+w]

        # Calculate Sobel gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate squared magnitude
        magnitude_sq = grad_x**2 + grad_y**2

        # Apply threshold if specified
        if threshold > 0:
            magnitude_sq = magnitude_sq[magnitude_sq > threshold**2]

        # Return sum
        return float(magnitude_sq.sum())

    @staticmethod
    def calculate_combined_sharpness(frame: np.ndarray,
                                    roi: Optional[tuple] = None) -> float:
        """
        Calculate a combined sharpness metric using multiple methods.

        Args:
            frame: Input frame (BGR or grayscale)
            roi: Optional region of interest as (x, y, w, h)

        Returns:
            Combined sharpness score (normalized)
        """
        # Calculate individual metrics
        lap_var = SharpnessAnalyzer.calculate_laplacian_variance(frame, roi)
        grad_mag = SharpnessAnalyzer.calculate_gradient_magnitude(frame, roi)
        tenengrad = SharpnessAnalyzer.calculate_tenengrad(frame, roi)

        # Normalize and combine (weighted average)
        # These weights can be tuned based on empirical performance
        combined = (
            0.4 * lap_var / (1 + lap_var) +
            0.3 * grad_mag / (1 + grad_mag) +
            0.3 * tenengrad / (1 + tenengrad)
        )

        return float(combined)

    @staticmethod
    def get_film_frame_roi(frame_shape: tuple,
                          sprocket_region: tuple = (0.0, 0.15)) -> tuple:
        """
        Get the ROI for the actual film frame, excluding sprocket holes.

        Args:
            frame_shape: Shape of the frame (height, width) or (height, width, channels)
            sprocket_region: (left_ratio, right_ratio) where sprocket holes are located

        Returns:
            ROI as (x, y, w, h)
        """
        height = frame_shape[0]
        width = frame_shape[1] if len(frame_shape) > 1 else frame_shape[0]

        # Define ROI excluding sprocket region
        x = int(width * sprocket_region[1]) + 10  # Small margin
        y = 0
        w = width - x - 10  # Margin on right side too
        h = height

        return (x, y, w, h)
