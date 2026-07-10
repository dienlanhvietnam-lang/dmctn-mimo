# main.py
# This script allows the user to choose which script to run.
import os
import sys
import json
from logo import print_logo, version
from colorama import Fore, Style, init
import locale
import platform
import requests
import subprocess
from branding import GITHUB_REPO, GITHUB_URL, env_get
from config import get_config, force_update_config, save_user_language
from icons import setup_console_encoding
import icons as _icons
import shutil
import re

setup_console_encoding()

# Only import windll on Windows systems
if platform.system() == 'Windows':
    import ctypes
    # Only import windll on Windows systems
    from ctypes import windll

# Initialize colorama
init()

# ASCII-safe console markers (Windows conhost compatible)
EMOJI = {
    "FILE": _icons.FILE,
    "BACKUP": _icons.BACKUP,
    "SUCCESS": _icons.SUCCESS,
    "ERROR": _icons.ERROR,
    "INFO": _icons.INFO,
    "RESET": _icons.RESET,
    "MENU": _icons.MENU,
    "ARROW": _icons.ARROW,
    "LANG": _icons.LANG,
    "UPDATE": _icons.RESET,
    "ADMIN": _icons.ADMIN,
    "AIRDROP": _icons.SUCCESS,
    "ROCKET": _icons.SUCCESS,
    "STAR": _icons.SUCCESS,
    "SUN": _icons.SUCCESS,
    "CONTRIBUTE": _icons.SUCCESS,
    "SETTINGS": _icons.MENU,
    "OAUTH": _icons.OAUTH,
}

# Function to check if running as frozen executable
def is_frozen():
    """Check if the script is running as a frozen executable."""
    return getattr(sys, 'frozen', False)

# Function to check admin privileges (Windows only)
def is_admin():
    """Check if the script is running with admin privileges (Windows only)."""
    if platform.system() == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    # Always return True for non-Windows to avoid changing behavior
    return True

# Function to restart with admin privileges
def run_as_admin():
    """Restart the current script with admin privileges (Windows only)."""
    if platform.system() != 'Windows':
        return False
        
    try:
        args = [sys.executable] + sys.argv
        
        # Request elevation via ShellExecute
        print(f"{Fore.YELLOW}{EMOJI['ADMIN']} Requesting administrator privileges...{Style.RESET_ALL}")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", args[0], " ".join('"' + arg + '"' for arg in args[1:]), None, 1)
        return True
    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} Failed to restart with admin privileges: {e}{Style.RESET_ALL}")
        return False

