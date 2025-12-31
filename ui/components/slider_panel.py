import customtkinter as ctk
import config
from ui.styles import Styles

class SliderPanel(ctk.CTkFrame):
    def __init__(self, master, title, from_, to, initial_value, command, step=1, number_format="{:.1f}"):
        super().__init__(master, fg_color="transparent")
        self.command = command
        self.number_format = number_format
        
        # Label Row
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 5))
        
        self.label = ctk.CTkLabel(
            self.header_frame, 
            text=title, 
            font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_MAIN, "bold"),
            text_color=Styles.text_color
        )
        self.label.pack(side="left")
        
        self.value_label = ctk.CTkLabel(
            self.header_frame, 
            text=number_format.format(initial_value),
            font=(Styles.FONT_FAMILY, Styles.FONT_SIZE_MAIN),
            text_color=Styles.text_color
        )
        self.value_label.pack(side="right")
        
        # Slider
        self.slider = ctk.CTkSlider(
            self,
            from_=from_,
            to=to,
            number_of_steps=(to-from_)/step if step else None,
            command=self._on_slide,
            fg_color="#E0E0E0",
            progress_color=Styles.primary_color,
            button_color=Styles.primary_color,
            button_hover_color=config.COLOR_ACCENT
        )
        self.slider.set(initial_value)
        self.slider.pack(fill="x")
        
        # Reset Button (Small dot or text)
        self.reset_btn = ctk.CTkButton(
            self.header_frame,
            text="↺",
            width=20,
            height=20,
            fg_color="transparent",
            text_color=Styles.primary_color,
            command=lambda: self.set_value(initial_value)
        )
        self.reset_btn.pack(side="right", padx=5)

    def _on_slide(self, value):
        self.value_label.configure(text=self.number_format.format(value))
        if self.command:
            self.command(value)

    def set_value(self, value):
        self.slider.set(value)
        self._on_slide(value)
