# ui_components.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import resources

class SettingsBar(QWidget):
    mode_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    layout_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 12, 20, 12)
        self.layout.setSpacing(24)
        
        # Mode Selector
        self.mode_label = QLabel("Mode")
        self.mode_label.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["time", "word", "quote"])
        self.mode_combo.currentTextChanged.connect(self.mode_changed.emit)
        self.layout.addWidget(self.mode_label)
        self.layout.addWidget(self.mode_combo)

        # Theme Selector (sync with current theme, avoid spurious emit on init)
        self.theme_label = QLabel("Theme")
        self.theme_label.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.theme_combo = QComboBox()
        theme_names = list(resources.THEMES.keys())
        self.theme_combo.addItems(theme_names)
        idx = theme_names.index(resources.CURRENT_THEME) if resources.CURRENT_THEME in theme_names else 0
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.blockSignals(False)
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        self.layout.addWidget(self.theme_label)
        self.layout.addWidget(self.theme_combo)

        # Layout Selector
        self.layout_label = QLabel("Layout")
        self.layout_label.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["qwerty", "dvorak"])
        self.layout_combo.currentTextChanged.connect(self.layout_changed.emit)
        self.layout.addWidget(self.layout_label)
        self.layout.addWidget(self.layout_combo)

        self.layout.addStretch()
        self.apply_theme()

    def apply_theme(self):
        theme = resources.get_theme()
        # Keep combo in sync with current theme (e.g. after loading config)
        theme_names = list(resources.THEMES.keys())
        if resources.CURRENT_THEME in theme_names:
            idx = theme_names.index(resources.CURRENT_THEME)
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(idx)
            self.theme_combo.blockSignals(False)
        self.setStyleSheet(f"""
            SettingsBar {{
                background-color: {theme['bg']};
                border: 1px solid {theme['main']};
                border-radius: 12px;
                color: {theme['main']};
            }}
        """)
        label_style = f"color: {theme['main']}; background: transparent; border: none;"
        self.mode_label.setStyleSheet(label_style)
        self.theme_label.setStyleSheet(label_style)
        self.layout_label.setStyleSheet(label_style)
        
        cb_style = f"""
            QComboBox {{
                background-color: {theme['main']};
                color: {theme['bg']};
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 100px;
                font-weight: bold;
            }}
            QComboBox:hover {{
                background-color: {theme['caret']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['bg']};
                color: {theme['main']};
                selection-background-color: {theme['caret']};
                selection-color: {theme['bg']};
                border-radius: 6px;
                padding: 4px;
            }}
        """
        self.mode_combo.setStyleSheet(cb_style)
        self.theme_combo.setStyleSheet(cb_style)
        self.layout_combo.setStyleSheet(cb_style)

class KeyboardVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)
        self.keys = {}
        self.current_layout = "qwerty"
        
        self.qwerty_rows = [
            "qwertyuiop[]",
            "asdfghjkl;'",
            "zxcvbnm,./"
        ]
        self.dvorak_rows = [
            "',.pyfgcrl/=",
            "aoeuidhtns-",
            ";qjkxbmnwvz"
        ]
        
        self.init_keys()
        self.apply_theme()

    def init_keys(self):
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        
        self.keys = {}
        rows = self.qwerty_rows if self.current_layout == "qwerty" else self.dvorak_rows
        
        for row_str in rows:
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignCenter)
            row_layout.setSpacing(6)
            for char in row_str:
                label = QLabel(char.upper())
                label.setFixedSize(44, 44)
                label.setAlignment(Qt.AlignCenter)
                label.setFont(QFont("Consolas", 11, QFont.Bold))
                row_layout.addWidget(label)
                self.keys[char] = label
            self.layout.addLayout(row_layout)
        
        # Add Spacebar
        space_layout = QHBoxLayout()
        space_layout.setAlignment(Qt.AlignCenter)
        space_label = QLabel("SPACE")
        space_label.setFixedSize(320, 40)
        space_label.setAlignment(Qt.AlignCenter)
        space_label.setFont(QFont("Consolas", 10, QFont.Bold))
        space_layout.addWidget(space_label)
        self.keys[" "] = space_label
        self.layout.addLayout(space_layout)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def set_layout(self, layout_name):
        self.current_layout = layout_name
        self.init_keys()
        self.apply_theme()

    def apply_theme(self):
        theme = resources.get_theme()
        self.setStyleSheet(f"""
            KeyboardVisualizer {{
                background-color: {theme['bg']};
                border: 1px solid {theme['main']};
                border-radius: 12px;
            }}
        """)
        for char, label in self.keys.items():
            label.setStyleSheet(f"""
                background-color: {theme['main']};
                color: {theme['bg']};
                border-radius: 8px;
                border: 1px solid transparent;
            """)

    def highlight_key(self, char, correct=True):
        theme = resources.get_theme()
        char_lower = char.lower()
        if char_lower in self.keys:
            label = self.keys[char_lower]
            color = theme['correct'] if correct else theme['error']
            label.setStyleSheet(f"""
                background-color: {color};
                color: {theme['bg']};
                border: 2px solid {theme['caret']};
                border-radius: 8px;
            """)
            QTimer.singleShot(150, lambda: self.reset_key(char_lower))

    def reset_key(self, char):
        theme = resources.get_theme()
        if char in self.keys:
            self.keys[char].setStyleSheet(f"""
                background-color: {theme['main']};
                color: {theme['bg']};
                border: 1px solid transparent;
                border-radius: 8px;
            """)

    def reset_keys(self):
        self.apply_theme()

class StatsHUD(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(4)
        
        # Timer Label
        self.time_label = QLabel("30")
        self.time_label.setFont(QFont("Consolas", 42, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.time_label)
        
        # Live WPM/Acc
        self.stats_label = QLabel("WPM: 0   ·   ACC: 100%")
        self.stats_label.setFont(QFont("Segoe UI", 13))
        self.stats_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.stats_label)
        
        self.apply_theme()

    def apply_theme(self):
        theme = resources.get_theme()
        self.setStyleSheet(f"""
            StatsHUD {{
                background-color: {theme['bg']};
                border: 1px solid {theme['main']};
                border-radius: 12px;
            }}
        """)
        self.time_label.setStyleSheet(f"color: {theme['caret']}; background: transparent; border: none;")
        self.stats_label.setStyleSheet(f"color: {theme['main']}; background: transparent; border: none;")

    def update_stats(self, time_left, wpm, acc):
        self.time_label.setText(str(time_left))
        self.stats_label.setText(f"WPM: {wpm}   ·   ACC: {acc}%")

class TypingDisplay(QTextEdit):
    key_pressed = pyqtSignal(str)
    restart_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameStyle(0)
        self.setFocusPolicy(Qt.StrongFocus)
        
        font = QFont()
        font.setFamily("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(resources.FONT_SIZE)
        self.setFont(font)
        
        self.viewport().setCursor(Qt.BlankCursor)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.apply_theme()

    def apply_theme(self):
        theme = resources.get_theme()
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg']};
                color: {theme['main']};
                border: 1px solid {theme['main']};
                border-radius: 12px;
                padding: 20px;
            }}
        """)

    def keyPressEvent(self, event):
        text = event.text()
        key = event.key()

        if key == Qt.Key_Tab:
            event.accept()
            self.restart_requested.emit()
            return

        if key == Qt.Key_Backspace:
            self.key_pressed.emit('\b')
        elif text:
            if len(text) == 1 and text.isprintable():
                self.key_pressed.emit(text)
            elif key == Qt.Key_Space:
                self.key_pressed.emit(" ")

    def render_text(self, target_text, user_input):
        theme = resources.get_theme()
        html = ""
        cursor_idx = len(user_input)

        for i, char in enumerate(target_text):
            color = theme['main']
            bg_color = "transparent"
            is_cursor = (i == cursor_idx)
            
            if i < len(user_input):
                if user_input[i] == char:
                    color = theme['correct']
                else:
                    color = theme['error']
            
            if is_cursor:
                bg_color = theme['caret']
                if color == theme['main']:
                    color = theme['bg']

            display_char = char
            if char == "<": display_char = "&lt;"
            elif char == ">": display_char = "&gt;"
            elif char == "&": display_char = "&amp;"
            
            span = f'<span style="color:{color}; background-color:{bg_color};">{display_char}</span>'
            html += span

        if cursor_idx >= len(target_text):
             html += f'<span style="background-color:{theme["caret"]}; color:{theme["bg"]};">&nbsp;</span>'

        final_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: 'Consolas', monospace; font-size: {resources.FONT_SIZE}pt; line-height: 1.5; }}
        </style>
        </head>
        <body>{html}</body>
        </html>
        """
        self.setHtml(final_html)
        text_cursor = self.textCursor()
        text_cursor.setPosition(min(cursor_idx, len(self.toPlainText())))
        self.setTextCursor(text_cursor)
        self.ensureCursorVisible()

