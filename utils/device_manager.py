import sounddevice as sd
import logging
import threading
from typing import List, Optional, Dict
import config

logger = logging.getLogger("DeviceManager")

class DeviceManager:
    def __init__(self):
        self._lock = threading.Lock()
        
    def list_audio_devices(self, kind=None) -> List[Dict]:
        """
        Lists available audio devices.
        kind: 'input', 'output', or None (both)
        """
        try:
            devices = sd.query_devices()
            device_list = []
            
            for i, dev in enumerate(devices):
                if kind == 'input' and dev['max_input_channels'] > 0:
                    device_list.append({'id': i, 'name': dev['name'], 'hostapi': dev['hostapi']})
                elif kind == 'output' and dev['max_output_channels'] > 0:
                    device_list.append({'id': i, 'name': dev['name'], 'hostapi': dev['hostapi']})
                elif kind is None:
                    device_list.append({'id': i, 'name': dev['name'], 'io': [dev['max_input_channels'], dev['max_output_channels']]})
                    
            return device_list
        except Exception as e:
            logger.error(f"Failed to query devices: {e}")
            return []

    def find_vb_cable(self, kind='input') -> Optional[int]:
        """
        Attempts to find 'CABLE Input' or similar virtual device.
        kind='input' means we are looking for the Recording device named 'CABLE Output' 
        OR the Playback device named 'CABLE Input' to send audio TO?
        
        The user wants:
        "Input: [Microphone (USB)]" -> Application -> "Output: [CABLE Input (Virtual)]"
        
        So for 'output' device selection, we want "CABLE Input".
        """
        devices = self.list_audio_devices(kind='output')
        
        # Keywords to search for
        keywords = ["cable input", "vb-audio", "vb-cable"]
        
        for dev in devices:
            name_lower = dev['name'].lower()
            if any(k in name_lower for k in keywords):
                logger.info(f"Found Virtual Cable: {dev['name']} (ID: {dev['id']})")
                return dev['id']
                
        logger.info("Virtual Cable not found.")
        return None

    def get_default_device(self, kind='input') -> Optional[int]:
        try:
            devices = self.list_audio_devices(kind=kind)
            
            if kind == 'input':
                # Prioritize real internal mics over virtual ones
                priority_keywords = ["internal microphone", "microphone array", "conexant"]
                avoid_keywords = ["voice.ai", "virtual", "cable"]
                
                # First pass: Look for high priority real mics
                for dev in devices:
                    name = dev['name'].lower()
                    if any(k in name for k in priority_keywords) and not any(k in name for k in avoid_keywords):
                        logger.info(f"Auto-selected real microphone: {dev['name']} (ID: {dev['id']})")
                        return dev['id']
            
            # Fallback to sounddevice default
            defaults = sd.default.device
            return defaults[0] if kind == 'input' else defaults[1]
        except Exception:
            return None
