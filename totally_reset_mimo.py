"""Totally reset MiMo CLI: wipe DB, memory, sessions, then new machine identity."""
from __future__ import annotations

import errno
import os
import shutil
import stat
import sys
import time
from datetime import datetime

from colorama import Fore, Style, init

from mimo_paths import (
    get_mimo_data_dir,
    get_mimo_database_files,
    get_mimo_deep_wipe_extra,
    get_mimo_identity_files,
    get_mimo_protected_dirs,
    get_mimo_wipe_dirs,
    get_mimo_wipe_files,
)
from mimo_account_slots import backup_active_auth_to_slot, has_xiaomi_auth
from reset_mimo_machine import EMOJI, _msg, reset_mimo_machine
from mimo_auth import finish_mimo_reset_guidance

init()

MIMO_PROCESS_NAMES = ("mimo.exe", "mimo", "mimocode.exe", "mimocode")


def quit_mimo_processes(translator=None, timeout: int = 8) -> int:
    """Terminate running MiMo / MiMoCode processes."""
    try:
        import psutil
    except ImportError:
        return 0

    killed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if name not in MIMO_PROCESS_NAMES:
                continue
            proc.terminate()
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        msg = _msg(translator, "mimo_total.quit_mimo", "Closing {count} MiMo process(es)...", count=killed)
        print(f"{Fore.CYAN}{EMOJI['INFO']} {msg}{Style.RESET_ALL}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            alive = False
            for proc in psutil.process_iter(["name"]):
                try:
                    if (proc.info.get("name") or "").lower() in MIMO_PROCESS_NAMES:
                        alive = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if not alive:
                break
            time.sleep(0.4)

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in MIMO_PROCESS_NAMES:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return killed


def _chmod_writable(path: str) -> None:
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass


def _rmtree_onerror(func, path, exc_info):
    exc = exc_info[1]
    if isinstance(exc, PermissionError) or getattr(exc, "errno", None) in (errno.EACCES, errno.EPERM):
        _chmod_writable(path)
        func(path)
        return
    raise exc


def _backup_path(src: str, backup_dir: str) -> None:
    if not os.path.exists(src):
        return
    dest = os.path.join(backup_dir, os.path.basename(src))
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dest)
    except OSError as exc:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} backup skip {os.path.basename(src)}: {exc}{Style.RESET_ALL}")


def _remove_path(path: str) -> None:
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=_rmtree_onerror)
    else:
        _chmod_writable(path)
        os.remove(path)


