import customtkinter as ctk
import config
from ui.styles import Styles

class EffectsPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="white", corner_radius=Styles.frame_corner_radius, border_width=Styles.frame_border_width, border_color=Styles.frame_border_color)
        
        self.engine = engine
        
        ctk.CTkLabel(self, text="Audio Effects", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_MAIN, "bold"), text_color=Styles.text_color).pack(anchor="w", padx=15, pady=(10,5))
        
        self.effects = [
            ("Reverb", "reverb"),
            ("Chorus", "chorus"),
            ("Distortion", "distortion"),
            ("Compressor", "compressor"),
            ("Delay", "delay")
        ]
        
        self.vars = {}
        
        for name, key in self.effects:
            var = ctk.BooleanVar(value=False)
            self.vars[key] = var
            chk = ctk.CTkCheckBox(
                self, 
                text=name, 
                variable=var,
                command=lambda k=key: self.toggle_effect(k),
                fg_color=Styles.primary_color
            )
            chk.pack(anchor="w", padx=20, pady=5)
            
            # Additional simplified controls could go here (e.g. wet level)

    def toggle_effect(self, key):
        enabled = self.vars[key].get()
        self.engine.update_params(f"effect:{key}:enabled", enabled)
