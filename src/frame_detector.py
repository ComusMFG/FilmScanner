"""
Frame Detection Module
Identifies individual film frames based on sprocket hole positions.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FilmFrame:
    """Represents a detected film frame."""
    frame_number: int  # Sequential frame number in the film
    y_start: int  # Top y-coordinate
    y_end: int  # Bottom y-coordinate
    sprocket_holes: List[Tuple[int, int]]  # Sprocket holes within this frame


class FrameDetector:
    """Detects individual film frames based on sprocket hole positions."""

    def __init__(self, holes_per_frame: int = 1, frame_height_pixels: Optional[int] = None):
        """
        Initialize the frame detector.

        Args:
            holes_per_frame: Number of sprocket holes per film frame (typically 1 for 8mm)
            frame_height_pixels: Expected frame height in pixels (if known)
        """
        self.holes_per_frame = holes_per_frame
        self.frame_height_pixels = frame_height_pixels

    def detect_frames(self,
                     sprocket_holes: List[Tuple[int, int]],
                     frame_height: int,
                     sprocket_spacing: Optional[float] = None) -> List[FilmFrame]:
        """
        Detect film frames based on sprocket hole positions.

        Args:
            sprocket_holes: List of (x, y) coordinates of sprocket holes
            frame_height: Height of the video frame in pixels
            sprocket_spacing: Average spacing between sprocket holes

        Returns:
            List of detected FilmFrame objects
        """
        if not sprocket_holes:
            return []

        # Calculate spacing if not provided
        if sprocket_spacing is None:
            if len(sprocket_holes) < 2:
                # Fallback: use entire frame height
                sprocket_spacing = frame_height
            else:
                spacings = []
                for i in range(len(sprocket_holes) - 1):
                    spacings.append(sprocket_holes[i + 1][1] - sprocket_holes[i][1])
                sprocket_spacing = np.median(spacings)

        frames = []

        if self.holes_per_frame == 1:
            # For 8mm film: one sprocket hole per frame
            # Frame boundaries are centered between sprocket holes
            for i, hole in enumerate(sprocket_holes):
                # Calculate frame boundaries
                if i == 0:
                    y_start = max(0, hole[1] - int(sprocket_spacing / 2))
                else:
                    y_start = int((sprocket_holes[i - 1][1] + hole[1]) / 2)

                if i == len(sprocket_holes) - 1:
                    y_end = min(frame_height, hole[1] + int(sprocket_spacing / 2))
                else:
                    y_end = int((hole[1] + sprocket_holes[i + 1][1]) / 2)

                # Create FilmFrame
                film_frame = FilmFrame(
                    frame_number=i,
                    y_start=y_start,
                    y_end=y_end,
                    sprocket_holes=[hole]
                )
                frames.append(film_frame)
        else:
            # For other film types with multiple holes per frame
            # Group holes into frames
            for i in range(0, len(sprocket_holes), self.holes_per_frame):
                frame_holes = sprocket_holes[i:i + self.holes_per_frame]

                if not frame_holes:
                    continue

                # Calculate frame boundaries
                first_hole_y = frame_holes[0][1]
                last_hole_y = frame_holes[-1][1]

                y_start = first_hole_y - int(sprocket_spacing / 2)
                y_end = last_hole_y + int(sprocket_spacing / 2)

                # Clamp to frame boundaries
                y_start = max(0, y_start)
                y_end = min(frame_height, y_end)

                film_frame = FilmFrame(
                    frame_number=i // self.holes_per_frame,
                    y_start=y_start,
                    y_end=y_end,
                    sprocket_holes=frame_holes
                )
                frames.append(film_frame)

        return frames

    def estimate_frame_position(self,
                                y_position: int,
                                sprocket_spacing: float,
                                reference_hole: Tuple[int, int]) -> float:
        """
        Estimate which film frame a given y-position corresponds to.

        Args:
            y_position: Y-coordinate to check
            sprocket_spacing: Spacing between sprocket holes
            reference_hole: Reference sprocket hole (x, y)

        Returns:
            Estimated frame number (can be fractional)
        """
        relative_y = y_position - reference_hole[1]
        frame_position = relative_y / sprocket_spacing

        return float(frame_position)

    def get_frame_roi(self, film_frame: FilmFrame, video_frame_width: int,
                     sprocket_region: Tuple[float, float] = (0.0, 0.15)) -> Tuple[int, int, int, int]:
        """
        Get the region of interest for a film frame, excluding sprocket holes.

        Args:
            film_frame: The FilmFrame object
            video_frame_width: Width of the video frame
            sprocket_region: (left_ratio, right_ratio) where sprocket holes are located

        Returns:
            ROI as (x, y, w, h)
        """
        x = int(video_frame_width * sprocket_region[1]) + 10
        y = film_frame.y_start
        w = video_frame_width - x - 10
        h = film_frame.y_end - film_frame.y_start

        return (x, y, w, h)
