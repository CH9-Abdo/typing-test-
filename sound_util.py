# sound_util.py - Optional error beep for typing mistakes
import math
import os
import struct
import wave

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_BEEP_PATH = os.path.join(_APP_DIR, "assets", "error_beep.wav")


def _ensure_beep_wav():
    """Create a short 440Hz beep WAV if it doesn't exist. Returns path."""
    if os.path.isfile(_BEEP_PATH):
        return _BEEP_PATH
    os.makedirs(os.path.dirname(_BEEP_PATH), exist_ok=True)
    rate = 22050
    duration = 0.08  # seconds
    freq = 440
    n = int(rate * duration)
    with wave.open(_BEEP_PATH, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        for i in range(n):
            t = i / rate
            val = int(32767 * 0.3 * (1 - i / n) * math.sin(2 * math.pi * freq * t))
            w.writeframes(struct.pack("<h", max(-32768, min(32767, val))))
    return _BEEP_PATH


def play_error_beep():
    """Play error beep using pygame.mixer. No-op if mixer not ready."""
    try:
        import pygame
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
        path = _ensure_beep_wav()
        snd = pygame.mixer.Sound(path)
        snd.set_volume(0.3)
        snd.play()
    except Exception:
        pass
