# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from ui_components import TypingDisplay, StatsHUD, ResultOverlay, SettingsBar, KeyboardVisualizer
from logic import TypingEngine
import resources

class PythonTypeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PythonType")
        self.resize(1100, 820)
        
        # Game Engine
        self.engine = TypingEngine(mode="time", duration=30)

        # Central Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(40, 24, 40, 24)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Settings Bar
        self.settings_bar = SettingsBar()
        self.settings_bar.setFixedWidth(800)
        self.settings_bar.mode_changed.connect(self.change_mode)
        self.settings_bar.theme_changed.connect(self.change_theme)
        self.settings_bar.layout_changed.connect(self.change_layout)
        self.main_layout.addWidget(self.settings_bar, alignment=Qt.AlignCenter)

        # UI Components
        self.hud = StatsHUD()
        self.hud.setFixedWidth(800)
        self.main_layout.addWidget(self.hud, alignment=Qt.AlignCenter)

        self.display = TypingDisplay()
        self.display.setFixedSize(800, 300)
        self.main_layout.addWidget(self.display, alignment=Qt.AlignCenter)

        # Keyboard Visualizer
        self.keyboard = KeyboardVisualizer()
        self.keyboard.setFixedWidth(800)
        self.main_layout.addWidget(self.keyboard, alignment=Qt.AlignCenter)
        
        # Connect Signals
        self.display.key_pressed.connect(self.handle_key)
        self.display.restart_requested.connect(self.restart_game)

        # Overlay (Result Screen) - Create it last and don't add to layout
        self.overlay = ResultOverlay(self.central_widget)
        self.overlay.hide()
        self.overlay.restart_requested.connect(self.restart_game)

        # Game Loop Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_tick)
        self.timer.start(100)

        # Initial Theme Apply
        self.apply_theme()
        self.update_display()
        
        # Ensure focus is on the typing display
        self.display.setFocus()

    def resizeEvent(self, event):
        # Center the overlay manually
        overlay_width = 700
        overlay_height = 500
        self.overlay.setGeometry(
            (self.width() - overlay_width) // 2,
            (self.height() - overlay_height) // 2,
            overlay_width,
            overlay_height
        )
        super().resizeEvent(event)

    def apply_theme(self):
        theme = resources.get_theme()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg']};
            }}
        """)
        self.settings_bar.apply_theme()
        self.hud.apply_theme()
        self.display.apply_theme()
        self.keyboard.apply_theme()
        self.overlay.apply_theme()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.restart_game()
            event.accept()
        else:
            super().keyPressEvent(event)

    def change_mode(self, mode):
        self.engine.mode = mode
        self.restart_game()

    def change_theme(self, theme_name):
        resources.CURRENT_THEME = theme_name
        self.apply_theme()
        self.update_display()

    def change_layout(self, layout_name):
        self.engine.layout = layout_name
        self.keyboard.set_layout(layout_name)
        self.restart_game()

    def handle_key(self, char):
        if self.engine.is_finished:
            return

        # Visual feedback on keyboard
        if char == '\b':
            self.keyboard.reset_keys()
        else:
            # Check if correct before processing to determine highlight color
            idx = len(self.engine.user_input)
            correct = False
            if idx < len(self.engine.target_text):
                correct = (char == self.engine.target_text[idx])
            
            self.keyboard.highlight_key(char, correct=correct)

        finished = self.engine.process_key(char)
        self.update_display()

        if finished:
            self.finish_game()

    def update_display(self):
        self.display.render_text(self.engine.target_text, self.engine.user_input)
        
    def game_tick(self):
        if self.engine.is_running:
            elapsed = self.engine.get_time_elapsed()
            
            if self.engine.mode == "time":
                remaining = self.engine.test_duration - int(elapsed)
                self.hud.update_stats(max(0, remaining), self.engine.wpm, self.engine.accuracy)
                if remaining <= 0:
                    self.finish_game()
            else:
                # In word/quote mode, timer counts up
                self.hud.update_stats(int(elapsed), self.engine.wpm, self.engine.accuracy)

    def finish_game(self):
        self.engine.stop()
        elapsed = int(self.engine.get_time_elapsed())
        self.hud.update_stats(elapsed, self.engine.wpm, self.engine.accuracy)
        
        # Format missed details
        missed_str = ""
        if not self.engine.missed_data:
            missed_str = "Perfect! No mistakes."
        else:
            misses = {}
            for exp, typed in self.engine.missed_data:
                key = f"'{exp}'" if exp != " " else "[Space]"
                misses[key] = misses.get(key, 0) + 1
            
            missed_str = "Characters missed:\n"
            for char, count in misses.items():
                missed_str += f"{char}: {count} times\n"

        # Hide main UI for better focus
        self.settings_bar.hide()
        self.hud.hide()
        self.display.hide()
        self.keyboard.hide()
        
        self.overlay.show_results(self.engine.wpm, self.engine.accuracy, missed_str)

    def restart_game(self):
        if self.engine.is_running:
            self.engine.stop()
            
        self.engine.reset()
        self.update_display()
        self.keyboard.reset_keys()
        
        # Show main UI
        self.settings_bar.show()
        self.hud.show()
        self.display.show()
        self.keyboard.show()
        
        if self.engine.mode == "time":
            self.hud.update_stats(self.engine.test_duration, 0, 100)
        else:
            self.hud.update_stats(0, 0, 100)
        self.overlay.hide()
        self.display.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PythonTypeApp()
    window.show()
    sys.exit(app.exec_())