class Translator:
    def __init__(self):
        self.translations = {}
        self.current_language = self.detect_system_language()  # Use correct method name
        self.fallback_language = 'en'  # Fallback language if translation is missing
        self.load_translations()
    
    def detect_system_language(self):
        """Detect system language and return corresponding language code"""
        env_lang = env_get("LANG", legacy_env="DMCTN_MIMO_LANG").strip().lower()
        if env_lang:
            return env_lang

        try:
            system = platform.system()
            
            if system == 'Windows':
                return self._detect_windows_language()
            else:
                return self._detect_unix_language()
                
        except Exception as e:
            print(f"{Fore.YELLOW}{EMOJI['INFO']} Failed to detect system language: {e}{Style.RESET_ALL}")
            return 'en'
    
    def _detect_windows_language(self):
        """Detect language on Windows systems"""
        try:
            # Ensure we are on Windows
            if platform.system() != 'Windows':
                return 'en'
                
            # Get keyboard layout
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            threadid = user32.GetWindowThreadProcessId(hwnd, 0)
            layout_id = user32.GetKeyboardLayout(threadid) & 0xFFFF
            
            # Map language ID to our language codes
            language_map = {
                0x0409: 'en',
                0x0422: 'vi',
            }
            
            return language_map.get(layout_id, 'en')
        except:
            return self._detect_unix_language()
    
    def _detect_unix_language(self):
        """Detect language on Unix-like systems (Linux, macOS)"""
        try:
            # Get the system locale
            system_locale = locale.getdefaultlocale()[0]
            if not system_locale:
                return 'en'
            
            system_locale = system_locale.lower()
            
            # Map locale to our language codes
            if system_locale.startswith('vi'):
                return 'vi'
            elif system_locale.startswith('en'):
                return 'en'

            env_lang = os.getenv('LANG', '').lower()
            if 'vi' in env_lang:
                return 'vi'

            return 'en'
        except:
            return 'en'
    
    def load_translations(self):
        """Load all available translations"""
        try:
            locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
            if hasattr(sys, '_MEIPASS'):
                locales_dir = os.path.join(sys._MEIPASS, 'locales')
            
            if not os.path.exists(locales_dir):
                print(f"{Fore.RED}{EMOJI['ERROR']} Locales directory not found{Style.RESET_ALL}")
                return

            for file in os.listdir(locales_dir):
                if file.endswith('.json'):
                    lang_code = file[:-5]  # Remove .json
                    try:
                        with open(os.path.join(locales_dir, file), 'r', encoding='utf-8') as f:
                            self.translations[lang_code] = json.load(f)
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        print(f"{Fore.RED}{EMOJI['ERROR']} Error loading {file}: {e}{Style.RESET_ALL}")
                        continue
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} Failed to load translations: {e}{Style.RESET_ALL}")
    
    def get(self, key, **kwargs):
        """Get translated text with fallback support"""
        try:
            # Try current language
            result = self._get_translation(self.current_language, key)
            if result == key and self.current_language != self.fallback_language:
                # Try fallback language if translation not found
                result = self._get_translation(self.fallback_language, key)
            return result.format(**kwargs) if kwargs else result
        except Exception:
            return key
    
    def _get_translation(self, lang_code, key):
        """Get translation for a specific language"""
        try:
            keys = key.split('.')
            value = self.translations.get(lang_code, {})
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, key)
                else:
                    return key
            return value
        except Exception:
            return key
    
    def set_language(self, lang_code):
        """Set current language with validation"""
        if lang_code in self.translations:
            self.current_language = lang_code
            return True
        return False

    def get_available_languages(self):
        """Get list of available languages"""
        return list(self.translations.keys())

# Create translator instance
translator = Translator()


def _T(key: str, **kwargs) -> str:
    """Translated string for current UI language."""
    return translator.get(key, **kwargs)


def render_mimo_account_status():
    """Render panel 02 — MiMo Pro account summary (active slot + auth.json)."""
    import json
    import ui
    from mimo_account_slots import extract_xiaomi_meta, list_slots
    from mimo_paths import get_mimo_auth_path

    slots_data = list_slots()
    active = next((s for s in slots_data["slots"] if s.get("active")), None)
    count = slots_data["count"]

    auth_dict: dict = {}
    auth_path = get_mimo_auth_path()
    if os.path.isfile(auth_path):
        try:
            with open(auth_path, encoding="utf-8") as f:
                auth_dict = json.load(f)
        except (json.JSONDecodeError, OSError):
            auth_dict = {}

    live_meta = extract_xiaomi_meta(auth_dict)
    has_pro_key = bool((auth_dict.get("xiaomi") or {}).get("key"))

    from chrome_profile import load_saved_profile

    saved_chrome = load_saved_profile()
    chrome_val = "—"
    if saved_chrome:
        profile_dir, display_name = saved_chrome
        chrome_val = display_name if display_name != profile_dir else profile_dir
        if display_name and display_name != profile_dir:
            chrome_val = f"{display_name} ({profile_dir})"

    ctx_val = _T("dashboard.context_none")
    try:
        from mimo_context_vault import list_context_slots

        ctx = list_context_slots()
        if ctx["count"] == 0:
            ctx_val = _T("dashboard.context_none")
        else:
            active_ctx = next((s for s in ctx["slots"] if s.get("active")), None)
            if active_ctx:
                ctx_val = _T("dashboard.context_active", label=active_ctx.get("label") or active_ctx.get("id"))
            else:
                ctx_val = _T("dashboard.slots_many", count=ctx["count"])
    except Exception:
        pass

    labels = [
        _T("dashboard.active_account"),
        _T("dashboard.mimo_uid"),
        _T("dashboard.api_key"),
        _T("dashboard.chrome_profile"),
        _T("dashboard.saved_slots"),
        _T("dashboard.context_slots"),
        _T("dashboard.pro_status"),
    ]
    w = max(ui.display_width(x) for x in labels)

    if active:
        account_val = active.get("label") or active.get("chrome_display_name") or active.get("id", "")
        uid_val = active.get("xiaomi_uid") or live_meta.get("uid") or "—"
        key_val = active.get("key_prefix") or live_meta.get("key_prefix") or "—"
    else:
        account_val = _T("dashboard.no_active_slot")
        uid_val = live_meta.get("uid") or "—"
        key_val = live_meta.get("key_prefix") or "—"

    if count == 0:
        slots_val = _T("dashboard.slots_none")
    elif count == 1:
        slots_val = _T("dashboard.slots_one")
    else:
        slots_val = _T("dashboard.slots_many", count=count)

    if has_pro_key:
        pro_val = _T("dashboard.pro_authenticated")
        pro_color = ui.OK
        icon = ui.ICON_OK
    elif count > 0:
        pro_val = _T("dashboard.pro_slots_saved")
        pro_color = ui.WARN
        icon = ui.ICON_WARN
    else:
        pro_val = _T("dashboard.pro_not_logged_in")
        pro_color = ui.ERR
        icon = ui.ICON_ERROR

    rows = [
        ui.kv(labels[0], account_val, w, value_color=ui.TEXT if active else ui.WARN),
        ui.kv(labels[1], uid_val or "—", w),
        ui.kv(labels[2], key_val or _T("dashboard.none"), w, value_color=ui.OK if key_val else ui.WARN),
        ui.kv(labels[3], chrome_val, w, value_color=ui.OK if saved_chrome else ui.WARN),
        ui.kv(labels[4], slots_val, w, value_color=ui.OK if count else ui.DIM),
        ui.kv(labels[5], ctx_val, w, value_color=ui.OK if ctx_val != _T("dashboard.context_none") else ui.DIM),
        ui.kv(labels[6], pro_val, w, value_color=pro_color),
    ]
    if not has_pro_key and count == 0:
        rows.append(ui.hint(_T("dashboard.hint_login")))

    ui.panel(rows, number="02", title=_T("dashboard.account_summary").upper(), icon=icon)


