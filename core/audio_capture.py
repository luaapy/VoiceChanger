import sounddevice as sd
import numpy as np
import threading
import queue
import time
import logging
import config
from utils.error_handler import safe_thread_run

logger = logging.getLogger("AudioCapture")

class AudioCapture:
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.queue = queue.Queue(maxsize=config.MAX_INPUT_QUEUE)
        self.running = False
        self.stream = None
        self.dropped_frames = 0
        self.error_event = threading.Event()
        
    def _callback(self, indata, frames, time_info, status):
        """Audio callback running in a separate thread managed by sounddevice"""
        if status:
            logger.warning(f"Input Stream Status: {status}")
            
        if not self.running:
            raise sd.CallbackAbort
            
        # Copy and flatten to 1D (Mono processing)
        # Moderate Gain Boost (10x) - reduced from 100x to prevent clipping artifacts
        data = indata.copy().flatten() * 10.0
        
        # Soft clipping using tanh to prevent harsh clipping artifacts
        data = np.tanh(data)  # This gives smoother clipping than hard clip
        
        # Aggressive Drop Policy
        # If queue is full, drop oldest item (FIFO) to make space for new
        # "MAX_INPUT_QUEUE = 3"
        try:
            self.queue.put(data, block=False)
        except queue.Full:
            try:
                # Drop oldest
                _ = self.queue.get_nowait()
                self.queue.put(data, block=False)
                
                self.dropped_frames += 1
                if self.dropped_frames % 50 == 0: # Log every 50 drops to avoid spam
                     logger.warning(f"Input Queue Full. Dropped {self.dropped_frames} frames.")
            except queue.Empty:
                pass # Should not happen if Full

    def start(self):
        if self.running:
            return

        self.running = True
        self.dropped_frames = 0
        self.error_event.clear()
        
        try:
            # We use a thread to start the stream because `sd.InputStream` with callback is non-blocking,
            # but we want to manage its lifecycle.
            # Actually, sounddevice streams are context managers or can be start()/stop().
            
            logger.info(f"Starting capture on device {self.device_id}")
            self.stream = sd.InputStream(
                device=self.device_id,
                channels=config.CHANNELS,
                samplerate=config.SAMPLE_RATE,
                blocksize=config.CHUNK_SIZE,
                callback=self._callback,
                dtype=np.float32
            )
            self.stream.start()
            
        except Exception as e:
            logger.critical(f"Failed to start capture stream: {e}")
            self.running = False
            self.error_event.set()
            raise e

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing input stream: {e}")
            self.stream = None

    def read(self, timeout=None):
        """Blocking read from queue with optional timeout"""
        return self.queue.get(block=True, timeout=timeout)
