"""Reset MiMo CLI machine identity for anonymous / no-login usage.

Modes:
  - full_wipe_context: new client IDs + clear auth (default legacy behavior)
  - full_preserve_context: snapshot context → new IDs → restore context
  - registry_only: only Windows registry MachineGuid/SQM (keep client + memory)
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime

from colorama import Fore, Style, init

from machine_id_utils import generate_mimo_client_ids, update_system_machine_ids
from mimo_account_slots import backup_active_auth_to_slot, has_xiaomi_auth
from mimo_auth import finish_mimo_reset_guidance
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

MODE_FULL_WIPE = "full_wipe_context"
MODE_FULL_PRESERVE = "full_preserve_context"
MODE_REGISTRY_ONLY = "registry_only"


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


def _update_registry(translator=None) -> None:
    if sys.platform != "win32":
        return
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


def _apply_auto_config(translator=None) -> None:
    print(f"{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
    try:
        from setup_mimo_auto import apply_mimo_auto_config

        cfg_path = apply_mimo_auto_config()
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.auto_config', 'MiMo Auto config: {path}', path=cfg_path)}{Style.RESET_ALL}")
    except Exception as exc:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} auto config: {exc}{Style.RESET_ALL}")
    finish_mimo_reset_guidance(translator)


def _rotate_identity(
    translator=None,
    *,
    clear_auth: bool = True,
    skip_backup: bool = False,
    skip_slot_backup: bool = False,
) -> None:
    data_dir = get_mimo_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    identity_files = get_mimo_identity_files()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(data_dir, f"backup_mimo_reset_{timestamp}")
    if not skip_backup:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"{Fore.YELLOW}{EMOJI['BACKUP']} {_msg(translator, 'mimo_reset.backup', 'Backup: {path}', path=backup_dir)}{Style.RESET_ALL}")
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
                        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.slots_kept', 'Saved accounts remain in accounts/ — use menu 6 to activate')}{Style.RESET_ALL}")
                except Exception as exc:
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} slot backup: {exc}{Style.RESET_ALL}")
            if not skip_backup:
                _backup_file(auth_path, backup_dir)
            try:
                os.remove(auth_path)
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_reset.auth_cleared', 'Removed auth.json for fresh anonymous session')}{Style.RESET_ALL}")
            except OSError as exc:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} auth.json: {exc}{Style.RESET_ALL}")


def reset_mimo_machine(
    translator=None,
    clear_auth: bool = True,
    skip_backup: bool = False,
    skip_slot_backup: bool = False,
    *,
    mode: str = MODE_FULL_WIPE,
    skip_registry: bool = False,
) -> bool:
    """Reset machine identity. mode: full_wipe_context | full_preserve_context | registry_only."""
    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.start', 'Resetting MiMo machine identity...')}{Style.RESET_ALL}")

    if mode == MODE_REGISTRY_ONLY:
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.mode_registry_only', 'Mode: registry only (keep client ID + local context)')}{Style.RESET_ALL}")
        if not skip_registry:
            _update_registry(translator)
        else:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_reset.registry_skipped', 'Registry update skipped (test mode)')}{Style.RESET_ALL}")
        _apply_auto_config(translator)
        return True

    snapshot_id = None
    if mode == MODE_FULL_PRESERVE:
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.mode_preserve', 'Mode: full reset + preserve local context')}{Style.RESET_ALL}")
        try:
            from totally_reset_mimo import quit_mimo_processes

            quit_mimo_processes(translator)
        except Exception:
            pass
        try:
            from mimo_context_vault import create_context_snapshot, has_local_context

            if has_local_context():
                result = create_context_snapshot(label=f"pre-reset-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                snapshot_id = result["slot_id"]
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.snapshot_ok', 'Context snapshot: {id}', id=snapshot_id)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_context.nothing_to_snapshot', 'No local context to snapshot')}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} context snapshot: {exc}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.mode_wipe', 'Mode: full reset (context not preserved)')}{Style.RESET_ALL}")

    _rotate_identity(
        translator,
        clear_auth=clear_auth,
        skip_backup=skip_backup,
        skip_slot_backup=skip_slot_backup,
    )

    if not skip_registry:
        _update_registry(translator)
    else:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_reset.registry_skipped', 'Registry update skipped (test mode)')}{Style.RESET_ALL}")

    if mode == MODE_FULL_PRESERVE and snapshot_id:
        try:
            from mimo_context_vault import restore_context_snapshot

            restore_context_snapshot(snapshot_id)
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.restore_ok', 'Local context restored: {id}', id=snapshot_id)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_context.local_only_disclaimer', 'Local context only — MiMo Auto server may not remember the old session after client ID change.')}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} context restore: {exc}{Style.RESET_ALL}")

    _apply_auto_config(translator)
    return True


def _prompt_reset_mode(translator=None) -> str | None:
    print(f"\n{Fore.CYAN}1. {_msg(translator, 'mimo_reset.mode_preserve', 'Full reset + keep local context')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}2. {_msg(translator, 'mimo_reset.mode_wipe', 'Full reset + discard context')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}3. {_msg(translator, 'mimo_reset.mode_registry_only', 'Registry only (keep client ID + context)')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}0. {_msg(translator, 'menu.exit', 'Cancel')}{Style.RESET_ALL}")
    choice = input(f"\n{Fore.CYAN}{_msg(translator, 'menu.input_choice', 'Choice ({choices})', choices='0-3')}: {Style.RESET_ALL}").strip()
    if choice == "0":
        return None
    if choice == "1":
        return MODE_FULL_PRESERVE
    if choice == "2":
        return MODE_FULL_WIPE
    if choice == "3":
        return MODE_REGISTRY_ONLY
    print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'menu.invalid_choice', 'Invalid choice')}{Style.RESET_ALL}")
    return None


def run(translator=None):
    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['RESET']} {_msg(translator, 'mimo_reset.title', 'Reset MiMo Machine ID')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    mode = _prompt_reset_mode(translator)
    if mode is None:
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_reset.cancelled', 'Reset cancelled.')}{Style.RESET_ALL}")
    else:
        reset_mimo_machine(translator, mode=mode)
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
