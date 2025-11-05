"""
Frame Tracking Module
Tracks film frames across video frames and selects the best (sharpest) instance.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from .frame_detector import FilmFrame
from .sharpness_analyzer import SharpnessAnalyzer


@dataclass
class FrameCandidate:
    """Represents a candidate image for a film frame."""
    video_frame_idx: int
    film_frame_number: int
    image: np.ndarray
    sharpness_score: float
    y_offset: int  # Vertical offset in the video frame


@dataclass
class TrackedFrame:
    """Represents a tracked film frame with multiple candidates."""
    film_frame_number: int
    candidates: List[FrameCandidate] = field(default_factory=list)
    best_candidate: Optional[FrameCandidate] = None

    def add_candidate(self, candidate: FrameCandidate):
        """Add a candidate and update best if necessary."""
        self.candidates.append(candidate)

        if self.best_candidate is None or candidate.sharpness_score > self.best_candidate.sharpness_score:
            self.best_candidate = candidate

    def get_best_image(self) -> Optional[np.ndarray]:
        """Get the best (sharpest) image for this frame."""
        if self.best_candidate:
            return self.best_candidate.image
        return None


class FrameTracker:
    """Tracks film frames across video and selects best instances."""

    def __init__(self,
                 target_frame_height: Optional[int] = None,
                 min_candidates: int = 3):
        """
        Initialize the frame tracker.

        Args:
            target_frame_height: Target height for output frames (None = use original)
            min_candidates: Minimum number of candidate frames before selecting best
        """
        self.target_frame_height = target_frame_height
        self.min_candidates = min_candidates
        self.tracked_frames: Dict[int, TrackedFrame] = {}
        self.sharpness_analyzer = SharpnessAnalyzer()

    def process_video_frame(self,
                           video_frame: np.ndarray,
                           video_frame_idx: int,
                           film_frames: List[FilmFrame],
                           sprocket_region: Tuple[float, float] = (0.0, 0.15)):
        """
        Process a video frame and extract film frame candidates.

        Args:
            video_frame: The video frame to process
            video_frame_idx: Index of this video frame
            film_frames: List of detected film frames in this video frame
            sprocket_region: Region where sprocket holes are located
        """
        frame_height, frame_width = video_frame.shape[:2]

        for film_frame in film_frames:
            # Extract the film frame region (excluding sprocket holes)
            x = int(frame_width * sprocket_region[1]) + 10
            y = film_frame.y_start
            w = frame_width - x - 10
            h = film_frame.y_end - film_frame.y_start

            # Validate dimensions
            if h <= 0 or w <= 0 or y < 0 or y + h > frame_height:
                continue

            # Extract the image
            film_frame_img = video_frame[y:y+h, x:x+w].copy()

            # Calculate sharpness
            roi = (0, 0, w, h)  # Use entire extracted region
            sharpness = self.sharpness_analyzer.calculate_laplacian_variance(
                film_frame_img, roi
            )

            # Resize if target height specified
            if self.target_frame_height and h != self.target_frame_height:
                aspect_ratio = w / h
                target_width = int(self.target_frame_height * aspect_ratio)
                film_frame_img = cv2.resize(
                    film_frame_img,
                    (target_width, self.target_frame_height),
                    interpolation=cv2.INTER_CUBIC
                )

            # Create candidate
            candidate = FrameCandidate(
                video_frame_idx=video_frame_idx,
                film_frame_number=film_frame.frame_number,
                image=film_frame_img,
                sharpness_score=sharpness,
                y_offset=y
            )

            # Add to tracked frames
            if film_frame.frame_number not in self.tracked_frames:
                self.tracked_frames[film_frame.frame_number] = TrackedFrame(
                    film_frame_number=film_frame.frame_number
                )

            self.tracked_frames[film_frame.frame_number].add_candidate(candidate)

    def get_output_frames(self, sorted_by_number: bool = True) -> List[np.ndarray]:
        """
        Get the best frames for output.

        Args:
            sorted_by_number: Whether to sort frames by frame number

        Returns:
            List of best frame images
        """
        if sorted_by_number:
            frame_numbers = sorted(self.tracked_frames.keys())
        else:
            frame_numbers = list(self.tracked_frames.keys())

        output_frames = []
        for frame_num in frame_numbers:
            tracked = self.tracked_frames[frame_num]
            best_img = tracked.get_best_image()
            if best_img is not None:
                output_frames.append(best_img)

        return output_frames

    def get_statistics(self) -> Dict:
        """
        Get statistics about tracked frames.

        Returns:
            Dictionary with statistics
        """
        total_frames = len(self.tracked_frames)
        total_candidates = sum(len(tf.candidates) for tf in self.tracked_frames.values())

        candidates_per_frame = []
        sharpness_improvements = []

        for tracked in self.tracked_frames.values():
            candidates_per_frame.append(len(tracked.candidates))

            if len(tracked.candidates) > 1:
                scores = [c.sharpness_score for c in tracked.candidates]
                improvement = (max(scores) - min(scores)) / (min(scores) + 1e-6)
                sharpness_improvements.append(improvement)

        return {
            'total_film_frames': total_frames,
            'total_candidates': total_candidates,
            'avg_candidates_per_frame': np.mean(candidates_per_frame) if candidates_per_frame else 0,
            'avg_sharpness_improvement': np.mean(sharpness_improvements) if sharpness_improvements else 0,
            'frames_with_multiple_candidates': sum(1 for c in candidates_per_frame if c > 1)
        }

    def visualize_candidates(self, film_frame_number: int) -> Optional[np.ndarray]:
        """
        Create a visualization showing all candidates for a film frame.

        Args:
            film_frame_number: The film frame number to visualize

        Returns:
            Composite image showing all candidates, or None if frame not found
        """
        if film_frame_number not in self.tracked_frames:
            return None

        tracked = self.tracked_frames[film_frame_number]
        candidates = tracked.candidates

        if not candidates:
            return None

        # Sort by sharpness (best first)
        sorted_candidates = sorted(candidates, key=lambda c: c.sharpness_score, reverse=True)

        # Create a grid
        num_candidates = len(sorted_candidates)
        cols = min(4, num_candidates)
        rows = (num_candidates + cols - 1) // cols

        # Get dimensions from first candidate
        h, w = sorted_candidates[0].image.shape[:2]

        # Create canvas
        canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)

        for idx, candidate in enumerate(sorted_candidates):
            row = idx // cols
            col = idx % cols

            img = candidate.image.copy()
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            # Add text overlay
            text = f"Sharp: {candidate.sharpness_score:.1f}"
            cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (0, 255, 0), 1)

            # Highlight best candidate
            if candidate == tracked.best_candidate:
                cv2.rectangle(img, (0, 0), (w-1, h-1), (0, 255, 0), 3)

            # Place in canvas
            canvas[row*h:(row+1)*h, col*w:(col+1)*w] = img

        return canvas
