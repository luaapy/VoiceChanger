import logging
import numpy as np
import scipy.signal
from dataclasses import dataclass, field

@dataclass
class BeautifySettings:
    """Configuration for the VoiceBeautifier.

    Attributes
    ----------
    deesser_strength: float (0.0‑1.0)
        Amount of s‑band attenuation. 0 disables the de‑esser.
    warmth: float (-10.0‑10.0)
        Low‑mid shelf gain in dB.
    presence: float (-10.0‑10.0)
        High‑mid shelf gain in dB.
    enabled: bool
        Master switch for the entire beautification pipeline.
    """
    deesser_strength: float = 0.5
    warmth: float = 0.0
    presence: float = 0.0
    enabled: bool = True

    def validate(self):
        """Clamp values to safe ranges.
        """
        self.deesser_strength = np.clip(self.deesser_strength, 0.0, 1.0)
        self.warmth = np.clip(self.warmth, -10.0, 10.0)
        self.presence = np.clip(self.presence, -10.0, 10.0)

class VoiceBeautifier:
    """Hybrid FFT + IIR based voice beautification.

    The class maintains cached filter coefficients for the low‑shelf (warmth)
    and high‑shelf (presence) filters to avoid recomputation on every frame.
    """

    def __init__(self):
        self.settings = BeautifySettings()
        self._bypass = False
        # Cached filter state
        self._warmth_filter = None
        self._presence_filter = None
        self._filter_cache_params = None

    # ---------------------------------------------------------------------
    # Public control API
    # ---------------------------------------------------------------------
    def enable(self):
        self.settings.enabled = True
        logging.info("VoiceBeautifier enabled")

    def disable(self):
        self.settings.enabled = False
        logging.info("VoiceBeautifier disabled")

    def set_bypass(self, bypass: bool):
        self._bypass = bypass
        logging.info(f"VoiceBeautifier bypass set to {bypass}")

    # ---------------------------------------------------------------------
    # Core processing
    # ---------------------------------------------------------------------
    def process(self, audio: np.ndarray, sr: int, settings: BeautifySettings | None = None) -> np.ndarray:
        """Process an audio buffer.

        Parameters
        ----------
        audio: np.ndarray
            Input audio (1‑D float array).
        sr: int
            Sample rate.
        settings: BeautifySettings | None
            Optional override settings for this call.
        """
        if settings:
            settings.validate()
            self.settings = settings

        if self._bypass or not self.settings.enabled:
            return audio

        try:
            # De‑esser (FFT based) – only if strength is non‑trivial
            if self.settings.deesser_strength > 0.01:
                audio = self.deesser(audio, sr)

            # EQ (IIR) – only if warmth or presence are significant
            if abs(self.settings.warmth) > 0.1 or abs(self.settings.presence) > 0.1:
                audio = self.eq(audio, sr, self.settings.warmth, self.settings.presence)

            return audio
        except Exception as e:
            logging.error(f"Beautification failed: {e}")
            return audio  # Fallback to unprocessed audio

    # ---------------------------------------------------------------------
    # De‑esser implementation (FFT based)
    # ---------------------------------------------------------------------
    def deesser(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Attenuate the s‑band (4‑8 kHz) using a simple spectral subtraction.
        """
        if len(audio) < 256:
            # Not enough samples for a reliable FFT – skip processing
            return audio

        # Perform short‑time FFT (window size 512, hop 256)
        win_len = 512
        hop = win_len // 2
        window = np.hanning(win_len)
        out = np.copy(audio)
        for start in range(0, len(audio) - win_len + 1, hop):
            frame = audio[start:start + win_len] * window
            spectrum = np.fft.rfft(frame)
            freqs = np.fft.rfftfreq(win_len, d=1.0 / sr)
            # Identify s‑band indices (4‑8 kHz)
            s_band = (freqs >= 4000) & (freqs <= 8000)
            # Reduce magnitude proportionally to strength
            reduction = 1.0 - self.settings.deesser_strength * 0.5
            spectrum[s_band] *= reduction
            # Inverse FFT
            processed = np.fft.irfft(spectrum)
            out[start:start + win_len] += (processed - frame) * window
        return out

    # ---------------------------------------------------------------------
    # EQ implementation (IIR bi‑quad shelves)
    # ---------------------------------------------------------------------
    def eq(self, audio: np.ndarray, sr: int, warmth: float, presence: float) -> np.ndarray:
        """Apply low‑shelf (warmth) and high‑shelf (presence) filters.
        """
        cache_key = (warmth, presence, sr)
        if self._filter_cache_params != cache_key:
            # Re‑compute filter coefficients
            self._warmth_filter = self._design_shelf_filter(
                sr, freq=200, gain=warmth, filter_type="low_shelf"
            )
            self._presence_filter = self._design_shelf_filter(
                sr, freq=3000, gain=presence, filter_type="high_shelf"
            )
            self._filter_cache_params = cache_key

        # Apply filters sequentially
        if self._warmth_filter:
            b, a = self._warmth_filter
            audio = scipy.signal.lfilter(b, a, audio)
        if self._presence_filter:
            b, a = self._presence_filter
            audio = scipy.signal.lfilter(b, a, audio)
        return audio

    # ---------------------------------------------------------------------
    # Helper: bi‑quad shelf design
    # ---------------------------------------------------------------------
    def _design_shelf_filter(self, sr: int, freq: float, gain: float, filter_type: str):
        """Return (b, a) coefficients for a shelf filter.

        Parameters
        ----------
        sr: int
            Sample rate.
        freq: float
            Center frequency of the shelf.
        gain: float
            Gain in dB (positive = boost, negative = cut).
        filter_type: str
            "low_shelf" or "high_shelf".
        """
        # Convert dB gain to linear amplitude
        A = 10 ** (gain / 40)
        omega = 2 * np.pi * freq / sr
        sn = np.sin(omega)
        cs = np.cos(omega)
        alpha = sn / 2 * np.sqrt((A + 1 / A) * (1 / 0.707 - 1) + 2)
        if filter_type == "low_shelf":
            b0 = A * ((A + 1) - (A - 1) * cs + 2 * np.sqrt(A) * alpha)
            b1 = 2 * A * ((A - 1) - (A + 1) * cs)
            b2 = A * ((A + 1) - (A - 1) * cs - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) + (A - 1) * cs + 2 * np.sqrt(A) * alpha
            a1 = -2 * ((A - 1) + (A + 1) * cs)
            a2 = (A + 1) + (A - 1) * cs - 2 * np.sqrt(A) * alpha
        else:  # high_shelf
            b0 = A * ((A + 1) + (A - 1) * cs + 2 * np.sqrt(A) * alpha)
            b1 = -2 * A * ((A - 1) + (A + 1) * cs)
            b2 = A * ((A + 1) + (A - 1) * cs - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) - (A - 1) * cs + 2 * np.sqrt(A) * alpha
            a1 = 2 * ((A - 1) - (A + 1) * cs)
            a2 = (A + 1) - (A - 1) * cs - 2 * np.sqrt(A) * alpha
        b = np.array([b0, b1, b2]) / a0
        a = np.array([1.0, a1 / a0, a2 / a0])
        return b, a
