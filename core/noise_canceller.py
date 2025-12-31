import logging
import numpy as np
import noisereduce

class NoiseCanceller:
    """Real‑time noise cancellation with safety, fallback and stats.

    Parameters
    ----------
    intensity: str, optional
        One of "light", "medium", "aggressive". Determines the
        ``prop_decrease`` parameter passed to ``noisereduce.reduce_noise``.
        Default is "medium".
    """

    def __init__(self, intensity: str = "medium"):
        # Core configuration
        self.intensity = intensity
        self._enabled = True
        self._fallback_mode = False  # Switch off if repeated errors occur
        self._process_count = 0
        self._error_count = 0

        # Mapping intensity to ``prop_decrease`` (0.0‑1.0)
        self._intensity_map = {
            "light": 0.5,
            "medium": 0.8,
            "aggressive": 1.0,
        }

        # Ensure a valid intensity value
        if self.intensity not in self._intensity_map:
            logging.warning(
                f"Invalid intensity '{self.intensity}' – falling back to 'medium'."
            )
            self.intensity = "medium"

    # ---------------------------------------------------------------------
    # Public control API
    # ---------------------------------------------------------------------
    def enable(self):
        """Enable processing (if previously disabled)."""
        self._enabled = True
        self._fallback_mode = False
        logging.info("NoiseCanceller enabled")

    def disable(self):
        """Disable processing – raw audio will be passed through unchanged."""
        self._enabled = False
        logging.info("NoiseCanceller disabled")

    def set_intensity(self, intensity: str):
        """Change the intensity level at runtime.

        Parameters
        ----------
        intensity: str
            "light", "medium" or "aggressive".
        """
        if intensity not in self._intensity_map:
            logging.error(f"Attempted to set invalid intensity '{intensity}'")
            return
        self.intensity = intensity
        logging.info(f"NoiseCanceller intensity set to '{intensity}'")

    # ---------------------------------------------------------------------
    # Core processing method
    # ---------------------------------------------------------------------
    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply noise reduction to a single audio frame.

        The method is defensive – it validates input, catches any exception
        from ``noisereduce`` and falls back to the original audio when an
        error occurs. After three consecutive errors the module automatically
        disables itself (fallback mode) to keep the pipeline stable.
        """
        if not self._enabled or self._fallback_mode:
            return audio

        try:
            # Basic validation – empty or silent buffers are returned unchanged
            if audio.size == 0 or np.all(audio == 0):
                return audio

            prop_decrease = self._intensity_map.get(self.intensity, 0.8)
            reduced = noisereduce.reduce_noise(
                y=audio,
                sr=sample_rate,
                prop_decrease=prop_decrease,
                stationary=True,  # better for short real‑time frames
            )
            self._process_count += 1
            return reduced

        except Exception as e:
            self._error_count += 1
            logging.error(f"Noise cancellation failed: {e}")
            # If we hit three consecutive errors, switch to fallback mode
            if self._error_count >= 3:
                self._fallback_mode = True
                logging.warning(
                    "NoiseCanceller entered fallback mode after repeated errors"
                )
            return audio

    # ---------------------------------------------------------------------
    # Statistics / monitoring
    # ---------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return processing statistics for UI or logging.

        Returns
        -------
        dict
            ``processed`` – number of successfully processed frames
            ``errors`` – total error count
            ``fallback`` – whether fallback mode is active
        """
        return {
            "processed": self._process_count,
            "errors": self._error_count,
            "fallback": self._fallback_mode,
        }
