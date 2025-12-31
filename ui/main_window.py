import customtkinter as ctk
import sys
import logging
from ui.styles import Styles
from core.engine import VoiceChangerEngine
from utils.device_manager import DeviceManager
import config

# Components
from ui.components.slider_panel import SliderPanel
from ui.components.device_selector import DeviceSelector
from ui.components.monitor_display import MonitorDisplay
from ui.components.effects_panel import EffectsPanel
from ui.components.preset_panel import PresetPanel

# New Advanced tab
from ui.tabs.advanced_tab import AdvancedTab

logger = logging.getLogger("MainWindow")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Init Engine
        self.engine = VoiceChangerEngine()
        self.device_manager = DeviceManager()

        # Setup Window
        self.title(config.APP_NAME)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(600, 500)

        # Theme
        ctk.set_appearance_mode(Styles.theme_mode)
        ctk.set_default_color_theme("blue")

        # Close Handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Build UI with tabs
        self._build_ui()

    def _build_ui(self):
        # Create Tabview
        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=10, pady=5)
        tabview.add("Basic")
        tabview.add("Advanced")

        # ----- Basic Tab (existing UI) -----
        basic_tab = tabview.tab("Basic")
        basic_tab.grid_columnconfigure(0, weight=1)
        basic_tab.grid_rowconfigure(1, weight=1)

        # Header / Monitor
        self.monitor = MonitorDisplay(basic_tab, self.engine)
        self.monitor.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Main Content Frame
        self.main_frame = ctk.CTkFrame(basic_tab, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Left Column (Controls)
        self.left_col = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Right Column (Effects/Presets)
        self.right_col = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Device Selector
        self.devices = DeviceSelector(self.left_col, self.device_manager, self.engine)
        self.devices.pack(fill="x", pady=5)

        # Pitch Control
        self.pitch_panel = SliderPanel(
            self.left_col, "Pitch Shift",
            from_=config.PITCH_MIN, to=config.PITCH_MAX,
            initial_value=0,
            command=lambda v: self.engine.update_params("pitch_shift", int(v)),
            step=1, number_format="{:.0f}"
        )
        self.pitch_panel.pack(fill="x", pady=10)

        # Formant Control
        self.formant_panel = SliderPanel(
            self.left_col, "Formant Ratio",
            from_=config.FORMANT_MIN, to=config.FORMANT_MAX,
            initial_value=1.0,
            command=lambda v: self.engine.update_params("formant_ratio", float(v)),
            step=0.05
        )
        self.formant_panel.pack(fill="x", pady=10)

        # Main Buttons
        self.btn_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=20)

        self.start_btn = ctk.CTkButton(
            self.btn_frame, text="START ENGINE",
            fg_color=config.COLOR_SUCCESS, height=45,
            command=self.toggle_engine
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=5)

        self.bypass_btn = ctk.CTkButton(
            self.btn_frame, text="BYPASS",
            fg_color=config.COLOR_WARNING, height=45,
            command=self.toggle_bypass
        )
        self.bypass_btn.pack(side="right", fill="x", expand=True, padx=5)

        # Presets Panel
        self.presets = PresetPanel(self.right_col, self.engine)
        self.presets.pack(fill="x", pady=5)

        # Effects Panel
        self.effects_ui = EffectsPanel(self.right_col, self.engine)
        self.effects_ui.pack(fill="both", expand=True, pady=10)

        # ----- Advanced Tab (new features) -----
        self.advanced_tab = AdvancedTab(tabview.tab("Advanced"), self.engine)
        self.advanced_tab.pack(fill="both", expand=True)

    def toggle_engine(self):
        if not self.engine.running:
            try:
                self.engine.start()
                self.start_btn.configure(text="STOP ENGINE", fg_color=config.COLOR_ERROR)
            except Exception as e:
                import tkinter.messagebox
                tkinter.messagebox.showerror("Error", f"Failed to start: {e}")
        else:
            self.engine.stop()
            self.start_btn.configure(text="START ENGINE", fg_color=config.COLOR_SUCCESS)

    def toggle_bypass(self):
        current = self.engine.params["bypass"]
        self.engine.update_params("bypass", not current)
        if not current:
            self.bypass_btn.configure(text="UN-BYPASS", fg_color="gray")
        else:
            self.bypass_btn.configure(text="BYPASS", fg_color=config.COLOR_WARNING)

    def on_close(self):
        self.engine.stop()
        self.destroy()
        sys.exit(0)
