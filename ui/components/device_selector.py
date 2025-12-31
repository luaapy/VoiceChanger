import customtkinter as ctk
import config
from ui.styles import Styles

class DeviceSelector(ctk.CTkFrame):
    def __init__(self, master, device_manager, engine):
        super().__init__(master, fg_color="white", corner_radius=Styles.frame_corner_radius, border_width=Styles.frame_border_width, border_color=Styles.frame_border_color)
        
        self.device_manager = device_manager
        self.engine = engine
        
        # Title
        ctk.CTkLabel(self, text="Audio Devices", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_MAIN, "bold"), text_color=Styles.text_color).pack(anchor="w", padx=15, pady=(10,5))
        
        # Grid layout for combos
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=15, pady=5)
        
        # Input
        ctk.CTkLabel(self.grid_frame, text="Input (Mic):", text_color=Styles.text_color).grid(row=0, column=0, sticky="w", pady=5)
        self.input_combo = ctk.CTkComboBox(self.grid_frame, width=250, command=self._on_input_change)
        self.input_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # Output
        ctk.CTkLabel(self.grid_frame, text="Output (Speaker/Cable):", text_color=Styles.text_color).grid(row=1, column=0, sticky="w", pady=5)
        self.output_combo = ctk.CTkComboBox(self.grid_frame, width=250, command=self._on_output_change)
        self.output_combo.grid(row=1, column=1, padx=10, pady=5)
        
        # Refresh Button
        self.refresh_btn = ctk.CTkButton(self.grid_frame, text="↻ Refresh", width=80, command=self.refresh_devices)
        self.refresh_btn.grid(row=0, column=2, rowspan=2, padx=5)

        self.input_map = {}
        self.output_map = {}
        self.refresh_devices()

    def refresh_devices(self):
        # Input
        inputs = self.device_manager.list_audio_devices(kind='input')
        self.input_map = {d['name']: d['id'] for d in inputs}
        self.input_combo.configure(values=list(self.input_map.keys()))
        
        # Default Input
        def_in = self.device_manager.get_default_device('input')
        if def_in is not None:
             for name, id_ in self.input_map.items():
                 if id_ == def_in:
                     self.input_combo.set(name)
                     self.engine.set_device('input', id_)
                     break

        # Output
        outputs = self.device_manager.list_audio_devices(kind='output')
        self.output_map = {d['name']: d['id'] for d in outputs}
        self.output_combo.configure(values=list(self.output_map.keys()))
        
        # Auto-detect VB Cable
        vb_cable_id = self.device_manager.find_vb_cable()
        if vb_cable_id is not None:
            for name, id_ in self.output_map.items():
                if id_ == vb_cable_id:
                    self.output_combo.set(name)
                    self.engine.set_device('output', id_)
                    break
        else:
            # Fallback
            def_out = self.device_manager.get_default_device('output')
            if def_out is not None:
                for name, id_ in self.output_map.items():
                    if id_ == def_out:
                        self.output_combo.set(name)
                        self.engine.set_device('output', id_)
                        break

    def _on_input_change(self, choice):
        if choice in self.input_map:
            self.engine.set_device('input', self.input_map[choice])

    def _on_output_change(self, choice):
        if choice in self.output_map:
            self.engine.set_device('output', self.output_map[choice])
