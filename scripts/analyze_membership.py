import re

p = r"E:\cursor31\cursor\resources\app\out\vs\workbench\workbench.desktop.main.js"
with open(p, encoding="utf-8", errors="ignore") as f:
    c = f.read()

for pat in [
    r'setApplicationUserPersistentStorage\(["\']membershipType["\']',
    r'applicationUserPersistentStorage\.membershipType\s*=',
    r'membershipType",Vr\.',
    r'"membershipType",',
]:
    matches = list(re.finditer(pat, c))
    print(pat, len(matches))
    for m in matches[:3]:
        print(" ", c[max(0, m.start() - 40): m.start() + 100])
