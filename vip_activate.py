"""Activate local VIP/Pro flags and patch Cursor UI."""
from colorama import Fore, Style, init
from cursor_auth import CursorAuth
from workbench_patches import apply_workbench_patches
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path
import os
import shutil
import tempfile
from datetime import datetime

init()

EMOJI = {
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "RESET": "🔄",
}


def patch_workbench_vip(translator=None):
    workbench_path = get_cursor_workbench_path(get_resolved_cursor_app_path())
    if not workbench_path:
        raise FileNotFoundError("workbench.desktop.main.js not found")

    with open(workbench_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    patched, applied = apply_workbench_patches(content)
    changed = patched != content
    if not changed:
        if not os.environ.get("CURSOR_FREE_VIP_QUIET"):
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {translator.get('vip.no_ui_changes') if translator else 'VIP UI patterns already applied or not found'}{Style.RESET_ALL}")
        return True

    if not os.environ.get("CURSOR_FREE_VIP_QUIET"):
        print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('vip.patches_applied', count=applied) if translator else f'Applied {applied} patches'}{Style.RESET_ALL}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{workbench_path}.vip.{timestamp}.bak"
    shutil.copy2(workbench_path, backup_path)

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", errors="ignore", delete=False) as tmp:
        tmp.write(patched)
        tmp_path = tmp.name
    shutil.move(tmp_path, workbench_path)
    if not os.environ.get("CURSOR_FREE_VIP_QUIET"):
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('vip.workbench_patched') if translator else 'VIP UI patched'}: {workbench_path}{Style.RESET_ALL}")
    return True


def activate_vip_membership(translator=None):
    auth = CursorAuth(translator)
    if not hasattr(auth, 'db_path') or not auth.db_path:
        return False
    updates = [
        ("cursorAuth/stripeMembershipType", "pro"),
        ("cursorAuth/stripeSubscriptionStatus", "active"),
    ]
    if not auth._write_updates(updates):
        return False
    auth._sync_storage_json(updates)
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('vip.membership_activated') if translator else 'VIP membership activated locally'}{Style.RESET_ALL}")
    return True


def run(translator=None):
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['RESET']} {translator.get('vip.title') if translator else 'Activate VIP Account'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    ok = activate_vip_membership(translator)
    try:
        patch_workbench_vip(translator)
    except PermissionError:
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {translator.get('vip.file_locked') if translator else 'File locked while Cursor is running; restart Cursor after closing it once to apply UI patch.'}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} {e}{Style.RESET_ALL}")
        ok = False
    if ok:
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {translator.get('vip.reload_hint') if translator else 'Reload Cursor: Ctrl+Shift+P -> Developer: Reload Window'}{Style.RESET_ALL}")
    return ok
