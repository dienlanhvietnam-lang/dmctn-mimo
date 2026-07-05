"""Internal Cursor Pro membership + workbench patches (used by reset/register flows)."""
from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime

from colorama import Fore, Style, init

from branding import env_flag
from cursor_auth import CursorAuth
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path
from workbench_patches import apply_workbench_patches

init()

EMOJI = {
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "RESET": "🔄",
}


def patch_workbench_pro(translator=None):
    workbench_path = get_cursor_workbench_path(get_resolved_cursor_app_path())
    if not workbench_path:
        raise FileNotFoundError("workbench.desktop.main.js not found")

    with open(workbench_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    patched, applied = apply_workbench_patches(content)
    changed = patched != content
    if not changed:
        if not env_flag("QUIET", legacy_env="DMCTN_MIMO_QUIET"):
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {translator.get('pro.no_ui_changes') if translator else 'Pro UI patterns already applied or not found'}{Style.RESET_ALL}")
        return True

    if not env_flag("QUIET", legacy_env="DMCTN_MIMO_QUIET"):
        print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('pro.patches_applied', count=applied) if translator else f'Applied {applied} patches'}{Style.RESET_ALL}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{workbench_path}.pro.{timestamp}.bak"
    shutil.copy2(workbench_path, backup_path)

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", errors="ignore", delete=False) as tmp:
        tmp.write(patched)
        tmp_path = tmp.name
    shutil.move(tmp_path, workbench_path)
    if not env_flag("QUIET", legacy_env="DMCTN_MIMO_QUIET"):
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('pro.workbench_patched') if translator else 'Pro UI patched'}: {workbench_path}{Style.RESET_ALL}")
    return True


def activate_pro_membership(translator=None):
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
    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('pro.membership_activated') if translator else 'Pro membership activated locally'}{Style.RESET_ALL}")
    return True
