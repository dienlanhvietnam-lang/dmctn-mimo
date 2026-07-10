"""Shared machine ID helpers for MiMo resets."""
from __future__ import annotations

import hashlib
import os
import secrets
import sys
import uuid


def generate_mimo_client_ids() -> dict[str, str]:
    """Generate MiMo anonymous client identity files."""
    installation_id = str(uuid.uuid4())
    return {
        "installation_id": installation_id,
        "mimo-free-client": hashlib.sha256(os.urandom(32)).hexdigest(),
        "mimo-key-name": f"mimo-code-cli-key-{secrets.token_hex(4)}",
    }


def update_windows_machine_guid() -> str:
    """Update HKLM MachineGuid. Requires administrator on Windows."""
    if sys.platform != "win32":
        raise OSError("Windows only")
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Cryptography",
        0,
        winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY,
    )
    new_guid = str(uuid.uuid4())
    winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, new_guid)
    winreg.CloseKey(key)
    return new_guid


def update_windows_sqm_machine_id() -> str:
    """Update HKLM SQMClient MachineId. Requires administrator on Windows."""
    if sys.platform != "win32":
        raise OSError("Windows only")
    import winreg

    new_guid = "{" + str(uuid.uuid4()).upper() + "}"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\SQMClient",
            0,
            winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY,
        )
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\SQMClient")
    winreg.SetValueEx(key, "MachineId", 0, winreg.REG_SZ, new_guid)
    winreg.CloseKey(key)
    return new_guid


def update_system_machine_ids(translator=None) -> dict[str, str]:
    """Update OS-level machine identifiers where supported."""
    results: dict[str, str] = {}
    if sys.platform == "win32":
        try:
            results["windows.MachineGuid"] = update_windows_machine_guid()
        except PermissionError as exc:
            msg = translator.get("reset.permission_denied") if translator else str(exc)
            raise PermissionError(msg) from exc
        sqm = update_windows_sqm_machine_id()
        if sqm:
            results["windows.SQMClient.MachineId"] = sqm
    elif sys.platform == "darwin":
        mac_machine_id = hashlib.sha512(os.urandom(64)).hexdigest()
        uuid_file = "/var/root/Library/Preferences/SystemConfiguration/com.apple.platform.uuid.plist"
        if os.path.exists(uuid_file):
            cmd = (
                f'sudo plutil -replace "UUID" -string "{mac_machine_id}" "{uuid_file}"'
            )
            if os.system(cmd) != 0:
                raise RuntimeError("plutil failed")
            results["macos.platform.uuid"] = mac_machine_id
    return results
