import numpy as np
import logging
from scipy import signal
import config

logger = logging.getLogger("PitchProcessor")

class PitchProcessor:
    """
    Real-time pitch processor using scipy resampling.
    Fast and works without external dependencies.
    """
    
    def __init__(self, sample_rate=config.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._error_count = 0
        
    def process(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        """
        Shifts pitch of audio by N semitones using fast resampling.
        """
        if len(audio) == 0:
            return audio
            
        # Bypass if no shift
        if abs(semitones) < 0.1:
            return audio.astype(np.float32)

        # Bounds checking
        semitones = max(config.PITCH_MIN, min(config.PITCH_MAX, semitones))
        
        try:
            # Calculate pitch ratio (2^(semitones/12))
            ratio = 2.0 ** (semitones / 12.0)
            n_samples = len(audio)
            
            # Resample to change pitch
            new_length = int(n_samples / ratio)
            if new_length < 10:
                return audio.astype(np.float32)
            
            # Use polyphase resampling for better quality
            shifted = signal.resample_poly(audio, new_length, n_samples)
            
            # Resample back to original length to maintain timing
            if len(shifted) != n_samples:
                shifted = signal.resample_poly(shifted, n_samples, len(shifted))
            
            # Ensure same length as input
            if len(shifted) > n_samples:
                shifted = shifted[:n_samples]
            elif len(shifted) < n_samples:
                shifted = np.pad(shifted, (0, n_samples - len(shifted)))
            
            return shifted.astype(np.float32)
            
        except Exception as e:
            self._error_count += 1
            if self._error_count <= 3:
                logger.error(f"Pitch shift failed: {e}")
            return audio.astype(np.float32)
    
    def reset(self):
        """Reset internal state."""
        pass
