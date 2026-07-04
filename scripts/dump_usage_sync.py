import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()

needles = [
    "fetchUserPricingInfo",
    "getUsage",
    "fetchUsage",
    "usageService",
    "UserPricingInfo",
    "limitHit",
    "onDemand",
    "spend",
    "quota",
    "refreshUsage",
    "pollUsage",
    "syncUsage",
]

for n in needles:
    for m in re.finditer(n, c):
        ctx = c[max(0, m.start()-30): m.start()+120]
        if "async " in ctx or "fetch(" in ctx or "=async" in ctx or "Service" in ctx:
            print(f"=== {n} @ {m.start()} ===")
            print(ctx[:200])
            print()
            break

# fetchUserPricingInfo function body
m = re.search(r"fetchUserPricingInfo=async\(\)=>|fetchUserPricingInfo\(\)\{", c)
if m:
    print("=== fetchUserPricingInfo body ===")
    print(c[m.start(): m.start()+1500])
