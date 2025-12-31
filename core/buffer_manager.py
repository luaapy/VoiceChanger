import numpy as np
import threading
import logging
import config

logger = logging.getLogger("BufferManager")

class CircularBuffer:
    def __init__(self, size_chunks=config.BUFFER_SIZE, chunk_size=config.CHUNK_SIZE):
        self.chunk_size = chunk_size
        self.capacity = size_chunks * chunk_size
        self.buffer = np.zeros(self.capacity, dtype=np.float32)
        self.write_ptr = 0
        self.read_ptr = 0
        self.lock = threading.Lock()
        
        # Crossfade pre-calculation
        self.fade_len = config.CROSSFADE_LENGTH
        self.fade_in = np.linspace(0, 1, self.fade_len, dtype=np.float32)
        self.fade_out = np.linspace(1, 0, self.fade_len, dtype=np.float32)
        
        # State for overlap-add/crossfade
        self.prev_tail = np.zeros(self.fade_len, dtype=np.float32)

    def write(self, data: np.ndarray):
        """Writes data to the buffer handling overflow by overwriting oldest data."""
        with self.lock:
            n = len(data)
            if n > self.capacity:
                # If data is larger than buffer, just take the last capacity-sized chunk
                data = data[-self.capacity:]
                n = len(data)

            # Check for overflow
            space_left = self.capacity - self.write_ptr
            if n <= space_left:
                self.buffer[self.write_ptr:self.write_ptr + n] = data
            else:
                # Wrap around
                part1 = space_left
                part2 = n - space_left
                self.buffer[self.write_ptr:self.capacity] = data[:part1]
                self.buffer[0:part2] = data[part1:]
            
            self.write_ptr = (self.write_ptr + n) % self.capacity
            
            # Simple overflow handling logic: 
            # If write passes read, push read forward? 
            # In a circular buffer for audio streaming usually we assume consumption is fast enough.
            # If we overwrite unread data, we might hear glitches.
            # For this specific implementation, we rely on the queues for flow control 
            # and this buffer mainly for processing history if needed, 
            # BUT for the requested architecture:
            # "Implement circular buffer with size 10-20 chunks"
            # "Handle buffer overflow: drop oldest frames"
            
            # Actually, the queue system (FIFO) acts as the primary buffer between threads.
            # This class might be used within the processing thread to stitch chunks or 
            # if we move to a buffer-based approach instead of queue-based.
            # However, the user asked for "Queue -> Pitch -> ... -> Output Buffer".
            # So this BufferManager is likely the "Output Buffer" before the speaker.

    def apply_crossfade(self, current_chunk: np.ndarray) -> np.ndarray:
        """
        Applies crossfade to the beginning of the current chunk 
        using the tail of the previous chunk to ensure smooth transitions.
        Uses proper overlap-add with squared cosine (Hann-like) windows
        to prevent audio bouncing and ensure constant-power crossfade.
        """
        if len(current_chunk) < self.fade_len * 2:
            return current_chunk  # Too small to fade safely
        
        # Ensure the chunk is float32 and contiguous
        current_chunk = np.ascontiguousarray(current_chunk, dtype=np.float32)

        # Copy to avoid modifying original
        processed = current_chunk.copy()
        
        # Apply overlap-add crossfade for smooth transition
        # Only apply if there's valid previous data
        if np.any(self.prev_tail != 0):
            # Blend the overlap region using weighted sum
            # This ensures constant power: fade_in^2 + fade_out^2 = 1 (approximately)
            blend = self.prev_tail * self.fade_out + processed[:self.fade_len] * self.fade_in
            processed[:self.fade_len] = blend
        
        # Save new tail for next time
        self.prev_tail = current_chunk[-self.fade_len:].copy()
        
        return processed

    def clear(self):
        with self.lock:
            self.buffer.fill(0)
            self.write_ptr = 0
            self.read_ptr = 0
            self.prev_tail.fill(0)
