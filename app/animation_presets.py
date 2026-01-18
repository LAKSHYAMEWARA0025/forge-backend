"""
Animation presets - Must match frontend animation presets exactly
"""

# Entry Animations
ENTRY_ANIMATIONS = [
    "fade_in",
    "pop_in",
    "slide_up",
    "slide_down",
    "slide_left",
    "slide_right",
    "slide_up_fade",
    "slide_down_fade",
    "slide_left_fade",
    "slide_right_fade",
    "scale_up",
    "scale_down",
    "scale_up_fade",
    "bounce_in",
]

# Exit Animations
EXIT_ANIMATIONS = [
    "fade_out",
    "pop_out",
    "slide_up_out",
    "slide_down_out",
    "slide_left_out",
    "slide_right_out",
    "slide_up_fade_out",
    "slide_down_fade_out",
    "slide_left_fade_out",
    "slide_right_fade_out",
    "scale_down_out",
    "scale_down_fade_out",
]

# Highlight Animations
HIGHLIGHT_ANIMATIONS = [
    "none",
    "pulse",
    "pulse_fade",
    "scale_up",
    "bounce_soft",
    "fade_emphasis",
    "color_emphasis",
    "scale_color_pulse",
]

# Video Animations
VIDEO_ANIMATIONS = [
    "none",
    "fade_in",
    "fade_out",
    "fade_in_out",
]

# All presets grouped by type
ALL_PRESETS = {
    "entry": ENTRY_ANIMATIONS,
    "exit": EXIT_ANIMATIONS,
    "highlight": HIGHLIGHT_ANIMATIONS,
    "video": VIDEO_ANIMATIONS,
}


def is_valid_preset(animation_type: str, preset_id: str) -> bool:
    """Check if a preset ID is valid for the given animation type"""
    presets = ALL_PRESETS.get(animation_type, [])
    return preset_id in presets


def get_all_presets() -> dict:
    """Get all available animation presets"""
    return ALL_PRESETS
