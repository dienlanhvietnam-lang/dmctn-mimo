"""Chrome profile discovery and browser session helpers (shared by OAuth + MiMo login)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

from colorama import Fore, Style, init
from DrissionPage import ChromiumOptions, ChromiumPage

import icons as _icons
from utils import get_default_chrome_path, should_keep_cursor_running

init()

EMOJI = {
    "INFO": _icons.INFO,
    "SUCCESS": _icons.SUCCESS,
    "ERROR": _icons.ERROR,
    "WARNING": _icons.WARNING,
}


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def get_user_data_directory() -> str:
    if os.name == "nt":
        possible_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
            os.path.expandvars(r"%LOCALAPPDATA%\Chromium\User Data"),
        ]
    elif sys.platform == "darwin":
        possible_paths = [
            os.path.expanduser("~/Library/Application Support/Google/Chrome"),
            os.path.expanduser("~/Library/Application Support/Chromium"),
        ]
    else:
        possible_paths = [
            os.path.expanduser("~/.config/google-chrome"),
            os.path.expanduser("~/.config/chromium"),
        ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    temp_profile = os.path.join(os.path.expanduser("~"), ".cursor_temp_profile")
    os.makedirs(temp_profile, exist_ok=True)
    return temp_profile


def get_browser_path() -> str | None:
    chrome_path = get_default_chrome_path()
    if chrome_path and os.path.exists(chrome_path):
        return chrome_path

    if os.name == "nt":
        alt_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        alt_paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        alt_paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]

    for path in alt_paths:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            return expanded
    return None


def get_available_profiles(user_data_dir: str | None = None) -> list[tuple[str, str]]:
    user_data_dir = user_data_dir or get_user_data_directory()
    try:
        profiles: list[tuple[str, str]] = []
        profile_names: dict[str, str] = {}
        local_state_path = os.path.join(user_data_dir, "Local State")
        if os.path.exists(local_state_path):
            with open(local_state_path, encoding="utf-8") as f:
                local_state = json.load(f)
            info_cache = local_state.get("profile", {}).get("info_cache", {})
            for profile_dir, info in info_cache.items():
                profile_dir = profile_dir.replace("\\", "/")
                profile_names[profile_dir] = info.get("name", profile_dir)

        for item in os.listdir(user_data_dir):
            if item == "Default" or (item.startswith("Profile ") and os.path.isdir(os.path.join(user_data_dir, item))):
                profiles.append((item, profile_names.get(item, item)))
        return sorted(profiles)
    except Exception:
        return []


def _profile_label(profile_dir: str, display_name: str | None = None) -> str:
    if display_name and display_name != profile_dir:
        return f"{display_name} ({profile_dir})"
    return profile_dir


def load_saved_profile(translator=None) -> tuple[str, str] | None:
    """Return saved (profile_dir, display_name) from config.ini, or None."""
    try:
        from config import get_config

        config = get_config(translator)
        if not config or not config.has_section("Chrome"):
            return None
        profile_dir = config.get("Chrome", "profile_directory", fallback="").strip()
        if not profile_dir:
            return None
        display_name = config.get("Chrome", "profile_display_name", fallback=profile_dir).strip() or profile_dir
        known = {d: n for d, n in get_available_profiles()}
        if profile_dir not in known:
            return None
        return profile_dir, known.get(profile_dir, display_name)
    except Exception:
        return None


def save_selected_profile(profile_dir: str, display_name: str, translator=None) -> bool:
    """Persist default Chrome profile to config.ini."""
    try:
        import utils
        from config import get_config

        config = get_config(translator)
        if not config:
            return False
        if not config.has_section("Chrome"):
            config.add_section("Chrome")
        config.set("Chrome", "profile_directory", profile_dir)
        config.set("Chrome", "profile_display_name", display_name or profile_dir)
        config_path = os.path.join(utils.get_app_config_dir(), "config.ini")
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        return True
    except Exception as exc:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'chrome_profile.save_failed', 'Could not save profile: {error}', error=str(exc))}{Style.RESET_ALL}")
        return False


def kill_browser_processes() -> None:
    try:
        if os.name == "nt":
            for proc in ("chrome.exe", "chromium.exe"):
                os.system(f"taskkill /f /im {proc} >nul 2>&1")
        else:
            for proc in ("chrome", "chromium", "chromium-browser"):
                os.system(f"pkill -f {proc} >/dev/null 2>&1")
        time.sleep(1)
    except Exception:
        pass


def prepare_profile_for_oauth(translator=None) -> None:
    """Close Chrome so OAuth can launch the selected profile reliably."""
    print(
        f"{Fore.YELLOW}{EMOJI['WARNING']} "
        f"{_msg(translator, 'chrome_profile.oauth_close_chrome', 'Closing Chrome for OAuth login (required for profile launch)...')}"
        f"{Style.RESET_ALL}"
    )
    kill_browser_processes()


def open_url_via_subprocess(url: str, profile_dir: str, translator=None) -> bool:
    """Open URL in Chrome with profile-directory via native process (Windows-friendly)."""
    chrome_path = get_browser_path()
    if not chrome_path:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'oauth.no_compatible_browser_found', 'No compatible browser found')}{Style.RESET_ALL}")
        return False
    user_data_dir = get_user_data_directory()
    args = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        url,
    ]
    try:
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError as exc:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'chrome_profile.open_failed', 'Chrome launch failed: {error}', error=str(exc))}{Style.RESET_ALL}")
        return False


def configure_browser_options(chrome_path: str, user_data_dir: str, active_profile: str) -> ChromiumOptions:
    co = ChromiumOptions()
    co.set_paths(browser_path=chrome_path, user_data_path=user_data_dir)
    co.set_argument(f"--profile-directory={active_profile}")
    co.set_argument("--no-first-run")
    co.set_argument("--no-default-browser-check")
    co.set_argument("--disable-gpu")
    if sys.platform.startswith("linux"):
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-dev-shm-usage")
    elif sys.platform == "darwin":
        co.set_argument("--disable-gpu-compositing")
    elif os.name == "nt":
        co.set_argument("--disable-features=TranslateUI")
    return co


def select_profile(translator=None, *, allow_exit: bool = True) -> tuple[str, str] | None:
    """Return (profile_dir, display_name) or None if cancelled."""
    profiles = get_available_profiles()
    if not profiles:
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'chrome_profile.no_profiles', 'No Chrome profiles found')}{Style.RESET_ALL}")
        return None

    saved = load_saved_profile(translator)
    if saved:
        profile_dir, display_name = saved
        print(
            f"{Fore.CYAN}{EMOJI['INFO']} "
            f"{_msg(translator, 'chrome_profile.current_saved', 'Current default: {profile}', profile=_profile_label(profile_dir, display_name))}"
            f"{Style.RESET_ALL}"
        )

    print(f"\n{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'chrome_profile.select_profile', 'Select a Chrome profile:')}{Style.RESET_ALL}")
    if allow_exit:
        print(f"{Fore.CYAN}0. {_msg(translator, 'menu.exit', 'Exit')}{Style.RESET_ALL}")
    for i, (dir_name, display_name) in enumerate(profiles, 1):
        marker = f" {Fore.GREEN}*{_msg(translator, 'chrome_profile.default_marker', 'default')}{Style.RESET_ALL}" if saved and dir_name == saved[0] else ""
        print(f"{Fore.CYAN}{i}. {display_name} ({dir_name}){marker}{Style.RESET_ALL}")

    while True:
        raw = input(
            f"\n{Fore.CYAN}{_msg(translator, 'menu.input_choice', 'Please enter your choice ({choices})', choices=f'0-{len(profiles)}')}: {Style.RESET_ALL}"
        ).strip()
        try:
            choice = int(raw)
            if choice == 0 and allow_exit:
                return None
            if 1 <= choice <= len(profiles):
                dir_name, display_name = profiles[choice - 1]
                print(
                    f"{Fore.GREEN}{EMOJI['SUCCESS']} "
                    f"{_msg(translator, 'chrome_profile.profile_selected', 'Selected profile: {profile}', profile=dir_name)}"
                    f"{Style.RESET_ALL}"
                )
                return dir_name, display_name
        except ValueError:
            pass
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'chrome_profile.invalid_selection', 'Invalid selection')}{Style.RESET_ALL}")


def resolve_profile_for_login(translator=None, *, allow_exit: bool = True) -> tuple[str, str] | None:
    """Use saved default profile when valid; otherwise prompt via select_profile()."""
    saved = load_saved_profile(translator)
    if saved:
        profile_dir, display_name = saved
        prompt = _msg(
            translator,
            "chrome_profile.use_saved_prompt",
            "Use saved Chrome profile {profile}? (Y/n): ",
            profile=_profile_label(profile_dir, display_name),
        )
        answer = input(f"{Fore.CYAN}{EMOJI['INFO']} {prompt}{Style.RESET_ALL}").strip().lower()
        if answer in ("", "y", "yes"):
            print(
                f"{Fore.GREEN}{EMOJI['SUCCESS']} "
                f"{_msg(translator, 'chrome_profile.using_saved', 'Using saved profile: {profile}', profile=_profile_label(profile_dir, display_name))}"
                f"{Style.RESET_ALL}"
            )
            return profile_dir, display_name
    return select_profile(translator, allow_exit=allow_exit)


def select_chrome_profile(translator=None, **kwargs) -> tuple[str, str] | None:
    """Menu 2 entry: pick and persist default Chrome profile for MiMo login."""
    picked = select_profile(translator, **kwargs)
    if not picked:
        return None
    profile_dir, display_name = picked
    if save_selected_profile(profile_dir, display_name, translator):
        print(
            f"{Fore.GREEN}{EMOJI['SUCCESS']} "
            f"{_msg(translator, 'chrome_profile.saved_default', 'Default profile saved: {profile}', profile=_profile_label(profile_dir, display_name))}"
            f"{Style.RESET_ALL}"
        )
    return picked


def run(translator=None) -> bool:
    """Interactive menu action: select + save default Chrome profile."""
    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'chrome_profile.title', 'Chrome Profile Selection')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    result = select_chrome_profile(translator)
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")
    return result is not None


def setup_browser(translator=None, profile_dir: str | None = None) -> ChromiumPage | None:
    """Launch Chrome with a profile; prompts for selection if profile_dir omitted."""
    user_data_dir = get_user_data_directory()
    chrome_path = get_browser_path()
    if not chrome_path:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'oauth.no_compatible_browser_found', 'No compatible browser found')}{Style.RESET_ALL}")
        return None

    if not profile_dir:
        if not should_keep_cursor_running():
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'chrome_profile.warning_chrome_close', 'Warning: closes Chrome processes')}{Style.RESET_ALL}")
            if input(f"{Fore.YELLOW}{_msg(translator, 'menu.continue_prompt', 'Continue? (y/N): ')} {Style.RESET_ALL}").lower() != "y":
                return None
            kill_browser_processes()
        picked = resolve_profile_for_login(translator)
        if not picked:
            return None
        profile_dir, _ = picked
    else:
        if not should_keep_cursor_running():
            kill_browser_processes()

    co = configure_browser_options(chrome_path, user_data_dir, profile_dir)
    return ChromiumPage(co)


class ChromeProfileSession:
    """Short-lived Chrome session bound to one profile directory."""

    def __init__(self, profile_dir: str, translator=None):
        self.profile_dir = profile_dir
        self.translator = translator
        self.browser: ChromiumPage | None = None

    def open_url(self, url: str, *, force_prepare: bool = True) -> bool:
        if force_prepare:
            prepare_profile_for_oauth(self.translator)
        user_data_dir = get_user_data_directory()
        chrome_path = get_browser_path()
        if not chrome_path:
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(self.translator, 'oauth.no_compatible_browser_found', 'No compatible browser found')}{Style.RESET_ALL}")
            return False

        # Prefer native Chrome launch — DrissionPage often fails when profile is locked.
        if open_url_via_subprocess(url, self.profile_dir, self.translator):
            return True

        try:
            co = configure_browser_options(chrome_path, user_data_dir, self.profile_dir)
            self.browser = ChromiumPage(co)
            self.browser.get(url)
            return True
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(self.translator, 'chrome_profile.drission_failed', 'DrissionPage failed: {error}', error=str(exc))}{Style.RESET_ALL}")
            return open_url_via_subprocess(url, self.profile_dir, self.translator)

    def close(self) -> None:
        if self.browser:
            try:
                self.browser.quit()
            except Exception:
                pass
            self.browser = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
