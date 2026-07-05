"""Reset MiMo CLI machine identity for anonymous / no-login usage.

Updates:
  - ~/.local/share/mimocode/installation_id
  - ~/.local/share/mimocode/mimo-free-client   (telemetry.machineId equivalent)
  - ~/.local/share/mimocode/mimo-key-name
  - Windows Registry MachineGuid + SQMClient MachineId
  - Optional auth.json wipe for fresh anonymous channel
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime

from colorama import Fore, Style, init

from machine_id_utils import generate_mimo_client_ids, update_system_machine_ids
from mimo_account_slots import backup_active_auth_to_slot, has_xiaomi_auth
from mimo_auth import finish_mimo_reset_guidance, verify_free_bootstrap
from mimo_paths import get_mimo_data_dir, get_mimo_identity_files

init()

EMOJI = {
    "BACKUP": "💾",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "RESET": "🔄",
    "WARNING": "⚠️",
}


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def _backup_file(path: str, backup_dir: str) -> None:
    if not os.path.isfile(path):
        return
    name = os.path.basename(path)
    shutil.copy2(path, os.path.join(backup_dir, name))


def reset_mimo_machine(translator=None, clear_auth: bool = True, skip_backup: bool = False, skip_slot_backup: bool = False) -> bool:
    data_dir = get_mimo_data_dir()
    os.makedirs(data_dir, exist_ok=True)

    identity_files = get_mimo_identity_files()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(data_dir, f"backup_mimo_reset_{timestamp}")
    if not skip_backup:
        os.makedirs(backup_dir, exist_ok=True)

    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.start', 'Resetting MiMo machine identity...')}{Style.RESET_ALL}")
    if not skip_backup:
        print(f"{Fore.YELLOW}{EMOJI['BACKUP']} {_msg(translator, 'mimo_reset.backup', 'Backup: {path}', path=backup_dir)}{Style.RESET_ALL}")

    if not skip_backup:
        for path in identity_files.values():
            _backup_file(path, backup_dir)

    new_ids = generate_mimo_client_ids()

    for name, value in new_ids.items():
        target = identity_files[name]
        with open(target, "w", encoding="utf-8") as f:
            f.write(value)
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {name}: {value}{Style.RESET_ALL}")

    if clear_auth:
        auth_path = identity_files["auth.json"]
        if os.path.isfile(auth_path):
            if has_xiaomi_auth(auth_path) and not skip_slot_backup:
                try:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    slot = backup_active_auth_to_slot(label=f"auto-backup-before-reset-{ts}")
                    if slot:
                        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.auth_slot_backup', 'Backed up Pro auth to slot: {id}', id=slot['slot_id'])}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.slots_kept', 'Saved accounts remain in accounts/ — use menu 7 to activate')}{Style.RESET_ALL}")
                except Exception as exc:
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} slot backup: {exc}{Style.RESET_ALL}")
            if not skip_backup:
                _backup_file(auth_path, backup_dir)
            try:
                os.remove(auth_path)
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.auth_cleared', 'Removed auth.json for fresh anonymous session')}{Style.RESET_ALL}")
            except OSError as exc:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} auth.json: {exc}{Style.RESET_ALL}")

    if sys.platform == "win32":
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.registry', 'Updating Windows MachineGuid + SQMClient MachineId...')}{Style.RESET_ALL}")
        try:
            system_ids = update_system_machine_ids(translator)
            for key, value in system_ids.items():
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {key}: {value}{Style.RESET_ALL}")
        except PermissionError:
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_reset.admin_required', 'Need Administrator for registry. Re-run start.bat as Admin.')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_reset.partial_ok', 'MiMo local IDs updated; registry skipped.')}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.RED}{EMOJI['ERROR']} registry: {exc}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
    try:
        from setup_mimo_auto import apply_mimo_auto_config
        cfg_path = apply_mimo_auto_config()
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.auto_config', 'MiMo Auto config: {path}', path=cfg_path)}{Style.RESET_ALL}")
    except Exception as exc:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} auto config: {exc}{Style.RESET_ALL}")
    finish_mimo_reset_guidance(translator)
    return True


def run(translator=None):
    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['RESET']} {_msg(translator, 'mimo_reset.title', 'Reset MiMo Machine ID')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    reset_mimo_machine(translator)
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
