#!/usr/bin/env python3
"""
Film Speed Calculator
Helps determine optimal film transit speed for sharp exposures based on
capture camera settings and film format.
"""

import sys
import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class FilmFormat:
    """Film format specifications."""
    name: str
    frame_height_mm: float  # Height of one film frame
    frame_pitch_mm: float   # Distance between frames (including border)
    frame_width_mm: float   # Width of one film frame


# Standard film format specifications
FILM_FORMATS = {
    '8mm': FilmFormat(
        name='Regular 8mm',
        frame_height_mm=4.88,
        frame_pitch_mm=4.88,  # Frame height = pitch for 8mm
        frame_width_mm=3.68
    ),
    'super8': FilmFormat(
        name='Super 8',
        frame_height_mm=5.79,
        frame_pitch_mm=4.23,  # Smaller pitch due to smaller borders
        frame_width_mm=5.36
    ),
    '16mm': FilmFormat(
        name='16mm',
        frame_height_mm=7.49,
        frame_pitch_mm=7.62,  # Standard 16mm pitch
        frame_width_mm=10.26
    )
}


class FilmSpeedCalculator:
    """Calculator for optimal film transit speed."""

    def __init__(self,
                 capture_fps: float,
                 film_format: FilmFormat,
                 capture_resolution_height: int = 1080,
                 shutter_angle: float = 180.0,
                 min_captures_per_frame: int = 5,
                 max_blur_pixels: float = 2.0):
        """
        Initialize the calculator.

        Args:
            capture_fps: Camera capture frame rate
            film_format: Film format specification
            capture_resolution_height: Camera vertical resolution in pixels
            shutter_angle: Camera shutter angle in degrees (180° = 50% exposure)
            min_captures_per_frame: Minimum camera frames per film frame desired
            max_blur_pixels: Maximum acceptable motion blur in pixels
        """
        self.capture_fps = capture_fps
        self.film_format = film_format
        self.capture_resolution_height = capture_resolution_height
        self.shutter_angle = shutter_angle
        self.min_captures_per_frame = min_captures_per_frame
        self.max_blur_pixels = max_blur_pixels

    def calculate_exposure_time(self) -> float:
        """
        Calculate exposure time per frame in seconds.

        Returns:
            Exposure time in seconds
        """
        # Exposure time based on shutter angle
        # 360° = full frame time, 180° = half frame time
        frame_time = 1.0 / self.capture_fps
        exposure_time = frame_time * (self.shutter_angle / 360.0)
        return exposure_time

    def calculate_pixels_per_mm(self, film_area_coverage: float = 0.8) -> float:
        """
        Calculate how many pixels correspond to 1mm of film.

        Args:
            film_area_coverage: What fraction of frame height contains film (0.8 = 80%)

        Returns:
            Pixels per millimeter
        """
        # Assume film height covers this fraction of the camera's vertical resolution
        pixels_for_film_frame = self.capture_resolution_height * film_area_coverage
        pixels_per_mm = pixels_for_film_frame / self.film_format.frame_height_mm
        return pixels_per_mm

    def calculate_max_speed_for_sharpness(self,
                                         film_area_coverage: float = 0.8) -> float:
        """
        Calculate maximum film speed to maintain sharpness.

        Args:
            film_area_coverage: What fraction of frame height contains film

        Returns:
            Maximum speed in mm/second
        """
        exposure_time = self.calculate_exposure_time()
        pixels_per_mm = self.calculate_pixels_per_mm(film_area_coverage)

        # Maximum distance film can move during exposure
        max_movement_mm = self.max_blur_pixels / pixels_per_mm

        # Speed = distance / time
        max_speed = max_movement_mm / exposure_time

        return max_speed

    def calculate_optimal_speed(self, film_area_coverage: float = 0.8) -> dict:
        """
        Calculate optimal film speed considering both sharpness and frame coverage.

        Args:
            film_area_coverage: What fraction of frame height contains film

        Returns:
            Dictionary with speed recommendations and analysis
        """
        # Maximum speed for sharpness
        max_speed_sharp = self.calculate_max_speed_for_sharpness(film_area_coverage)

        # Speed needed to get desired captures per film frame
        # Time for one film frame to pass = frame_pitch / speed
        # Number of captures = time × capture_fps
        # Therefore: captures_per_frame = (frame_pitch / speed) × capture_fps
        # Solving for speed: speed = (frame_pitch × capture_fps) / captures_per_frame
        speed_for_min_captures = (
            self.film_format.frame_pitch_mm * self.capture_fps / self.min_captures_per_frame
        )

        # Recommended speed is the slower of the two (more conservative)
        recommended_speed = min(max_speed_sharp, speed_for_min_captures)

        # Calculate actual performance at recommended speed
        exposure_time = self.calculate_exposure_time()
        pixels_per_mm = self.calculate_pixels_per_mm(film_area_coverage)

        movement_during_exposure = recommended_speed * exposure_time
        blur_pixels = movement_during_exposure * pixels_per_mm

        time_per_film_frame = self.film_format.frame_pitch_mm / recommended_speed
        captures_per_frame = time_per_film_frame * self.capture_fps

        film_fps = recommended_speed / self.film_format.frame_pitch_mm

        # Calculate speed in inches per second (common in DIY film scanners)
        mm_per_inch = 25.4
        speed_inches_per_second = recommended_speed / mm_per_inch

        return {
            'recommended_speed_mm_per_sec': recommended_speed,
            'recommended_speed_inches_per_sec': speed_inches_per_second,
            'max_speed_for_sharpness': max_speed_sharp,
            'speed_for_min_captures': speed_for_min_captures,
            'limiting_factor': 'sharpness' if max_speed_sharp < speed_for_min_captures else 'capture_coverage',
            'expected_blur_pixels': blur_pixels,
            'expected_captures_per_frame': captures_per_frame,
            'film_frames_per_second': film_fps,
            'exposure_time_ms': exposure_time * 1000,
            'pixels_per_mm': pixels_per_mm,
            'time_per_film_frame_sec': time_per_film_frame
        }

    def print_recommendations(self, film_area_coverage: float = 0.8):
        """Print detailed recommendations."""
        results = self.calculate_optimal_speed(film_area_coverage)

        print("=" * 70)
        print("FILM SPEED CALCULATOR")
        print("=" * 70)
        print(f"\nFilm Format: {self.film_format.name}")
        print(f"  Frame dimensions: {self.film_format.frame_width_mm:.2f}mm × "
              f"{self.film_format.frame_height_mm:.2f}mm")
        print(f"  Frame pitch: {self.film_format.frame_pitch_mm:.2f}mm")

        print(f"\nCamera Settings:")
        print(f"  Capture FPS: {self.capture_fps}")
        print(f"  Resolution height: {self.capture_resolution_height}px")
        print(f"  Shutter angle: {self.shutter_angle}°")
        print(f"  Exposure time: {results['exposure_time_ms']:.2f}ms")

        print(f"\nProcessing Requirements:")
        print(f"  Min captures per frame: {self.min_captures_per_frame}")
        print(f"  Max blur tolerance: {self.max_blur_pixels} pixels")

        print(f"\n" + "=" * 70)
        print("RECOMMENDED FILM SPEED")
        print("=" * 70)
        print(f"  {results['recommended_speed_mm_per_sec']:.2f} mm/sec")
        print(f"  {results['recommended_speed_inches_per_sec']:.3f} inches/sec")

        print(f"\nLimiting Factor: {results['limiting_factor'].upper()}")
        if results['limiting_factor'] == 'sharpness':
            print("  → Speed limited by motion blur during exposure")
            print(f"  → Could go faster ({results['speed_for_min_captures']:.2f} mm/s) "
                  "but would blur")
        else:
            print("  → Speed limited by need for multiple captures per frame")
            print(f"  → Could go slower for sharper images "
                  f"(max {results['max_speed_for_sharpness']:.2f} mm/s)")

        print(f"\nExpected Performance:")
        print(f"  Motion blur: {results['expected_blur_pixels']:.2f} pixels")
        print(f"  Captures per film frame: {results['expected_captures_per_frame']:.1f}")
        print(f"  Film frames per second: {results['film_frames_per_second']:.2f}")
        print(f"  Time per film frame: {results['time_per_film_frame_sec']:.3f} sec")

        print(f"\nImage Scale:")
        print(f"  {results['pixels_per_mm']:.1f} pixels per mm of film")
        print(f"  Film frame is ~{results['pixels_per_mm'] * self.film_format.frame_height_mm:.0f} "
              f"pixels tall")

        # Warnings and recommendations
        print(f"\n" + "=" * 70)
        print("SETUP RECOMMENDATIONS")
        print("=" * 70)

        if results['expected_blur_pixels'] > 1.0:
            print("⚠ WARNING: Expected blur > 1 pixel")
            print("  → Consider: slower film speed, faster shutter, or higher resolution")
        elif results['expected_blur_pixels'] < 0.3:
            print("✓ Excellent: Very sharp captures expected")
        else:
            print("✓ Good: Acceptable sharpness expected")

        if results['expected_captures_per_frame'] < 3:
            print("⚠ WARNING: Very few captures per frame")
            print("  → Consider: slower film speed or higher camera FPS")
        elif results['expected_captures_per_frame'] > 20:
            print("ℹ Info: Many captures per frame (processing will be slower)")
            print("  → Consider: faster film speed to reduce processing time")
        else:
            print(f"✓ Good: {results['expected_captures_per_frame']:.1f} captures "
                  "per frame is ideal")

        if self.capture_fps < 30:
            print("ℹ Info: Low camera FPS")
            print("  → Higher FPS (60+) recommended for better frame selection")

        print("=" * 70)