def print_menu():
    """Render panel 03 (actions menu)."""
    import ui

    labels = {
        0: translator.get('menu.exit'),
        1: translator.get('menu.select_language'),
        2: translator.get('menu.select_chrome_profile'),
        3: translator.get('menu.reset_mimo_machine'),
        4: translator.get('menu.totally_reset_mimo'),
        5: translator.get('menu.mimo_platform_login'),
        6: translator.get('menu.mimo_manage_accounts'),
        7: translator.get('menu.deep_reset_mimo'),
        8: translator.get('menu.manage_context'),
    }

    def cell(n):
        return f"{ui.KEYNUM}[{n}]{ui.RESET} {ui.TEXT}{labels[n]}{ui.RESET}"

    left_cells = [cell(i) for i in (0, 1, 2, 3, 4)]
    right_cells = [cell(i) for i in (5, 6, 7, 8)]
    left_w = max(ui.display_width(c) for c in left_cells)

    rows = []
    for i, left in enumerate(left_cells):
        right = right_cells[i] if i < len(right_cells) else ""
        gap = left_w - ui.display_width(left) + 4
        rows.append(f"{left}{' ' * gap}{right}" if right else left)

    title = _T("dashboard.action_menu")
    ui.panel(rows, number="03", title=title.upper(), icon=ui.ICON_MENU)


def _prompt_hint() -> str:
    return _T("dashboard.prompt")


def _show_help() -> None:
    import ui
    lines = [
        ui.hint(_T("dashboard.help_menu5")),
        ui.hint(_T("dashboard.help_menu6")),
        ui.hint(_T("dashboard.help_menu7")),
        ui.hint(_T("dashboard.help_menu8")),
        ui.hint(_T("dashboard.help_reload")),
        ui.hint(_T("dashboard.help_exit")),
    ]
    ui.panel(lines, title=_T("dashboard.help_title").upper(), icon=ui.ICON_INFO)


def render_dashboard(*, run_update_check: bool = False) -> None:
    """Draw panels 02–03 (MiMo account summary + menu)."""
    render_mimo_account_status()
    print_menu()

