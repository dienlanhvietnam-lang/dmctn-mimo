import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()

patterns = [
    r"full_stripe_profile",
    r"stripe_profile",
    r"refreshMembership",
    r"refreshAccessToken",
    r"refreshAuthentication",
    r"scheduleTeamPolicyCheck",
    r"setInterval.*refresh",
    r"/auth/",
]
for pat in patterns:
    ms = list(re.finditer(pat, c))
    print(f"{pat:30} {len(ms)}")

# extract refreshMembership function start
m = re.search(r"this\.refreshMembership=async\(\)=>\{", c)
if m:
    print("\n--- refreshMembership (first 2500 chars) ---")
    print(c[m.start() : m.start() + 2500])
