# PythonType

A minimalist typing test application built with Python and Pygame, inspired by Monkeytype.

## Features
- **Clean Interface**: Dark mode with distraction-free typing area.
- **Real-time Feedback**: Instant character validation (correct/incorrect).
- **Smooth Caret**: Modern, smooth sliding cursor animation for a fluid typing experience.
- **Live Metrics**: Words Per Minute (WPM) and Accuracy tracking.
- **Game Modes**: 
    - **Time**: 15/30/60/120 s
    - **Word**: 10/25/50/100 words
    - **Quote**: Practice typing famous quotes.
    - **Practice**: Automatically generates tests based on your frequently missed characters.
- **History & Progress**: 
    - View your last 50 attempts in a dedicated history window.
    - **Graphical Analysis**: Visual curve of your WPM over time with a moving average trend line.
- **Themes**: Monkeytype, GitHub, Nord, Dracula, Solarized, Gruvbox, One Dark, Catppuccin, Rose Pine, Tokyo Night, Everforest, **High contrast**, and more.
- **Layout**: QWERTY or Dvorak (keyboard visualizer).
- **Settings**: Font size (small/medium/large), optional sound on error, reduced motion (disables smooth caret).
- **Persistent Config**: Theme, layout, mode, duration, word count, font size, and options are saved automatically.
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
- **History**: `typing_history.json` (next to the script). Stores your typing session results.
- **Stats**: `typing_stats.json` (next to the script). Tracks your missed characters to power the "Practice" mode.

## Tests
From the project root:
```bash
python -m pytest tests/ -v
# or
python -m unittest tests.test_logic -v
```

## Project Structure
- `main.py` – Entry point (Pygame GUI)
- `logic.py` – Game logic, stats, and history management
- `resources.py` – Themes, word/quote lists, font size options
- `config.py` – Load/save settings
- `sound_util.py` – Optional error beep
- `fonts/` – Optional Roboto fonts