# tests/test_logic.py - Unit tests for TypingEngine and HistoryManager
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

# Run from project root so imports work
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import TypingEngine, HistoryManager


class TestTypingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TypingEngine(mode="word", duration=30, word_count=5)

    def test_reset_sets_target_text(self):
        self.engine.reset()
        self.assertIsInstance(self.engine.target_text, str)
        self.assertGreater(len(self.engine.target_text), 0)
        self.assertEqual(self.engine.user_input, "")
        self.assertFalse(self.engine.is_running)
        self.assertFalse(self.engine.is_finished)

    def test_process_key_starts_timer(self):
        self.engine.reset()
        self.assertFalse(self.engine.is_running)
        self.engine.process_key("a")
        self.assertTrue(self.engine.is_running)

    def test_process_key_correct_char(self):
        self.engine.reset()
        first_char = self.engine.target_text[0]
        finished = self.engine.process_key(first_char)
        self.assertEqual(self.engine.user_input, first_char)
        self.assertFalse(finished)

    def test_process_key_wrong_char_tracks_missed(self):
        self.engine.reset()
        first_char = self.engine.target_text[0]
        wrong = "x" if first_char != "x" else "y"
        self.engine.process_key(wrong)
        self.assertEqual(len(self.engine.missed_data), 1)
        self.assertEqual(self.engine.missed_data[0][0], first_char)
        self.assertEqual(self.engine.missed_data[0][1], wrong)

    def test_process_key_backspace(self):
        self.engine.reset()
        c = self.engine.target_text[0]
        self.engine.process_key(c)
        self.engine.process_key("\b")
        self.assertEqual(self.engine.user_input, "")

    def test_word_mode_completion_returns_true(self):
        self.engine.reset()
        finished = False
        for c in self.engine.target_text:
            finished = self.engine.process_key(c)
        self.assertTrue(finished)

    def test_quote_mode_completion_returns_true(self):
        engine = TypingEngine(mode="quote", duration=30)
        engine.reset()
        finished = False
        for c in engine.target_text:
            finished = engine.process_key(c)
        self.assertTrue(finished)

    def test_does_not_append_past_end(self):
        self.engine.reset()
        for c in self.engine.target_text:
            self.engine.process_key(c)
        len_after = len(self.engine.user_input)
        self.engine.process_key("x")  # extra key
        self.assertEqual(len(self.engine.user_input), len_after)

    def test_calculate_stats_wpm_accuracy(self):
        self.engine.reset()
        self.engine.start()
        for c in self.engine.target_text[:10]:
            self.engine.process_key(c)
        self.engine.calculate_stats()
        self.assertGreaterEqual(self.engine.wpm, 0)
        self.assertGreaterEqual(self.engine.accuracy, 0)
        self.assertLessEqual(self.engine.accuracy, 100)


class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self.tmp.close()
        self.original_path = HistoryManager.FILE_PATH
        HistoryManager.FILE_PATH = self.tmp.name

    def tearDown(self):
        HistoryManager.FILE_PATH = self.original_path
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_save_and_load_history(self):
        HistoryManager.save_attempt({
            "mode": "time", "wpm": 50, "accuracy": 95, "missed_count": 2
        })
        history = HistoryManager.load_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["wpm"], 50)
        self.assertEqual(history[0]["accuracy"], 95)

    def test_load_empty_returns_list(self):
        history = HistoryManager.load_history()
        self.assertEqual(history, [])

    def test_get_previous_attempt(self):
        HistoryManager.save_attempt({"mode": "time", "wpm": 40, "accuracy": 90, "missed_count": 0})
        HistoryManager.save_attempt({"mode": "time", "wpm": 50, "accuracy": 95, "missed_count": 2})
        prev = HistoryManager.get_previous_attempt()
        self.assertIsNotNone(prev)
        self.assertEqual(prev["wpm"], 40)


if __name__ == "__main__":
    unittest.main()
