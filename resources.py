# resources.py

# Themes (bg, main text, correct, error, caret/accent)
THEMES = {
    "monkeytype": {
        "bg": "#323437",
        "main": "#646669",
        "correct": "#d1d0c5",
        "error": "#ca4754",
        "caret": "#e2b714"
    },
    "github_light": {
        "bg": "#ffffff",
        "main": "#959da5",
        "correct": "#24292e",
        "error": "#d73a49",
        "caret": "#0366d6"
    },
    "github_dark": {
        "bg": "#0d1117",
        "main": "#484f58",
        "correct": "#c9d1d9",
        "error": "#f85149",
        "caret": "#58a6ff"
    },
    "mint": {
        "bg": "#053b3e",
        "main": "#479599",
        "correct": "#f1fffa",
        "error": "#ff5a5f",
        "caret": "#00ff9c"
    },
    "nord": {
        "bg": "#2e3440",
        "main": "#4c566a",
        "correct": "#eceff4",
        "error": "#bf616a",
        "caret": "#88c0d0"
    },
    "dracula": {
        "bg": "#282a36",
        "main": "#6272a4",
        "correct": "#f8f8f2",
        "error": "#ff5555",
        "caret": "#bd93f9"
    },
    "solarized_dark": {
        "bg": "#002b36",
        "main": "#586e75",
        "correct": "#839496",
        "error": "#dc322f",
        "caret": "#268bd2"
    },
    "solarized_light": {
        "bg": "#fdf6e3",
        "main": "#657b83",
        "correct": "#586e75",
        "error": "#dc322f",
        "caret": "#268bd2"
    },
    "gruvbox_dark": {
        "bg": "#282828",
        "main": "#928374",
        "correct": "#ebdbb2",
        "error": "#fb4934",
        "caret": "#fabd2f"
    },
    "gruvbox_light": {
        "bg": "#fbf1c7",
        "main": "#7c6f64",
        "correct": "#3c3836",
        "error": "#cc241d",
        "caret": "#b57614"
    },
    "one_dark": {
        "bg": "#282c34",
        "main": "#5c6370",
        "correct": "#abb2bf",
        "error": "#e06c75",
        "caret": "#61afef"
    },
    "catppuccin_mocha": {
        "bg": "#1e1e2e",
        "main": "#6c7086",
        "correct": "#cdd6f4",
        "error": "#f38ba8",
        "caret": "#89b4fa"
    },
    "rose_pine": {
        "bg": "#191724",
        "main": "#6e6a86",
        "correct": "#e0def4",
        "error": "#eb6f92",
        "caret": "#9ccfd8"
    },
    "tokyo_night": {
        "bg": "#1a1b26",
        "main": "#565f89",
        "correct": "#a9b1d6",
        "error": "#f7768e",
        "caret": "#7aa2f7"
    },
    "everforest": {
        "bg": "#2f333e",
        "main": "#7f897d",
        "correct": "#d3c6aa",
        "error": "#e67e80",
        "caret": "#7fbbb3"
    },
}

# Current Theme (Default)
CURRENT_THEME = "monkeytype"

def get_theme():
    return THEMES[CURRENT_THEME]

# Colors (Monkeytype Theme - kept for compatibility initially)
COLOR_BG = THEMES["monkeytype"]["bg"]
COLOR_TEXT_Main = THEMES["monkeytype"]["main"]
COLOR_TEXT_CORRECT = THEMES["monkeytype"]["correct"]
COLOR_TEXT_ERROR = THEMES["monkeytype"]["error"]
COLOR_CARET = THEMES["monkeytype"]["caret"]

# Fonts
FONT_FAMILY = "Consolas, 'Courier New', monospace"
FONT_SIZE = 24

# Word List (Top ~200 common English words)
WORD_LIST = [
    "the", "be", "of", "and", "a", "to", "in", "he", "have", "it", "that", "for", "they", "i", "with", "as", "not", "on", "she", "at",
    "by", "this", "we", "you", "do", "but", "from", "or", "which", "one", "would", "all", "will", "there", "say", "who", "make", "when",
    "can", "more", "if", "no", "man", "out", "other", "so", "what", "time", "up", "go", "about", "than", "into", "could", "state", "only",
    "new", "year", "some", "take", "come", "these", "know", "see", "use", "get", "like", "then", "first", "any", "work", "now", "may",
    "such", "give", "over", "think", "most", "even", "find", "day", "also", "after", "way", "many", "must", "look", "before", "great",
    "back", "through", "long", "where", "much", "should", "well", "people", "down", "own", "just", "because", "good", "each", "those",
    "feel", "seem", "how", "high", "too", "place", "little", "world", "very", "still", "nation", "hand", "old", "life", "tell", "write",
    "become", "here", "show", "house", "both", "between", "need", "mean", "call", "develop", "under", "last", "right", "move", "thing",
    "general", "school", "never", "same", "another", "begin", "while", "number", "part", "turn", "real", "leave", "might", "want", "point",
    "form", "off", "child", "few", "small", "since", "against", "ask", "late", "home", "interest", "large", "person", "end", "open",
    "public", "follow", "during", "present", "without", "again", "hold", "govern", "around", "possible", "head", "consider", "word",
    "program", "problem", "however", "lead", "system", "set", "order", "eye", "plan", "run", "keep", "face", "fact", "group", "play",
    "stand", "increase", "early", "course", "change", "help", "line"
]

QUOTE_LIST = [
    "The only way to do great work is to love what you do.",
    "Stay hungry, stay foolish.",
    "Be the change that you wish to see in the world.",
    "In the middle of difficulty lies opportunity.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "Believe you can and you're halfway there.",
    "Life is what happens when you're making other plans.",
    "The future belongs to those who believe in the beauty of their dreams.",
    "Do not go where the path may lead, go instead where there is no path and leave a trail."
]
