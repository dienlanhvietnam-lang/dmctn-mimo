"""MiMo free-channel bootstrap verify and optional xiaomi auth setup."""
from __future__ import annotations

import json
import os
from typing import Any

import requests
from colorama import Fore, Style

from mimo_paths import get_mimo_identity_files

MIMO_FREE_BOOTSTRAP_URL = "https://api.xiaomimimo.com/api/free-ai/bootstrap"

EMOJI = {
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
}


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def read_mimo_free_client() -> str:
    path = get_mimo_identity_files()["mimo-free-client"]
    if not os.path.isfile(path):
        raise FileNotFoundError(f"mimo-free-client not found: {path}")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def verify_free_bootstrap(client_id: str | None = None, timeout: int = 15) -> dict[str, Any]:
    """Exchange mimo-free-client for anonymous JWT (MiMo Auto channel)."""
    client_id = client_id or read_mimo_free_client()
    response = requests.post(
        MIMO_FREE_BOOTSTRAP_URL,
        json={"client": client_id},
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RuntimeError(f"bootstrap failed: HTTP {response.status_code} {response.text[:200]}")
    data = response.json()
    if not data.get("jwt"):
        raise RuntimeError("bootstrap response missing jwt")
    return data


def write_xiaomi_auth(api_key: str, base_url: str = "https://api.xiaomimimo.com/v1") -> str:
    """Write paid Xiaomi API credentials for models like mimo-v2.5-pro."""
    auth_path = get_mimo_identity_files()["auth.json"]
    payload: dict[str, Any] = {}
    if os.path.isfile(auth_path):
        with open(auth_path, encoding="utf-8") as f:
            payload = json.load(f)
    payload["xiaomi"] = {
        "type": "api",
        "key": api_key.strip(),
        "metadata": {"base_url": base_url.rstrip("/")},
    }
    os.makedirs(os.path.dirname(auth_path), exist_ok=True)
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return auth_path


def finish_mimo_reset_guidance(translator=None) -> None:
    """Verify MiMo Auto bootstrap and explain how to avoid 401 after auth wipe."""
    print(f"\n{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
    try:
        verify_free_bootstrap()
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.bootstrap_ok', 'MiMo Auto bootstrap OK (anonymous channel ready)')}{Style.RESET_ALL}")
    except Exception as exc:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_reset.bootstrap_fail', 'MiMo Auto bootstrap check failed: {error}', error=str(exc))}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.next_steps_title', 'Next steps in MiMo CLI:')}{Style.RESET_ALL}")
    print(f"  1. {_msg(translator, 'mimo_reset.next_auto', 'Press Tab → switch to MiMo Auto (free, no API key)')}")
    print(f"  2. {_msg(translator, 'mimo_reset.next_pro', 'MiMo-V2.5-Pro needs Xiaomi API key → run: mimo providers login')}")
    print(f"  3. {_msg(translator, 'mimo_reset.next_restart', 'Restart: mimo/start.bat')}")
    print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_reset.401_hint', '401 Invalid API Key = using Pro model without auth.json after reset')}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.done', 'MiMo machine reset complete.')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
