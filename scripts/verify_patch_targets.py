"""List workbench patch targets still present (compact by default)."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from workbench_patches import get_workbench_replacements, count_pending_patches, _skip_replacement
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path


def collect_pending(content):
    items = []
    for old in get_workbench_replacements():
        if _skip_replacement(old, content):
            continue
        count = content.count(old)
        if count:
            items.append({"pattern": old[:70], "count": count})
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    wb = get_cursor_workbench_path(get_resolved_cursor_app_path())
    content = Path(wb).read_text(encoding="utf-8", errors="ignore")
    pending_items = collect_pending(content)
    pending = count_pending_patches(content)

    if args.verbose:
        for item in pending_items:
            print(f"{item['count']:3d}  {item['pattern']}")

    if args.json:
        print(json.dumps({"pending": pending, "items": pending_items[:20]}, ensure_ascii=False))
    elif not args.verbose:
        print(f"patches pending={pending}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
