"""
Configuration and constants for Real-Time Voice Changer
"""
import os

# App Info
APP_NAME = "Real-Time Voice Changer"
VERSION = "1.0.0"

# Audio Settings
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
CHANNELS = 1
BUFFER_SIZE = 30  # Circular buffer size in chunks (increased for smoother playback)
CROSSFADE_LENGTH = 256  # Samples (reduced for lower latency crossfading)

# Processing Limits
PITCH_MIN = -12
PITCH_MAX = 12
FORMANT_MIN = 0.5
FORMANT_MAX = 2.0

# Queue Management (Balanced for Smooth Audio)
MAX_INPUT_QUEUE = 5      # Increased from 3 - more buffer room
MAX_OUTPUT_QUEUE = 8     # Increased from 5 - prevents underruns
MIN_OUTPUT_QUEUE = 3     # Keep at least this many to prevent underruns
TARGET_LATENCY_MS = 120  # Slightly higher for stability
MAX_LATENCY_MS = 200     # Warning threshold

# Performance
GC_INTERVAL = 1000  # Run GC every N frames
USE_MOCK_EFFECTS = False  # Set to True if pedalboard fails to import (auto-detected usually)

# Thread Settings
CAPTURE_THREAD_PRIORITY = "high"
PROCESSING_THREAD_PRIORITY = "normal"
OUTPUT_THREAD_PRIORITY = "high"

# Error Handling
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
AUTO_RECOVERY = True

# UI Settings
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 600
UPDATE_RATE = 30  # FPS for UI updates

# Colors (No Purple!)
COLOR_BACKGROUND = "#F5F5F5"
COLOR_PRIMARY = "#2196F3"    # Blue
COLOR_SECONDARY = "#4CAF50"  # Green
COLOR_ACCENT = "#1976D2"     # Darker Blue
COLOR_SUCCESS = "#4CAF50"
COLOR_WARNING = "#FF9800"
COLOR_ERROR = "#F44336"
COLOR_TEXT = "#212121"
COLOR_DISABLED = "#BDBDBD"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRESET_DIR = os.path.join(BASE_DIR, "presets")
LOG_FILE = os.path.join(BASE_DIR, "voice_changer.log")

# Ensure preset dir exists
os.makedirs(PRESET_DIR, exist_ok=True)