def interactive_calculator():
    """Run interactive calculator."""
    print("=" * 70)
    print("FILM SPEED CALCULATOR - Interactive Mode")
    print("=" * 70)

    # Get film format
    print("\nSelect film format:")
    print("  1. Regular 8mm")
    print("  2. Super 8")
    print("  3. 16mm")
    choice = input("Enter choice (1-3): ").strip()

    format_map = {'1': '8mm', '2': 'super8', '3': '16mm'}
    if choice not in format_map:
        print("Invalid choice!")
        return

    film_format = FILM_FORMATS[format_map[choice]]

    # Get camera settings
    print("\nEnter camera settings:")
    try:
        capture_fps = float(input("  Capture FPS (e.g., 60): ").strip())
        resolution_height = int(input("  Vertical resolution in pixels (e.g., 1080): ").strip())

        shutter_input = input("  Shutter angle in degrees (default 180°, press Enter to use default): ").strip()
        shutter_angle = float(shutter_input) if shutter_input else 180.0

        min_captures_input = input("  Minimum captures per frame (default 5, press Enter to use default): ").strip()
        min_captures = int(min_captures_input) if min_captures_input else 5

        blur_input = input("  Max acceptable blur in pixels (default 2.0, press Enter to use default): ").strip()
        max_blur = float(blur_input) if blur_input else 2.0

    except ValueError:
        print("Invalid input!")
        return

    # Calculate and display
    calculator = FilmSpeedCalculator(
        capture_fps=capture_fps,
        film_format=film_format,
        capture_resolution_height=resolution_height,
        shutter_angle=shutter_angle,
        min_captures_per_frame=min_captures,
        max_blur_pixels=max_blur
    )

    print("\n")
    calculator.print_recommendations()


