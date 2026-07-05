"""ASCII-safe console icons and UTF-8 console setup for Windows terminals."""
from __future__ import annotations

import sys

# Visible on legacy Windows conhost / cp1252 (no emoji / special Unicode)
INFO = "[i]"
SUCCESS = "[+]"
ERROR = "[x]"
WARNING = "[!]"
ARROW = "->"
LANG = "[@]"
RESET = "[~]"
FILE = "[f]"
BACKUP = "[b]"
ADMIN = "[*]"
OAUTH = "[k]"
MENU = "[=]"


def setup_console_encoding() -> None:
    """Best-effort UTF-8 console; ASCII icons remain safe if this fails."""
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
