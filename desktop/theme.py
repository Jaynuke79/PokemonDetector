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

from PySide6.QtCore import QSize

ELEMENTAL_TYPES_PATH = Path(__file__).with_name("elemental_types.json")
PREFERRED_UI_SCALE = 1.5
SMALLEST_UI_SCALE = 0.8
UNSCALED_SIZE = QSize(860, 620)
UNSCALED_MINIMUM = QSize(640, 470)
FRAME_ALLOWANCE = QSize(16, 64)
FALLBACK_POINT_SIZE = 9.0
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


def ui_scale_for(available_width, available_height):
    """The largest scale, up to PREFERRED_UI_SCALE, at which the window still fits.

    The sizes are logical pixels, so a display already scaled by the OS gets a
    smaller UI scale on top of it rather than a window larger than the screen.
    """
    fit = min(
        (available_width - FRAME_ALLOWANCE.width()) / UNSCALED_MINIMUM.width(),
        (available_height - FRAME_ALLOWANCE.height()) / UNSCALED_MINIMUM.height(),
    )
    return max(SMALLEST_UI_SCALE, min(PREFERRED_UI_SCALE, fit))


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


def stylesheet(scale=1.0, base_point_size=FALLBACK_POINT_SIZE):
    """The window stylesheet with every length and font size multiplied by scale.

    base_point_size is the system font size that unstyled text would use.
    """

    def px(length):
        return f"{max(1, round(length * scale))}px"

    def pt(size):
        return f"{size * scale:.1f}pt"

    return f"""
    QMenuBar, QMenu, QWidget#body QWidget {{
        font-size: {pt(base_point_size)};
    }}
    QMainWindow, QMenuBar {{
        background: {DESK};
        color: {WHITE};
    }}
    QMenuBar::item {{
        background: transparent;
        padding: {px(4)} {px(10)};
        border: {px(2)} solid transparent;
        border-radius: {px(4)};
    }}
    QMenuBar::item:selected, QMenuBar::item:pressed {{
        background: {BODY_RED_DARK};
        border-color: {FOCUS_ON_DARK};
    }}
    QMenu {{
        background: {SHELL};
        color: {INK};
        border: {px(1)} solid {SHELL_EDGE};
    }}
    QMenu::item {{
        padding: {px(5)} {px(18)};
    }}
    QMenu::item:selected {{
        background: {FOCUS_ON_LIGHT};
        color: {WHITE};
    }}
    QWidget#body QLabel#wordmark {{
        color: {WHITE};
        font-size: {pt(17)};
        font-weight: 800;
        letter-spacing: {px(2)};
    }}
    QWidget#body QLabel#tagline {{
        color: {WHITE};
        font-size: {pt(9)};
        font-weight: 600;
        letter-spacing: {px(1)};
    }}
    QWidget#body QFrame#bezel, QWidget#body QFrame#resultCard {{
        background: {SHELL};
        border: {px(1)} solid {SHELL_EDGE};
        border-radius: {px(18)};
    }}
    QWidget#body QLabel {{
        background: transparent;
        color: {INK};
    }}
    QWidget#body QLabel#screen {{
        background: {SCREEN};
        color: {SCREEN_TEXT};
        border: {px(3)} solid {SCREEN_EDGE};
        border-radius: {px(12)};
        padding: {px(14)};
        font-size: {pt(11)};
    }}
    QWidget#body QLabel[readable="true"] {{
        border: {px(2)} solid transparent;
        border-radius: {px(5)};
        padding: {px(1)} {px(6)} {px(1)} {px(3)};
    }}
    QWidget#body QLabel[readable="true"]:focus {{
        border-color: {FOCUS_ON_LIGHT};
    }}
    QWidget#body QLabel#cardCaption, QWidget#body QLabel#othersCaption {{
        color: {INK_MUTED};
        font-size: {pt(8)};
        font-weight: 700;
        letter-spacing: {px(2)};
        padding-left: {px(5)};
    }}
    QWidget#body QLabel#topName {{
        color: {INK};
        font-size: {pt(21)};
        font-weight: 800;
    }}
    QWidget#body QLabel#topConfidence {{
        color: {INK};
        font-size: {pt(15)};
        font-weight: 700;
    }}
    QWidget#body QLabel#cardPlaceholder {{
        color: {INK_MUTED};
        font-size: {pt(10)};
        padding-left: {px(5)};
    }}
    QWidget#body QLabel#typeBadge {{
        font-size: {pt(8)};
        font-weight: 800;
        letter-spacing: {px(1)};
    }}
    QWidget#body QLabel#statusLabel {{
        background: {LCD};
        color: {LCD_TEXT};
        border: {px(2)} solid {LCD};
        border-radius: {px(8)};
        padding: {px(6)} {px(10)};
        font-family: "Consolas", "DejaVu Sans Mono", monospace;
        font-size: {pt(9)};
    }}
    QWidget#body QLabel#statusLabel:focus {{
        border-color: {FOCUS_ON_DARK};
    }}
    QWidget#body QPushButton#openButton {{
        background: {INK};
        color: {WHITE};
        border: {px(3)} solid {INK};
        border-radius: {px(14)};
        padding: {px(6)} {px(18)};
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
        border-radius: {px(4)};
        max-height: {px(8)};
        min-height: {px(8)};
    }}
    QWidget#body QProgressBar::chunk {{
        background: {BAR_FILL};
        border-radius: {px(4)};
    }}
    QWidget#body QProgressBar#topBar {{
        border-radius: {px(7)};
        max-height: {px(14)};
        min-height: {px(14)};
    }}
    QWidget#body QProgressBar#topBar::chunk {{
        border-radius: {px(7)};
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {BAR_FILL}, stop:1 {SCAN_GLOW});
    }}
    QWidget#body QProgressBar#busyBar {{
        background: {LCD};
        border-radius: {px(3)};
        max-height: {px(6)};
        min-height: {px(6)};
    }}
    QWidget#body QProgressBar#busyBar::chunk {{
        background: {LCD_TEXT};
        border-radius: {px(3)};
    }}
"""
