import customtkinter as ctk
import logging
from ui.styles import Styles
from core.noise_canceller import NoiseCanceller
from core.voice_beautifier import VoiceBeautifier, BeautifySettings
from core.voice_slot_manager import VoiceSlotManager
from pynput import keyboard

logger = logging.getLogger("AdvancedTab")

class AdvancedTab(ctk.CTkFrame):
    """Tab containing controls for Noise Cancellation, Voice Beautification, and Multi‑Voice slots.
    """

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        self._setup_ui()
        self._setup_hotkeys()
        self.after(200, self._update_status)  # periodic UI status refresh

    # ---------------------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------------------
    def _setup_ui(self):
        # ----- Noise Cancellation Group -----
        self.noise_group = ctk.CTkFrame(self, fg_color="transparent")
        self.noise_group.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.noise_group, text="Noise Cancellation", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_SUB, "bold"), text_color=Styles.text_color).pack(anchor="w")
        self.noise_toggle = ctk.CTkSwitch(self.noise_group, text="Enabled", command=self._toggle_noise)
        self.noise_toggle.select()
        self.noise_toggle.pack(anchor="w", pady=2)
        self.noise_intensity = ctk.CTkOptionMenu(self.noise_group, values=["light", "medium", "aggressive"], command=self._set_noise_intensity)
        self.noise_intensity.set("medium")
        self.noise_intensity.pack(anchor="w", pady=2)
        self.noise_status = ctk.CTkLabel(self.noise_group, text="Status: Inactive", text_color="gray")
        self.noise_status.pack(anchor="w", pady=2)

        # ----- Voice Beautification Group -----
        self.beautify_group = ctk.CTkFrame(self, fg_color="transparent")
        self.beautify_group.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.beautify_group, text="Voice Beautification", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_SUB, "bold"), text_color=Styles.text_color).pack(anchor="w")
        self.beautify_toggle = ctk.CTkSwitch(self.beautify_group, text="Enabled", command=self._toggle_beautify)
        self.beautify_toggle.select()
        self.beautify_toggle.pack(anchor="w", pady=2)
        # De‑esser slider
        self.deesser_slider = ctk.CTkSlider(self.beautify_group, from_=0.0, to=1.0, number_of_steps=100, command=self._set_deesser)
        self.deesser_slider.set(0.5)
        ctk.CTkLabel(self.beautify_group, text="De‑esser Strength").pack(anchor="w")
        self.deesser_slider.pack(fill="x")
        # Warmth slider
        self.warmth_slider = ctk.CTkSlider(self.beautify_group, from_=-10.0, to=10.0, number_of_steps=200, command=self._set_warmth)
        self.warmth_slider.set(0.0)
        ctk.CTkLabel(self.beautify_group, text="Warmth (dB)").pack(anchor="w")
        self.warmth_slider.pack(fill="x")
        # Presence slider
        self.presence_slider = ctk.CTkSlider(self.beautify_group, from_=-10.0, to=10.0, number_of_steps=200, command=self._set_presence)
        self.presence_slider.set(0.0)
        ctk.CTkLabel(self.beautify_group, text="Presence (dB)").pack(anchor="w")
        self.presence_slider.pack(fill="x")
        self.beautify_status = ctk.CTkLabel(self.beautify_group, text="Status: Inactive", text_color="gray")
        self.beautify_status.pack(anchor="w", pady=2)

        # ----- Multi‑Voice Slot Group -----
        self.slot_group = ctk.CTkFrame(self, fg_color="transparent")
        self.slot_group.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.slot_group, text="Voice Slots", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_SUB, "bold"), text_color=Styles.text_color).pack(anchor="w")
        self.slot_selector = ctk.CTkOptionMenu(self.slot_group, values=[f"Slot {i+1}" for i in range(5)], command=self._select_slot)
        self.slot_selector.set("Slot 1")
        self.slot_selector.pack(anchor="w", pady=2)
        self.slot_status = ctk.CTkLabel(self.slot_group, text="Active: Slot 1", text_color="green")
        self.slot_status.pack(anchor="w", pady=2)

        # ----- Performance Metrics -----
        self.metrics_group = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_group.pack(fill="x", pady=5, padx=5)
        self.latency_label = ctk.CTkLabel(self.metrics_group, text="Latency: -- ms")
        self.latency_label.pack(anchor="w")
        self.cpu_label = ctk.CTkLabel(self.metrics_group, text="CPU: -- %")
        self.cpu_label.pack(anchor="w")

        # ----- Preset Buttons -----
        self.preset_group = ctk.CTkFrame(self, fg_color="transparent")
        self.preset_group.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.preset_group, text="Presets", font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_SUB, "bold"), text_color=Styles.text_color).pack(anchor="w")
        for name, func in self._preset_actions().items():
            btn = ctk.CTkButton(self.preset_group, text=name, command=func, width=80)
            btn.pack(side="left", padx=3, pady=2)

    # ---------------------------------------------------------------------
    # UI Callbacks – connect to engine core objects
    # ---------------------------------------------------------------------
    def _toggle_noise(self):
        if self.noise_toggle.get():
            self.engine.noise_canceller.enable()
        else:
            self.engine.noise_canceller.disable()

    def _set_noise_intensity(self, value):
        self.engine.noise_canceller.set_intensity(value)

    def _toggle_beautify(self):
        self.engine.beautifier.set_bypass(not self.beautify_toggle.get())

    def _set_deesser(self, value):
        self.engine.beautifier.settings.deesser_strength = float(value)

    def _set_warmth(self, value):
        self.engine.beautifier.settings.warmth = float(value)

    def _set_presence(self, value):
        self.engine.beautifier.settings.presence = float(value)

    def _select_slot(self, value):
        # value like "Slot 3"
        idx = int(value.split()[-1]) - 1
        self.engine.voice_slot_manager.switch_to(idx)

    # ---------------------------------------------------------------------
    # Hotkey Listener (local only)
    # ---------------------------------------------------------------------
    def _setup_hotkeys(self):
        def on_press(key):
            try:
                if key == keyboard.Key.f1:
                    self._select_slot("Slot 1")
                elif key == keyboard.Key.f2:
                    self._select_slot("Slot 2")
                elif key == keyboard.Key.f3:
                    self._select_slot("Slot 3")
                elif key == keyboard.Key.f4:
                    self._select_slot("Slot 4")
                elif key == keyboard.Key.f5:
                    self._select_slot("Slot 5")
            except Exception as e:
                logger.error(f"Hotkey error: {e}")
        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()

    # ---------------------------------------------------------------------
    # Periodic status refresh
    # ---------------------------------------------------------------------
    def _update_status(self):
        # Noise status
        stats = self.engine.noise_canceller.get_stats()
        if self.engine.noise_canceller._enabled:
            self.noise_status.configure(text=f"Active ({stats['processed']} frames)", text_color="green")
        else:
            self.noise_status.configure(text="Inactive", text_color="gray")
        # Beautify status
        if self.engine.beautifier.settings.enabled:
            self.beautify_status.configure(text="Enabled", text_color="green")
        else:
            self.beautify_status.configure(text="Disabled", text_color="gray")
        # Slot status
        cur = self.engine.voice_slot_manager.get_current_slot() + 1
        self.slot_status.configure(text=f"Active: Slot {cur}")
        # Performance metrics from engine.stats
        stats = getattr(self.engine, "stats", {})
        self.latency_label.configure(text=f"Latency: {stats.get('latency_ms', '--'):.1f} ms")
        self.cpu_label.configure(text=f"CPU: {stats.get('cpu_percent', '--'):.1f} %")
        # schedule next update
        self.after(500, self._update_status)

    # ---------------------------------------------------------------------
    # Preset actions
    # ---------------------------------------------------------------------
    def _preset_actions(self):
        return {
            "Clean": self._apply_clean_preset,
            "Broadcast": self._apply_broadcast_preset,
            "Podcast": self._apply_podcast_preset,
            "Radio DJ": self._apply_radio_dj_preset,
            "ASMR": self._apply_asmr_preset,
            "Gaming": self._apply_gaming_preset,
            "Deep Voice": self._apply_deep_voice_preset,
            "Bright": self._apply_bright_preset,
            "Natural": self._apply_natural_preset,
            "Studio": self._apply_studio_preset,
            "Warm FM": self._apply_warm_fm_preset,
            "Crisp": self._apply_crisp_preset,
            "Telephone": self._apply_telephone_preset,
        }

    def _apply_preset(self, noise_on, intensity, deesser, warmth, presence):
        """Helper to apply a preset configuration."""
        if noise_on:
            self.noise_toggle.select()
        else:
            self.noise_toggle.deselect()
        self.noise_intensity.set(intensity)
        self.beautify_toggle.select()
        self.deesser_slider.set(deesser)
        self.warmth_slider.set(warmth)
        self.presence_slider.set(presence)
        self._toggle_noise()
        self._set_noise_intensity(intensity)
        self._set_deesser(deesser)
        self._set_warmth(warmth)
        self._set_presence(presence)

    def _apply_clean_preset(self):
        self._apply_preset(True, "medium", 0.6, 2.0, 3.0)

    def _apply_broadcast_preset(self):
        self._apply_preset(True, "aggressive", 0.8, 4.0, 5.0)

    def _apply_podcast_preset(self):
        self._apply_preset(True, "light", 0.4, 1.0, 2.0)

    def _apply_radio_dj_preset(self):
        self._apply_preset(True, "aggressive", 0.7, 6.0, 7.0)

    def _apply_asmr_preset(self):
        self._apply_preset(True, "light", 0.2, -2.0, -1.0)

    def _apply_gaming_preset(self):
        self._apply_preset(True, "medium", 0.5, 0.0, 4.0)

    def _apply_deep_voice_preset(self):
        self._apply_preset(True, "medium", 0.4, 8.0, -2.0)

    def _apply_bright_preset(self):
        self._apply_preset(True, "light", 0.3, -3.0, 6.0)

    def _apply_natural_preset(self):
        self._apply_preset(False, "light", 0.0, 0.0, 0.0)

    def _apply_studio_preset(self):
        self._apply_preset(True, "aggressive", 0.9, 3.0, 4.0)

    def _apply_warm_fm_preset(self):
        self._apply_preset(True, "medium", 0.5, 5.0, 2.0)

    def _apply_crisp_preset(self):
        self._apply_preset(True, "medium", 0.7, -1.0, 5.0)

    def _apply_telephone_preset(self):
        self._apply_preset(False, "light", 0.0, -5.0, -3.0)

