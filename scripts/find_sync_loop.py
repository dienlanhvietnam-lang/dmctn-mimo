import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

c = open(get_cursor_workbench_path(get_resolved_cursor_app_path()), encoding="utf-8", errors="ignore").read()

needles = [
    "async refreshAuthentication(){await this.getAccessToken()||await this.refreshAccessToken(),await this.refreshMembership()}",
    "scheduleTeamPolicyCheck(){this.hasScheduledTeamPolicyCheck||(this.hasScheduledTeamPolicyCheck=!0,setTimeout(()=>{this.hasScheduledTeamPolicyCheck=!1,this.runTeamPolicyCheck()},3e3))}",
    'this.refreshMembership=async()=>{this.authDebugLog("refreshMembership: called");const U=this.accessToken()',
    "await this.cursorAuthenticationService.refreshMembership()",
    "setTimeout(()=>{e.cursorAuthenticationService.refreshMembership()},2e3)",
    "const We=async()=>{try{await this.cursorAuthenticationService.refreshMembership()",
]
for n in needles:
    print(f"count={c.count(n)}  {n[:90]}")

print("\n--- refreshAuthentication variants ---")
for m in re.finditer(r"refreshAuthentication=\w+\(\)=>|async refreshAuthentication\(\)", c):
    print(c[m.start() : m.start() + 200])

print("\n--- auth refresh interval ---")
for m in re.finditer(r"refreshMembership\(\)", c):
    ctx = c[max(0, m.start() - 80) : m.start() + 80]
    if "setInterval" in ctx or "setTimeout" in ctx or "We=async" in ctx or "86400" in ctx or "60*1e3" in ctx:
        print("...", ctx, "...")
