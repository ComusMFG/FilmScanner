#!/usr/bin/env python3
"""
FilmScanner CLI
Command-line interface for 8mm film digitization.
"""

import argparse
import sys
from pathlib import Path
from src.film_processor import FilmProcessor


def main():
    parser = argparse.ArgumentParser(
        description='Process continuous 8mm film video into individual frames',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - process video with default settings
  python film_scanner.py input.mp4 -o output.mp4

  # Specify output frame rate (default is 18 fps for 8mm film)
  python film_scanner.py input.mp4 -o output.mp4 --fps 24

  # Save frames as individual images instead of video
  python film_scanner.py input.mp4 --save-images output_frames/

  # Adjust sprocket detection parameters for different lighting
  python film_scanner.py input.mp4 -o output.mp4 --threshold 40 --min-area 30 --max-area 3000

  # Resize output frames to specific height (maintains aspect ratio)
  python film_scanner.py input.mp4 -o output.mp4 --height 720
        """
    )

    # Required arguments
    parser.add_argument('input', type=str,
                       help='Input video file path')

    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument('-o', '--output', type=str,
                             help='Output video file path')
    output_group.add_argument('--save-images', type=str, metavar='DIR',
                             help='Save frames as images to directory')
    output_group.add_argument('--fps', type=float, default=18.0,
                             help='Output video frame rate (default: 18 for 8mm film)')
    output_group.add_argument('--codec', type=str, default='mp4v',
                             help='Output video codec FourCC code (default: mp4v)')
    output_group.add_argument('--height', type=int,
                             help='Target output frame height in pixels (default: original)')

    # Sprocket detection options
    sprocket_group = parser.add_argument_group('sprocket detection options')
    sprocket_group.add_argument('--threshold', type=int, default=50,
                               help='Binary threshold for sprocket detection (default: 50)')
    sprocket_group.add_argument('--min-area', type=int, default=50,
                               help='Minimum sprocket hole area in pixels (default: 50)')
    sprocket_group.add_argument('--max-area', type=int, default=5000,
                               help='Maximum sprocket hole area in pixels (default: 5000)')
    sprocket_group.add_argument('--detection-left', type=float, default=0.0,
                               help='Left boundary of sprocket detection region as ratio (default: 0.0)')
    sprocket_group.add_argument('--detection-right', type=float, default=0.15,
                               help='Right boundary of sprocket detection region as ratio (default: 0.15)')
    sprocket_group.add_argument('--holes-per-frame', type=int, default=1,
                               help='Number of sprocket holes per film frame (default: 1 for 8mm)')

    # Processing options
    proc_group = parser.add_argument_group('processing options')
    proc_group.add_argument('--debug', action='store_true',
                           help='Enable debug output')

    args = parser.parse_args()

    # Validate arguments
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    if not args.output and not args.save_images:
        print("Error: Must specify either --output or --save-images", file=sys.stderr)
        return 1

    # Create processor
    try:
        processor = FilmProcessor(
            min_hole_area=args.min_area,
            max_hole_area=args.max_area,
            detection_region=(args.detection_left, args.detection_right),
            threshold_value=args.threshold,
            holes_per_frame=args.holes_per_frame,
            target_frame_height=args.height
        )

        # Process video
        print("=" * 70)
        print("FilmScanner - 8mm Film Digitization")
        print("=" * 70)

        stats = processor.process_video(
            input_path=args.input,
            output_path=args.output,
            output_fps=args.fps,
            fourcc=args.codec,
            debug=args.debug
        )

        # Save as images if requested
        if args.save_images:
            frames = processor.frame_tracker.get_output_frames()
            processor.save_frames_as_images(frames, args.save_images)

        # Print statistics
        print("\n" + "=" * 70)
        print("PROCESSING STATISTICS")
        print("=" * 70)
        print(f"Input frames processed:      {stats['input_frames']}")
        print(f"Film frames extracted:       {stats['total_film_frames']}")
        print(f"Output frames generated:     {stats['output_frames']}")
        print(f"Avg candidates per frame:    {stats['avg_candidates_per_frame']:.1f}")
        print(f"Frames with >1 candidate:    {stats['frames_with_multiple_candidates']}")
        if stats['avg_sharpness_improvement'] > 0:
            print(f"Avg sharpness improvement:   {stats['avg_sharpness_improvement']*100:.1f}%")
        print("=" * 70)
        print("✓ Processing complete!")

        return 0

    except Exception as e:
        print(f"\nError during processing: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
