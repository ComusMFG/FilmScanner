"""
Film Processor Module
Main processing pipeline for converting continuous film video to individual frames.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Callable
from tqdm import tqdm

from .sprocket_detector import SprocketDetector
from .frame_detector import FrameDetector
from .frame_tracker import FrameTracker
from .sharpness_analyzer import SharpnessAnalyzer


class FilmProcessor:
    """Main processor for 8mm film digitization."""

    def __init__(self,
                 min_hole_area: int = 50,
                 max_hole_area: int = 5000,
                 detection_region: tuple = (0.0, 0.15),
                 threshold_value: int = 50,
                 holes_per_frame: int = 1,
                 target_frame_height: Optional[int] = None):
        """
        Initialize the film processor.

        Args:
            min_hole_area: Minimum sprocket hole area in pixels
            max_hole_area: Maximum sprocket hole area in pixels
            detection_region: (left, right) ratios for sprocket detection
            threshold_value: Threshold for sprocket detection
            holes_per_frame: Number of sprocket holes per film frame
            target_frame_height: Target output frame height (None = original)
        """
        self.sprocket_detector = SprocketDetector(
            min_hole_area=min_hole_area,
            max_hole_area=max_hole_area,
            detection_region=detection_region,
            threshold_value=threshold_value
        )
        self.frame_detector = FrameDetector(holes_per_frame=holes_per_frame)
        self.frame_tracker = FrameTracker(target_frame_height=target_frame_height)
        self.detection_region = detection_region

    def process_video(self,
                     input_path: str,
                     output_path: Optional[str] = None,
                     output_fps: float = 18.0,
                     fourcc: str = 'mp4v',
                     debug: bool = False,
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> dict:
        """
        Process a video file of continuous film capture.

        Args:
            input_path: Path to input video file
            output_path: Path for output video (None = auto-generate)
            output_fps: Frame rate for output video
            fourcc: FourCC code for output video codec
            debug: Whether to save debug visualization
            progress_callback: Optional callback function(current, total)

        Returns:
            Dictionary with processing statistics
        """
        # Open input video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")

        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Input video: {input_path}")
        print(f"  Resolution: {frame_width}x{frame_height}")
        print(f"  FPS: {input_fps}")
        print(f"  Total frames: {total_frames}")
        print(f"\nProcessing frames...")

        # Process each video frame
        video_frame_idx = 0
        sprocket_spacing = None

        with tqdm(total=total_frames, desc="Analyzing video", unit="frame") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Detect sprocket holes
                sprocket_holes = self.sprocket_detector.detect_sprocket_holes(frame)

                # Update sprocket spacing estimate
                if len(sprocket_holes) >= 2:
                    spacing = self.sprocket_detector.get_sprocket_spacing(sprocket_holes)
                    if spacing:
                        if sprocket_spacing is None:
                            sprocket_spacing = spacing
                        else:
                            # Smooth the spacing estimate
                            sprocket_spacing = 0.9 * sprocket_spacing + 0.1 * spacing

                # Detect film frames
                film_frames = self.frame_detector.detect_frames(
                    sprocket_holes, frame_height, sprocket_spacing
                )

                # Track frames
                self.frame_tracker.process_video_frame(
                    frame, video_frame_idx, film_frames, self.detection_region
                )

                video_frame_idx += 1
                pbar.update(1)

                if progress_callback:
                    progress_callback(video_frame_idx, total_frames)

        cap.release()

        # Get output frames
        print("\nExtracting best frames...")
        output_frames = self.frame_tracker.get_output_frames(sorted_by_number=True)

        if not output_frames:
            raise ValueError("No frames were extracted from the video!")

        print(f"Extracted {len(output_frames)} frames")

        # Write output video if path specified
        if output_path:
            self._write_output_video(output_frames, output_path, output_fps, fourcc)

        # Get statistics
        stats = self.frame_tracker.get_statistics()
        stats['output_frames'] = len(output_frames)
        stats['input_frames'] = total_frames
        stats['output_fps'] = output_fps

        return stats

    def _write_output_video(self,
                           frames: list,
                           output_path: str,
                           fps: float,
                           fourcc: str):
        """
        Write frames to an output video file.

        Args:
            frames: List of frame images
            output_path: Output video path
            fps: Output frame rate
            fourcc: FourCC codec code
        """
        if not frames:
            return

        # Get output dimensions from first frame
        first_frame = frames[0]
        height, width = first_frame.shape[:2]

        # Create output directory if needed
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create video writer
        fourcc_code = cv2.VideoWriter_fourcc(*fourcc)
        out = cv2.VideoWriter(output_path, fourcc_code, fps, (width, height))

        if not out.isOpened():
            raise ValueError(f"Could not create output video: {output_path}")

        print(f"\nWriting output video: {output_path}")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps}")
        print(f"  Frames: {len(frames)}")

        # Write frames
        with tqdm(total=len(frames), desc="Writing video", unit="frame") as pbar:
            for frame in frames:
                # Ensure frame is BGR
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

                # Ensure correct size
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))

                out.write(frame)
                pbar.update(1)

        out.release()
        print(f"✓ Output video saved successfully")

    def save_frames_as_images(self,
                              frames: list,
                              output_dir: str,
                              prefix: str = "frame",
                              format: str = "png"):
        """
        Save individual frames as image files.

        Args:
            frames: List of frame images
            output_dir: Output directory path
            prefix: Filename prefix
            format: Image format (png, jpg, etc.)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving {len(frames)} frames to {output_dir}")

        with tqdm(total=len(frames), desc="Saving images", unit="frame") as pbar:
            for idx, frame in enumerate(frames):
                filename = f"{prefix}_{idx:06d}.{format}"
                filepath = output_path / filename
                cv2.imwrite(str(filepath), frame)
                pbar.update(1)

        print(f"✓ Frames saved successfully")
