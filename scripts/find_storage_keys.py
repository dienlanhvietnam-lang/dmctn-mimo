import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()

# Zmt is likely assigned near k8i (subscription status key)
for key in ["Zmt", "k8i", "_Bi"]:
    for m in re.finditer(rf"{key}=\"[^\"]+\"", c):
        print(c[m.start() : m.start() + 80])
        break
    else:
        # try minified form Zmt="..."
        idx = c.find(f'{key}="')
        if idx >= 0:
            print(c[idx : idx + 80])
