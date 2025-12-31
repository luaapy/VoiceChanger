import unittest
from unittest.mock import MagicMock, patch
import queue
import numpy as np
import time
from voice_changer_realtime.core.audio_capture import AudioCapture
from voice_changer_realtime.core.audio_output import AudioOutput
from voice_changer_realtime import config

class TestDeviceLogic(unittest.TestCase):
    
    @patch('sounddevice.InputStream')
    def test_capture_lifecycle(self, mock_stream_cls):
        """Test start/stop and queue logic for capture"""
        mock_stream = MagicMock()
        mock_stream_cls.return_value = mock_stream
        
        cap = AudioCapture()
        cap.start()
        
        self.assertTrue(cap.running)
        mock_stream.start.assert_called_once()
        
        cap.stop()
        self.assertFalse(cap.running)
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

    @patch('sounddevice.InputStream')
    def test_capture_overflow_handling(self, mock_stream_cls):
        """Test that capture drops oldest frames when full"""
        cap = AudioCapture()
        cap.queue = queue.Queue(maxsize=2)
        cap.running = True
        
        # Simulate callback filling queue
        data1 = np.array([1])
        data2 = np.array([2])
        data3 = np.array([3])
        
        # Helper to simulate callback
        def trigger_callback(d):
            cap._callback(d, 1024, None, None)
            
        trigger_callback(data1)
        trigger_callback(data2)
        
        self.assertEqual(cap.queue.qsize(), 2)
        
        # This should force drop of data1
        trigger_callback(data3)
        
        self.assertEqual(cap.queue.qsize(), 2)
        item = cap.queue.get()
        # Expect data2 (since 1 was dropped)
        self.assertTrue(np.array_equal(item, data2))
        
        item = cap.queue.get()
        self.assertTrue(np.array_equal(item, data3))

    @patch('sounddevice.OutputStream')
    def test_output_underrun_handling(self, mock_stream_cls):
        """Test output callback inserts silence on empty queue"""
        out = AudioOutput()
        out.running = True
        
        buffer = np.ones(1024, dtype=np.float32) # Buffer with noise
        
        # Callback with empty queue
        out._callback(buffer, 1024, None, None)
        
        # Buffer should be zeroed
        self.assertTrue(np.all(buffer == 0))
        self.assertEqual(out.underflow_count, 1)

    @patch('sounddevice.OutputStream')
    def test_output_latency_catchup(self, mock_stream_cls):
        """Test output queue dropping to reduce latency"""
        out = AudioOutput()
        # Override config for test
        # default max is 5, min is 2
        
        # Fill queue to max
        for i in range(5):
            out.queue.put(i)
            
        self.assertEqual(out.queue.qsize(), 5)
        
        # Add one more, should trigger drop logic
        out.write(99)
        
        # Logic: while qsize > MIN(2): get().
        # So it should drop until 2 are left, then put new one -> 3 total.
        # However, the loop condition is `while qsize > MIN`.
        # Initial 5. Drop -> 4. Drop -> 3. Drop -> 2. Stop loop.
        # Then put(99). Final size 3.
        
        self.assertEqual(out.queue.qsize(), 3)
        
        # Remaining items should be the newest ones: 3, 4, 99
        # Dropped: 0, 1, 2
        items = list(out.queue.queue)
        self.assertEqual(items, [3, 4, 99])

if __name__ == '__main__':
    unittest.main()
