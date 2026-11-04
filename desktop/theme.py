"""
Colours, stylesheet and elemental type data for the scanner look.

main.py uses this for the splash before torch is imported, so nothing here may
import desktop.worker or lib.
"""

import ctypes
import json
import os
import sys
from pathlib import Path

ELEMENTAL_TYPES_PATH = Path(__file__).with_name("elemental_types.json")
REDUCED_MOTION_ENV = "POKE_REDUCED_MOTION"
SPI_GETCLIENTAREAANIMATION = 0x1042

DESK = "#17171c"
BODY_RED = "#c62a35"
BODY_RED_DARK = "#8e1a24"
BODY_RED_LIGHT = "#d33a45"
SHELL = "#f4f1ec"
SHELL_EDGE = "#d9d3c9"
INK = "#1d1d24"
INK_MUTED = "#55545e"
WHITE = "#ffffff"
SCREEN = "#0d1820"
SCREEN_EDGE = "#26343f"
SCREEN_TEXT = "#cfefff"
SCAN_GLOW = "#39e0ff"
LCD = "#13201a"
LCD_TEXT = "#b8f5c8"
ERROR_BANNER = "#5c0f17"
ERROR_TEXT = "#ffd9dc"
FOCUS_ON_DARK = "#ffd23f"
FOCUS_ON_LIGHT = "#1e4fd8"
BAR_GROOVE = "#e2ddd4"
BAR_FILL = "#1e8fb0"
LED_READY = "#39d36b"
LED_BUSY = "#ffb020"
LED_ERROR = "#ff4757"
LED_OFF = "#5a1118"

BADGE_DARK_TEXT = "#111418"
TYPE_COLOURS = {
    "Normal": "#c9c3a8",
    "Fire": "#e8622a",
    "Water": "#2f6ad0",
    "Electric": "#f5c518",
    "Grass": "#4fae45",
    "Ice": "#8fd9d4",
    "Fighting": "#b2332b",
    "Poison": "#9446a8",
    "Ground": "#d6b25e",
    "Flying": "#9db3f0",
    "Psychic": "#f0568a",
    "Bug": "#9db52a",
    "Rock": "#b39a4b",
    "Ghost": "#5a4a8e",
    "Dragon": "#5b3fd6",
    "Steel": "#aeb4c2",
    "Fairy": "#f2a6d6",
}


def relative_luminance(colour):
    """WCAG 2 relative luminance of a #rrggbb colour."""
    channels = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    red, green, blue = linear
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first, second):
    lighter, darker = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def badge_text_colour(background):
    return max((BADGE_DARK_TEXT, WHITE), key=lambda c: contrast_ratio(c, background))


def load_elemental_types(path=ELEMENTAL_TYPES_PATH):
    """Map each class name to its elemental types, or {} if the file is unusable."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        name: [kind for kind in kinds if kind in TYPE_COLOURS]
        for name, kinds in data.items()
        if isinstance(kinds, list)
    }


def prefers_reduced_motion():
    """True if POKE_REDUCED_MOTION is set, or Windows has animations turned off."""
    if os.environ.get(REDUCED_MOTION_ENV, "") not in ("", "0"):
        return True
    if sys.platform != "win32":
        return False
    enabled = ctypes.c_int(1)
    ok = ctypes.windll.user32.SystemParametersInfoW(
        SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(enabled), 0
    )
    return bool(ok) and not enabled.value


STYLESHEET = f"""
QMainWindow, QMenuBar {{
    background: {DESK};
    color: {WHITE};
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border: 2px solid transparent;
    border-radius: 4px;
}}
QMenuBar::item:selected, QMenuBar::item:pressed {{
    background: {BODY_RED_DARK};
    border-color: {FOCUS_ON_DARK};
}}
QMenu {{
    background: {SHELL};
    color: {INK};
    border: 1px solid {SHELL_EDGE};
}}
QMenu::item {{
    padding: 5px 18px;
}}
QMenu::item:selected {{
    background: {FOCUS_ON_LIGHT};
    color: {WHITE};
}}
QWidget#body QLabel#wordmark {{
    color: {WHITE};
    font-size: 17pt;
    font-weight: 800;
    letter-spacing: 2px;
}}
QWidget#body QLabel#tagline {{
    color: {WHITE};
    font-size: 9pt;
    font-weight: 600;
    letter-spacing: 1px;
}}
QWidget#body QFrame#bezel, QWidget#body QFrame#resultCard {{
    background: {SHELL};
    border: 1px solid {SHELL_EDGE};
    border-radius: 18px;
}}
QWidget#body QLabel {{
    background: transparent;
    color: {INK};
}}
QWidget#body QLabel#screen {{
    background: {SCREEN};
    color: {SCREEN_TEXT};
    border: 3px solid {SCREEN_EDGE};
    border-radius: 12px;
    padding: 14px;
    font-size: 11pt;
}}
QWidget#body QLabel[readable="true"] {{
    border: 2px solid transparent;
    border-radius: 5px;
    padding: 1px 6px 1px 3px;
}}
QWidget#body QLabel[readable="true"]:focus {{
    border-color: {FOCUS_ON_LIGHT};
}}
QWidget#body QLabel#cardCaption, QWidget#body QLabel#othersCaption {{
    color: {INK_MUTED};
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 2px;
    padding-left: 5px;
}}
QWidget#body QLabel#topName {{
    color: {INK};
    font-size: 21pt;
    font-weight: 800;
}}
QWidget#body QLabel#topConfidence {{
    color: {INK};
    font-size: 15pt;
    font-weight: 700;
}}
QWidget#body QLabel#cardPlaceholder {{
    color: {INK_MUTED};
    font-size: 10pt;
    padding-left: 5px;
}}
QWidget#body QLabel#typeBadge {{
    font-size: 8pt;
    font-weight: 800;
    letter-spacing: 1px;
}}
QWidget#body QLabel#statusLabel {{
    background: {LCD};
    color: {LCD_TEXT};
    border: 2px solid {LCD};
    border-radius: 8px;
    padding: 6px 10px;
    font-family: "Consolas", "DejaVu Sans Mono", monospace;
    font-size: 9pt;
}}
QWidget#body QLabel#statusLabel:focus {{
    border-color: {FOCUS_ON_DARK};
}}
QWidget#body QPushButton#openButton {{
    background: {INK};
    color: {WHITE};
    border: 3px solid {INK};
    border-radius: 16px;
    padding: 6px 18px;
    font-weight: 700;
}}
QWidget#body QPushButton#openButton:hover {{
    background: #34343f;
    border-color: #34343f;
}}
QWidget#body QPushButton#openButton:pressed {{
    background: #000000;
}}
QWidget#body QPushButton#openButton:focus {{
    border-color: {FOCUS_ON_LIGHT};
}}
QWidget#body QProgressBar {{
    background: {BAR_GROOVE};
    border: none;
    border-radius: 4px;
    max-height: 8px;
    min-height: 8px;
}}
QWidget#body QProgressBar::chunk {{
    background: {BAR_FILL};
    border-radius: 4px;
}}
QWidget#body QProgressBar#topBar {{
    border-radius: 7px;
    max-height: 14px;
    min-height: 14px;
}}
QWidget#body QProgressBar#topBar::chunk {{
    border-radius: 7px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {BAR_FILL}, stop:1 {SCAN_GLOW});
}}
QWidget#body QProgressBar#busyBar {{
    background: {LCD};
    border-radius: 3px;
    max-height: 6px;
    min-height: 6px;
}}
QWidget#body QProgressBar#busyBar::chunk {{
    background: {LCD_TEXT};
    border-radius: 3px;
}}
"""
