# Plan for PythonType (Monkeytype Clone)

## 1. Project Structure
- `main.py`: Entry point and main window controller.
- `ui_components.py`: Custom widgets for the typing area and HUD.
- `logic.py`: Game state, WPM calculation, and word generation.
- `resources.py`: Color palettes and the word list.

## 2. Key Features
- **Word Display:** A steady stream of words that wraps lines.
- **Input Handling:** Catch keypress events to validate against the current character.
- **Timer:** QTimer triggering every second to update time remaining.
- **Results Screen:** Simple overlay showing final WPM/Accuracy.

## 3. Visuals (Monkeytype Theme)
- Background: #323437
- Text (Untyped): #646669
- Text (Correct): #d1d0c5
- Text (Incorrect): #ca4754
- Font: Monospaced (Consolas, Roboto Mono, or Courier New).
