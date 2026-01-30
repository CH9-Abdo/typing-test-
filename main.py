# main.py - PythonType (Pygame)
import os
import pygame
import sys
from logic import TypingEngine, HistoryManager
import resources
import config
import sound_util

# --- Helpers ---
def hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

# --- Constants ---
WINDOW_W = 1100
WINDOW_H = 820
CONTENT_W = 800
HUD_TIMER_SIZE = 42
KEY_SIZE = 44
KEY_SPACE_W = 320
KEY_SPACE_H = 40
KEY_GAP = 6
KEYBOARD_ROWS_QWERTY = ["qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./"]
KEYBOARD_ROWS_DVORAK = ["',.pyfgcrl/=", "aoeuidhtns-", ";qjkxbmnwvz"]
HIGHLIGHT_MS = 150
THEME_DROPDOWN_MAX_H = 220
THEME_ITEM_H = 26
CARET_BLINK_MS = 500

def _font_path(name):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "fonts", name)

def _load_font(path, size):
    if os.path.isfile(path):
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    return None

def main():
    pygame.init()
    pygame.display.set_caption("PythonType")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    # Load config and apply to resources
    cfg = config.load_config()
    resources.CURRENT_THEME = cfg.get("theme", "monkeytype")
    font_size_px = config.get_font_size_px(cfg.get("font_size", "medium"))
    resources.FONT_SIZE = font_size_px

    roboto_regular = _font_path("Roboto-Regular.ttf")
    roboto_bold = _font_path("Roboto-Bold.ttf")
    font_mono = _load_font(roboto_regular, font_size_px) or pygame.font.SysFont("consolas", font_size_px)
    font_mono_large = _load_font(roboto_regular, HUD_TIMER_SIZE) or pygame.font.SysFont("consolas", HUD_TIMER_SIZE)
    font_ui = _load_font(roboto_regular, 13) or pygame.font.SysFont("segoeui", 13)
    font_ui_bold = _load_font(roboto_bold, 10) or pygame.font.SysFont("segoeui", 10, bold=True)
    font_key = _load_font(roboto_bold, 11) or pygame.font.SysFont("consolas", 11, bold=True)

    # Game state from config
    engine = TypingEngine(
        mode=cfg.get("mode", "time"),
        duration=int(cfg.get("duration", 30)),
        word_count=int(cfg.get("word_count", 25))
    )
    engine.layout = cfg.get("layout", "qwerty")
    mode_options = ["time", "word", "quote"]
    theme_names = list(resources.THEMES.keys())
    layout_options = ["qwerty", "dvorak"]
    duration_options = config.DURATION_OPTIONS
    word_count_options = config.WORD_COUNT_OPTIONS

    current_mode = cfg.get("mode", "time")
    current_theme_name = resources.CURRENT_THEME
    current_layout = cfg.get("layout", "qwerty")
    current_duration = engine.test_duration
    current_word_count = engine.target_word_count
    current_font_size = cfg.get("font_size", "medium")
    sound_on_error = cfg.get("sound_on_error", False)
    reduced_motion = cfg.get("reduced_motion", False)

    show_overlay = False
    overlay_wpm = 0
    overlay_acc = 0
    overlay_missed = ""

    theme_dropdown_rects = None
    theme_dropdown_scroll = 0
    key_highlight = None
    caret_visible = True
    last_caret_toggle = 0

    def save_cfg():
        c = {
            "theme": current_theme_name,
            "layout": current_layout,
            "mode": current_mode,
            "duration": current_duration,
            "word_count": current_word_count,
            "font_size": current_font_size,
            "sound_on_error": sound_on_error,
            "reduced_motion": reduced_motion,
        }
        config.save_config(c)

    # Content area (centered)
    def content_rect():
        w, h = screen.get_size()
        x = max(0, (w - CONTENT_W) // 2)
        return x, 24, CONTENT_W, h - 48

    def get_theme():
        return {k: hex_to_rgb(v) for k, v in resources.get_theme().items()}

    # ---- Layout / rects ----
    def layout_rects(cx, cy, cw):
        """Returns dict of section names -> (x, y, w, h) in content area."""
        y = cy
        settings_h = 92   # Two rows with separator
        settings_rect = (cx, y, cw, settings_h)
        y += settings_h + 20

        # HUD
        hud_h = 100
        hud_rect = (cx, y, cw, hud_h)
        y += hud_h + 20

        # Typing display
        display_h = 300
        display_rect = (cx, y, cw, display_h)
        y += display_h + 20

        # Keyboard (variable height)
        keyboard_rect = (cx, y, cw, 220)
        return {
            "settings": settings_rect,
            "hud": hud_rect,
            "display": display_rect,
            "keyboard": keyboard_rect,
        }

    # ---- Draw settings bar ----
    def draw_settings_bar(surface, theme, cx, cy, cw, ch):
        rect = pygame.Rect(cx, cy, cw, ch)
        pygame.draw.rect(surface, theme["main"], rect, 1)
        pygame.draw.rect(surface, theme["bg"], rect.inflate(-2, -2))

        x = cx + 20
        y_center = cy + ch // 2

        # Mode
        label = font_ui_bold.render("Mode", True, theme["main"])
        surface.blit(label, (x, y_center - label.get_height() // 2))
        x += label.get_width() + 12
        mode_rects = {}
        for opt in mode_options:
            tw, th = font_ui_bold.size(opt.upper())
            pw, ph = tw + 24, 32
            r = pygame.Rect(x, y_center - ph // 2, pw, ph)
            mode_rects[opt] = r
            color = theme["caret"] if opt == current_mode else theme["main"]
            pygame.draw.rect(surface, color, r)
            txt = font_ui_bold.render(opt.upper(), True, theme["bg"])
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
            x += pw + 12
        x += 24

        # Theme
        label = font_ui_bold.render("Theme", True, theme["main"])
        surface.blit(label, (x, y_center - label.get_height() // 2))
        x += label.get_width() + 12
        theme_btn = pygame.Rect(x, y_center - 16, 140, 32)
        pygame.draw.rect(surface, theme["main"], theme_btn)
        txt = font_ui_bold.render(current_theme_name[:12], True, theme["bg"])
        surface.blit(txt, (theme_btn.centerx - txt.get_width() // 2, theme_btn.centery - txt.get_height() // 2))
        x += theme_btn.width + 24

        # Layout
        label = font_ui_bold.render("Layout", True, theme["main"])
        surface.blit(label, (x, y_center - label.get_height() // 2))
        x += label.get_width() + 12
        layout_rects = {}
        for opt in layout_options:
            tw, th = font_ui_bold.size(opt.upper())
            pw, ph = tw + 24, 32
            r = pygame.Rect(x, y_center - ph // 2, pw, ph)
            layout_rects[opt] = r
            color = theme["caret"] if opt == current_layout else theme["main"]
            pygame.draw.rect(surface, color, r)
            txt = font_ui_bold.render(opt.upper(), True, theme["bg"])
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
            x += pw + 12

        # Row 2: Time, Words, Font, Sound, Reduced motion (fixed spacing)
        row2_y = cy + 56
        row2_h = 28
        gap = 10
        x2 = cx + 20
        duration_rects = {}
        for d in duration_options:
            r = pygame.Rect(x2, row2_y, 38, row2_h)
            duration_rects[d] = r
            color = theme["caret"] if d == current_duration else theme["main"]
            pygame.draw.rect(surface, color, r)
            txt = font_ui_bold.render(str(d), True, theme["bg"])
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
            x2 += 38 + 4
        x2 += gap
        words_rects = {}
        for w in word_count_options:
            r = pygame.Rect(x2, row2_y, 38, row2_h)
            words_rects[w] = r
            color = theme["caret"] if w == current_word_count else theme["main"]
            pygame.draw.rect(surface, color, r)
            txt = font_ui_bold.render(str(w), True, theme["bg"])
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
            x2 += 38 + 4
        x2 += gap
        font_rects = {}
        for f in ["small", "medium", "large"]:
            pw = 50
            r = pygame.Rect(x2, row2_y, pw, row2_h)
            font_rects[f] = r
            color = theme["caret"] if f == current_font_size else theme["main"]
            pygame.draw.rect(surface, color, r)
            txt = font_ui_bold.render(f[0].upper(), True, theme["bg"])
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
            x2 += pw + 4
        x2 += gap
        sound_rect = pygame.Rect(x2, row2_y, 58, row2_h)
        color = theme["caret"] if sound_on_error else theme["main"]
        pygame.draw.rect(surface, color, sound_rect)
        txt = font_ui_bold.render("Sound", True, theme["bg"])
        surface.blit(txt, (sound_rect.centerx - txt.get_width() // 2, sound_rect.centery - txt.get_height() // 2))
        x2 += 58 + gap
        reduced_rect = pygame.Rect(x2, row2_y, 72, row2_h)
        color = theme["caret"] if reduced_motion else theme["main"]
        pygame.draw.rect(surface, color, reduced_rect)
        txt = font_ui_bold.render("Reduced", True, theme["bg"])
        surface.blit(txt, (reduced_rect.centerx - txt.get_width() // 2, reduced_rect.centery - txt.get_height() // 2))
        # Separator line between row 1 and row 2
        pygame.draw.line(surface, theme["main"], (cx + 10, cy + 48), (cx + cw - 10, cy + 48), 1)

        return {
            "mode": mode_rects, "theme": theme_btn, "layout": layout_rects,
            "duration": duration_rects, "words": words_rects, "font": font_rects,
            "sound": sound_rect, "reduced": reduced_rect,
        }

    def get_settings_bar_rects(cx, cy, cw, ch):
        """Return same rect dict as draw_settings_bar, for hit testing without drawing."""
        x = cx + 20
        y_center = cy + 26
        x += font_ui_bold.size("Mode")[0] + 12
        mode_rects = {}
        for opt in mode_options:
            pw, ph = 52, 32
            r = pygame.Rect(x, y_center - ph // 2, pw, ph)
            mode_rects[opt] = r
            x += pw + 12
        x += 24
        x += font_ui_bold.size("Theme")[0] + 12
        theme_btn = pygame.Rect(x, y_center - 16, 140, 32)
        x += theme_btn.width + 24
        x += font_ui_bold.size("Layout")[0] + 12
        layout_rects = {}
        for opt in layout_options:
            pw, ph = 52, 32
            r = pygame.Rect(x, y_center - ph // 2, pw, ph)
            layout_rects[opt] = r
            x += pw + 12
        row2_y = cy + 56
        row2_h = 28
        gap = 10
        x2 = cx + 20
        duration_rects = {d: pygame.Rect(x2 + i * (38 + 4), row2_y, 38, row2_h) for i, d in enumerate(duration_options)}
        x2 += len(duration_options) * (38 + 4) + gap
        words_rects = {w: pygame.Rect(x2 + i * (38 + 4), row2_y, 38, row2_h) for i, w in enumerate(word_count_options)}
        x2 += len(word_count_options) * (38 + 4) + gap
        font_rects = {}
        for f in ["small", "medium", "large"]:
            pw = 50
            font_rects[f] = pygame.Rect(x2, row2_y, pw, row2_h)
            x2 += pw + 4
        x2 += gap
        sound_rect = pygame.Rect(x2, row2_y, 58, row2_h)
        x2 += 58 + gap
        reduced_rect = pygame.Rect(x2, row2_y, 72, row2_h)
        return {
            "mode": mode_rects, "theme": theme_btn, "layout": layout_rects,
            "duration": duration_rects, "words": words_rects, "font": font_rects,
            "sound": sound_rect, "reduced": reduced_rect,
        }

    # ---- Draw HUD ----
    def draw_hud(surface, theme, cx, cy, cw, ch, time_val, wpm, acc):
        rect = pygame.Rect(cx, cy, cw, ch)
        pygame.draw.rect(surface, theme["main"], rect, 1)
        pygame.draw.rect(surface, theme["bg"], rect.inflate(-2, -2))
        time_surf = font_mono_large.render(str(time_val), True, theme["caret"])
        surface.blit(time_surf, (cx + 24, cy + 12))
        stats_surf = font_ui.render(f"WPM: {wpm}   ·   ACC: {acc}%", True, theme["main"])
        surface.blit(stats_surf, (cx + 24, cy + 60))

    # ---- Wrap text into lines (by pixel width) ----
    def wrap_text(text, font, max_width):
        lines = []
        line = ""
        for ch in text:
            test = line + ch
            w = font.size(test)[0]
            if w <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = ch
        if line:
            lines.append(line)
        return lines

    # ---- Draw typing display ----
    def draw_display(surface, theme, cx, cy, cw, ch, target_text, user_input, caret_visible=True):
        rect = pygame.Rect(cx, cy, cw, ch)
        pygame.draw.rect(surface, theme["main"], rect, 1)
        pygame.draw.rect(surface, theme["bg"], rect.inflate(-2, -2))
        padding = 20
        inner_w = cw - 2 * padding
        inner_x, inner_y = cx + padding, cy + padding

        target_lines = wrap_text(target_text, font_mono, inner_w)
        line_height = font_mono.get_height() + 4
        cursor_idx = len(user_input)

        py = inner_y
        idx = 0
        for tline in target_lines:
            uline = user_input[idx : idx + len(tline)] if idx < len(user_input) else ""
            px = inner_x
            for i, tc in enumerate(tline):
                color = theme["main"]
                bg = None
                is_cursor = caret_visible and (idx + i) == cursor_idx
                if i < len(uline):
                    if uline[i] == tc:
                        color = theme["correct"]
                    else:
                        color = theme["error"]
                if is_cursor:
                    bg = theme["caret"]
                    if color == theme["main"]:
                        color = theme["bg"]
                cs = font_mono.render(tc, True, color)
                if bg is not None:
                    pygame.draw.rect(surface, bg, (px, py, cs.get_width(), line_height))
                surface.blit(cs, (px, py))
                px += cs.get_width()
            if caret_visible and idx + len(tline) == cursor_idx:
                cw_char = font_mono.size(" ")[0]
                pygame.draw.rect(surface, theme["caret"], (px, py, cw_char, line_height))
            idx += len(tline)
            py += line_height

    # ---- Keyboard key rects (for hit test and highlight) ----
    def build_key_rects(cx, cy, cw, layout_name):
        rows = KEYBOARD_ROWS_QWERTY if layout_name == "qwerty" else KEYBOARD_ROWS_DVORAK
        key_w = KEY_SIZE
        key_gap = KEY_GAP
        key_rects = {}
        # One block width so all rows align; each row centered within it
        max_row_len = max(len(r) for r in rows)
        block_width = max_row_len * (key_w + key_gap) - key_gap
        block_left = cx + (cw - block_width) // 2
        row_y = cy + 16
        for row_str in rows:
            row_width = len(row_str) * (key_w + key_gap) - key_gap
            start_x = block_left + (block_width - row_width) // 2
            x = start_x
            for ch in row_str:
                key_rects[ch] = pygame.Rect(x, row_y, key_w, key_w)
                x += key_w + key_gap
            row_y += key_w + key_gap
        # Spacebar centered in block
        space_x = block_left + (block_width - KEY_SPACE_W) // 2
        key_rects[" "] = pygame.Rect(space_x, row_y, KEY_SPACE_W, KEY_SPACE_H)
        return key_rects

    def draw_keyboard(surface, theme, cx, cy, cw, ch, layout_name, highlight_char=None, highlight_correct=True):
        rect = pygame.Rect(cx, cy, cw, ch)
        pygame.draw.rect(surface, theme["main"], rect, 1)
        pygame.draw.rect(surface, theme["bg"], rect.inflate(-2, -2))
        key_rects = build_key_rects(cx, cy, cw, layout_name)
        for ch, r in key_rects.items():
            if ch == highlight_char:
                color = theme["correct"] if highlight_correct else theme["error"]
            else:
                color = theme["main"]
            pygame.draw.rect(surface, color, r)
            label = "SPACE" if ch == " " else ch.upper()
            txt = font_key.render(label, True, theme["bg"])
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
        return key_rects

    # ---- Result overlay ----
    def draw_overlay(surface, theme, wpm, acc, missed_str):
        sw, sh = surface.get_size()
        ow, oh = 700, 500
        ox, oy = (sw - ow) // 2, (sh - oh) // 2
        rect = pygame.Rect(ox, oy, ow, oh)
        pygame.draw.rect(surface, theme["main"], rect, 2)
        pygame.draw.rect(surface, theme["bg"], rect.inflate(-4, -4))
        # Title
        title = font_ui_bold.render("Results", True, theme["caret"])
        surface.blit(title, (rect.centerx - title.get_width() // 2, oy + 36))
        # WPM / ACC
        wpm_label = font_ui_bold.render("WPM", True, theme["main"])
        surface.blit(wpm_label, (rect.centerx - 120 - wpm_label.get_width() // 2, oy + 80))
        wpm_val = font_mono_large.render(str(wpm), True, theme["caret"])
        surface.blit(wpm_val, (rect.centerx - 120 - wpm_val.get_width() // 2, oy + 100))
        acc_label = font_ui_bold.render("ACC", True, theme["main"])
        surface.blit(acc_label, (rect.centerx + 120 - acc_label.get_width() // 2, oy + 80))
        acc_val = font_mono_large.render(f"{acc}%", True, theme["caret"])
        surface.blit(acc_val, (rect.centerx + 120 - acc_val.get_width() // 2, oy + 100))
        # Missed details (multiline)
        y = oy + 160
        for line in missed_str.split("\n"):
            line_surf = font_ui.render(line[:80], True, theme["main"])
            surface.blit(line_surf, (ox + 40, y))
            y += line_surf.get_height() + 4
        # Previous attempt
        prev = HistoryManager.get_previous_attempt()
        if prev:
            comp = font_ui.render(f"Previous: {prev['wpm']} WPM | {prev['accuracy']}% ACC", True, theme["main"])
            surface.blit(comp, (ox + 40, y + 8))
        hint = font_ui_bold.render("Press TAB to restart", True, theme["main"])
        surface.blit(hint, (rect.centerx - hint.get_width() // 2, oy + oh - 50))

    # ---- Theme dropdown (scrollable, max height) ----
    def open_theme_dropdown(theme_btn_rect):
        nonlocal theme_dropdown_rects, theme_dropdown_scroll
        theme_dropdown_scroll = 0
        ty = theme_btn_rect.bottom + 4
        tx = theme_btn_rect.left
        theme_dropdown_rects = []
        for i, name in enumerate(theme_names):
            r = pygame.Rect(tx, ty + i * THEME_ITEM_H, 180, THEME_ITEM_H - 2)
            theme_dropdown_rects.append((r, name))
        return theme_dropdown_rects

    # ---- Game logic helpers ----
    def finish_game():
        nonlocal show_overlay, overlay_wpm, overlay_acc, overlay_missed
        engine.stop()
        overlay_wpm = engine.wpm
        overlay_acc = engine.accuracy
        if not engine.missed_data:
            overlay_missed = "Perfect! No mistakes."
        else:
            misses = {}
            for exp, typed in engine.missed_data:
                key = f"'{exp}'" if exp != " " else "[Space]"
                misses[key] = misses.get(key, 0) + 1
            overlay_missed = "Characters missed:\n"
            for char, count in misses.items():
                overlay_missed += f"{char}: {count} times\n"
        show_overlay = True

    def restart_game():
        nonlocal show_overlay, theme_dropdown_rects, key_highlight, caret_visible
        if engine.is_running:
            engine.stop()
        engine.reset()
        show_overlay = False
        theme_dropdown_rects = None
        key_highlight = None
        caret_visible = True

    # ---- Main loop ----
    last_tick = pygame.time.get_ticks()
    settings_rects_cache = None
    theme_dropdown_rects = None

    running = True
    while running:
        now = pygame.time.get_ticks()
        theme = get_theme()
        cx, cy, cw, ch = content_rect()
        layouts = layout_rects(cx, cy, cw)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if show_overlay:
                        restart_game()
                    else:
                        restart_game()
                    continue
                if show_overlay:
                    continue
                if event.key == pygame.K_BACKSPACE:
                    char = "\b"
                else:
                    char = event.unicode if event.unicode and event.unicode.isprintable() else None
                    if event.key == pygame.K_SPACE:
                        char = " "
                if char is not None:
                    if char == "\b":
                        key_highlight = None
                    else:
                        idx = len(engine.user_input)
                        correct = idx < len(engine.target_text) and engine.target_text[idx] == char
                        key_highlight = (char, correct, now)
                        if sound_on_error and not correct and idx < len(engine.target_text):
                            try:
                                sound_util.play_error_beep()
                            except Exception:
                                pass
                    if not engine.is_finished:
                        finished = engine.process_key(char)
                        if finished:
                            finish_game()
            elif event.type == pygame.MOUSEWHEEL:
                if theme_dropdown_rects:
                    max_scroll = max(0, len(theme_names) * THEME_ITEM_H - THEME_DROPDOWN_MAX_H)
                    theme_dropdown_scroll = max(0, min(max_scroll, theme_dropdown_scroll - event.y * 30))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                pos = event.pos
                # Theme dropdown (account for scroll)
                if theme_dropdown_rects:
                    tx = theme_dropdown_rects[0][0].x
                    ty = theme_dropdown_rects[0][0].y
                    drop_h = min(THEME_DROPDOWN_MAX_H, len(theme_names) * THEME_ITEM_H)
                    vis_top = ty - theme_dropdown_scroll
                    if (tx <= pos[0] <= tx + 180 and vis_top <= pos[1] <= vis_top + drop_h):
                        item_idx = (pos[1] - vis_top + theme_dropdown_scroll) // THEME_ITEM_H
                        if 0 <= item_idx < len(theme_names):
                            name = theme_names[item_idx]
                            resources.CURRENT_THEME = name
                            current_theme_name = name
                            save_cfg()
                            theme_dropdown_rects = None
                    else:
                        theme_dropdown_rects = None
                    continue
                # Settings bar clicks
                sx, sy, sw, sh = layouts["settings"]
                settings_rects_cache = get_settings_bar_rects(sx, sy, sw, sh)
                if settings_rects_cache["theme"].collidepoint(pos):
                    theme_dropdown_rects = open_theme_dropdown(settings_rects_cache["theme"])
                    continue
                for opt, r in settings_rects_cache["mode"].items():
                    if r.collidepoint(pos):
                        current_mode = opt
                        engine.mode = opt
                        save_cfg()
                        restart_game()
                        break
                for opt, r in settings_rects_cache["layout"].items():
                    if r.collidepoint(pos):
                        current_layout = opt
                        engine.layout = opt
                        save_cfg()
                        restart_game()
                        break
                for d, r in settings_rects_cache["duration"].items():
                    if r.collidepoint(pos):
                        current_duration = d
                        engine.test_duration = d
                        save_cfg()
                        restart_game()
                        break
                for w, r in settings_rects_cache["words"].items():
                    if r.collidepoint(pos):
                        current_word_count = w
                        engine.target_word_count = w
                        save_cfg()
                        restart_game()
                        break
                for f, r in settings_rects_cache["font"].items():
                    if r.collidepoint(pos):
                        current_font_size = f
                        save_cfg()
                        break
                if settings_rects_cache["sound"].collidepoint(pos):
                    sound_on_error = not sound_on_error
                    save_cfg()
                if settings_rects_cache["reduced"].collidepoint(pos):
                    reduced_motion = not reduced_motion
                    save_cfg()
                    if reduced_motion:
                        caret_visible = True

        # Game tick (timer)
        if not show_overlay and engine.is_running:
            elapsed = engine.get_time_elapsed()
            if engine.mode == "time":
                remaining = engine.test_duration - int(elapsed)
                if remaining <= 0:
                    finish_game()
        if now - last_tick >= 100:
            last_tick = now
        # Blinking caret (unless reduced motion or overlay)
        if not show_overlay and not reduced_motion and not engine.is_finished:
            if now - last_caret_toggle >= CARET_BLINK_MS:
                caret_visible = not caret_visible
                last_caret_toggle = now

        # Clear and draw
        screen.fill(theme["bg"])
        if not show_overlay:
            sx, sy, sw, sh = layouts["settings"]
            settings_rects_cache = draw_settings_bar(screen, theme, sx, sy, sw, sh)
            hx, hy, hw, hh = layouts["hud"]
            if engine.mode == "time":
                remaining = max(0, engine.test_duration - int(engine.get_time_elapsed())) if engine.is_running else engine.test_duration
                time_val = remaining
            else:
                time_val = int(engine.get_time_elapsed()) if engine.is_running else 0
            draw_hud(screen, theme, hx, hy, hw, hh, time_val, engine.wpm, engine.accuracy)
            dx, dy, dw, dh = layouts["display"]
            draw_display(screen, theme, dx, dy, dw, dh, engine.target_text, engine.user_input, caret_visible=caret_visible)
            kx, ky, kw, kh = layouts["keyboard"]
            highlight_char = None
            highlight_correct = True
            if key_highlight:
                hchar, hcorrect, htime = key_highlight
                if now - htime < HIGHLIGHT_MS:
                    highlight_char = hchar
                    highlight_correct = hcorrect
                else:
                    key_highlight = None
            draw_keyboard(screen, theme, kx, ky, kw, kh, current_layout, highlight_char, highlight_correct)
            if theme_dropdown_rects:
                tx, ty = theme_dropdown_rects[0][0].x, theme_dropdown_rects[0][0].y
                drop_h = min(THEME_DROPDOWN_MAX_H, len(theme_names) * THEME_ITEM_H)
                clip_rect = pygame.Rect(tx, ty, 180, drop_h)
                screen.set_clip(clip_rect)
                for i, (r, name) in enumerate(theme_dropdown_rects):
                    draw_r = pygame.Rect(r.x, r.y - theme_dropdown_scroll, r.w, r.h)
                    if draw_r.bottom <= ty or draw_r.top >= ty + drop_h:
                        continue
                    pygame.draw.rect(screen, theme["main"], draw_r, 1)
                    pygame.draw.rect(screen, theme["bg"], draw_r.inflate(-2, -2))
                    t = font_ui.render(name[:20], True, theme["main"])
                    screen.blit(t, (draw_r.x + 4, draw_r.centery - t.get_height() // 2))
                screen.set_clip(None)
        else:
            draw_overlay(screen, theme, overlay_wpm, overlay_acc, overlay_missed)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