def main():
    """Main CLI interface."""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("""
Film Speed Calculator
Calculates optimal film transit speed for sharp exposures.

Usage:
  python film_speed_calculator.py [options]
  python film_speed_calculator.py --interactive

Options:
  --interactive, -i     Run in interactive mode
  --format FORMAT       Film format: 8mm, super8, or 16mm
  --fps FPS            Camera capture frame rate
  --resolution HEIGHT   Camera vertical resolution in pixels
  --shutter ANGLE      Shutter angle in degrees (default: 180)
  --min-captures N     Minimum captures per frame (default: 5)
  --max-blur PIXELS    Maximum blur in pixels (default: 2.0)

Examples:
  # Interactive mode
  python film_speed_calculator.py --interactive

  # Calculate for 60fps 4K camera with Super 8 film
  python film_speed_calculator.py --format super8 --fps 60 --resolution 2160

  # Calculate for 120fps HD camera with regular 8mm
  python film_speed_calculator.py --format 8mm --fps 120 --resolution 1080 --shutter 90
""")
        return

    # Check for interactive mode
    if '--interactive' in sys.argv or '-i' in sys.argv:
        interactive_calculator()
        return

    # Parse arguments
    args = sys.argv[1:]
    params = {}

    i = 0
    while i < len(args):
        if args[i] == '--format' and i + 1 < len(args):
            params['format'] = args[i + 1]
            i += 2
        elif args[i] == '--fps' and i + 1 < len(args):
            params['fps'] = float(args[i + 1])
            i += 2
        elif args[i] == '--resolution' and i + 1 < len(args):
            params['resolution'] = int(args[i + 1])
            i += 2
        elif args[i] == '--shutter' and i + 1 < len(args):
            params['shutter'] = float(args[i + 1])
            i += 2
        elif args[i] == '--min-captures' and i + 1 < len(args):
            params['min_captures'] = int(args[i + 1])
            i += 2
        elif args[i] == '--max-blur' and i + 1 < len(args):
            params['max_blur'] = float(args[i + 1])
            i += 2
        else:
            i += 1

    # Check required parameters
    if not params:
        print("No arguments provided. Use --interactive or --help for usage information.")
        print("\nQuick start: python film_speed_calculator.py --interactive")
        return

    if 'format' not in params or 'fps' not in params:
        print("Error: --format and --fps are required")
        print("Use --help for usage information")
        return

    # Create calculator
    film_format = FILM_FORMATS.get(params['format'])
    if not film_format:
        print(f"Error: Invalid format '{params['format']}'. Use: 8mm, super8, or 16mm")
        return

    calculator = FilmSpeedCalculator(
        capture_fps=params['fps'],
        film_format=film_format,
        capture_resolution_height=params.get('resolution', 1080),
        shutter_angle=params.get('shutter', 180.0),
        min_captures_per_frame=params.get('min_captures', 5),
        max_blur_pixels=params.get('max_blur', 2.0)
    )

    calculator.print_recommendations()


if __name__ == '__main__':
    main()
