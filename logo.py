from colorama import init
from dotenv import load_dotenv
import os

from branding import APP_NAME

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))
version = os.getenv("VERSION", "2.0.0")

init()

# Hexagon-style brand mark (3 rows, visible width 7)
_MARK = ["╭─────╮", "│  D  │", "╰─────╯"]


def print_logo(translator=None):
    """Render the dashboard header panel (brand mark + title + links)."""
    import ui
    from colorama import Fore

    def _t(key: str, fallback: str) -> str:
        if not translator:
            return fallback
        value = translator.get(key)
        return value if value and value != key else fallback

    dash = _t("header.dashboard", "Bảng điều khiển")
    product = _t("header.product_line", "MiMo FREE v2.0.0 • DMCTN")
    tagline = _t("header.tagline", "Free MIMO 07/26")
    lang_hint = _t("header.lang_hint", "Press 1 to change language")

    title = f"{ui.TITLE}{dash} {APP_NAME}{ui.RESET}"
    if "•" in product:
        left, right = product.split("•", 1)
        subtitle = f"{ui.DIM}{left.strip()}{ui.RESET}  •  {ui.OK}{right.strip()}{ui.RESET}"
    else:
        subtitle = f"{ui.DIM}{product}{ui.RESET}"
    footer = f"{ui.ACCENT}{tagline}{ui.RESET}    {ui.DIM}{lang_hint}{ui.RESET}"

    marks = [
        f"{ui.BORDER}{m.replace('D', f'{Fore.LIGHTCYAN_EX}D{Fore.CYAN}') if i == 1 else m}{ui.RESET}"
        for i, m in enumerate(_MARK)
    ]
    lines = [
        f"{marks[0]}   {title}",
        f"{marks[1]}   {subtitle}",
        f"{marks[2]}   {footer}",
    ]
    print()
    ui.panel(lines)


if __name__ == "__main__":
    print_logo()
