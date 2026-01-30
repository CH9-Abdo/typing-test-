# logic.py
import random
import time
import json
import os
from resources import WORD_LIST, QUOTE_LIST

class HistoryManager:
    FILE_PATH = "typing_history.json"

    @staticmethod
    def save_attempt(data):
        history = HistoryManager.load_history()
        history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": data.get("mode"),
            "wpm": data.get("wpm"),
            "accuracy": data.get("accuracy"),
            "missed": data.get("missed_count")
        })
        # Keep only last 50
        history = history[-50:]
        try:
            with open(HistoryManager.FILE_PATH, "w") as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    @staticmethod
    def load_history():
        if os.path.exists(HistoryManager.FILE_PATH):
            try:
                with open(HistoryManager.FILE_PATH, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    @staticmethod
    def get_last_attempt():
        history = HistoryManager.load_history()
        return history[-1] if history else None

    @staticmethod
    def get_previous_attempt():
        """Returns the attempt before the last one (for comparison after current run is saved)."""
        history = HistoryManager.load_history()
        return history[-2] if len(history) >= 2 else None

class TypingEngine:
    def __init__(self, mode="time", duration=30, word_count=25):
        self.mode = mode # "time", "word", "quote"
        self.test_duration = duration
        self.target_word_count = word_count
        self.words = []
        self.target_text = ""
        self.user_input = ""
        self.start_time = 0
        self.is_running = False
        self.is_finished = False
        self.wpm = 0
        self.accuracy = 0
        self.correct_chars = 0
        self.total_chars = 0
        self.missed_data = [] # List of (expected, typed) tuples for mistakes
        
        self.reset()

    def reset(self):
        if self.mode == "time":
            self.words = random.sample(WORD_LIST, 100) # Get more words for time mode
            self.target_text = " ".join(self.words)
        elif self.mode == "word":
            self.words = random.sample(WORD_LIST, self.target_word_count)
            self.target_text = " ".join(self.words)
        elif self.mode == "quote":
            self.target_text = random.choice(QUOTE_LIST)
            
        self.user_input = ""
        self.start_time = 0
        self.is_running = False
        self.is_finished = False
        self.wpm = 0
        self.accuracy = 100
        self.correct_chars = 0
        self.total_chars = 0
        self.missed_data = []

    def start(self):
        if not self.is_running and not self.is_finished:
            self.is_running = True
            self.start_time = time.time()

    def stop(self):
        self.is_running = False
        self.is_finished = True
        self.calculate_stats()
        
        # Save to history
        HistoryManager.save_attempt({
            "mode": self.mode,
            "wpm": self.wpm,
            "accuracy": self.accuracy,
            "missed_count": len(self.missed_data)
        })

    def process_key(self, key_text):
        if self.is_finished:
            return False

        if not self.is_running:
            self.start()

        # Handle backspace
        if key_text == '\b': 
            if len(self.user_input) > 0:
                self.user_input = self.user_input[:-1]
                # Optional: remove last missed data if it was at this position? 
                # Monkeytype usually counts every mistake even if corrected.
        else:
            # Track mistake and append only if not past end
            idx = len(self.user_input)
            if idx < len(self.target_text):
                expected = self.target_text[idx]
                if key_text != expected:
                    self.missed_data.append((expected, key_text))
                self.user_input += key_text
                self.total_chars += 1

        self.calculate_stats()

        # In word/quote mode, test is complete when user has typed the full text
        if self.mode in ("word", "quote") and len(self.user_input) >= len(self.target_text):
            return True
        return False

    def calculate_stats(self):
        if not self.start_time:
            return

        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed == 0:
            elapsed = 0.001

        # Count correct chars
        self.correct_chars = 0
        for i, char in enumerate(self.user_input):
            if i < len(self.target_text) and char == self.target_text[i]:
                self.correct_chars += 1
        
        # WPM: (correct_chars / 5) / (minutes)
        minutes = elapsed / 60
        self.wpm = int((self.correct_chars / 5) / minutes)
        
        # Accuracy
        if len(self.user_input) > 0:
            self.accuracy = int((self.correct_chars / len(self.user_input)) * 100)
        else:
            self.accuracy = 100

    def get_time_elapsed(self):
        if not self.is_running:
            return 0
        return time.time() - self.start_time
