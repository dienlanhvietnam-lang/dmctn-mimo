import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()
m = re.search(r"this\.refreshMembership=async\(\)=>\{", c)
if not m:
    print("not found")
    raise SystemExit(1)
start = m.start()
# find matching brace - crude: take 8000 chars
chunk = c[start : start + 12000]
Path(__file__).with_name("_refreshMembership_body.txt").write_text(chunk, encoding="utf-8")
print(f"wrote {len(chunk)} chars from offset {start}")
