"""Verify anti-revert workbench patches (compact output for agent loops)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

# Support both cs.* (3.11+) and Vr.* (3.10.x) — pass if either variant patched
CHECK_GROUPS = [
    ("force store PRO", ["i=cs.PRO,this.storageService.store(Hgt", "s=Vr.PRO,this.storageService.store(Zmt,s,-1,1)"]),
    ("default PRO", ["default:return cs.PRO}},this.openAIKey", "default:return Vr.PRO}},this.openAIKey"]),
    ("getter PRO", ["membershipType(){return cs.PRO}", "membershipType(){return Vr.PRO}"]),
    ("force active", ['i="active",this.storageService.store(KAc,i,-1,1)', 's="active",this.storageService.store(k8i,s,-1,1)']),
    ("_membershipType PRO", ["this._membershipType=()=>cs.PRO", "this._membershipType=()=>Vr.PRO"]),
    ("reactive sync PRO", ['setApplicationUserPersistentStorage("membershipType",cs.PRO)', 'setApplicationUserPersistentStorage("membershipType",Vr.PRO)']),
    ("api response PRO", ['this.storeMembershipType(cs.PRO),this.storeSubscriptionStatus("active")', 'this.storeMembershipType(Vr.PRO),this.storeSubscriptionStatus("active")']),
]

NEGATIVE = [
    ("old store FREE gone", ["i=i??cs.FREE,this.storageService.store(Hgt", "s=s??Vr.FREE"]),
    ("store FREE fallback gone", ["j||this.storeMembershipType(cs.FREE)", "z||this.storeMembershipType(Vr.FREE)"]),
]


def _group_ok(content, needles):
    return any(n in content for n in needles)


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
    total = len(CHECK_GROUPS) + len(NEGATIVE)
    for name, needles in CHECK_GROUPS:
        ok = _group_ok(content, needles)
        if not ok:
            failed.append(name)
        if args.verbose:
            print(f"{'OK' if ok else 'FAIL'}  {name}")

    for name, needles in NEGATIVE:
        ok = not any(n in content for n in needles)
        if not ok:
            failed.append(name)
        if args.verbose:
            print(f"{'OK' if ok else 'FAIL'}  {name}")

    if args.json:
        print(json.dumps({"ok": len(failed) == 0, "failed": failed, "total": total}))
    elif not args.verbose:
        status = "OK" if not failed else "FAIL"
        print(f"antirevert {status} {total - len(failed)}/{total}")
        if failed:
            print("missing:", ", ".join(failed))
    elif failed:
        print(f"missing: {', '.join(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
