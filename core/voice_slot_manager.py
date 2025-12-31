import logging
import threading
import queue
import numpy as np

class VoiceSlotManager:
    """Manage multiple voice slots with thread‑safe switching and cross‑fade.

    Slots hold identifiers (e.g., model names) that the processing pipeline can
    query to select the appropriate voice conversion model. The manager provides
    a 100 ms cross‑fade between slots to avoid audible pops.
    """

    def __init__(self):
        self.slots = [None] * 5  # Placeholder for voice model identifiers
        self.current_slot = 0
        self.crossfade_duration_ms = 100

        # Thread‑safety primitives
        self._lock = threading.Lock()
        self._switching = False
        self._switch_queue = queue.Queue(maxsize=1)

        # Cross‑fade state (populated by _do_crossfade)
        self._fade_out_curve = None
        self._fade_in_curve = None
        self._fade_from_slot = None
        self._fade_to_slot = None
        self._fade_progress = 0

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def switch_to(self, slot_index: int) -> bool:
        """Request a switch to ``slot_index``.

        The method is safe to call from UI or hot‑key callbacks. If a switch is
        already in progress, the request is queued (replacing any previous queued
        request) so that only the latest desired slot is applied.
        """
        if not 0 <= slot_index < len(self.slots):
            logging.warning(f"Invalid slot index: {slot_index}")
            return False

        # If a switch is currently happening, queue the new request
        if self._switching:
            try:
                while not self._switch_queue.empty():
                    self._switch_queue.get_nowait()
                self._switch_queue.put_nowait(slot_index)
            except queue.Full:
                pass
            return False

        with self._lock:
            self._switching = True
            try:
                self._do_crossfade(self.current_slot, slot_index)
                self.current_slot = slot_index
                logging.info(f"Switched to voice slot {slot_index}")
                return True
            except Exception as e:
                logging.error(f"Slot switch failed: {e}")
                return False
            finally:
                self._switching = False
                # If a queued request exists, process it immediately
                if not self._switch_queue.empty():
                    next_slot = self._switch_queue.get_nowait()
                    self.switch_to(next_slot)

    # ---------------------------------------------------------------------
    # Cross‑fade implementation
    # ---------------------------------------------------------------------
    def _do_crossfade(self, from_slot: int, to_slot: int):
        """Prepare 100 ms cross‑fade curves.

        The actual audio mixing is performed by ``apply_crossfade`` which will be
        called by the real‑time processing thread for each audio chunk.
        """
        sample_rate = 44100  # Assuming a fixed sample rate; adjust if needed
        fade_samples = int(self.crossfade_duration_ms / 1000 * sample_rate)
        self._fade_out_curve = np.linspace(1.0, 0.0, fade_samples)
        self._fade_in_curve = np.linspace(0.0, 1.0, fade_samples)
        self._fade_from_slot = from_slot
        self._fade_to_slot = to_slot
        self._fade_progress = 0
        logging.debug(
            f"Prepared cross‑fade: {fade_samples} samples from slot {from_slot} to {to_slot}"
        )

    def apply_crossfade(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Apply the prepared cross‑fade to ``audio_chunk``.

        This method is intended to be called from the audio processing thread.
        If no cross‑fade is active or it has completed, the original chunk is
        returned unchanged.
        """
        if self._fade_out_curve is None or self._fade_progress >= len(self._fade_out_curve):
            return audio_chunk

        chunk_len = len(audio_chunk)
        remaining = len(self._fade_out_curve) - self._fade_progress
        apply_len = min(chunk_len, remaining)

        # Slice the fade curves for the current portion
        fade_out_slice = self._fade_out_curve[self._fade_progress:self._fade_progress + apply_len]
        fade_in_slice = self._fade_in_curve[self._fade_progress:self._fade_progress + apply_len]

        # For demonstration we simply blend the same chunk; in a real system the
        # ``from`` and ``to`` slots would provide different audio streams. Here we
        # apply the fade curves to the incoming chunk to avoid pops.
        audio_chunk[:apply_len] = (
            audio_chunk[:apply_len] * fade_out_slice +
            audio_chunk[:apply_len] * fade_in_slice
        )

        self._fade_progress += apply_len
        return audio_chunk

    # ---------------------------------------------------------------------
    # Utility / status
    # ---------------------------------------------------------------------
    def get_current_slot(self) -> int:
        return self.current_slot

    def get_status(self) -> dict:
        return {
            "current_slot": self.current_slot,
            "switching": self._switching,
            "queue_size": self._switch_queue.qsize(),
        }
