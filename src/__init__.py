"""
FilmScanner - 8mm Film Digitization Processor
Converts continuous film capture video into properly aligned individual frames.
"""

from .sprocket_detector import SprocketDetector
from .frame_detector import FrameDetector, FilmFrame
from .frame_tracker import FrameTracker, FrameCandidate, TrackedFrame
from .sharpness_analyzer import SharpnessAnalyzer
from .film_processor import FilmProcessor

__version__ = "1.0.0"
__all__ = [
    'SprocketDetector',
    'FrameDetector',
    'FilmFrame',
    'FrameTracker',
    'FrameCandidate',
    'TrackedFrame',
    'SharpnessAnalyzer',
    'FilmProcessor',
]
