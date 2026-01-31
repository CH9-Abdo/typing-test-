# logic.py
import random
import time
import json
import os
import sys
from resources import WORD_LIST, QUOTE_LIST

def _app_dir():
    return os.path.dirname(os.path.abspath(__file__))

class StatsManager:
    FILE_PATH = os.path.join(_app_dir(), "typing_stats.json")

    @staticmethod
    def load_stats():
        if os.path.exists(StatsManager.FILE_PATH):
            try:
                with open(StatsManager.FILE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    @staticmethod
    def save_stats(stats):
        try:
            with open(StatsManager.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=4)
        except OSError as e:
            print(f"Error saving stats: {e}", file=sys.stderr)

    @staticmethod
    def update_missed_chars(missed_list):
        """missed_list is list of (expected, typed) tuples"""
        stats = StatsManager.load_stats()
        missed_counts = stats.get("missed_chars", {})
        
        for expected, typed in missed_list:
            # We track the character that was EXPECTED but missed
            # We can also track based on what was typed wrong if we want, but usually you practice what you missed.
            char = expected
            if char not in missed_counts:
                missed_counts[char] = 0
            missed_counts[char] += 1
            
        stats["missed_chars"] = missed_counts
        StatsManager.save_stats(stats)

    @staticmethod
    def get_weighted_words(count=25):
        stats = StatsManager.load_stats()
        missed_counts = stats.get("missed_chars", {})
        
        if not missed_counts:
            # No data, return random
            return random.sample(WORD_LIST, min(len(WORD_LIST), count))
        
        # Score words based on missed chars
        # Score = sum of counts of chars in word
        word_scores = []
        for word in WORD_LIST:
            score = 0
            for char in word:
                score += missed_counts.get(char, 0)
            # Add a small base score so even non-missed words have a tiny chance/weight if needed, 
            # or just to differentiate 0 score.
            # But here we want to prioritize missed.
            if score > 0:
                word_scores.append((word, score))
        
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # If we have enough scored words, pick from top 50% or top N
        # Let's simple strategy: Pick top 30% of words with problems, then sample?
        # Or just take top 'count' words? That might be repetitive.
        # Let's take top 50 problematic words and sample 'count' from them.
        
        top_candidates = [w for w, s in word_scores[:50]]
        
        if len(top_candidates) < count:
            # Fill rest with random
            needed = count - len(top_candidates)
            others = [w for w in WORD_LIST if w not in top_candidates]
            result = top_candidates + random.sample(others, min(len(others), needed))
            random.shuffle(result)
            return result
        
        return random.sample(top_candidates, count)


class HistoryManager:
    FILE_PATH = os.path.join(_app_dir(), "typing_history.json")
    _last_save_error = None  # Optional: UI can check and show message

    @staticmethod
    def save_attempt(data):
        HistoryManager._last_save_error = None
        history = HistoryManager.load_history()
        history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": data.get("mode"),
            "wpm": data.get("wpm"),
            "accuracy": data.get("accuracy"),
            "missed": data.get("missed_count")
        })
        history = history[-50:]
        try:
            with open(HistoryManager.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except OSError as e:
            HistoryManager._last_save_error = str(e)
            print(f"Error saving history: {e}", file=sys.stderr)

    @staticmethod
    def load_history():
        if os.path.exists(HistoryManager.FILE_PATH):
            try:
                with open(HistoryManager.FILE_PATH, "r", encoding="utf-8") as f:
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
        self.mode = mode  # "time", "word", "quote", "practice"
        self.test_duration = duration
        self.target_word_count = word_count
        self.layout = "qwerty"  # "qwerty" or "dvorak" (for keyboard visualizer)
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
        elif self.mode == "practice":
            self.words = StatsManager.get_weighted_words(self.target_word_count)
            self.target_text = " ".join(self.words)
            
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
        
        # Save detailed stats
        if self.missed_data:
             StatsManager.update_missed_chars(self.missed_data)

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

        # In word/quote/practice mode, test is complete when user has typed the full text
        if self.mode in ("word", "quote", "practice") and len(self.user_input) >= len(self.target_text):
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
