# config.py - Persist and load app settings
import json
import os

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_CONFIG_DIR, "typing_config.json")

DEFAULTS = {
    "theme": "monkeytype",
    "layout": "qwerty",
    "mode": "time",
    "duration": 30,
    "word_count": 25,
    "font_size": "medium",  # small | medium | large
    "sound_on_error": False,
    "reduced_motion": False,
}

# Allowed values for validation
DURATION_OPTIONS = [15, 30, 60, 120]
WORD_COUNT_OPTIONS = [10, 25, 50, 100]
FONT_SIZE_MAP = {"small": 20, "medium": 28, "large": 36}


def load_config():
    """Load config from JSON; return dict with defaults for missing keys."""
    if not os.path.isfile(CONFIG_PATH):
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        out = DEFAULTS.copy()
        for k, v in data.items():
            if k in out and v is not None:
                out[k] = v
        return out
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.copy()


def save_config(data):
    """Save config dict to JSON. Returns True on success, False on error."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as e:
        import sys
        print(f"Error saving config: {e}", file=sys.stderr)
        return False


def get_font_size_px(size_name):
    """Return font size in pixels for small/medium/large."""
    return FONT_SIZE_MAP.get(size_name, 24)
