"""MiMo Platform login via mimo CLI + Chrome profile, with API-key fallback."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from colorama import Fore, Style, init

from branding import cli_process_env
import icons as _icons
from chrome_profile import ChromeProfileSession, resolve_profile_for_login, save_selected_profile
from mimo_account_slots import activate_slot, create_slot_from_auth, extract_xiaomi_meta
from mimo_auth import write_xiaomi_auth
from mimo_paths import get_mimo_auth_path

init()

EMOJI = {
    "SUCCESS": _icons.SUCCESS,
    "ERROR": _icons.ERROR,
    "INFO": _icons.INFO,
    "WARNING": _icons.WARNING,
    "OAUTH": _icons.OAUTH,
}

# Phase 0 spike: platform.xiaomimimo.com/authorize?pk=...&redirect_uri=...
OAUTH_URL_RE = re.compile(
    r"https://platform\.xiaomimimo\.com/authorize\?[^\s\|\"\'<>]+",
    re.IGNORECASE,
)
OAUTH_URL_FALLBACK_RE = re.compile(
    r"https://[^\s\|\"\'<>]*xiaomi[^\s\|\"\'<>]*",
    re.IGNORECASE,
)
LOGIN_TIMEOUT_SEC = 120
URL_CAPTURE_TIMEOUT_SEC = 45


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def resolve_mimo_cmd() -> str:
    """Resolve mimo.cmd from repo mimo/ bundle."""
    root = Path(__file__).resolve().parent
    candidates = [
        root / "mimo" / "node_modules" / ".bin" / "mimo.cmd",
        root / "mimo" / "node_modules" / ".bin" / "mimo",
    ]
    if sys.platform == "win32":
        for path in candidates:
            if path.suffix == ".cmd" and path.is_file():
                return str(path)
    for path in candidates:
        if path.is_file():
            return str(path)
    raise FileNotFoundError("mimo CLI not found — run npm install in mimo/")


def _read_auth_mtime() -> float | None:
    path = get_mimo_auth_path()
    if os.path.isfile(path):
        return os.path.getmtime(path)
    return None


def _auth_has_xiaomi_key(before_mtime: float | None = None) -> bool:
    path = get_mimo_auth_path()
    if not os.path.isfile(path):
        return False
    if before_mtime is not None and os.path.getmtime(path) <= before_mtime:
        return False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return bool(data.get("xiaomi", {}).get("key"))
    except (json.JSONDecodeError, OSError):
        return False


def _stream_reader(pipe, sink: list[str]) -> None:
    try:
        for line in iter(pipe.readline, ""):
            sink.append(line)
    finally:
        pipe.close()


def extract_oauth_url(lines: list[str]) -> str | None:
    """Parse OAuth authorize URL from mimo CLI log lines."""
    for line in lines:
        match = OAUTH_URL_RE.search(line)
        if match:
            return match.group(0).rstrip("|").strip().rstrip(",")
        match = OAUTH_URL_FALLBACK_RE.search(line)
        if match:
            url = match.group(0).rstrip("|").strip().rstrip(",")
            # Skip bare localhost callback lines, not authorize URLs with redirect_uri=127.0.0.1
            if url.startswith(("http://127.0.0.1", "https://127.0.0.1")):
                continue
            if "authorize" in url.lower() or "xiaomimimo" in url.lower():
                return url
    return None


def _scan_lines_for_url(lines: list[str], verbose: bool) -> str | None:
    oauth_url = extract_oauth_url(lines)
    if oauth_url and verbose:
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} OAuth URL captured{Style.RESET_ALL}")
    return oauth_url


def run_providers_login(
    *,
    timeout: int = URL_CAPTURE_TIMEOUT_SEC,
    verbose: bool = True,
    lang: str | None = None,
) -> tuple[str | None, int, list[str]]:
    """Start `mimo providers login -p xiaomi`; return (oauth_url, exit_code, log_lines).

    Returns as soon as the OAuth URL appears in CLI output (does not wait for auth).
    """
    cmd = [
        resolve_mimo_cmd(),
        "providers", "login", "-p", "xiaomi",
        "--print-logs", "--log-level", "INFO",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).resolve().parent / "mimo"),
        bufsize=1,
        env=cli_process_env(lang),
    )

    lines: list[str] = []
    reader = threading.Thread(target=_stream_reader, args=(proc.stdout, lines), daemon=True)
    reader.start()

    oauth_url: str | None = None
    deadline = time.time() + timeout
    printed = 0
    while time.time() < deadline:
        if verbose and printed < len(lines):
            for line in lines[printed:]:
                print(line, end="")
            printed = len(lines)
        if not oauth_url:
            oauth_url = _scan_lines_for_url(lines, verbose=False)
            if oauth_url:
                if verbose:
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} OAuth URL captured{Style.RESET_ALL}")
                break
        if proc.poll() is not None:
            break
        time.sleep(0.2)

    reader.join(timeout=1)
    if not oauth_url:
        oauth_url = extract_oauth_url(lines)

    # CLI keeps listening for callback; detach so browser step is not blocked.
    if proc.poll() is None and oauth_url:
        threading.Thread(target=proc.wait, daemon=True).start()
    elif proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except (subprocess.TimeoutExpired, OSError):
            try:
                proc.kill()
            except OSError:
                pass

    return oauth_url, proc.returncode or 0, lines


def login_with_api_key(api_key: str, translator=None) -> dict:
    path = write_xiaomi_auth(api_key)
    return create_slot_from_auth(path, label="api-key", activate=True)


def run_platform_login(translator=None) -> bool:
    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['OAUTH']} {_msg(translator, 'mimo_login.title', 'MiMo Platform Login (Chrome profile)')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"1. {_msg(translator, 'mimo_login.chrome', 'Chrome profile + OAuth (recommended)')}")
    print(f"2. {_msg(translator, 'mimo_login.api_key', 'Paste API key (fallback)')}")
    print(f"0. {_msg(translator, 'menu.exit', 'Exit')}")

    mode = input(f"\n{EMOJI['INFO']} {_msg(translator, 'menu.input_choice', 'Please enter your choice ({choices})', choices='0-2')}: ").strip()
    if mode == "0":
        return False
    if mode == "2":
        key = input(f"{EMOJI['INFO']} {_msg(translator, 'mimo_login.paste_key', 'Xiaomi API key')}: ").strip()
        if not key:
            return False
        result = login_with_api_key(key, translator)
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_login.slot_saved', 'Slot {id} saved & activated', id=result['slot_id'])}{Style.RESET_ALL}")
        return True

    picked = resolve_profile_for_login(translator)
    if not picked:
        return False
    profile_dir, display_name = picked
    save_selected_profile(profile_dir, display_name, translator)

    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_login.starting_cli', 'Starting mimo providers login...')}{Style.RESET_ALL}")
    oauth_url, exit_code, log_tail = run_providers_login(
        lang=getattr(translator, "current_language", None) if translator else None,
    )
    if not oauth_url:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_login.no_url', 'OAuth URL not found in CLI output (exit {code})', code=exit_code)}{Style.RESET_ALL}")
        if log_tail:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} Last CLI lines:{Style.RESET_ALL}")
            for line in log_tail[-8:]:
                print(f"  {line.rstrip()}")
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_login.fallback_hint', 'Try option 2 (paste API key) or open mimo providers login manually')}{Style.RESET_ALL}")
        manual = input(f"{Fore.CYAN}{_msg(translator, 'mimo_login.paste_url', 'Paste OAuth URL manually (Enter to cancel): ')}{Style.RESET_ALL}").strip()
        if manual.startswith("http"):
            oauth_url = manual
        else:
            return False

    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_login.opening_browser', 'Opening OAuth URL in Chrome profile {profile}...', profile=profile_dir)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {oauth_url}{Style.RESET_ALL}")

    from chrome_profile import prepare_profile_for_oauth

    prepare_profile_for_oauth(translator)
    session = ChromeProfileSession(profile_dir, translator)
    try:
        opened = session.open_url(oauth_url, force_prepare=False)
        if not opened:
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_login.browser_failed', 'Could not open Chrome — paste URL into your profile manually')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  {oauth_url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_login.complete_in_browser', 'Complete login in browser (timeout {sec}s)...', sec=LOGIN_TIMEOUT_SEC)}{Style.RESET_ALL}")
        deadline = time.time() + LOGIN_TIMEOUT_SEC
        before_mtime = _read_auth_mtime()
        while time.time() < deadline:
            if _auth_has_xiaomi_key(before_mtime):
                break
            time.sleep(1)
    finally:
        session.close()

    if not _auth_has_xiaomi_key():
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_login.timeout', 'Login timed out — auth.json not updated')}{Style.RESET_ALL}")
        return False

    default_label = display_name or profile_dir
    label = input(f"{EMOJI['INFO']} {_msg(translator, 'mimo_login.label_prompt', 'Account label', )} [{default_label}]: ").strip() or default_label
    result = create_slot_from_auth(
        label=label,
        chrome_profile=profile_dir,
        chrome_display_name=display_name,
        activate=True,
    )
    meta = extract_xiaomi_meta(json.load(open(get_mimo_auth_path(), encoding="utf-8")))
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_login.done', 'Slot {id} — uid={uid} key={key}', id=result['slot_id'], uid=meta['uid'], key=meta['key_prefix'])}{Style.RESET_ALL}")
    return True


def run(translator=None):
    try:
        run_platform_login(translator)
    except Exception as exc:
        print(f"{Fore.RED}{EMOJI['ERROR']} {exc}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
