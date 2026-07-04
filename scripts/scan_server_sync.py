import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()

patterns = [
    "full_stripe_profile",
    "stripe_profile",
    "fetchUserPricingInfo",
    "getUsage",
    "usage",
    "analyticsService",
    "trackEvent",
    "telemetryService",
    "refreshMembership",
    "refreshAuthentication",
    "/auth/",
    "api2.cursor",
    "cursor.sh/auth",
    "on-demand",
    "Auto + Composer",
    "membershipType",
    "pollRepoBlocklist",
    "fetchUserPrivacyMode",
    "getTeams",
    "dashboardClient",
    "authBackendClient",
]

print(f"size={len(c)}\n")
for pat in patterns:
    n = len(re.findall(re.escape(pat) if "/" not in pat and "+" not in pat else pat, c))
    if n:
        print(f"{pat:35} {n}")

# usage UI related
for pat in ["Auto \\+ Composer", "Additional usage beyond limits", "on-demand spend"]:
    ms = list(re.finditer(pat, c))
    if ms:
        m = ms[0]
        print(f"\n--- {pat} ---")
        print(c[max(0, m.start()-100): m.start()+200])
