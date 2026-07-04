"""Verify anti-revert workbench patches (compact output for agent loops)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

CHECKS = [
    ("force store PRO", "s=Vr.PRO,this.storageService.store(Zmt,s,-1,1)", True),
    ("default PRO", "default:return Vr.PRO}},this.openAIKey", True),
    ("getter PRO", "membershipType(){return Vr.PRO}", True),
    ("force active", 's="active",this.storageService.store(k8i,s,-1,1)', True),
    ("old store FREE gone", "s=s??Vr.FREE", False),
    ("_membershipType PRO", "this._membershipType=()=>Vr.PRO", True),
    ("_subscriptionStatus active", 'this._subscriptionStatus=()=>"active"', True),
    ("reactive sync PRO", 'setApplicationUserPersistentStorage("membershipType",Vr.PRO)', True),
    ("api response PRO", 'this.storeMembershipType(Vr.PRO),this.storeSubscriptionStatus("active")', True),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="One-line JSON summary")
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
        print(f"antirevert {status} {len(CHECKS) - len(failed)}/{len(CHECKS)}")
        if failed:
            print("missing:", ", ".join(failed))
    elif failed:
        print(f"missing: {', '.join(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
