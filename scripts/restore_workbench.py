"""Emergency restore workbench.desktop.main.js (fix IDE hang).

Strips CFV-NET-LAG fetch hook or restores from latest clean backup.
Run with Cursor CLOSED:
  python scripts/restore_workbench.py
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

CFV_NET_LAG_MARKER = "/*CFV-NET-LAG*/"

MARKER_END = "})();"


def strip_net_lag(content: str) -> tuple[str, bool]:
    if CFV_NET_LAG_MARKER not in content:
        return content, False
    idx = content.find(CFV_NET_LAG_MARKER)
    end = content.find(MARKER_END, idx)
    if end < 0:
        return content, False
    return content[end + len(MARKER_END) :], True


def find_clean_backup(workbench_dir: Path) -> Path | None:
    candidates = []
    for path in workbench_dir.glob("workbench.desktop.main.js*"):
        if path.name == "workbench.desktop.main.js":
            continue
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:120]
        except OSError:
            continue
        if CFV_NET_LAG_MARKER in head:
            continue
        candidates.append((path.stat().st_mtime, path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def main():
    wb = Path(get_cursor_workbench_path(get_resolved_cursor_app_path()))
    if not wb.is_file():
        print(f"ERROR: workbench not found: {wb}")
        return 1

    content = wb.read_text(encoding="utf-8", errors="ignore")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    broken_backup = wb.with_suffix(f".broken.{ts}.bak")
    shutil.copy2(wb, broken_backup)
    print(f"Saved broken copy: {broken_backup.name}")

    stripped, did_strip = strip_net_lag(content)
    if did_strip:
        wb.write_text(stripped, encoding="utf-8", errors="ignore")
        print("Removed CFV-NET-LAG fetch hook from workbench.")
        print("Restart Cursor now.")
        return 0

    backup = find_clean_backup(wb.parent)
    if backup:
        shutil.copy2(backup, wb)
        print(f"Restored from: {backup.name}")
        print("Restart Cursor now.")
        return 0

    print("No CFV hook found and no clean backup available.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
