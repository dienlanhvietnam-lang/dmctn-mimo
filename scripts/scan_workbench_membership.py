import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import get_cursor_workbench_path, get_resolved_cursor_app_path

p = get_cursor_workbench_path(get_resolved_cursor_app_path())
c = open(p, encoding="utf-8", errors="ignore").read()

patterns = [
    "refreshMembership",
    "storeMembershipType",
    "Vr.FREE",
    "membershipType()",
    "stripeMembershipType",
    "subscriptionStatus",
    "confirmed-free",
    'setApplicationUserPersistentStorage("membershipType"',
    "storageService.get(Zmt",
    "_membershipType",
]

print(f"workbench: {p}\n")
for pat in patterns:
    print(f"{pat:55} {c.count(pat)}")

needles = [
    ("force store PRO", "s=Vr.PRO,this.storageService.store(Zmt,s,-1,1)"),
    ("default PRO", "default:return Vr.PRO}},this.openAIKey"),
    ("getter PRO", "membershipType(){return Vr.PRO}"),
    ("force active", 's="active",this.storageService.store(k8i,s,-1,1)'),
    ("old store FREE", "s=s??Vr.FREE"),
    ("store FREE fallback", "storeMembershipType(Vr.FREE)"),
]
print("\nPatch status:")
for name, needle in needles:
    bad = name.startswith("old") or "fallback" in name
    ok = (needle not in c) if bad else (needle in c)
    print(f"  {'OK' if ok else 'FAIL'}  {name}")
