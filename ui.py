"""Console UI theme for MiMo VIP: rounded panels, section badges, status icons.

Renders the dashboard look (header + numbered panels + prompt bar) using
colorama's 16-color palette so it works in both Windows Terminal and legacy
conhost. Width is measured with east-asian awareness so Vietnamese diacritics
and CJK stay aligned.
"""
from __future__ import annotations

import re
import shutil
import unicodedata

from colorama import Back, Fore, Style, init

init()

# --- palette (semantic) -------------------------------------------------------
BORDER = Fore.CYAN
TITLE = Fore.LIGHTCYAN_EX + Style.BRIGHT
ACCENT = Fore.LIGHTCYAN_EX
TEXT = Fore.WHITE
DIM = Fore.LIGHTBLACK_EX
OK = Fore.LIGHTGREEN_EX
WARN = Fore.LIGHTYELLOW_EX
ERR = Fore.LIGHTRED_EX
KEYNUM = Fore.LIGHTCYAN_EX + Style.BRIGHT
RESET = Style.RESET_ALL

# --- box drawing --------------------------------------------------------------
TL, TR, BL, BR = "╭", "╮", "╰", "╯"
H, V = "─", "│"

MIN_WIDTH = 62
MAX_WIDTH = 100

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
# rough emoji ranges that render as double-width
_EMOJI_RANGES = (
    (0x1F300, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0xFE00, 0xFE0F),
)


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _char_width(ch: str) -> int:
    code = ord(ch)
    if unicodedata.combining(ch):
        return 0
    for lo, hi in _EMOJI_RANGES:
        if lo <= code <= hi:
            return 2
    if unicodedata.east_asian_width(ch) in ("F", "W"):
        return 2
    return 1


def display_width(text: str) -> int:
    """Visible width of a string, ignoring ANSI and counting CJK/emoji as 2."""
    return sum(_char_width(c) for c in strip_ansi(text))


def box_width() -> int:
    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        cols = 80
    return max(MIN_WIDTH, min(cols - 1, MAX_WIDTH))


def _pad(text: str, width: int) -> str:
    """Right-pad a (possibly colored) string to a visible width."""
    gap = width - display_width(text)
    return text + " " * gap if gap > 0 else text


# --- status icons (fixed visible width = 3) -----------------------------------
ICON_W = 3
ICON_ERROR = f"{ERR}[x]{RESET}"
ICON_WARN = f"{WARN}[!]{RESET}"
ICON_OK = f"{OK}[+]{RESET}"
ICON_MENU = f"{ACCENT}[=]{RESET}"
ICON_INFO = f"{ACCENT}[i]{RESET}"


def _top_border(number: str | None, title: str) -> str:
    w = box_width()
    used = 1  # TL
    parts = [f"{BORDER}{TL}"]

    if number:
        badge = f"{Back.CYAN}{Fore.BLACK}{Style.BRIGHT} {number} {RESET}"
        parts.append(f"{BORDER}{H}{RESET}{badge}")
        used += 1 + 4  # ─ + " NN "
    if title:
        label = f"{BORDER}{H}{RESET} {TITLE}{title}{RESET} "
        parts.append(label)
        used += 1 + 1 + display_width(title) + 1  # ─ + space + title + space

    fill = w - used - 1  # room for TR
    parts.append(f"{BORDER}{H * max(0, fill)}{TR}{RESET}")
    return "".join(parts)


def _bottom_border() -> str:
    w = box_width()
    return f"{BORDER}{BL}{H * (w - 2)}{BR}{RESET}"


def _row(content: str, icon: str | None = None) -> str:
    w = box_width()
    inner = w - 4  # "│ " + content + " │"
    if icon:
        text_area = inner - ICON_W - 1
        body = _pad(content, text_area) + " " + icon
        body = _pad(body, inner)
    else:
        body = _pad(content, inner)
    return f"{BORDER}{V}{RESET} {body} {BORDER}{V}{RESET}"


def panel(lines: list[str], *, number: str | None = None, title: str = "", icon: str | None = None) -> None:
    """Print a rounded panel. Icon (if any) is placed at the right of the first row."""
    print(_top_border(number, title))
    for i, line in enumerate(lines):
        print(_row(line, icon if i == 0 else None))
    print(_bottom_border())


def kv(label: str, value: str, label_w: int, *, value_color: str = TEXT) -> str:
    """A 'label : value' row with the colon aligned at label_w."""
    padded = label + " " * max(0, label_w - display_width(label))
    return f"{TEXT}{padded}{DIM} : {value_color}{value}{RESET}"


def hint(text: str) -> str:
    return f"{DIM}{text}{RESET}"


def print_prompt_box(text: str) -> None:
    """Print the bottom prompt panel (mockup: rounded box with >_ hint)."""
    w = box_width()
    top = f"{BORDER}{TL}{H * (w - 2)}{TR}{RESET}"
    inner = w - 4
    hint = f"{OK}{Style.BRIGHT}>_{RESET} {TEXT}{text}{RESET}"
    body = _pad(hint, inner)
    row = f"{BORDER}{V}{RESET} {body} {BORDER}{V}{RESET}"
    print(f"{top}\n{row}\n{_bottom_border()}")


def read_prompt(text: str) -> str:
    """Show prompt panel then read a line of input."""
    print_prompt_box(text)
    return input(f" {OK}{Style.BRIGHT}>_{RESET} ").strip()
