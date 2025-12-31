import threading
import queue
import time
import numpy as np
import logging
import psutil
from typing import Dict, Any

from core.audio_capture import AudioCapture
from core.audio_output import AudioOutput
from core.pitch_processor import PitchProcessor
from core.formant_processor import FormantProcessor
from core.effects_chain import EffectsChain
from core.buffer_manager import CircularBuffer
import config
from utils.error_handler import safe_thread_run, ErrorTracker

# NEW imports for upgraded features
from core.noise_canceller import NoiseCanceller
from core.voice_beautifier import VoiceBeautifier
from core.voice_slot_manager import VoiceSlotManager

logger = logging.getLogger("VoiceChangerEngine")

class VoiceChangerEngine:
    def __init__(self):
        self.running = False
        
        # Components
        self.capture = AudioCapture()
        self.output = AudioOutput()
        self.pitch_proc = PitchProcessor()
        self.formant_proc = FormantProcessor()
        self.effects = EffectsChain()
        self.buffer_manager = CircularBuffer()  # Used for crossfading
        self.error_tracker = ErrorTracker()

        # NEW core modules
        self.noise_canceller = NoiseCanceller(intensity="medium")
        self.noise_canceller.disable()  # Disabled by default - can cause bouncing
        self.beautifier = VoiceBeautifier()
        self.beautifier.disable()  # Disabled by default - can cause bouncing
        self.voice_slot_manager = VoiceSlotManager()
        
        # State
        self.params = {
            "pitch_shift": 0.0,
            "formant_ratio": 1.0,
            "bypass": False,
            "volume": 1.0
        }
        
        # Threads
        self.process_thread = None
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Performance Metrics
        self.stats = {
            "fps": 0,
            "latency_ms": 0,
            "cpu_percent": 0,
            "ram_mb": 0
        }

    def set_device(self, kind: str, device_id: int):
        if kind == 'input':
            self.capture.device_id = device_id
        elif kind == 'output':
            self.output.device_id = device_id

    def update_params(self, param: str, value: Any):
        if param in self.params:
            self.params[param] = value
        elif param.startswith("effect:"):
            # Format: "effect:reverb:room_size"
            parts = param.split(":")
            if len(parts) == 3:
                self.effects.update_params(parts[1], **{parts[2]: value})
            elif len(parts) == 4 and parts[2] == "enabled":
                # Format: "effect:reverb:enabled" value=True/False
                self.effects.update_params(parts[1], enabled=value)

    def start(self):
        if self.running:
            return
        
        logger.info("Starting Voice Changer Engine...")
        self.stop_event.clear()
        self.running = True
        
        # Start Audio I/O
        try:
            # Reset processors to clear any stale state
            self.pitch_proc.reset()
            self.formant_proc.reset()
            self.buffer_manager.clear()
            
            self.capture.start()
            self.output.start()
        except Exception as e:
            logger.critical(f"Engine start failed: {e}")
            self.stop()
            raise e
        
        # Start Processing Thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        # Start Monitor Thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        logger.info("Stopping Engine...")
        self.running = False
        self.stop_event.set()
        
        # Stop I/O
        self.capture.stop()
        self.output.stop()
        
        # Join threads with timeout
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=0.5)

    @safe_thread_run(auto_recovery=True)
    def _process_loop(self):
        """Main Audio Processing Pipeline"""
        frame_count = 0
        
        while not self.stop_event.is_set():
            try:
                # 1. Capture Audio
                try:
                    audio_chunk = self.capture.read(timeout=0.5)
                except queue.Empty:
                    continue
                
                start_time = time.perf_counter()
                
                # 2. Bypass Check
                if self.params["bypass"]:
                    processed = audio_chunk.copy()
                else:
                    processed = audio_chunk.copy()
                    
                    # NOTE: Noise cancellation and beautification are DISABLED
                    # because noisereduce library is too slow for real-time processing
                    # and causes frame drops which create "bouncing" audio
                    
                    # 3. Pitch Shift
                    if self.params["pitch_shift"] != 0:
                        processed = self.pitch_proc.process(processed, self.params["pitch_shift"])
                    
                    # 4. Formant Shift
                    if self.params["formant_ratio"] != 1.0:
                        processed = self.formant_proc.process(processed, self.params["formant_ratio"])
                    
                    # 5. Effects Chain (only if simple effects are enabled)
                    processed = self.effects.process(processed)
                    
                    # 6. Ensure Mono after effects
                    if processed.ndim > 1:
                        processed = np.mean(processed, axis=0 if processed.shape[0] < processed.shape[1] else 1)
                    
                    # 7. Ensure float32 and flatten
                    processed = np.ascontiguousarray(processed.flatten(), dtype=np.float32)
                
                # 9. Volume
                if self.params["volume"] != 1.0:
                    processed = processed.flatten() * self.params["volume"]
                
                # 10. Output
                self.output.write(processed.astype(np.float32))
                
                # Debug logging every 100 frames
                if frame_count % 100 == 0:
                    peak = np.max(np.abs(processed))
                    logger.info(f"Audio Processing - Peak Level: {peak:.4f} | Queue Size: {self.capture.queue.qsize()}")
                
                # GC & stats
                frame_count += 1
                if frame_count % config.GC_INTERVAL == 0:
                    import gc
                    gc.collect()
                
                proc_time = (time.perf_counter() - start_time) * 1000
                self.stats["latency_ms"] = proc_time + (self.output.queue.qsize() * (config.CHUNK_SIZE/config.SAMPLE_RATE*1000))
            
            except Exception as e:
                self.error_tracker.log_error("ProcessingLoop", str(e))
                try:
                    self.output.write(np.zeros(config.CHUNK_SIZE, dtype=np.float32))
                except:
                    pass
    
    @safe_thread_run()
    def _monitor_loop(self):
        """Updates performance stats"""
        process = psutil.Process()
        while not self.stop_event.is_set():
            time.sleep(1.0)
            self.stats["cpu_percent"] = process.cpu_percent()
            self.stats["ram_mb"] = process.memory_info().rss / 1024 / 1024
            self.stats["fps"] = config.SAMPLE_RATE / config.CHUNK_SIZE
            if self.stats["ram_mb"] > 500:
                logger.warning(f"High Memory Usage: {self.stats['ram_mb']:.1f} MB")
            if self.stats["latency_ms"] > config.MAX_LATENCY_MS:
                pass  # UI can handle warning
