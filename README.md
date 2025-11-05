# FilmScanner - 8mm Film Digitization

A software-based solution for digitizing 8mm film that converts continuously captured video into properly aligned, stabilized individual frames.

## Overview

FilmScanner eliminates the need for complex hardware with intermittent frame advance or stepper motors. Simply capture your 8mm film with continuous motion, and let the software handle frame detection, alignment, and selection of the sharpest image for each frame.

## How It Works

The processing pipeline consists of several key steps:

1. **Sprocket Hole Detection**: Identifies sprocket holes along the film edge using computer vision techniques
2. **Frame Boundary Detection**: Uses sprocket hole positions to determine where each film frame begins and ends
3. **Frame Tracking**: Tracks each film frame across multiple video frames as it moves through the capture area
4. **Sharpness Analysis**: Calculates sharpness metrics for each instance of a film frame
5. **Best Frame Selection**: Selects the sharpest instance of each film frame for the output
6. **Frame Assembly**: Combines the best frames into a properly aligned output video

### Key Features

- **Automatic Frame Detection**: Detects frame boundaries using sprocket holes
- **Sharpness-Based Selection**: Automatically selects the sharpest image for each frame
- **Flexible Output**: Generate video files or individual image sequences
- **Customizable Parameters**: Adjust detection parameters for different capture setups
- **Progress Tracking**: Real-time progress reporting during processing

## Installation

### Requirements

- Python 3.8 or higher
- OpenCV
- NumPy
- SciPy
- tqdm

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd FilmScanner
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Process a video file with default settings:

```bash
python film_scanner.py input.mp4 -o output.mp4
```

### Common Options

**Specify output frame rate:**
```bash
python film_scanner.py input.mp4 -o output.mp4 --fps 24
```

**Save frames as individual images:**
```bash
python film_scanner.py input.mp4 --save-images output_frames/
```

**Resize output frames:**
```bash
python film_scanner.py input.mp4 -o output.mp4 --height 720
```

### Advanced Options

**Adjust sprocket detection parameters:**

If sprocket holes aren't being detected properly, adjust these parameters:

```bash
python film_scanner.py input.mp4 -o output.mp4 \
  --threshold 40 \
  --min-area 30 \
  --max-area 3000 \
  --detection-right 0.2
```

- `--threshold`: Binary threshold for hole detection (lower = more sensitive)
- `--min-area`: Minimum hole size in pixels
- `--max-area`: Maximum hole size in pixels
- `--detection-left` / `--detection-right`: Region to search for holes (as ratio of frame width)

### Complete Options

```
positional arguments:
  input                 Input video file path

output options:
  -o OUTPUT, --output OUTPUT
                        Output video file path
  --save-images DIR     Save frames as images to directory
  --fps FPS             Output video frame rate (default: 18 for 8mm film)
  --codec CODEC         Output video codec FourCC code (default: mp4v)
  --height HEIGHT       Target output frame height in pixels (default: original)

sprocket detection options:
  --threshold THRESHOLD
                        Binary threshold for sprocket detection (default: 50)
  --min-area MIN_AREA   Minimum sprocket hole area in pixels (default: 50)
  --max-area MAX_AREA   Maximum sprocket hole area in pixels (default: 5000)
  --detection-left DETECTION_LEFT
                        Left boundary of detection region as ratio (default: 0.0)
  --detection-right DETECTION_RIGHT
                        Right boundary of detection region as ratio (default: 0.15)
  --holes-per-frame HOLES_PER_FRAME
                        Number of sprocket holes per film frame (default: 1 for 8mm)

processing options:
  --debug               Enable debug output
```

## Capture Setup Tips

For best results when capturing your film:

1. **Lighting**: Use even, bright backlighting to create strong contrast for sprocket holes
2. **Speed**: Maintain consistent film speed - not too fast or too slow
3. **Focus**: Keep the film in focus throughout the capture
4. **Position**: Ensure sprocket holes are visible on one edge of the frame
5. **Camera**: Use the highest resolution available (4K recommended)

### Recommended Capture Settings

- **Resolution**: 4K (3840x2160) or higher
- **Frame Rate**: 60fps or higher
- **Film Speed**: ~3-5 inches per second
- **Sprocket Position**: Left 10-15% of frame

## Architecture

The project is organized into several modules:

### Core Modules

- **`sprocket_detector.py`**: Detects sprocket holes using computer vision
- **`frame_detector.py`**: Identifies film frame boundaries based on sprocket positions
- **`sharpness_analyzer.py`**: Calculates image sharpness using multiple metrics
- **`frame_tracker.py`**: Tracks frames across video and selects best instances
- **`film_processor.py`**: Main processing pipeline that coordinates all modules

### Processing Flow

```
Input Video
    ↓
Sprocket Detection (per video frame)
    ↓
Frame Boundary Detection
    ↓
Frame Extraction & Tracking
    ↓
Sharpness Analysis
    ↓
Best Frame Selection
    ↓
Output Assembly
    ↓
Output Video/Images
```

## Technical Details

### Sprocket Detection

Uses OpenCV's contour detection on thresholded images to find dark circular regions (sprocket holes) in a defined region of the frame.

### Sharpness Metrics

Multiple sharpness metrics are available:
- **Laplacian Variance**: Detects high-frequency content (edges)
- **Gradient Magnitude**: Measures edge strength
- **Tenengrad**: Sobel-based focus measure

The Laplacian variance is used by default as it provides good results for most cases.

### Frame Tracking

As the film moves through the capture area, each film frame appears in multiple consecutive video frames. The tracker:
1. Identifies which film frame each video frame contains
2. Extracts and stores multiple instances of each film frame
3. Calculates sharpness for each instance
4. Selects the sharpest instance for output

## Troubleshooting

### No frames detected

- Adjust `--threshold` value (try lower values like 30-40)
- Check that sprocket holes are visible in the video
- Adjust `--detection-right` if holes are in a different position
- Ensure adequate lighting contrast

### Poor quality output

- Increase capture resolution
- Improve lighting setup
- Reduce film movement speed
- Check focus during capture

### Frames misaligned

- Ensure consistent film speed during capture
- Check for proper sprocket hole detection
- Adjust `--min-area` and `--max-area` if holes are being missed

## Examples

### Processing Standard 8mm Film

```bash
python film_scanner.py my_film.mp4 -o output.mp4 --fps 18
```

### High-Quality Processing

```bash
python film_scanner.py my_film.mp4 -o output.mp4 \
  --fps 24 \
  --height 1080 \
  --codec avc1
```

### Batch Processing

```bash
for file in *.mp4; do
    python film_scanner.py "$file" -o "processed_${file}"
done
```

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

This project uses OpenCV for computer vision processing and implements various sharpness metrics from image processing literature.
