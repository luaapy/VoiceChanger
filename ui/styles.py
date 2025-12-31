import config

class Styles:
    # Style Constants
    FONT_FAMILY = "Segoe UI" # Standard Windows Font
    FONT_SIZE_MAIN = 12
    FONT_SIZE_SUB = 14
    FONT_SIZE_TITLE = 20
    FONT_SIZE_SMALL = 10

    # Color Themes
    bg_color = config.COLOR_BACKGROUND
    primary_color = config.COLOR_PRIMARY
    secondary_color = config.COLOR_SECONDARY
    text_color = config.COLOR_TEXT
    
    # CTk Theme Settings
    theme_mode = "Light" # Since background is #F5F5F5
    
    # Component Specifics
    button_height = 40
    button_corner_radius = 8
    
    slider_height = 20
    slider_progress_color = config.COLOR_PRIMARY
    
    frame_corner_radius = 10
    frame_border_width = 1
    frame_border_color = "#E0E0E0"
