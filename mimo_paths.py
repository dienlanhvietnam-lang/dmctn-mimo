"""Resolve MiMo CLI / MiMoCode local data paths."""
from __future__ import annotations

import os
import sys


def get_mimo_config_dir() -> str:
    if sys.platform == "win32":
        return os.path.join(os.getenv("USERPROFILE", os.path.expanduser("~")), ".config", "mimocode")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/mimocode")
    return os.path.expanduser("~/.config/mimocode")


def get_mimo_data_dir() -> str:
    if sys.platform == "win32":
        return os.path.join(os.getenv("USERPROFILE", os.path.expanduser("~")), ".local", "share", "mimocode")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/mimocode")
    return os.path.expanduser("~/.local/share/mimocode")


def get_mimo_identity_files() -> dict[str, str]:
    data_dir = get_mimo_data_dir()
    return {
        "installation_id": os.path.join(data_dir, "installation_id"),
        "mimo-free-client": os.path.join(data_dir, "mimo-free-client"),
        "mimo-key-name": os.path.join(data_dir, "mimo-key-name"),
        "auth.json": os.path.join(data_dir, "auth.json"),
    }


def get_mimo_auth_path() -> str:
    """Active auth.json path (alias for identity_files['auth.json'])."""
    return get_mimo_identity_files()["auth.json"]


def get_mimo_accounts_dir() -> str:
    return os.path.join(get_mimo_data_dir(), "accounts")


def get_mimo_manifest_path() -> str:
    return os.path.join(get_mimo_accounts_dir(), "manifest.json")


def get_mimo_protected_dirs() -> list[str]:
    """Directories preserved during MiMo total reset (Pro account slots)."""
    return ["accounts"]


def get_mimo_deep_wipe_extra() -> list[str]:
    """Extra paths wiped only by menu 7 (deep reset): slots + .config/mimocode."""
    extras = [get_mimo_accounts_dir()]
    config_dir = get_mimo_config_dir()
    data_dir = get_mimo_data_dir()
    if os.path.normcase(os.path.abspath(config_dir)) != os.path.normcase(os.path.abspath(data_dir)):
        extras.append(config_dir)
    return extras


def get_mimo_database_files() -> list[str]:
    data_dir = get_mimo_data_dir()
    return [
        os.path.join(data_dir, name)
        for name in ("mimocode.db", "mimocode.db-shm", "mimocode.db-wal")
    ]


def get_mimo_wipe_dirs() -> list[str]:
    data_dir = get_mimo_data_dir()
    protected = set(get_mimo_protected_dirs())
    return [
        os.path.join(data_dir, name)
        for name in ("memory", "storage", "snapshot", "plans", "log", "tool-output", "compose")
        if name not in protected
    ]


def get_mimo_wipe_files() -> list[str]:
    data_dir = get_mimo_data_dir()
    return [os.path.join(data_dir, "trusted-workspaces.json")]


def get_dmctn_protected_paths() -> list[str]:
    """DMCTN-owned paths that must never be wiped with mimocode data."""
    from mimo_context_paths import get_context_vault_dir

    return [get_context_vault_dir()]
