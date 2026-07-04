"""Compact auth diagnostic — only cursorAuth keys (no git-ipc noise)."""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_config

AUTH_PREFIX = "cursorAuth/"

INTERESTING_SUFFIXES = (
    "accessToken",
    "refreshToken",
    "cachedEmail",
    "stripeMembershipType",
    "stripeSubscriptionStatus",
    "cachedSignUpType",
)


def _truncate(value, limit=80):
    text = str(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _load_paths():
    config = get_config()
    if not config:
        return None, None
    if sys.platform == "win32":
        section = "WindowsPaths"
    elif sys.platform == "darwin":
        section = "MacPaths"
    else:
        section = "LinuxPaths"
    storage = config.get(section, "storage_path", fallback="")
    sqlite = config.get(section, "sqlite_path", fallback="")
    return storage, sqlite


def _interesting_key(key):
    if not key.startswith(AUTH_PREFIX):
        return False
    suffix = key[len(AUTH_PREFIX) :]
    return suffix in INTERESTING_SUFFIXES


def run(compact=True):
    storage_path, sqlite_path = _load_paths()
    lines = []

    if storage_path and os.path.exists(storage_path):
        with open(storage_path, encoding="utf-8") as f:
            data = json.load(f)
        for key in sorted(data):
            if _interesting_key(key):
                lines.append(f"storage {key}={_truncate(data[key])}")
    else:
        lines.append("storage missing")

    if sqlite_path and os.path.exists(sqlite_path):
        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT key, value FROM ItemTable WHERE key LIKE ? ORDER BY key",
            (AUTH_PREFIX + "%",),
        )
        for key, val in cur.fetchall():
            if _interesting_key(key):
                lines.append(f"sqlite  {key}={_truncate(val)}")
        conn.close()
    else:
        lines.append("sqlite missing")

    if compact:
        print("\n".join(lines))
    else:
        print("=== auth (cursorAuth only) ===")
        for line in lines:
            print(f"  {line}")


def main():
    parser = argparse.ArgumentParser(description="Auth diagnostic (compact by default)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    run(compact=not args.verbose)


if __name__ == "__main__":
    main()
