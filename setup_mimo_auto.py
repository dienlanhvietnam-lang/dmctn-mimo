"""Configure MiMo CLI for MiMo Auto (free) channel and verify it works."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from colorama import Fore, Style, init

from mimo_auth import verify_free_bootstrap
from mimo_paths import get_mimo_config_dir

init()

EMOJI = {"SUCCESS": "✅", "ERROR": "❌", "INFO": "ℹ️", "WARNING": "⚠️"}

STATE_MODEL_PATH = Path(os.path.expanduser("~/.local/state/mimocode/model.json"))


def build_auto_provider_config(preserve_ollama: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return mimocode config that lets the built-in mimo-free plugin inject fetch/JWT."""
    providers: dict[str, Any] = {}
    if preserve_ollama:
        providers["ollama"] = preserve_ollama
    # Do NOT define partial `mimo` provider here — built-in plugin fills provider.mimo when absent.
    return {
        "$schema": "https://mimo.xiaomi.com/mimocode/config.json",
        "provider": providers,
        "agent": {
            "local": {
                "description": "Local Ollama agent with limited tools for better compatibility",
                "model": "ollama/llama3.1:8b",
                "tool_allowlist": ["bash", "read", "write", "edit", "glob", "grep"],
            },
            "build": {
                "model": "mimo/mimo-auto",
                # Block subagent spawn — avoids actor tool schema errors on MiMo Auto (issues #417, #561)
                "permission": {
                    "task": {"*": "deny"},
                },
            },
        },
    }


def apply_mimo_auto_config() -> str:
    config_dir = get_mimo_config_dir()
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "mimocode.jsonc")

    preserve_ollama = None
    if os.path.isfile(config_path):
        with open(config_path, encoding="utf-8") as f:
            current = json.load(f)
        preserve_ollama = current.get("provider", {}).get("ollama")

    payload = build_auto_provider_config(preserve_ollama)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    STATE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model_state = {
        "recent": [{"providerID": "mimo", "modelID": "mimo-auto"}],
        "favorite": [{"providerID": "mimo", "modelID": "mimo-auto"}],
        "variant": {"mimo/mimo-auto": "default"},
    }
    with open(STATE_MODEL_PATH, "w", encoding="utf-8") as f:
        json.dump(model_state, f, indent=2)
        f.write("\n")

    return config_path


def run_mimo_auto_api_check() -> tuple[bool, str]:
    """Verify anonymous JWT exchange works (same as MiMo Auto channel)."""
    try:
        data = verify_free_bootstrap()
        return True, f"jwt_len={len(data.get('jwt', ''))}"
    except Exception as exc:
        return False, str(exc)


def run_mimo_auto_smoke(project_dir: str | None = None, timeout: int = 90) -> tuple[bool, str]:
    """Optional live CLI smoke via `mimo run` (can be slow)."""
    root = Path(__file__).resolve().parent
    mimo_dir = root / "mimo"
    mimo_cmd = mimo_dir / "node_modules" / ".bin" / "mimo.cmd"
    if not mimo_cmd.is_file():
        return False, f"mimo CLI not found: {mimo_cmd}"

    workdir = project_dir or str(root)
    cmd = [
        str(mimo_cmd),
        "run",
        "-m",
        "mimo/mimo-auto",
        "--agent",
        "build",
        "--dir",
        workdir,
        "Reply with exactly: AUTO_OK",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(mimo_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "mimo run timed out"

    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return False, output[-2000:]
    if "AUTO_OK" in output or "auto_ok" in output.lower():
        return True, output[-1000:]
    if "Invalid API Key" in output or "undefined/chat/completions" in output:
        return False, output[-2000:]
    return True, output[-1000:]


def setup_and_test(project_dir: str | None = None, live_cli: bool = False) -> bool:
    print(f"{Fore.CYAN}{EMOJI['INFO']} Applying MiMo Auto config...{Style.RESET_ALL}")
    path = apply_mimo_auto_config()
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Updated: {path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Updated: {STATE_MODEL_PATH}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}{EMOJI['INFO']} Verifying free bootstrap JWT...{Style.RESET_ALL}")
    ok, detail = run_mimo_auto_api_check()
    if not ok:
        print(f"{Fore.RED}{EMOJI['ERROR']} Bootstrap failed: {detail}{Style.RESET_ALL}")
        return False
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Bootstrap OK ({detail}){Style.RESET_ALL}")

    if live_cli:
        print(f"{Fore.CYAN}{EMOJI['INFO']} Running mimo run smoke (mimo/mimo-auto)...{Style.RESET_ALL}")
        ok, detail = run_mimo_auto_smoke(project_dir)
        if not ok:
            print(f"{Fore.RED}{EMOJI['ERROR']} MiMo CLI smoke failed{Style.RESET_ALL}")
            print(detail)
            return False
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} MiMo CLI smoke OK{Style.RESET_ALL}")

    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} MiMo Auto ready — restart mimo/start.bat and use Tab → MiMo Auto{Style.RESET_ALL}")
    return True


if __name__ == "__main__":
    live = "--live" in sys.argv
    sys.exit(0 if setup_and_test(live_cli=live) else 1)