def select_language():
    """Language selection menu"""
    print(f"\n{Fore.CYAN}{EMOJI['LANG']} {translator.get('menu.select_language')}:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'─' * 40}{Style.RESET_ALL}")
    
    languages = translator.get_available_languages()
    for i, lang in enumerate(languages):
        lang_name = translator.get(f"languages.{lang}")
        print(f"{Fore.GREEN}{i}{Style.RESET_ALL}. {lang_name}")
    
    try:
        choice = input(f"\n{EMOJI['ARROW']} {Fore.CYAN}{translator.get('menu.input_choice', choices=f'0-{len(languages)-1}')}: {Style.RESET_ALL}")
        if choice.isdigit() and 0 <= int(choice) < len(languages):
            lang_code = languages[int(choice)]
            if translator.set_language(lang_code):
                save_user_language(lang_code)
                os.environ["DMCTN_MIMO_LANG"] = lang_code
            return True
        else:
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('menu.invalid_choice')}{Style.RESET_ALL}")
            return False
    except (ValueError, IndexError):
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('menu.invalid_choice')}{Style.RESET_ALL}")
        return False

def check_latest_version():
    """Check the latest release; return a status dict for the system-status panel."""
    try:
        # Get latest version from GitHub API with timeout and proper headers
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'DMCTN-MiMo-Updater'
        }
        response = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers=headers,
            timeout=10
        )
        
        # Check if rate limit exceeded
        if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
            return ("fail", "GitHub API rate limit exceeded")
        
        # Check if response is successful
        if response.status_code != 200:
            raise Exception(f"GitHub API returned status code {response.status_code}")
            
        response_data = response.json()
        if "tag_name" not in response_data:
            raise Exception("No version tag found in GitHub response")
            
        latest_version = response_data["tag_name"].lstrip('v')
        
        # Validate version format
        if not latest_version:
            raise Exception("Invalid version format received")
        
        # Parse versions for proper comparison
        def parse_version(version_str):
            """Parse version string into tuple for proper comparison"""
            try:
                return tuple(map(int, version_str.split('.')))
            except ValueError:
                # Fallback to string comparison if parsing fails
                return version_str
                
        current_version_tuple = parse_version(version)
        latest_version_tuple = parse_version(latest_version)
        
        # Compare versions properly
        is_newer_version_available = False
        if isinstance(current_version_tuple, tuple) and isinstance(latest_version_tuple, tuple):
            is_newer_version_available = current_version_tuple < latest_version_tuple
        else:
            # Fallback to string comparison
            is_newer_version_available = version != latest_version
        
        if is_newer_version_available:
            print(f"\n{Fore.YELLOW}{EMOJI['INFO']} {translator.get('updater.new_version_available', current=version, latest=latest_version)}{Style.RESET_ALL}")
            
            # get and show changelog
            try:
                changelog_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/CHANGELOG.md"
                changelog_response = requests.get(changelog_url, timeout=10)
                
                if changelog_response.status_code == 200:
                    changelog_content = changelog_response.text
                    
                    # get latest version changelog
                    latest_version_pattern = f"## v{latest_version}"
                    changelog_sections = changelog_content.split("## v")
                    
                    latest_changes = None
                    for section in changelog_sections:
                        if section.startswith(latest_version):
                            latest_changes = section
                            break
                    
                    if latest_changes:
                        print(f"\n{Fore.CYAN}{'─' * 40}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{translator.get('updater.changelog_title')}:{Style.RESET_ALL}")
                        
                        # show changelog content (max 10 lines)
                        changes_lines = latest_changes.strip().split('\n')
                        for i, line in enumerate(changes_lines[1:11]):  # skip version number line, max 10 lines
                            if line.strip():
                                print(f"{Fore.WHITE}{line.strip()}{Style.RESET_ALL}")
                        
                        # if changelog more than 10 lines, show ellipsis
                        if len(changes_lines) > 11:
                            print(f"{Fore.WHITE}...{Style.RESET_ALL}")
                        
                        print(f"{Fore.CYAN}{'─' * 40}{Style.RESET_ALL}")
            except Exception as changelog_error:
                # get changelog failed
                pass
            
            # Ask user if they want to update
            while True:
                choice = input(f"\n{EMOJI['ARROW']} {Fore.CYAN}{translator.get('updater.update_confirm', choices='Y/n')}: {Style.RESET_ALL}").lower()
                if choice in ['', 'y', 'yes']:
                    break
                elif choice in ['n', 'no']:
                    return ("update", latest_version)
                else:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('menu.invalid_choice')}{Style.RESET_ALL}")
            
            try:
                # Execute update command based on platform
                if platform.system() == 'Windows':
                    update_command = f'irm https://raw.githubusercontent.com/{GITHUB_REPO}/main/scripts/install.ps1 | iex'
                    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', update_command], check=True)
                else:
                    # For Linux/Mac, download and execute the install script
                    install_script_url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/main/scripts/install.sh'
                    
                    # First verify the script exists
                    script_response = requests.get(install_script_url, timeout=5)
                    if script_response.status_code != 200:
                        raise Exception("Installation script not found")
                        
                    # Save and execute the script
                    with open('install.sh', 'wb') as f:
                        f.write(script_response.content)
                    
                    os.chmod('install.sh', 0o755)  # Make executable
                    subprocess.run(['./install.sh'], check=True)
                    
                    # Clean up
                    if os.path.exists('install.sh'):
                        os.remove('install.sh')
                
                print(f"\n{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('updater.updating')}{Style.RESET_ALL}")
                sys.exit(0)
                
            except Exception as update_error:
                return ("update", latest_version)
        else:
            # If current version is newer or equal to latest version
            if current_version_tuple > latest_version_tuple:
                return ("dev", f"v{version} > v{latest_version}")
            return ("ok", f"v{version}")

    except requests.exceptions.RequestException as e:
        return ("network", str(e))

    except Exception as e:
        return ("fail", str(e))

