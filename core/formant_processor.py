import numpy as np
import logging
from scipy import signal
import config

logger = logging.getLogger("FormantProcessor")

class FormantProcessor:
    """
    Real-time formant processor using polyphase resampling.
    """
    
    def __init__(self, sample_rate=config.SAMPLE_RATE):
        self.sample_rate = sample_rate

    def process(self, audio: np.ndarray, ratio: float) -> np.ndarray:
        """
        Shifts formants using polyphase resampling.
        Ratio < 1.0: Deeper voice (Male-like)
        Ratio > 1.0: Higher voice (Female-like)
        """
        # Bypass if ratio is close to 1.0
        if abs(ratio - 1.0) < 0.05:
            return audio.astype(np.float32)
            
        # Bounds check
        ratio = max(config.FORMANT_MIN, min(config.FORMANT_MAX, ratio))
        
        if len(audio) == 0:
            return audio
        
        try:
            n_samples = len(audio)
            
            # Calculate new length for formant shift
            new_len = int(n_samples / ratio)
            if new_len < 10:
                return audio.astype(np.float32)
            
            # Step 1: Resample to shift formants
            resampled = signal.resample_poly(audio, new_len, n_samples)
            
            # Step 2: Resample back to original length
            result = signal.resample_poly(resampled, n_samples, len(resampled))
            
            # Ensure same length as input
            if len(result) > n_samples:
                result = result[:n_samples]
            elif len(result) < n_samples:
                result = np.pad(result, (0, n_samples - len(result)))
            
            return result.astype(np.float32)

        except Exception as e:
            logger.error(f"Formant shift failed: {e}")
            return audio.astype(np.float32)
    
    def reset(self):
        """Reset internal state."""
        pass
