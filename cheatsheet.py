#!/usr/bin/env python3
"""
Zed Cheat Sheet — PDF Generator

Generates a clean, organized PDF cheat sheet with all essential Zed shortcuts.
Displays both Windows (Ctrl) and macOS (Cmd) variants side by side.

Usage:


    uv run cheatsheet.py              # Generate cheatsheet.pdf
    uv run cheatsheet.py --open       # Generate and open
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fpdf import FPDF

# ─── Shortcuts Data ───────────────────────────────────────────────────────────
# Format: (description, windows_shortcut, mac_shortcut)
# Shortcuts marked with * are custom (from keymap.json)

SHORTCUTS: dict[str, list[tuple[str, str, str]]] = {
    "General": [
        ("Command palette", "Ctrl+Shift+P", "Cmd+Shift+P"),
        ("Settings", "Ctrl+,", "Cmd+,"),
        ("Keymap file", "Ctrl+K  Ctrl+S", "Cmd+K  Cmd+S"),
        ("Toggle left dock", "Ctrl+B", "Cmd+B"),
        ("Toggle bottom dock", "Ctrl+J", "Cmd+J"),
        ("Toggle right dock", "Ctrl+Alt+B", "Cmd+Alt+B"),
        ("Quick open file", "Ctrl+P", "Cmd+P"),
        ("Reopen closed tab", "Ctrl+Shift+T", "Cmd+Shift+T"),
        ("Save all", "Ctrl+Alt+S", "Cmd+Alt+S"),
    ],
    "Navigation": [
        ("Go to line", "Ctrl+G", "Cmd+G"),
        ("Go to symbol (file)", "Ctrl+Shift+O", "Cmd+Shift+O"),
        ("Go to symbol (project)", "Ctrl+T", "Cmd+T"),
        ("Go to definition", "F12", "F12"),
        ("Definition (split)", "Alt+F12", "Alt+F12"),
        ("Go to implementation", "Ctrl+F12", "Ctrl+F12"),
        ("All references *", "Shift+F12", "Shift+F12"),
        ("Go to type definition *", "Ctrl+Shift+F12", "Cmd+F12"),
        ("Go to declaration *", "Alt+Ctrl+F12", "Alt+Ctrl+F12"),
        ("Open file from results", "Alt+Enter", "Alt+Enter"),
        ("Multibuffer: excerpt précédent *", "Ctrl+Up", "Cmd+Up"),
        ("Multibuffer: excerpt suivant *", "Ctrl+Down", "Cmd+Down"),
        ("Go back", "Alt+Left", "Ctrl+-"),
        ("Go forward", "Alt+Right", "Ctrl+Shift+-"),
        ("Go to bracket *", "Ctrl+Shift+>", "Cmd+Shift+>"),
        ("Switch tab left", "Ctrl+PageUp", "Cmd+Alt+Left"),
        ("Switch tab right", "Ctrl+PageDown", "Cmd+Alt+Right"),
        ("File explorer", "Ctrl+Shift+E", "Cmd+Shift+E"),
        ("Outline panel", "Ctrl+Shift+O", "Cmd+Shift+O"),
    ],
    "Editing": [
        ("Duplicate line", "Ctrl+Shift+D", "Cmd+Shift+D"),
        ("Move line up", "Alt+Up", "Alt+Up"),
        ("Move line down", "Alt+Down", "Alt+Down"),
        ("Delete line", "Ctrl+Shift+K", "Cmd+Shift+K"),
        ("Toggle comment", "Ctrl+/", "Cmd+/"),
    ],
    "Selection": [
        ("Select line", "Ctrl+L", "Cmd+L"),
        ("Expand selection", "Ctrl+Shift+Right", "Cmd+Shift+Right"),
        ("Shrink selection", "Ctrl+Shift+Left", "Cmd+Shift+Left"),
        ("Add cursor above", "Ctrl+Alt+Up", "Cmd+Alt+Up"),
        ("Add cursor below", "Ctrl+Alt+Down", "Cmd+Alt+Down"),
        ("Select next occurrence", "Ctrl+D", "Cmd+D"),
        ("Select all occurrences", "Ctrl+Shift+L", "Cmd+Shift+L"),
        ("Add cursor at click", "Alt+Click", "Alt+Click"),
        ("Column select", "Shift+Alt+Drag", "Shift+Alt+Drag"),
    ],
    "Search & Replace": [
        ("Find in project", "Ctrl+Shift+F", "Cmd+Shift+F"),
        ("Next match", "F3 / Enter", "Cmd+G / Enter"),
        ("Previous match", "Shift+F3", "Cmd+Shift+G"),
        ("Toggle regex", "Alt+R", "Alt+R"),
        ("Toggle case", "Alt+C", "Alt+C"),
        ("Toggle whole word", "Alt+W", "Alt+W"),
    ],
    "Code Intelligence": [
        ("Trigger autocomplete", "Ctrl+Space", "Ctrl+Space"),
        ("Quick fix / Code action", "Ctrl+.", "Cmd+."),
        ("Rename symbol *", "Ctrl+Shift+R", "Cmd+Shift+R"),
        ("Show hover info", "Ctrl+K  Ctrl+I", "Cmd+K  Cmd+I"),
        ("Show diagnostics", "Ctrl+Shift+M", "Cmd+Shift+M"),
        ("Next diagnostic", "F8", "F8"),
        ("Previous diagnostic", "Shift+F8", "Shift+F8"),
    ],
    "Folding": [
        ("Toggle fold", "Ctrl+K  Ctrl+L", "Cmd+K  Cmd+L"),
        ("Fold all", "Ctrl+K  Ctrl+0", "Cmd+K  Cmd+0"),
        ("Unfold all", "Ctrl+K  Ctrl+J", "Cmd+K  Cmd+J"),
        ("Fold level 1", "Ctrl+K  Ctrl+1", "Cmd+K  Cmd+1"),
        ("Fold level 2", "Ctrl+K  Ctrl+2", "Cmd+K  Cmd+2"),
    ],
    "Terminal & Panels": [
        ("Focus terminal *", "Ctrl+Alt+T", "Cmd+Alt+T"),
        ("New terminal", "Ctrl+`", "Ctrl+`"),
        ("Toggle terminal panel", "Ctrl+`", "Ctrl+`"),
        ("Split terminal", "In tmux: Ctrl+A |", "In tmux: Ctrl+A |"),
        ("Close tmux pane", "In tmux: Ctrl+A x", "In tmux: Ctrl+A x"),
        ("Git panel", "Ctrl+Alt+G", "Cmd+Alt+G"),
        ("Diagnostics panel", "Ctrl+Shift+M", "Cmd+Shift+M"),
    ],
    "AI Agent": [
        ("Toggle agent panel", "Ctrl+Shift+;", "Cmd+Shift+;"),
        ("Inline assist", "Ctrl+Enter", "Cmd+Enter"),
    ],
    "Splits & Panes": [
        ("Focus pane left *", "Ctrl+Alt+Left", "Cmd+Alt+Left"),
        ("Focus pane right *", "Ctrl+Alt+Right", "Cmd+Alt+Right"),
        ("Focus pane up", "Ctrl+K  Ctrl+Up", "Cmd+K  Cmd+Up"),
        ("Focus pane down", "Ctrl+K  Ctrl+Down", "Cmd+K  Cmd+Down"),
    ],
}


# ─── Colors ───────────────────────────────────────────────────────────────────

# Category header colors (pastel palette)
CATEGORY_COLORS: dict[str, tuple[int, int, int]] = {
    "General": (66, 133, 244),  # Blue
    "Navigation": (52, 168, 83),  # Green
    "Editing": (234, 67, 53),  # Red
    "Selection": (251, 188, 4),  # Yellow
    "Search & Replace": (171, 71, 188),  # Purple
    "Code Intelligence": (0, 172, 193),  # Teal
    "Folding": (255, 112, 67),  # Orange
    "Terminal & Panels": (66, 133, 244),  # Blue
    "AI Agent": (171, 71, 188),  # Purple
    "Splits & Panes": (52, 168, 83),  # Green
}

BG_DARK = (30, 30, 30)
BG_CARD = (42, 42, 42)
TEXT_WHITE = (240, 240, 240)
TEXT_DIM = (160, 160, 160)
TEXT_KEY = (255, 255, 255)
KEY_BG = (60, 60, 60)
KEY_BORDER = (80, 80, 80)
CUSTOM_BADGE = (255, 193, 7)  # Gold for custom shortcuts


# ─── PDF Generator ────────────────────────────────────────────────────────────


class CheatSheetPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.col_count = 3
        self.margin = 6
        self.col_gap = 4
        self.usable_w = 297 - 2 * self.margin  # A4 landscape width
        self.col_w = (
            self.usable_w - (self.col_count - 1) * self.col_gap
        ) / self.col_count
        self.current_col = 0
        self.col_y = 0.0
        self.page_top = 0.0
        self.page_bottom = 210 - self.margin  # A4 landscape height

    def _col_x(self) -> float:
        return self.margin + self.current_col * (self.col_w + self.col_gap)

    def _next_col(self) -> None:
        self.current_col += 1
        if self.current_col >= self.col_count:
            self.current_col = 0
            self.add_page()
            self._draw_bg()
            self._draw_header()
        self.col_y = self.page_top

    def _space_left(self) -> float:
        return self.page_bottom - self.col_y

    def _draw_bg(self) -> None:
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, 297, 210, "F")

    def _draw_header(self) -> None:
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*TEXT_WHITE)
        self.set_xy(self.margin, self.margin)
        self.cell(self.usable_w * 0.5, 6, "Zed Cheat Sheet", align="L")

        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*TEXT_DIM)
        self.set_xy(self.margin, self.margin + 6)
        self.cell(
            self.usable_w * 0.5,
            4,
            "Windows (Ctrl)  |  macOS (Cmd)  |  * = custom shortcut",
            align="L",
        )

        self.page_top = self.margin + 12
        self.col_y = self.page_top

    def _draw_category_header(self, name: str) -> None:
        color = CATEGORY_COLORS.get(name, (100, 100, 100))
        x = self._col_x()
        h = 5.5

        # Colored bar
        self.set_fill_color(*color)
        self.rect(x, self.col_y, self.col_w, h, "F")

        # Title text
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(255, 255, 255)
        self.set_xy(x + 3, self.col_y + 0.3)
        self.cell(self.col_w - 6, h - 0.6, name.upper(), align="L")

        self.col_y += h + 1

    def _draw_shortcut_row(
        self, desc: str, win: str, mac: str, is_custom: bool = False
    ) -> None:
        x = self._col_x()
        row_h = 4.8

        # Alternating row bg
        self.set_fill_color(*BG_CARD)
        self.rect(x, self.col_y, self.col_w, row_h, "F")

        # Description
        self.set_font("Helvetica", "", 6.5)
        self.set_text_color(*TEXT_WHITE)
        desc_w = self.col_w * 0.38
        self.set_xy(x + 2, self.col_y + 0.2)

        if is_custom:
            # Custom badge
            self.set_font("Helvetica", "B", 5)
            self.set_text_color(*CUSTOM_BADGE)
            self.cell(2.5, row_h - 0.4, "*", align="L")
            self.set_font("Helvetica", "", 6.5)
            self.set_text_color(*TEXT_WHITE)
            self.cell(desc_w - 2.5, row_h - 0.4, desc, align="L")
        else:
            self.cell(desc_w, row_h - 0.4, desc, align="L")

        # Windows shortcut
        key_w = self.col_w * 0.31
        self.set_xy(x + desc_w + 2, self.col_y + 0.2)
        self._draw_key_badge(win, key_w)

        # Mac shortcut
        self.set_xy(x + desc_w + key_w + 3, self.col_y + 0.2)
        self._draw_key_badge(mac, key_w)

        self.col_y += row_h + 0.3

    def _draw_key_badge(self, text: str, max_w: float) -> None:
        """Draw a keyboard-style badge for the shortcut."""
        self.set_font("Courier", "B", 5.5)
        self.set_text_color(*TEXT_KEY)
        self.set_fill_color(*KEY_BG)
        self.set_draw_color(*KEY_BORDER)

        # Calculate text width for the badge
        tw = self.get_string_width(text) + 3
        tw = min(tw, max_w - 1)
        bh = 3.6

        bx = self.get_x()
        by = self.get_y() + 0.3

        # Rounded rect badge
        self.rect(bx, by, tw, bh, "FD")
        self.set_xy(bx + 1.5, by + 0.1)
        self.cell(tw - 3, bh - 0.2, text, align="L")

    def _category_height(self, shortcuts: list) -> float:
        """Estimate height needed for a category."""
        return 5.5 + 1 + len(shortcuts) * 5.1 + 2

    def generate(self) -> None:
        self.add_page()
        self._draw_bg()
        self._draw_header()

        for category, shortcuts in SHORTCUTS.items():
            needed = self._category_height(shortcuts)

            if self._space_left() < needed:
                self._next_col()

            # If still doesn't fit after column switch (very tall category),
            # just draw what we can
            self._draw_category_header(category)

            for desc, win_key, mac_key in shortcuts:
                is_custom = desc.endswith("*")
                clean_desc = desc.rstrip(" *")

                if self._space_left() < 7:
                    self._next_col()

                self._draw_shortcut_row(clean_desc, win_key, mac_key, is_custom)

            self.col_y += 3  # spacing between categories


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    output = Path(__file__).resolve().parent / "zed-cheatsheet.pdf"

    pdf = CheatSheetPDF()
    pdf.generate()
    pdf.output(str(output))

    print(f"  Generated: {output}")
    print(f"  Size: {output.stat().st_size / 1024:.0f} KB")

    if "--open" in sys.argv:
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(output)])
            elif sys.platform == "win32":
                subprocess.run(["start", str(output)], shell=True)
            else:
                subprocess.run(["xdg-open", str(output)])
        except FileNotFoundError:
            print("  Could not open PDF automatically.")


if __name__ == "__main__":
    main()
