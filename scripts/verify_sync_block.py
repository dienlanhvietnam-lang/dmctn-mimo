"""Verify server auth/usage sync is blocked in workbench (compact output)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

CHECKS = [
    # membership sync
    ("refreshMembership noop", "this.refreshMembership=async()=>{return;", True),
    ("refreshAuthentication noop", "async refreshAuthentication(){return}", True),
    ("team policy noop", "scheduleTeamPolicyCheck(){return}", True),
    ("2s refresh disabled", "setTimeout(()=>{},2e3)", True),
    # periodic loop (new je or legacy We)
    ("periodic loop noop", "const je=async()=>{return;try{await this.cursorAuthenticationService.refreshMembership()", True),
    ("loop startup disabled", "/*je();*/const st=10;", True),
    # usage / pricing / privacy sync
    ("fetchUserPricingInfo noop", "this.fetchUserPricingInfo=async()=>{return;", True),
    ("fetchUserPrivacyMode noop", "this.fetchUserPrivacyMode=async J=>{return;", True),
    ("getTeams noop", "async getTeams(){return[];", True),
    ("performFetch noop", "async performFetch(n){return;", True),
    ("refetch noop", "async refetch(n=!1){return;", True),
    ("fetchPlanInfo noop", "async fetchPlanInfo(n=!1){return;", True),
    # must NOT exist (raw sync)
    ("raw refreshMembership", 'this.refreshMembership=async()=>{this.authDebugLog("refreshMembership: called")', False),
    ("raw getCurrentPeriodUsage fetch", "async performFetch(n){this.setIsLoading(!0),this.setError(null);try{const t=await(await this.cursorAuthenticationService.dashboardClient()).getCurrentPeriodUsage", False),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    content = open(
        get_cursor_workbench_path(get_resolved_cursor_app_path()),
        encoding="utf-8",
        errors="ignore",
    ).read()

    failed = []
    for name, needle, should_contain in CHECKS:
        found = needle in content
        ok = found if should_contain else not found
        if not ok:
            failed.append(name)
        if args.verbose:
            print(f"{'OK' if ok else 'FAIL'}  {name}")

    if args.json:
        print(json.dumps({"ok": len(failed) == 0, "failed": failed, "total": len(CHECKS)}))
    elif not args.verbose:
        status = "OK" if not failed else "FAIL"
        print(f"syncblock {status} {len(CHECKS) - len(failed)}/{len(CHECKS)}")
        if failed:
            print("missing:", ", ".join(failed))
    elif failed:
        print(f"missing: {', '.join(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
