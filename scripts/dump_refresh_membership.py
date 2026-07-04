import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()
out = []
for i, m in enumerate(re.finditer("refreshMembership", c)):
    s = max(0, m.start() - 150)
    e = min(len(c), m.start() + 350)
    out.append(f"=== #{i+1} ===\n{c[s:e]}\n")
Path(__file__).with_name("_refreshMembership_snippets.txt").write_text("\n".join(out), encoding="utf-8")
print(f"wrote {len(out)} snippets")