def main():
    # Check for admin privileges if running as executable on Windows only
    if platform.system() == 'Windows' and is_frozen() and not is_admin():
        print(f"{Fore.YELLOW}{EMOJI['ADMIN']} {translator.get('menu.admin_required')}{Style.RESET_ALL}")
        if run_as_admin():
            sys.exit(0)  # Exit after requesting admin privileges
        else:
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {translator.get('menu.admin_required_continue')}{Style.RESET_ALL}")
    
    # Initialize configuration
    config = get_config(translator)
    if not config:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('menu.config_init_failed')}{Style.RESET_ALL}")
        return
    if config.has_option('Utils', 'language'):
        config_lang = config.get('Utils', 'language').strip().lower()
        if config_lang:
            translator.set_language(config_lang)
    env_lang = env_get("LANG", legacy_env="DMCTN_MIMO_LANG")
    if env_lang:
        translator.set_language(env_lang)
    print_logo(translator)
    force_update_config(translator)

    if config.getboolean('Utils', 'enabled_update_check'):
        check_latest_version()

    render_dashboard()

    import ui
    while True:
        try:
            choice = ui.read_prompt(_prompt_hint()).lower()
            if choice in ('q', 'quit', 'exit'):
                print(f"\n{Fore.YELLOW}{EMOJI['INFO']} {translator.get('menu.exit')}...{Style.RESET_ALL}")
                return
            if choice == 'h':
                _show_help()
                continue
            if choice == 'r':
                render_dashboard()
                continue

            if choice == "0":
                print(f"\n{Fore.YELLOW}{EMOJI['INFO']} {translator.get('menu.exit')}...{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}")
                return
            elif choice == "1":
                if select_language():
                    print_logo(translator)
                    render_dashboard(run_update_check=False)
                continue
            elif choice == "2":
                import chrome_profile
                chrome_profile.run(translator)
                render_dashboard(run_update_check=False)
            elif choice == "3":
                import reset_mimo_machine
                reset_mimo_machine.run(translator)
                render_dashboard(run_update_check=False)
            elif choice == "4":
                import totally_reset_mimo
                totally_reset_mimo.run(translator)
                render_dashboard(run_update_check=False)
            elif choice == "5":
                import mimo_platform_login
                mimo_platform_login.run(translator)
                render_dashboard(run_update_check=False)
            elif choice == "6":
                import mimo_manage_accounts
                mimo_manage_accounts.run(translator)
                render_dashboard(run_update_check=False)
            elif choice == "7":
                import totally_reset_mimo
                totally_reset_mimo.run_deep(translator)
                render_dashboard(run_update_check=False)
            elif choice == "8":
                import mimo_manage_context
                mimo_manage_context.run(translator)
                render_dashboard(run_update_check=False)
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('menu.invalid_choice')}{Style.RESET_ALL}")
                render_dashboard(run_update_check=False)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}{EMOJI['INFO']} {translator.get('menu.program_terminated')}{Style.RESET_ALL}")
            return
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('menu.error_occurred', error=str(e))}{Style.RESET_ALL}")
            render_dashboard(run_update_check=False)

if __name__ == "__main__":
    main()