import numpy as np
import logging
import config

logger = logging.getLogger("EffectsChain")

# Try to import pedalboard, fallback to mocks if not available (Linux env issues)
try:
    from pedalboard import Pedalboard, Reverb, Chorus, Distortion, Compressor, Delay, Mix
    PEDALBOARD_AVAILABLE = True
    if config.USE_MOCK_EFFECTS:
        raise ImportError("Forced mock effects")
except ImportError:
    logger.warning("Pedalboard library not found or disabled. Using MOCK effects.")
    PEDALBOARD_AVAILABLE = False

class EffectsChain:
    def __init__(self, sample_rate=config.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.enabled = True
        
        # State for mocks
        self.mock_delay_buffer = np.zeros(sample_rate * 2, dtype=np.float32) # 2 sec buffer
        self.mock_ptr = 0
        
        # Active Parameters
        self.params = {
            "reverb": {"enabled": False, "room_size": 0.5, "wet_level": 0.3},
            "chorus": {"enabled": False, "rate_hz": 1.0, "depth": 0.5},
            "distortion": {"enabled": False, "drive_db": 0},
            "compressor": {"enabled": False, "threshold_db": -20, "ratio": 4},
            "delay": {"enabled": False, "time": 0.3, "feedback": 0.5}
        }
        
        self.board = None
        self._update_board()

    def _update_board(self):
        """Rebuilds the Pedalboard chain based on params"""
        if not PEDALBOARD_AVAILABLE:
            return

        effects = []
        
        p = self.params
        
        if p["distortion"]["enabled"]:
            effects.append(Distortion(drive_db=p["distortion"]["drive_db"]))
            
        if p["chorus"]["enabled"]:
            effects.append(Chorus(rate_hz=p["chorus"]["rate_hz"], depth=p["chorus"]["depth"]))
            
        if p["reverb"]["enabled"]:
            effects.append(Reverb(room_size=p["reverb"]["room_size"], wet_level=p["reverb"]["wet_level"]))
            
        if p["delay"]["enabled"]:
             effects.append(Delay(delay_seconds=p["delay"]["time"], feedback=p["delay"]["feedback"]))

        if p["compressor"]["enabled"]:
            effects.append(Compressor(threshold_db=p["compressor"]["threshold_db"], ratio=p["compressor"]["ratio"]))
            
        self.board = Pedalboard(effects)

    def update_params(self, effect_name, **kwargs):
        if effect_name in self.params:
            self.params[effect_name].update(kwargs)
            self._update_board()

    def process(self, audio: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return audio
            
        # Bypass if no effects enabled (Optimization)
        if not any(e["enabled"] for e in self.params.values()):
            return audio

        if PEDALBOARD_AVAILABLE and self.board:
            try:
                # Pedalboard expects (channels, samples) or just (samples)
                # Ensure input is float32
                audio = audio.astype(np.float32)
                processed = self.board(audio, self.sample_rate)
                return processed
            except Exception as e:
                logger.error(f"Pedalboard process failed: {e}")
                return audio
        else:
            return self._process_mock(audio)

    def _process_mock(self, audio: np.ndarray) -> np.ndarray:
        """Simple numpy implementations for testing/fallback"""
        processed = audio.copy()
        p = self.params
        
        # 1. Distortion (Hard clipping)
        if p["distortion"]["enabled"]:
            drive = 1.0 + (p["distortion"]["drive_db"] / 20.0)
            processed = np.clip(processed * drive, -1.0, 1.0)
            
        # 2. Reverb (Simple Feedback Delay Network approximation)
        if p["reverb"]["enabled"]:
            # Very dumb reverb: add decayed noise? No, add decayed previous buffer
            # Just simple fake implementation
            wet = p["reverb"]["wet_level"]
            processed = processed * (1 - wet) + (processed * 0.5) * wet # Just volume change really
            
        # 3. Delay (Circular buffer echo)
        if p["delay"]["enabled"]:
            # Basic implementation for unit testing flow
            delay_samples = int(p["delay"]["time"] * self.sample_rate)
            feedback = p["delay"]["feedback"]
            
            # This requires persistent state which is hard in block processing 
            # without a proper ring buffer. 
            # For mock purposes, we skip complex stateful delay to avoid glitches.
            pass

        return processed
