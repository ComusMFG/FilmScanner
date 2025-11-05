#!/usr/bin/env python3
"""
Programmatic Usage Example
Demonstrates how to use FilmScanner as a library in your own code.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import FilmProcessor


def basic_processing():
    """Basic example: Process a video with default settings."""
    processor = FilmProcessor()

    stats = processor.process_video(
        input_path='input.mp4',
        output_path='output.mp4',
        output_fps=18.0
    )

    print(f"Processed {stats['output_frames']} frames")


def custom_parameters():
    """Example with custom parameters."""
    processor = FilmProcessor(
        min_hole_area=30,           # Smaller sprocket holes
        max_hole_area=3000,         # Adjust for your setup
        detection_region=(0.0, 0.2), # Search left 20% of frame
        threshold_value=40,         # More sensitive detection
        holes_per_frame=1,          # 8mm film standard
        target_frame_height=720     # Resize to 720p
    )

    stats = processor.process_video(
        input_path='my_film.mp4',
        output_path='processed_film.mp4',
        output_fps=24.0,
        fourcc='avc1'  # H.264 codec
    )

    return stats


def save_individual_frames():
    """Example: Extract frames as individual images."""
    processor = FilmProcessor()

    # Process video (no output video)
    stats = processor.process_video(
        input_path='input.mp4',
        output_path=None,  # Don't create video
        output_fps=18.0
    )

    # Get the processed frames
    frames = processor.frame_tracker.get_output_frames()

    # Save as images
    processor.save_frames_as_images(
        frames=frames,
        output_dir='output_frames',
        prefix='frame',
        format='png'
    )

    print(f"Saved {len(frames)} images")


def custom_processing_with_callback():
    """Example with progress callback."""
    def progress_callback(current, total):
        percent = (current / total) * 100
        if current % 100 == 0:  # Print every 100 frames
            print(f"Progress: {current}/{total} ({percent:.1f}%)")

    processor = FilmProcessor()

    stats = processor.process_video(
        input_path='input.mp4',
        output_path='output.mp4',
        output_fps=18.0,
        progress_callback=progress_callback
    )

    return stats


def access_detailed_tracking_info():
    """Example: Access detailed frame tracking information."""
    processor = FilmProcessor()

    stats = processor.process_video(
        input_path='input.mp4',
        output_path=None
    )

    # Access the frame tracker
    tracker = processor.frame_tracker

    # Get statistics
    stats = tracker.get_statistics()
    print(f"Total film frames: {stats['total_film_frames']}")
    print(f"Average candidates per frame: {stats['avg_candidates_per_frame']:.2f}")
    print(f"Average sharpness improvement: {stats['avg_sharpness_improvement']*100:.1f}%")

    # Access individual tracked frames
    for frame_num, tracked_frame in tracker.tracked_frames.items():
        print(f"\nFrame {frame_num}:")
        print(f"  Candidates: {len(tracked_frame.candidates)}")
        if tracked_frame.best_candidate:
            print(f"  Best sharpness: {tracked_frame.best_candidate.sharpness_score:.2f}")

    # Get frames
    output_frames = tracker.get_output_frames()
    print(f"\nTotal output frames: {len(output_frames)}")


def visualize_candidate_selection():
    """Example: Visualize how candidates were selected for a specific frame."""
    import cv2

    processor = FilmProcessor()

    # Process video
    processor.process_video(
        input_path='input.mp4',
        output_path=None
    )

    # Visualize candidates for frame 10
    frame_num = 10
    visualization = processor.frame_tracker.visualize_candidates(frame_num)

    if visualization is not None:
        cv2.imwrite(f'frame_{frame_num}_candidates.png', visualization)
        print(f"Saved visualization for frame {frame_num}")


if __name__ == '__main__':
    print("FilmScanner Programmatic Usage Examples")
    print("=" * 50)
    print("\nSee the functions in this file for usage examples:")
    print("  - basic_processing()")
    print("  - custom_parameters()")
    print("  - save_individual_frames()")
    print("  - custom_processing_with_callback()")
    print("  - access_detailed_tracking_info()")
    print("  - visualize_candidate_selection()")
    print("\nModify this file to run the examples you want to try.")
