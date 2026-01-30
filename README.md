# PythonType

A minimalist typing test application built with Python and Pygame, inspired by Monkeytype.

## Features
- **Clean Interface**: Dark mode with distraction-free typing area.
- **Real-time Feedback**: Instant character validation (correct/incorrect), blinking caret.
- **Live Metrics**: Words Per Minute (WPM) and Accuracy tracking.
- **Game Modes**: **Time** (15/30/60/120 s), **Word** (10/25/50/100 words), **Quote**.
- **Themes**: Monkeytype, GitHub, Nord, Dracula, Solarized, Gruvbox, One Dark, Catppuccin, Rose Pine, Tokyo Night, Everforest, **High contrast**, and more.
- **Layout**: QWERTY or Dvorak (keyboard visualizer).
- **Settings**: Font size (small/medium/large), optional sound on error, reduced motion (no caret blink).
- **Persistent Config**: Theme, layout, mode, duration, word count, font size, and options are saved and restored on next run.
- **Quick Restart**: Press `Tab` at any time to reset.

## Requirements
- Python 3.x
- pygame

Optional: place **Roboto-Regular.ttf** and **Roboto-Bold.ttf** in the `fonts/` folder (see [Google Fonts](https://fonts.google.com/specimen/Roboto)).

## Installation
```bash
pip install pygame
```

## How to Run
```bash
python main.py
```

## Config & Data
- **Config**: `typing_config.json` (next to the script). Stores theme, layout, mode, duration, word count, font size, sound on error, reduced motion.
- **History**: `typing_history.json` (next to the script). Last 50 attempts (WPM, accuracy, mode). Used for “previous attempt” on the results screen.

## Tests
From the project root:
```bash
python -m pytest tests/ -v
# or
python -m unittest tests.test_logic -v
```

## Project Structure
- `main.py` – Entry point (Pygame)
- `logic.py` – TypingEngine, HistoryManager
- `resources.py` – Themes, word/quote lists, font size options
- `config.py` – Load/save settings (typing_config.json)
- `sound_util.py` – Optional error beep (generates `assets/error_beep.wav` if missing)
- `fonts/` – Optional Roboto fonts
- `tests/test_logic.py` – Unit tests for engine and history
