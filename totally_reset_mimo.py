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


def totally_reset_mimo(translator=None) -> bool:
    data_dir = get_mimo_data_dir()
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['RESET']} {_msg(translator, 'mimo_total.title', 'Totally Reset MiMo CLI')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_total.warning', 'This deletes mimocode.db, memory, sessions, and auth. Cannot undo except from backup.')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_total.accounts_protected', 'Protected: {dirs} (Pro account slots kept)', dirs=', '.join(get_mimo_protected_dirs()))}{Style.RESET_ALL}")

    auth_path = get_mimo_identity_files()["auth.json"]
    if has_xiaomi_auth(auth_path):
        try:
            backup = backup_active_auth_to_slot()
            if backup:
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_total.slot_backup', 'Pro auth backed up to slot {id}', id=backup['slot_id'])}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.YELLOW}{EMOJI['WARNING']} slot backup: {exc}{Style.RESET_ALL}")

    quit_mimo_processes(translator)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(data_dir, f"backup_mimo_total_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"{Fore.YELLOW}{EMOJI['BACKUP']} {_msg(translator, 'mimo_total.backup', 'Backup: {path}', path=backup_dir)}{Style.RESET_ALL}")

    targets = get_mimo_database_files() + get_mimo_wipe_files()
    for directory in get_mimo_wipe_dirs():
        targets.append(directory)

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

    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_total.identity', 'Applying new machine identity + registry...')}{Style.RESET_ALL}")
    reset_mimo_machine(translator, clear_auth=True, skip_backup=True)

    if failed:
        print(f"\n{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_total.partial', 'Some paths locked (close MiMo and retry or delete manually):')}{Style.RESET_ALL}")
        for item in failed:
            print(f"{Fore.YELLOW}  - {item}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_total.done', 'Totally reset complete ({count} items removed). Run mimo/start.bat again.', count=removed)}{Style.RESET_ALL}")
    finish_mimo_reset_guidance(translator)
    return not failed


def run(translator=None):
    try:
        totally_reset_mimo(translator)
    except Exception as exc:
        print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'menu.error_occurred', 'Error: {error}', error=str(exc))}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
