import numpy as np
import pytest
from core.noise_canceller import NoiseCanceller

@pytest.fixture
def sample_audio():
    # Generate a noisy sine wave
    sr = 44100
    t = np.linspace(0, 1, sr, endpoint=False)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    noise = 0.05 * np.random.randn(sr)
    return tone + noise, sr

def test_noise_canceller_intensity_levels(sample_audio):
    audio, sr = sample_audio
    for intensity in ["light", "medium", "aggressive"]:
        nc = NoiseCanceller(intensity=intensity)
        out = nc.process(audio, sr)
        # Output should have same shape and dtype
        assert out.shape == audio.shape
        assert out.dtype == audio.dtype
        # Processed frames count should increase
        stats = nc.get_stats()
        assert stats["processed"] >= 1

def test_noise_canceller_fallback_on_error(monkeypatch, sample_audio):
    audio, sr = sample_audio
    nc = NoiseCanceller()
    # Force an exception in reduce_noise
    def bad_reduce(*args, **kwargs):
        raise RuntimeError("forced error")
    monkeypatch.setattr('noisereduce.reduce_noise', bad_reduce)
    # Call process three times to trigger fallback
    for _ in range(3):
        out = nc.process(audio, sr)
        assert np.allclose(out, audio)  # should return original on error
    stats = nc.get_stats()
    assert stats["fallback"] is True
    assert stats["errors"] >= 3