def totally_reset_mimo(
    translator=None,
    *,
    deep: bool = False,
    wipe_vault: bool | None = None,
    auto_snapshot: bool | None = None,
    auto_restore: bool | None = None,
    skip_prompts: bool = False,
) -> bool:
    data_dir = get_mimo_data_dir()
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    if deep:
        print(f"{Fore.CYAN}{EMOJI['RESET']} {_msg(translator, 'mimo_deep.title', 'Deep Reset MiMo CLI (slots + config)')}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}{EMOJI['RESET']} {_msg(translator, 'mimo_total.title', 'Totally Reset MiMo CLI')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")

    if deep:
        print(f"{Fore.RED}{EMOJI['WARNING']} {_msg(translator, 'mimo_deep.warning', 'Deletes ALL slots, .config/mimocode, DB, memory, sessions, and auth. Cannot undo except from backup.')}{Style.RESET_ALL}")
        if not skip_prompts:
            confirm = input(f"{Fore.RED}{_msg(translator, 'mimo_deep.confirm', 'Type YES to confirm deep reset: ')}{Style.RESET_ALL}").strip()
            if confirm != "YES":
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_deep.cancelled', 'Deep reset cancelled.')}{Style.RESET_ALL}")
                return False
    else:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_total.warning', 'This deletes mimocode.db, memory, sessions, and auth. Cannot undo except from backup.')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_total.accounts_protected', 'Protected: {dirs} (Pro account slots kept)', dirs=', '.join(get_mimo_protected_dirs()))}{Style.RESET_ALL}")

    auth_path = get_mimo_identity_files()["auth.json"]
    if not deep and has_xiaomi_auth(auth_path):
        try:
            backup = backup_active_auth_to_slot()
            if backup:
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_total.slot_backup', 'Pro auth backed up to slot {id}', id=backup['slot_id'])}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} slot backup: {exc}{Style.RESET_ALL}")

    quit_mimo_processes(translator)

    # Optional context snapshot before wipe
    snapshot_id = None
    try:
        from mimo_context_vault import create_context_snapshot, has_local_context

        do_snap = auto_snapshot
        if do_snap is None and not skip_prompts and has_local_context():
            ans = input(f"{Fore.CYAN}{_msg(translator, 'mimo_total.snapshot_prompt', 'Snapshot local context to Context Vault before wipe? (Y/n): ')}{Style.RESET_ALL}").strip().lower()
            do_snap = ans != "n"
        elif do_snap is None:
            do_snap = False
        if do_snap and has_local_context():
            result = create_context_snapshot(label=f"pre-total-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            snapshot_id = result["slot_id"]
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.snapshot_ok', 'Context snapshot: {id}', id=snapshot_id)}{Style.RESET_ALL}")
    except Exception as exc:
        print(f"{Fore.YELLOW}{EMOJI['WARNING']} context snapshot: {exc}{Style.RESET_ALL}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_label = "mimo_deep" if deep else "mimo_total"
    backup_dir = os.path.join(data_dir, f"backup_{backup_label}_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"{Fore.YELLOW}{EMOJI['BACKUP']} {_msg(translator, 'mimo_total.backup', 'Backup: {path}', path=backup_dir)}{Style.RESET_ALL}")

    targets = get_mimo_database_files() + get_mimo_wipe_files()
    for directory in get_mimo_wipe_dirs():
        targets.append(directory)
    if deep:
        targets.extend(get_mimo_deep_wipe_extra())
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_deep.extra', 'Also removing: accounts/ + .config/mimocode (if separate)')}{Style.RESET_ALL}")

    # De-duplicate while preserving order
    seen: set[str] = set()
    unique_targets: list[str] = []
    for path in targets:
        norm = os.path.normcase(os.path.abspath(path))
        if norm in seen:
            continue
        seen.add(norm)
        unique_targets.append(path)
    targets = unique_targets

    removed = 0
    failed: list[str] = []
    for path in targets:
        if not os.path.exists(path):
            continue
        rel = os.path.relpath(path, data_dir)
        _backup_path(path, backup_dir)
        try:
            _remove_path(path)
            removed += 1
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_total.removed', 'Removed: {path}', path=rel)}{Style.RESET_ALL}")
        except OSError as exc:
            failed.append(f"{rel}: {exc}")
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_total.remove_failed', 'Could not remove: {path}', path=rel)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  {exc}{Style.RESET_ALL}")

    # Deep reset: optional vault wipe (default keep)
    do_wipe_vault = wipe_vault
    if deep and do_wipe_vault is None and not skip_prompts:
        ans = input(f"{Fore.YELLOW}{_msg(translator, 'mimo_deep.wipe_vault_prompt', 'Also wipe Context Vault (.dmctn-mimo/context)? (y/N): ')}{Style.RESET_ALL}").strip().lower()
        do_wipe_vault = ans == "y"
    if deep and do_wipe_vault:
        try:
            from mimo_context_vault import wipe_context_vault

            n = wipe_context_vault()
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_deep.vault_wiped', 'Context Vault wiped ({count} slots)', count=n)}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} vault wipe: {exc}{Style.RESET_ALL}")
    elif deep:
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_deep.vault_kept', 'Context Vault kept (use menu 8 to restore)')}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_total.identity', 'Applying new machine identity + registry...')}{Style.RESET_ALL}")
    reset_mimo_machine(translator, clear_auth=True, skip_backup=True, skip_slot_backup=deep)

    # Optional restore after wipe
    do_restore = auto_restore
    if do_restore is None and not skip_prompts and snapshot_id:
        ans = input(f"{Fore.CYAN}{_msg(translator, 'mimo_total.restore_prompt', 'Restore context from vault after reset? (Y/n): ')}{Style.RESET_ALL}").strip().lower()
        do_restore = ans != "n"
    if do_restore and snapshot_id:
        try:
            from mimo_context_vault import restore_context_snapshot

            restore_context_snapshot(snapshot_id)
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.restore_ok', 'Local context restored: {id}', id=snapshot_id)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_context.local_only_disclaimer', 'Local context only')}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} context restore: {exc}{Style.RESET_ALL}")

    if failed:
        print(f"\n{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_total.partial', 'Some paths locked (close MiMo and retry or delete manually):')}{Style.RESET_ALL}")
        for item in failed:
            print(f"{Fore.YELLOW}  - {item}{Style.RESET_ALL}")

    done_key = "mimo_deep.done" if deep else "mimo_total.done"
    done_fallback = (
        "Deep reset complete ({count} items removed). Re-login via menu 5."
        if deep
        else "Totally reset complete ({count} items removed). Run mimo/start.bat again."
    )
    print(f"\n{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, done_key, done_fallback, count=removed)}{Style.RESET_ALL}")
    finish_mimo_reset_guidance(translator)
    return not failed


def run(translator=None):
    try:
        totally_reset_mimo(translator)
    except Exception as exc:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'menu.error_occurred', 'Error: {error}', error=str(exc))}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


def run_deep(translator=None):
    try:
        totally_reset_mimo(translator, deep=True)
    except Exception as exc:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'menu.error_occurred', 'Error: {error}', error=str(exc))}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
