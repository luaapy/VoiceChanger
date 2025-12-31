import customtkinter as ctk
import config
from ui.styles import Styles

class MonitorDisplay(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="white", corner_radius=Styles.frame_corner_radius, border_width=Styles.frame_border_width, border_color=Styles.frame_border_color)
        
        self.engine = engine
        
        # Stats Row
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=10)
        
        # Latency
        self.latency_label = ctk.CTkLabel(self.stats_frame, text="Latency: 0 ms", font=("Consolas", 12), text_color=Styles.text_color)
        self.latency_label.pack(side="left", padx=10)
        
        # CPU
        self.cpu_label = ctk.CTkLabel(self.stats_frame, text="CPU: 0%", font=("Consolas", 12), text_color=Styles.text_color)
        self.cpu_label.pack(side="left", padx=10)
        
        # Memory
        self.mem_label = ctk.CTkLabel(self.stats_frame, text="RAM: 0 MB", font=("Consolas", 12), text_color=Styles.text_color)
        self.mem_label.pack(side="left", padx=10)
        
        # Status
        self.status_label = ctk.CTkLabel(self.stats_frame, text="● STOPPED", text_color="gray", font=("Consolas", 12, "bold"))
        self.status_label.pack(side="right", padx=10)
        
        self.update_stats()

    def update_stats(self):
        stats = self.engine.stats
        
        # Latency Color
        lat = stats["latency_ms"]
        lat_color = config.COLOR_SUCCESS if lat < 100 else (config.COLOR_WARNING if lat < 150 else config.COLOR_ERROR)
        self.latency_label.configure(text=f"Latency: {lat:.0f} ms", text_color=lat_color)
        
        self.cpu_label.configure(text=f"CPU: {stats['cpu_percent']:.0f}%")
        self.mem_label.configure(text=f"RAM: {stats['ram_mb']:.0f} MB")
        
        # Status
        if self.engine.running:
            if self.engine.params["bypass"]:
                self.status_label.configure(text="● BYPASS", text_color=config.COLOR_WARNING)
            else:
                self.status_label.configure(text="● ACTIVE", text_color=config.COLOR_SUCCESS)
        else:
            self.status_label.configure(text="● STOPPED", text_color="gray")
            
        self.after(500, self.update_stats)