class ResultOverlay(QWidget):
    restart_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 36, 40, 36)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(24)
        self.setLayout(self.layout)

        # Title
        self.title_label = QLabel("Results")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.layout.addWidget(self.title_label)

        # Main Stats Row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(60)
        self.stats_row.setAlignment(Qt.AlignCenter)

        self.wpm_container = self._create_stat_box("WPM", "0")
        self.acc_container = self._create_stat_box("ACC", "0%")
        
        self.stats_row.addWidget(self.wpm_container)
        self.stats_row.addWidget(self.acc_container)
        self.layout.addLayout(self.stats_row)

        # Missed Words / Error details
        self.details_label = QLabel("Summary")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.layout.addWidget(self.details_label)

        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setFixedSize(580, 140)
        self.error_log.setFrameStyle(0)
        self.error_log.setFont(QFont("Consolas", 11))
        self.layout.addWidget(self.error_log, alignment=Qt.AlignCenter)

        self.hint = QLabel("Press TAB to restart")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self.layout.addWidget(self.hint)
        
        self.hide()
        self.apply_theme()

    def _create_stat_box(self, label_text, value_text):
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setSpacing(4)
        
        l = QLabel(label_text)
        l.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        l.setAlignment(Qt.AlignCenter)
        
        v = QLabel(value_text)
        v.setFont(QFont("Consolas", 44, QFont.Bold))
        v.setAlignment(Qt.AlignCenter)
        
        lay.addWidget(l)
        lay.addWidget(v)
        
        container.title_label = l
        container.value_label = v
        return container

    def apply_theme(self):
        theme = resources.get_theme()
        self.setStyleSheet(f"""
            ResultOverlay {{
                background-color: {theme['bg']};
                border: 2px solid {theme['main']};
                border-radius: 16px;
            }}
        """)
        self.title_label.setStyleSheet(f"color: {theme['caret']}; background: transparent; border: none;")
        for box in [self.wpm_container, self.acc_container]:
            box.title_label.setStyleSheet(f"color: {theme['main']}; background: transparent; border: none;")
            box.value_label.setStyleSheet(f"color: {theme['caret']}; background: transparent; border: none;")
        
        self.details_label.setStyleSheet(f"color: {theme['main']}; border-top: 1px solid {theme['main']}; padding-top: 12px; background: transparent;")
        self.error_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg']};
                color: {theme['main']};
                border: 1px solid {theme['main']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        self.hint.setStyleSheet(f"color: {theme['main']}; margin-top: 8px; background: transparent; border: none;")

    def show_results(self, wpm, acc, missed_details="No mistakes! Well done."):
        self.wpm_container.value_label.setText(str(wpm))
        self.acc_container.value_label.setText(f"{acc}%")
        
        # Load previous attempt (before this one) for comparison
        from logic import HistoryManager
        previous = HistoryManager.get_previous_attempt()
        comparison = ""
        if previous:
            comparison = f"\n\nPrevious: {previous['wpm']} WPM | {previous['accuracy']}% ACC"

        self.error_log.setText(missed_details + comparison)
        self.show()
        self.raise_()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            event.accept()
            self.restart_requested.emit()
            self.hide()
