"""Restore Cursor install files to pre-patch state.

Run with Cursor CLOSED:
  python scripts/restore_cursor_original.py
  python scripts/restore_cursor_original.py --keep-backups
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_config
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

PATCH_MARKERS = [
    "this.refreshMembership=async()=>{return;",
    "i=cs.PRO,this.storageService.store(Hgt",
    "s=Vr.PRO,this.storageService.store(Zmt",
    "MiMo FREE",
    "Cursor Free Pro",
    "notifications-toasts hidden",
    "Bypass-Version-Pin",
    "async performFetch(n){return;",
    "async performFetch(e){return;",
    "/*je();*/",
    "/*We();*/",
    "/*CFV-NET-LAG*/",
]


def _score_clean(content: str) -> int:
    return sum(1 for m in PATCH_MARKERS if m in content)


def find_best_workbench_backup(workbench: Path) -> Path | None:
    candidates = []
    for path in workbench.parent.glob("workbench.desktop.main.js*"):
        if path.name == workbench.name:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        candidates.append((_score_clean(content), path.stat().st_size, path))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], -x[1]))
    return candidates[0][2]


def restore_workbench(workbench: Path) -> str:
    current = workbench.read_text(encoding="utf-8", errors="ignore")
    if _score_clean(current) == 0:
        return "workbench already clean"

    backup = find_best_workbench_backup(workbench)
    if not backup:
        raise FileNotFoundError("No workbench backup found to restore from")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(workbench, workbench.with_name(f"workbench.desktop.main.js.patched.{ts}.bak"))
    shutil.copy2(backup, workbench)
    return f"workbench restored from {backup.name}"


def restore_product_json(app_dir: Path) -> str:
    product = app_dir / "product.json"
    old = app_dir / "product.json.old"
    if not old.is_file():
        return "product.json: no .old backup"
    if product.read_text(encoding="utf-8") == old.read_text(encoding="utf-8"):
        return "product.json unchanged"
    shutil.copy2(product, product.with_suffix(".json.before_restore"))
    shutil.copy2(old, product)
    return "product.json restored from product.json.old"


def clear_pro_auth_flags() -> str:
    config = get_config()
    if not config:
        return "auth: config missing, skipped"

    if sys.platform == "win32":
        section = "WindowsPaths"
    elif sys.platform == "darwin":
        section = "MacPaths"
    else:
        section = "LinuxPaths"

    if not config.has_section(section):
        return "auth: paths missing, skipped"

    keys = ("cursorAuth/stripeMembershipType", "cursorAuth/stripeSubscriptionStatus")
    sqlite_path = config.get(section, "sqlite_path", fallback="")
    storage_path = config.get(section, "storage_path", fallback="")

    removed = []
    if sqlite_path and os.path.isfile(sqlite_path):
        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()
        for key in keys:
            cur.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
            if cur.rowcount:
                removed.append(f"sqlite:{key}")
        conn.commit()
        conn.close()

    if storage_path and os.path.isfile(storage_path):
        with open(storage_path, encoding="utf-8") as f:
            data = json.load(f)
        changed = False
        for key in keys:
            if key in data:
                del data[key]
                removed.append(f"storage:{key}")
                changed = True
        if changed:
            with open(storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    return "auth: removed " + ", ".join(removed) if removed else "auth: no Pro overrides found"


def cleanup_backups(workbench_dir: Path, keep: bool) -> str:
    if keep:
        return "backups kept"
    removed = 0
    for path in workbench_dir.glob("workbench.desktop.main.js*"):
        if path.name == "workbench.desktop.main.js":
            continue
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return f"removed {removed} workbench backup files"


def main():
    parser = argparse.ArgumentParser(description="Restore Cursor to original (remove patches)")
    parser.add_argument("--keep-backups", action="store_true", help="Keep .bak files after restore")
    parser.add_argument("--skip-auth", action="store_true", help="Do not clear local Pro auth flags")
    args = parser.parse_args()

    app_path = Path(get_resolved_cursor_app_path())
    workbench = Path(get_cursor_workbench_path(app_path))
    if not workbench.is_file():
        print(f"ERROR: workbench not found: {workbench}")
        return 1

    results = []
    try:
        results.append(restore_workbench(workbench))
    except Exception as e:
        print(f"ERROR workbench: {e}")
        return 1

    results.append(restore_product_json(app_path.parent))
    if not args.skip_auth:
        results.append(clear_pro_auth_flags())
    results.append(cleanup_backups(workbench.parent, args.keep_backups))

    content = workbench.read_text(encoding="utf-8", errors="ignore")
    markers = _score_clean(content)
    print("restore OK")
    for line in results:
        print(f"  - {line}")
    print(f"  - patch markers in workbench: {markers}")
    if markers:
        print("WARNING: workbench may still contain patches. Reinstall Cursor if needed.")
        return 1
    print("Restart Cursor: close fully, then reopen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
