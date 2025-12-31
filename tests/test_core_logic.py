import unittest
import numpy as np
from voice_changer_realtime.core.buffer_manager import CircularBuffer
from voice_changer_realtime.core.pitch_processor import PitchProcessor
from voice_changer_realtime.core.formant_processor import FormantProcessor
from voice_changer_realtime.core.effects_chain import EffectsChain
from voice_changer_realtime import config

class TestCoreLogic(unittest.TestCase):
    
    def test_circular_buffer_overflow(self):
        """Test that buffer overwrites oldest data correctly"""
        buf = CircularBuffer(size_chunks=2, chunk_size=4) # Capacity 8 samples
        data1 = np.array([1, 2, 3, 4], dtype=np.float32)
        data2 = np.array([5, 6, 7, 8], dtype=np.float32)
        data3 = np.array([9, 10, 11, 12], dtype=np.float32)
        
        buf.write(data1)
        buf.write(data2)
        # Buffer should be [1,2,3,4,5,6,7,8]
        self.assertTrue(np.array_equal(buf.buffer, np.concatenate([data1, data2])))
        
        buf.write(data3)
        # Buffer should be [9,10,11,12,5,6,7,8] (Circular) 
        # Wait, write ptr moves.
        # write_ptr was 0 -> 4 -> 8(0)
        # write data3 at 0.
        expected = np.array([9, 10, 11, 12, 5, 6, 7, 8], dtype=np.float32)
        self.assertTrue(np.array_equal(buf.buffer, expected))

    def test_pitch_processor_bounds(self):
        """Test bounds checking for pitch shifter"""
        proc = PitchProcessor()
        audio = np.zeros(1024, dtype=np.float32)
        
        # Test max bounds
        # We can't easily inspect internal args passed to rubberband without mocking it,
        # but we can ensure it doesn't crash with extreme values.
        res = proc.process(audio, 100) # Should clamp to 12
        self.assertEqual(len(res), 1024)
        
        res = proc.process(audio, -100) # Should clamp to -12
        self.assertEqual(len(res), 1024)

    def test_formant_processor_resizing(self):
        """Test that formant processor resamples correctly"""
        proc = FormantProcessor()
        audio = np.ones(100, dtype=np.float32)
        
        # Ratio 2.0 (Higher) -> Half length
        res = proc.process(audio, 2.0)
        self.assertEqual(len(res), 50)
        
        # Ratio 0.5 (Deeper) -> Double length
        res = proc.process(audio, 0.5)
        self.assertEqual(len(res), 200)

    def test_effects_chain_bypass(self):
        """Test that disabled effects return original audio"""
        chain = EffectsChain()
        chain.enabled = False
        audio = np.random.rand(1024).astype(np.float32)
        
        res = chain.process(audio)
        self.assertTrue(np.array_equal(audio, res))

if __name__ == '__main__':
    unittest.main()
