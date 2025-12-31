import customtkinter as ctk
import json
import os
import config
from ui.styles import Styles

class PresetPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="white", corner_radius=Styles.frame_corner_radius, border_width=Styles.frame_border_width, border_color=Styles.frame_border_color)
        
        self.engine = engine
        
        ctk.CTkLabel(self, text="Presets", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_MAIN, "bold"), text_color=Styles.text_color).pack(anchor="w", padx=15, pady=(10,5))
        
        self.combo = ctk.CTkComboBox(self, width=200, command=self.load_preset)
        self.combo.pack(padx=15, pady=5)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=5)
        
        ctk.CTkButton(btn_frame, text="Save", width=80, command=self.save_preset).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reload", width=80, command=self.scan_presets).pack(side="left", padx=5)
        
        self.scan_presets()

    def scan_presets(self):
        try:
            files = [f for f in os.listdir(config.PRESET_DIR) if f.endswith('.json')]
            names = [os.path.splitext(f)[0] for f in files]
            self.combo.configure(values=names)
            if "Default" in names:
                self.combo.set("Default")
        except Exception:
            pass

    def load_preset(self, name):
        try:
            path = os.path.join(config.PRESET_DIR, f"{name}.json")
            with open(path, 'r') as f:
                data = json.load(f)
                
            # Apply Params
            if "pitch_shift" in data:
                self.engine.update_params("pitch_shift", data["pitch_shift"])
                # Ideally UI sliders should update too via an observer pattern. 
                # For this simplicity, we assume UI pulls from engine or we manually trigger.
                # Here we just push to engine.
                
            if "formant_ratio" in data:
                self.engine.update_params("formant_ratio", data["formant_ratio"])
                
            if "effects" in data:
                for fx, params in data["effects"].items():
                    if "enabled" in params:
                        self.engine.update_params(f"effect:{fx}:enabled", params["enabled"])
                    for k, v in params.items():
                        if k != "enabled":
                            self.engine.update_params(f"effect:{fx}:{k}", v)
                            
        except Exception as e:
            print(f"Error loading preset: {e}")

    def save_preset(self):
        # Placeholder for save dialog logic
        pass
