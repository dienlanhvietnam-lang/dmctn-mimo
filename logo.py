from colorama import Fore, Style, init
from dotenv import load_dotenv
import os
import shutil
import re
from branding import APP_NAME, GITHUB_URL

# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Build the full path to the .env file
env_path = os.path.join(current_dir, '.env')

# Load environment variables, specifying the .env file path
load_dotenv(env_path)
# Get the version number, using the default value if not found
version = os.getenv('VERSION', '1.0.0')

# Initialize colorama
init()

# get terminal width
def get_terminal_width():
    try:
        columns, _ = shutil.get_terminal_size()/2
        return columns
    except:
        return 80  # default width

# center display text (not handling Chinese characters)
def center_multiline_text(text, handle_chinese=False):
    width = get_terminal_width()
    lines = text.split('\n')
    centered_lines = []
    
    for line in lines:
        # calculate actual display width (remove ANSI color codes)
        clean_line = line
        for color in [Fore.CYAN, Fore.YELLOW, Fore.GREEN, Fore.RED, Fore.BLUE, Style.RESET_ALL]:
            clean_line = clean_line.replace(color, '')
        
        # remove all ANSI escape sequences to get the actual length
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_line = ansi_escape.sub('', clean_line)
        
        # calculate display width
        if handle_chinese:
            # consider Chinese characters occupying two positions
            display_width = 0
            for char in clean_line:
                if ord(char) > 127:  # non-ASCII characters
                    display_width += 2
                else:
                    display_width += 1
        else:
            # not handling Chinese characters
            display_width = len(clean_line)
        
        # calculate the number of spaces to add
        padding = max(0, (width - display_width) // 2)
        centered_lines.append(' ' * padding + line)
    
    return '\n'.join(centered_lines)

# original LOGO text
LOGO_TEXT = f"""{Fore.CYAN}
███╗   ███╗██╗███╗   ██╗ ██████╗      ██╗   ██╗██╗██████╗ 
████╗ ████║██║████╗  ██║██╔═══██╗     ██║   ██║██║██╔══██╗
██╔████╔██║██║██╔██╗ ██║██║   ██║     ██║   ██║██║██████╔╝
██║╚██╔╝██║██║██║╚██╗██║██║   ██║     ╚██╗ ██╔╝██║██╔═══╝ 
██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝      ╚████╔╝ ██║██║     
╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝       ╚═══╝  ╚═╝╚═╝     
{Style.RESET_ALL}"""

DESCRIPTION_TEXT = f"""{Fore.YELLOW}
{APP_NAME} Pro Activator v{version}{Fore.GREEN}
Author: Pin Studios (hovanhoa)"""

OTHER_INFO_TEXT = f"""{Fore.YELLOW}
Github: {GITHUB_URL}{Fore.RED}
Press 1 to change language | 按下 1 键切换语言{Style.RESET_ALL}"""

# center display LOGO and DESCRIPTION
CURSOR_LOGO = center_multiline_text(LOGO_TEXT, handle_chinese=False)
CURSOR_DESCRIPTION = center_multiline_text(DESCRIPTION_TEXT, handle_chinese=False)
CURSOR_OTHER_INFO = center_multiline_text(OTHER_INFO_TEXT, handle_chinese=True)

# Hexagon-style brand mark (3 rows, visible width 7)
_MARK = ["╭─────╮", f"│  {Fore.LIGHTCYAN_EX}M{Fore.CYAN}  │", "╰─────╯"]


def print_logo(translator=None):
    """Render the dashboard header panel (brand mark + title + links)."""
    import ui

    def _t(key: str, fallback: str) -> str:
        if not translator:
            return fallback
        value = translator.get(key)
        return value if value and value != key else fallback

    dash = _t("header.dashboard", "Bảng điều khiển")
    product = _t("header.product_line", "MiMo FREE v0.1 • DMCTN")
    tagline = _t("header.tagline", "Free MIMO 07/26")
    lang_hint = _t("header.lang_hint", "Press 1 to change language")

    title = f"{ui.TITLE}{dash} {APP_NAME}{ui.RESET}"
    if "•" in product:
        left, right = product.split("•", 1)
        subtitle = f"{ui.DIM}{left.strip()}{ui.RESET}  •  {ui.OK}{right.strip()}{ui.RESET}"
    else:
        subtitle = f"{ui.DIM}{product}{ui.RESET}"
    footer = f"{ui.ACCENT}{tagline}{ui.RESET}    {ui.DIM}{lang_hint}{ui.RESET}"

    marks = [f"{ui.BORDER}{m}{ui.RESET}" for m in _MARK]
    lines = [
        f"{marks[0]}   {title}",
        f"{marks[1]}   {subtitle}",
        f"{marks[2]}   {footer}",
    ]
    print()
    ui.panel(lines)


if __name__ == "__main__":
    print_logo()
