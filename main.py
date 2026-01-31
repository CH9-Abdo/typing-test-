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
CONTENT_W = 850  # Slightly wider for better spacing
HUD_TIMER_SIZE = 48
KEY_SIZE = 46
KEY_SPACE_W = 340
KEY_SPACE_H = 42
KEY_GAP = 6
KEYBOARD_ROWS_QWERTY = ["qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./"]
KEYBOARD_ROWS_DVORAK = ["',.pyfgcrl/=", "aoeuidhtns-", ";qjkxbmwvz"]
HIGHLIGHT_MS = 150
THEME_DROPDOWN_MAX_H = 300
THEME_ITEM_H = 32
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
    # Allow resizing
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    # Load config and apply
    cfg = config.load_config()
    resources.CURRENT_THEME = cfg.get("theme", "monkeytype")
    font_size_px = config.get_font_size_px(cfg.get("font_size", "medium"))
    resources.FONT_SIZE = font_size_px

    # --- Fonts ---
    # Increased UI font sizes for better readability
    roboto_regular = _font_path("Roboto-Regular.ttf")
    roboto_bold = _font_path("Roboto-Bold.ttf")
    
    font_mono = _load_font(roboto_regular, font_size_px) or pygame.font.SysFont("consolas", font_size_px)
    font_mono_large = _load_font(roboto_regular, HUD_TIMER_SIZE) or pygame.font.SysFont("consolas", HUD_TIMER_SIZE)
    
    # UI Fonts
    font_ui = _load_font(roboto_regular, 16) or pygame.font.SysFont("segoeui", 16)
    font_ui_bold = _load_font(roboto_bold, 14) or pygame.font.SysFont("segoeui", 14, bold=True)
    font_ui_small = _load_font(roboto_bold, 12) or pygame.font.SysFont("segoeui", 12, bold=True)
    font_key = _load_font(roboto_bold, 14) or pygame.font.SysFont("consolas", 14, bold=True)

    # Game state
    engine = TypingEngine(
        mode=cfg.get("mode", "time"),
        duration=int(cfg.get("duration", 30)),
        word_count=int(cfg.get("word_count", 25))
    )
    engine.layout = cfg.get("layout", "qwerty")
    
    # Options
    mode_options = ["time", "word", "quote"]
    theme_names = list(resources.THEMES.keys())
    layout_options = ["qwerty", "dvorak"]
    duration_options = config.DURATION_OPTIONS
    word_count_options = config.WORD_COUNT_OPTIONS

    # Local state mirrors config for UI
    current_mode = cfg.get("mode", "time")
    current_theme_name = resources.CURRENT_THEME
    current_layout = cfg.get("layout", "qwerty")
    current_duration = engine.test_duration
    current_word_count = engine.target_word_count
    current_font_size = cfg.get("font_size", "medium")
    sound_on_error = cfg.get("sound_on_error", False)
    reduced_motion = cfg.get("reduced_motion", False)

    # UI State
    show_overlay = False
    show_history = False  # New history window state
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

    # --- Layout Calculations ---
    def content_rect():
        w, h = screen.get_size()
        x = max(0, (w - CONTENT_W) // 2)
        # Add some top padding
        return x, 40, CONTENT_W, h - 60

    def get_theme():
        return {k: hex_to_rgb(v) for k, v in resources.get_theme().items()}

    def layout_rects(cx, cy, cw):
        """Returns dict of section names -> (x, y, w, h) in content area."""
        y = cy
        # Increased settings height for cleaner 2-row layout
        settings_h = 110 
        settings_rect = (cx, y, cw, settings_h)
        y += settings_h + 30

        # HUD
        hud_h = 90
        hud_rect = (cx, y, cw, hud_h)
        y += hud_h + 20

        # Typing display
        display_h = 280
        display_rect = (cx, y, cw, display_h)
        y += display_h + 30

        # Keyboard
        keyboard_rect = (cx, y, cw, 240)
        return {
            "settings": settings_rect,
            "hud": hud_rect,
            "display": display_rect,
            "keyboard": keyboard_rect,
        }

    # --- Drawing Helpers ---
    def draw_button_bg(surface, rect, color, border_color=None, radius=6):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border_color:
            pygame.draw.rect(surface, border_color, rect, 1, border_radius=radius)

    def draw_text_centered(surface, text, font, color, center_pos):
        surf = font.render(text, True, color)
        surface.blit(surf, (center_pos[0] - surf.get_width() // 2, center_pos[1] - surf.get_height() // 2))

    # ---- Settings Bar ----
    def draw_settings_bar(surface, theme, cx, cy, cw, ch):
        # Background for settings area (optional, cleaner without full box)
        # pygame.draw.rect(surface, theme["bg"], (cx, cy, cw, ch))

        # --- Row 1: Game Mode & Specific Options ---
        y_row1 = cy
        x = cx
        
        # Mode Label
        lbl = font_ui_bold.render("Mode:", True, theme["main"])
        surface.blit(lbl, (x, y_row1 + 8))
        x += lbl.get_width() + 12

        mode_rects = {}
        for opt in mode_options:
            label = opt.title()
            w, h = font_ui.size(label)
            w += 24
            h += 16
            r = pygame.Rect(x, y_row1, w, h)
            mode_rects[opt] = r
            
            is_active = (opt == current_mode)
            bg_color = theme["caret"] if is_active else theme["bg"]
            text_color = theme["bg"] if is_active else theme["main"]
            border = None if is_active else theme["main"]
            
            draw_button_bg(surface, r, bg_color, border, radius=6)
            draw_text_centered(surface, label, font_ui_bold, text_color, r.center)
            x += w + 8
        
        # Separator
        x += 20
        pygame.draw.line(surface, theme["main"], (x, y_row1 + 5), (x, y_row1 + 25), 1)
        x += 20

        # Dynamic Options based on mode
        duration_rects = {}
        words_rects = {}
        
        if current_mode == "time":
            for d in duration_options:
                label = str(d)
                w, h = font_ui.size(label)
                w += 20
                h += 16
                r = pygame.Rect(x, y_row1, w, h)
                duration_rects[d] = r
                
                is_active = (d == current_duration)
                bg_color = theme["caret"] if is_active else theme["bg"]
                text_color = theme["bg"] if is_active else theme["main"]
                border = None if is_active else theme["main"]

                draw_button_bg(surface, r, bg_color, border, radius=6)
                draw_text_centered(surface, label, font_ui_bold, text_color, r.center)
                x += w + 6

        elif current_mode == "word":
            for w_count in word_count_options:
                label = str(w_count)
                w, h = font_ui.size(label)
                w += 20
                h += 16
                r = pygame.Rect(x, y_row1, w, h)
                words_rects[w_count] = r
                
                is_active = (w_count == current_word_count)
                bg_color = theme["caret"] if is_active else theme["bg"]
                text_color = theme["bg"] if is_active else theme["main"]
                border = None if is_active else theme["main"]

                draw_button_bg(surface, r, bg_color, border, radius=6)
                draw_text_centered(surface, label, font_ui_bold, text_color, r.center)
                x += w + 6
        
        elif current_mode == "quote":
            # Quote mode usually determines length automatically, but we can show a label
            lbl = font_ui.render("Random Quote", True, theme["main"])
            surface.blit(lbl, (x, y_row1 + 8))


        # --- Row 2: Global Settings (Theme, Font, etc) ---
        y_row2 = cy + 50
        x = cx

        # Theme Dropdown Button
        theme_lbl_w = font_ui.size(current_theme_name)[0] + 40
        theme_btn = pygame.Rect(x, y_row2, max(140, theme_lbl_w), 34)
        draw_button_bg(surface, theme_btn, theme["main"], radius=6)
        draw_text_centered(surface, current_theme_name, font_ui_bold, theme["bg"], theme_btn.center)
        x += theme_btn.width + 16

        # Layout
        layout_rects = {}
        for l_opt in layout_options:
            label = l_opt.upper()
            w, h = font_ui_small.size(label)
            w += 16
            h += 14
            r = pygame.Rect(x, y_row2, w, h)
            layout_rects[l_opt] = r
            
            is_active = (l_opt == current_layout)
            bg_color = theme["caret"] if is_active else theme["bg"]
            text_color = theme["bg"] if is_active else theme["main"]
            border = None if is_active else theme["main"]
            
            draw_button_bg(surface, r, bg_color, border, radius=6)
            draw_text_centered(surface, label, font_ui_small, text_color, r.center)
            x += w + 6
        
        x += 16 

        # Font Size
        font_rects = {}
        for f_opt in ["small", "medium", "large"]:
            label = f_opt[0].upper()
            w, h = 34, 34
            r = pygame.Rect(x, y_row2, w, h)
            font_rects[f_opt] = r
            
            is_active = (f_opt == current_font_size)
            bg_color = theme["caret"] if is_active else theme["bg"]
            text_color = theme["bg"] if is_active else theme["main"]
            border = None if is_active else theme["main"]
            
            draw_button_bg(surface, r, bg_color, border, radius=6)
            draw_text_centered(surface, label, font_ui_bold, text_color, r.center)
            x += w + 6

        x += 16

        # Toggles (Sound, Reduced Motion)
        sound_rect = pygame.Rect(x, y_row2, 40, 34)
        is_active = sound_on_error
        bg_color = theme["caret"] if is_active else theme["bg"]
        text_color = theme["bg"] if is_active else theme["main"]
        border = None if is_active else theme["main"]
        draw_button_bg(surface, sound_rect, bg_color, border, radius=6)
        # Simple icon or text for sound
        draw_text_centered(surface, "Snd", font_ui_small, text_color, sound_rect.center)
        x += 46

        reduced_rect = pygame.Rect(x, y_row2, 40, 34)
        is_active = reduced_motion
        bg_color = theme["caret"] if is_active else theme["bg"]
        text_color = theme["bg"] if is_active else theme["main"]
        border = None if is_active else theme["main"]
        draw_button_bg(surface, reduced_rect, bg_color, border, radius=6)
        draw_text_centered(surface, "Mot", font_ui_small, text_color, reduced_rect.center)
        
        # --- History Button (Right Aligned) ---
        hist_w = 100
        hist_rect = pygame.Rect(cx + cw - hist_w, y_row2, hist_w, 34)
        draw_button_bg(surface, hist_rect, theme["bg"], theme["caret"], radius=6)
        draw_text_centered(surface, "History", font_ui_bold, theme["caret"], hist_rect.center)

        return {
            "mode": mode_rects, "theme": theme_btn, "layout": layout_rects,
            "duration": duration_rects, "words": words_rects, "font": font_rects,
            "sound": sound_rect, "reduced": reduced_rect, "history": hist_rect
        }

    # Only used for hit testing logic without drawing, similar to draw_settings_bar logic
    def get_settings_bar_rects(cx, cy, cw, ch):
        y_row1 = cy
        x = cx
        x += font_ui_bold.size("Mode:")[0] + 12
        mode_rects = {}
        for opt in mode_options:
            w = font_ui.size(opt.title())[0] + 24
            mode_rects[opt] = pygame.Rect(x, y_row1, w, 16 + font_ui.get_height())
            x += w + 8
        x += 40 
        duration_rects = {}
        words_rects = {}
        if current_mode == "time":
            for d in duration_options:
                w = font_ui.size(str(d))[0] + 20
                duration_rects[d] = pygame.Rect(x, y_row1, w, 16 + font_ui.get_height())
                x += w + 6
        elif current_mode == "word":
            for w_count in word_count_options:
                w = font_ui.size(str(w_count))[0] + 20
                words_rects[w_count] = pygame.Rect(x, y_row1, w, 16 + font_ui.get_height())
                x += w + 6

        y_row2 = cy + 50
        x = cx
        theme_lbl_w = font_ui.size(current_theme_name)[0] + 40
        theme_btn = pygame.Rect(x, y_row2, max(140, theme_lbl_w), 34)
        x += theme_btn.width + 16
        layout_rects = {}
        for l_opt in layout_options:
            w = font_ui_small.size(l_opt.upper())[0] + 16
            layout_rects[l_opt] = pygame.Rect(x, y_row2, w, 14 + font_ui_small.get_height())
            x += w + 6
        x += 16
        font_rects = {}
        for f_opt in ["small", "medium", "large"]:
            font_rects[f_opt] = pygame.Rect(x, y_row2, 34, 34)
            x += 40
        x += 16
        sound_rect = pygame.Rect(x, y_row2, 40, 34)
        x += 46
        reduced_rect = pygame.Rect(x, y_row2, 40, 34)
        
        hist_w = 100
        hist_rect = pygame.Rect(cx + cw - hist_w, y_row2, hist_w, 34)

        return {
            "mode": mode_rects, "theme": theme_btn, "layout": layout_rects,
            "duration": duration_rects, "words": words_rects, "font": font_rects,
            "sound": sound_rect, "reduced": reduced_rect, "history": hist_rect
        }

    # ---- Draw HUD ----
    def draw_hud(surface, theme, cx, cy, cw, ch, time_val, wpm, acc):
        # Clean hud, just text, no box
        time_surf = font_mono_large.render(str(time_val), True, theme["caret"])
        surface.blit(time_surf, (cx + 20, cy + 10))
        
        # Stats aligned right
        stats_text = f"WPM: {wpm}   ACC: {acc}%"
        stats_surf = font_ui.render(stats_text, True, theme["main"])
        surface.blit(stats_surf, (cx + cw - stats_surf.get_width() - 20, cy + 30))

    # ---- Wrap text ----
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

    # ---- Draw Display ----
    def draw_display(surface, theme, cx, cy, cw, ch, target_text, user_input, caret_visible=True):
        rect = pygame.Rect(cx, cy, cw, ch)
        pygame.draw.rect(surface, theme["bg"], rect) # Just fill bg
        
        padding = 10
        inner_w = cw - 2 * padding
        inner_x, inner_y = cx + padding, cy + padding

        target_lines = wrap_text(target_text, font_mono, inner_w)
        line_height = font_mono.get_height() + 8 # More breathing room
        cursor_idx = len(user_input)

        py = inner_y
        idx = 0
        
        # Limit rows to fit
        max_rows = ch // line_height
        
        for row_idx, tline in enumerate(target_lines):
            if row_idx >= max_rows: break
            
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
            
            # Cursor at end of line
            if caret_visible and idx + len(tline) == cursor_idx:
                cw_char = font_mono.size(" ")[0]
                pygame.draw.rect(surface, theme["caret"], (px, py, cw_char, line_height))
                
            idx += len(tline)
            py += line_height

    # ---- Keyboard ----
    def build_key_rects(cx, cy, cw, layout_name):
        rows = KEYBOARD_ROWS_QWERTY if layout_name == "qwerty" else KEYBOARD_ROWS_DVORAK
        key_w = KEY_SIZE
        key_gap = KEY_GAP
        key_rects = {}
        max_row_len = max(len(r) for r in rows)
        block_width = max_row_len * (key_w + key_gap) - key_gap
        block_left = cx + (cw - block_width) // 2
        row_y = cy + 10
        for row_str in rows:
            row_width = len(row_str) * (key_w + key_gap) - key_gap
            start_x = block_left + (block_width - row_width) // 2
            x = start_x
            for ch in row_str:
                key_rects[ch] = pygame.Rect(x, row_y, key_w, key_w)
                x += key_w + key_gap
            row_y += key_w + key_gap
        space_x = block_left + (block_width - KEY_SPACE_W) // 2
        key_rects[" "] = pygame.Rect(space_x, row_y, KEY_SPACE_W, KEY_SPACE_H)
        return key_rects

    def draw_keyboard(surface, theme, cx, cy, cw, ch, layout_name, highlight_char=None, highlight_correct=True):
        key_rects = build_key_rects(cx, cy, cw, layout_name)
        for ch, r in key_rects.items():
            if ch == highlight_char:
                color = theme["correct"] if highlight_correct else theme["error"]
                bg_col = color
                txt_col = theme["bg"]
            else:
                bg_col = theme["main"]
                txt_col = theme["bg"]
                # Dim the keyboard a bit if not active
                # But simple is fine
            
            pygame.draw.rect(surface, bg_col, r, border_radius=4)
            label = "SPACE" if ch == " " else ch.upper()
            txt = font_key.render(label, True, txt_col)
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
        return key_rects

    # ---- Overlays ----
    def draw_overlay(surface, theme, wpm, acc, missed_str):
        # Semi-transparent bg
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        sw, sh = surface.get_size()
        ow, oh = 600, 450
        ox, oy = (sw - ow) // 2, (sh - oh) // 2
        rect = pygame.Rect(ox, oy, ow, oh)
        
        pygame.draw.rect(surface, theme["bg"], rect, border_radius=12)
        pygame.draw.rect(surface, theme["main"], rect, 2, border_radius=12)

        # Content
        draw_text_centered(surface, "Result", font_ui_bold, theme["caret"], (rect.centerx, oy + 40))
        
        # WPM / ACC Big
        y = oy + 100
        wpm_str = f"{wpm} WPM"
        acc_str = f"{acc}% ACC"
        
        wpm_surf = font_mono_large.render(wpm_str, True, theme["main"])
        acc_surf = font_mono_large.render(acc_str, True, theme["main"])
        
        surface.blit(wpm_surf, (rect.centerx - wpm_surf.get_width() - 20, y))
        surface.blit(acc_surf, (rect.centerx + 20, y))

        # Missed
        y += 80
        if missed_str:
            lines = missed_str.split("\n")
            for line in lines[:5]: # Show max 5 lines
                t = font_ui.render(line, True, theme["error"])
                surface.blit(t, (rect.centerx - t.get_width() // 2, y))
                y += 24
        else:
            t = font_ui.render("Perfect!", True, theme["correct"])
            surface.blit(t, (rect.centerx - t.get_width() // 2, y))

        # Hint
        hint = font_ui.render("Press TAB to restart", True, theme["main"])
        surface.blit(hint, (rect.centerx - hint.get_width() // 2, rect.bottom - 40))

    def draw_history_overlay(surface, theme):
        # Semi-transparent bg
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        sw, sh = surface.get_size()
        ow, oh = 800, 650
        ox, oy = (sw - ow) // 2, (sh - oh) // 2
        rect = pygame.Rect(ox, oy, ow, oh)
        
        pygame.draw.rect(surface, theme["bg"], rect, border_radius=12)
        pygame.draw.rect(surface, theme["main"], rect, 2, border_radius=12)

        draw_text_centered(surface, "Typing History", font_ui_bold, theme["caret"], (rect.centerx, oy + 30))
        
        # --- Table (Top Half) ---
        headers = ["Date", "Mode", "WPM", "Accuracy", "Missed"]
        col_x = [ox + 40, ox + 220, ox + 350, ox + 450, ox + 580]
        header_y = oy + 60
        
        for i, h in enumerate(headers):
            txt = font_ui_bold.render(h, True, theme["main"])
            surface.blit(txt, (col_x[i], header_y))
        
        pygame.draw.line(surface, theme["main"], (ox + 20, header_y + 25), (ox + ow - 20, header_y + 25), 1)

        history = HistoryManager.load_history()
        # Show last 10 for table to save space for graph
        recent_count = 10
        recent = list(reversed(history))[:recent_count]
        
        row_y = header_y + 35
        for entry in recent:
            date_str = entry.get("timestamp", "")[5:-3]
            mode_str = entry.get("mode", "?").title()
            wpm_val = str(entry.get("wpm", 0))
            acc_val = f"{entry.get('accuracy', 0)}%"
            miss_val = str(entry.get("missed", 0))

            vals = [date_str, mode_str, wpm_val, acc_val, miss_val]
            for i, val in enumerate(vals):
                c = theme["main"]
                if i == 2: c = theme["caret"]
                txt = font_ui.render(val, True, c)
                surface.blit(txt, (col_x[i], row_y))
            row_y += 28

        # --- Graph (Bottom Half) ---
        # Graph area
        graph_rect = pygame.Rect(ox + 60, row_y + 20, ow - 120, oh - (row_y - oy) - 60)
        # pygame.draw.rect(surface, theme["main"], graph_rect, 1) # Debug border
        
        # Data for graph (last 50)
        graph_data = history[-50:]
        if len(graph_data) > 1:
            wpm_values = [d.get("wpm", 0) for d in graph_data]
            max_wpm = max(wpm_values)
            min_wpm = min(wpm_values)
            if max_wpm == min_wpm:
                max_wpm += 10
                min_wpm = max(0, min_wpm - 10)
            
            # Draw axes labels
            max_lbl = font_ui_small.render(str(max_wpm), True, theme["main"])
            min_lbl = font_ui_small.render(str(min_wpm), True, theme["main"])
            surface.blit(max_lbl, (graph_rect.left - max_lbl.get_width() - 8, graph_rect.top))
            surface.blit(min_lbl, (graph_rect.left - min_lbl.get_width() - 8, graph_rect.bottom - min_lbl.get_height()))

            # Draw lines
            points = []
            count = len(wpm_values)
            for i, wpm in enumerate(wpm_values):
                # x: spread evenly
                px = graph_rect.left + (i / (count - 1)) * graph_rect.width
                # y: scale based on min/max
                # (val - min) / (max - min) --> 0..1
                # y = bottom - normalized * height
                norm = (wpm - min_wpm) / (max_wpm - min_wpm)
                py = graph_rect.bottom - norm * graph_rect.height
                points.append((px, py))
            
            if len(points) >= 2:
                pygame.draw.lines(surface, theme["caret"], False, points, 2)
                for p in points:
                    pygame.draw.circle(surface, theme["caret"], (int(p[0]), int(p[1])), 3)
            
            # Title for graph
            g_title = font_ui_small.render("WPM Progress (Last 50)", True, theme["main"])
            surface.blit(g_title, (graph_rect.centerx - g_title.get_width() // 2, graph_rect.bottom + 10))
        
        elif len(graph_data) == 1:
             msg = font_ui.render("Not enough data for graph", True, theme["main"])
             surface.blit(msg, (graph_rect.centerx - msg.get_width()//2, graph_rect.centery))
        else:
             msg = font_ui.render("No history data", True, theme["main"])
             surface.blit(msg, (graph_rect.centerx - msg.get_width()//2, graph_rect.centery))

        # Close hint
        close = font_ui.render("Press ESC or Click History button to Close", True, theme["main"])
        surface.blit(close, (rect.centerx - close.get_width() // 2, rect.bottom - 40))


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

    def finish_game():
        nonlocal show_overlay, overlay_wpm, overlay_acc, overlay_missed
        engine.stop()
        overlay_wpm = engine.wpm
        overlay_acc = engine.accuracy
        if not engine.missed_data:
            overlay_missed = ""
        else:
            misses = {}
            for exp, typed in engine.missed_data:
                key = f"'{exp}'" if exp != " " else "[Space]"
                misses[key] = misses.get(key, 0) + 1
            overlay_missed = "Characters missed:\n"
            sorted_misses = sorted(misses.items(), key=lambda item: item[1], reverse=True)
            for char, count in sorted_misses[:5]:
                overlay_missed += f"{char}: {count}\n"
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
                save_cfg()
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if show_history:
                    if event.key == pygame.K_ESCAPE:
                        show_history = False
                    continue

                if event.key == pygame.K_TAB:
                    restart_game()
                    continue
                
                if show_overlay:
                    if event.key == pygame.K_ESCAPE:
                        restart_game()
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
                
                # If history open, clicking anywhere (or specific button) could close it? 
                # Let's enforce clicking the History button to toggle back or Esc.
                if show_history:
                     # Check if clicked outside history box? For now, just check History button below or simple toggle
                     # We need rects to check the history button again.
                     sx, sy, sw, sh = layouts["settings"]
                     settings_rects_cache = get_settings_bar_rects(sx, sy, sw, sh)
                     if settings_rects_cache["history"].collidepoint(pos):
                         show_history = False
                     else:
                         # Click outside could close?
                         # Let's stick to toggle button
                         pass
                     continue

                # Theme dropdown
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

                # Settings clicks
                sx, sy, sw, sh = layouts["settings"]
                settings_rects_cache = get_settings_bar_rects(sx, sy, sw, sh)
                
                if settings_rects_cache["history"].collidepoint(pos):
                    show_history = not show_history
                    continue

                if show_overlay:
                    continue # Block settings interaction when result overlay is up (except history?)
                
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
                        # Need to reload fonts
                        font_size_px = config.get_font_size_px(f)
                        resources.FONT_SIZE = font_size_px
                        font_mono = _load_font(roboto_regular, font_size_px) or pygame.font.SysFont("consolas", font_size_px)
                        break
                if settings_rects_cache["sound"].collidepoint(pos):
                    sound_on_error = not sound_on_error
                    save_cfg()
                if settings_rects_cache["reduced"].collidepoint(pos):
                    reduced_motion = not reduced_motion
                    save_cfg()
                    if reduced_motion:
                        caret_visible = True

        # --- Update ---
        if not show_overlay and not show_history and engine.is_running:
            elapsed = engine.get_time_elapsed()
            if engine.mode == "time":
                remaining = engine.test_duration - int(elapsed)
                if remaining <= 0:
                    finish_game()
        
        if now - last_tick >= 100:
            last_tick = now
        
        if not show_overlay and not show_history and not reduced_motion and not engine.is_finished:
            if now - last_caret_toggle >= CARET_BLINK_MS:
                caret_visible = not caret_visible
                last_caret_toggle = now

        # --- Draw ---
        screen.fill(theme["bg"])
        
        # Always draw UI base
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
        if key_highlight and not show_history:
            hchar, hcorrect, htime = key_highlight
            if now - htime < HIGHLIGHT_MS:
                highlight_char = hchar
                highlight_correct = hcorrect
            else:
                key_highlight = None
        draw_keyboard(screen, theme, kx, ky, kw, kh, current_layout, highlight_char, highlight_correct)

        # Dropdown on top of main UI, but below overlays
        if theme_dropdown_rects and not show_history and not show_overlay:
            tx, ty = theme_dropdown_rects[0][0].x, theme_dropdown_rects[0][0].y
            drop_h = min(THEME_DROPDOWN_MAX_H, len(theme_names) * THEME_ITEM_H)
            clip_rect = pygame.Rect(tx, ty, 180, drop_h)
            screen.set_clip(clip_rect)
            for i, (r, name) in enumerate(theme_dropdown_rects):
                draw_r = pygame.Rect(r.x, r.y - theme_dropdown_scroll, r.w, r.h)
                if draw_r.bottom <= ty or draw_r.top >= ty + drop_h:
                    continue
                pygame.draw.rect(screen, theme["main"], draw_r, border_radius=0)
                # Separator
                pygame.draw.line(screen, theme["bg"], draw_r.bottomleft, draw_r.bottomright)
                
                t = font_ui.render(name[:20], True, theme["bg"])
                screen.blit(t, (draw_r.x + 8, draw_r.centery - t.get_height() // 2))
            screen.set_clip(None)

        if show_overlay:
            draw_overlay(screen, theme, overlay_wpm, overlay_acc, overlay_missed)
        
        if show_history:
            draw_history_overlay(screen, theme)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()