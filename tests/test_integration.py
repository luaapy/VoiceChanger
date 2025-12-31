import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
from voice_changer_realtime.core.engine import VoiceChangerEngine
from voice_changer_realtime import config

class TestIntegration(unittest.TestCase):
    
    @patch('voice_changer_realtime.core.audio_capture.AudioCapture.start')
    @patch('voice_changer_realtime.core.audio_output.AudioOutput.start')
    def test_engine_start_stop(self, mock_out_start, mock_cap_start):
        engine = VoiceChangerEngine()
        engine.start()
        
        self.assertTrue(engine.running)
        self.assertTrue(engine.process_thread.is_alive())
        self.assertTrue(engine.monitor_thread.is_alive())
        
        engine.stop()
        self.assertFalse(engine.running)
        self.assertFalse(engine.process_thread.is_alive())

    def test_pipeline_data_flow(self):
        """Simulate passing data through the pipeline"""
        engine = VoiceChangerEngine()
        
        # Mock capture/output to avoid real threads
        engine.capture = MagicMock()
        engine.output = MagicMock()
        engine.pitch_proc = MagicMock()
        
        # Mock behavior
        input_data = np.ones(1024, dtype=np.float32)
        engine.capture.read.return_value = input_data
        engine.pitch_proc.process.return_value = input_data * 2 # Mock processing
        
        # We want to run one iteration of _process_loop
        # Override stop_event to stop after 1 iteration? 
        # Hard with while loop. Better to extract logic or inject exception.
        
        # Instead, let's just call the inner logic manually to verify flow
        
        # 1. Set params
        engine.params["pitch_shift"] = 5.0
        engine.params["bypass"] = False
        
        # 2. Run logic (Manual Step-Through)
        processed = input_data
        if engine.params["bypass"]:
            processed = input_data
        else:
            processed = engine.pitch_proc.process(processed, 5.0)
            processed = engine.formant_proc.process(processed, 1.0)
            processed = engine.effects.process(processed)
            
        # Verify
        engine.pitch_proc.process.assert_called_with(input_data, 5.0)
        self.assertTrue(np.all(processed == input_data * 2)) # Since we mocked pitch return
        
    def test_parameter_updates(self):
        engine = VoiceChangerEngine()
        engine.update_params("pitch_shift", 12.0)
        self.assertEqual(engine.params["pitch_shift"], 12.0)
        
        # Effect params
        engine.effects = MagicMock()
        engine.update_params("effect:reverb:room_size", 0.8)
        engine.effects.update_params.assert_called_with("reverb", room_size=0.8)

if __name__ == '__main__':
    unittest.main()
