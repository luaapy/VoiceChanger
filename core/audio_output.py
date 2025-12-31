import sounddevice as sd
import numpy as np
import threading
import queue
import logging
import config
from utils.error_handler import safe_thread_run

logger = logging.getLogger("AudioOutput")

class AudioOutput:
    def __init__(self, device_id=None):
        self.device_id = device_id
        # Output queue slightly larger to buffer against processing jitter
        self.queue = queue.Queue(maxsize=config.MAX_OUTPUT_QUEUE)
        self.running = False
        self.stream = None
        self.underflow_count = 0
        self.lock = threading.Lock()
        
    def _callback(self, outdata, frames, time_info, status):
        if status:
            logger.warning(f"Output Stream Status: {status}")
            
        if not self.running:
            raise sd.CallbackAbort
            
        try:
            # Try to get data from queue
            data = self.queue.get(block=False)
            
            # Ensure data is float32 and flattened first
            data = np.asarray(data, dtype=np.float32).flatten()
            
            # Resize to match expected frames if needed
            expected_samples = frames
            if len(data) < expected_samples:
                # Pad with zeros if too short
                data = np.pad(data, (0, expected_samples - len(data)), mode='constant')
            elif len(data) > expected_samples:
                # Truncate if too long
                data = data[:expected_samples]
            
            # Reshape for output (samples, channels)
            outdata[:] = data.reshape(-1, 1)
                
        except queue.Empty:
            # Buffer Underflow - fill with silence
            outdata.fill(0)
            self.underflow_count += 1
            if self.underflow_count % 50 == 0:
                logger.warning(f"Output Underflow (Silence inserted). Total: {self.underflow_count}")

    def start(self):
        if self.running:
            return
            
        self.running = True
        try:
            logger.info(f"Starting output on device {self.device_id}")
            self.stream = sd.OutputStream(
                device=self.device_id,
                channels=config.CHANNELS,
                samplerate=config.SAMPLE_RATE,
                blocksize=config.CHUNK_SIZE,
                callback=self._callback,
                dtype=np.float32
            )
            self.stream.start()
        except Exception as e:
            logger.critical(f"Failed to start output stream: {e}")
            self.running = False
            raise e

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing output stream: {e}")
            self.stream = None

    def write(self, data):
        """
        Write processed audio to the output queue.
        Implements smart dropping if queue is too full (Latency control).
        """
        try:
            # Check if queue is dangerously full (Latency buildup)
            qsize = self.queue.qsize()
            
            if qsize >= config.MAX_OUTPUT_QUEUE:
                # Drop oldest items until we have breathing room (e.g., down to MIN_OUTPUT_QUEUE)
                # This catches up latency instantly at the cost of a skip
                drop_count = 0
                while self.queue.qsize() > config.MIN_OUTPUT_QUEUE:
                    try:
                        self.queue.get_nowait()
                        drop_count += 1
                    except queue.Empty:
                        break
                if drop_count > 0:
                    logger.debug(f"Latency catch-up: Dropped {drop_count} output frames")
            
            self.queue.put(data, block=True, timeout=0.2)
            
        except queue.Full:
            logger.warning("Output queue full, dropping frame (Should be handled by smart drop above)")
            pass
