#!/usr/bin/env python3
"""12-phase health check + auto-fix loop until clean.

Usage:
  python scripts/phase_loop.py              # run once, compact output
  python scripts/phase_loop.py --fix        # auto-fix then re-check
  python scripts/phase_loop.py --fix --loop # repeat fix until all pass (max 8 rounds)
  python scripts/phase_loop.py -v           # verbose per phase
"""
from __future__ import annotations

import argparse
import compileall
import io
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("CURSOR_FREE_VIP_LANG", "vi")
os.environ.setdefault("CURSOR_FREE_VIP_KEEP_RUNNING", "1")

PHASES = [
    "01_syntax",
    "02_imports",
    "03_locales",
    "04_config",
    "05_cursor_paths",
    "06_auth_token",
    "07_auth_membership",
    "08_e2e_smoke",
    "09_antirevert",
    "10_sync_block",
    "11_patches_complete",
    "12_translator_keys",
]

CORE_MODULES = [
    "main", "config", "utils", "cursor_auth", "cursor_acc_info",
    "vip_activate", "workbench_patches", "reset_machine_manual",
    "bypass_token_limit", "bypass_version", "disable_auto_update",
    "check_user_authorized", "oauth_auth", "totally_reset_cursor", "quit_cursor",
]

LOCALE_KEYS = [
    "menu.activate_vip",
    "vip.title",
    "vip.membership_activated",
    "vip.workbench_patched",
    "vip.patches_applied",
    "vip.reload_hint",
    "vip.sync_blocked",
    "auth.storage_synced",
    "update.keep_cursor_running",
]


def _nested_get(data: dict, dotted: str):
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _quiet_run(fn):
    os.environ["CURSOR_FREE_VIP_QUIET"] = "1"
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return fn()


class PhaseRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: dict[str, tuple[bool, str]] = {}

    def run_phase(self, name: str) -> tuple[bool, str]:
        handler = getattr(self, f"phase_{name.split('_', 1)[1]}", None)
        if not handler:
            return False, "no handler"
        try:
            ok, msg = handler()
            self.results[name] = (ok, msg)
            if self.verbose:
                mark = "OK" if ok else "FAIL"
                print(f"  [{mark}] {name}: {msg}")
            return ok, msg
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            self.results[name] = (False, msg)
            if self.verbose:
                print(f"  [FAIL] {name}: {msg}")
            return False, msg

    def phase_syntax(self):
        ok = compileall.compile_dir(str(ROOT), quiet=1)
        return bool(ok), "compileall" if ok else "syntax errors"

    def phase_imports(self):
        failed = []
        for mod in CORE_MODULES:
            try:
                __import__(mod)
            except Exception as e:
                failed.append(f"{mod}:{e}")
        return not failed, "all ok" if not failed else "; ".join(failed[:3])

    def phase_locales(self):
        errors = []
        for path in (ROOT / "locales").glob("*.json"):
            try:
                json.load(path.open(encoding="utf-8"))
            except Exception as e:
                errors.append(f"{path.name}:{e}")
        vi = json.load((ROOT / "locales/vi.json").open(encoding="utf-8"))
        en = json.load((ROOT / "locales/en.json").open(encoding="utf-8"))
        for key in LOCALE_KEYS:
            if _nested_get(vi, key) is None:
                errors.append(f"vi missing {key}")
            if _nested_get(en, key) is None:
                errors.append(f"en missing {key}")
        return not errors, "ok" if not errors else "; ".join(errors[:4])

    def phase_config(self):
        from config import get_config
        cfg = get_config()
        if not cfg:
            return False, "get_config returned None"
        section = "WindowsPaths" if sys.platform == "win32" else "MacPaths" if sys.platform == "darwin" else "LinuxPaths"
        if not cfg.has_section(section):
            return False, f"missing section {section}"
        path = cfg.get(section, "cursor_path", fallback="")
        return bool(path), f"cursor_path={path or 'empty'}"

    def phase_cursor_paths(self):
        from utils import get_resolved_cursor_app_path, get_cursor_workbench_path, get_cursor_product_json_path
        app = get_resolved_cursor_app_path()
        wb = get_cursor_workbench_path(app)
        pj = get_cursor_product_json_path(app)
        if not app or not os.path.isdir(app):
            return False, f"app dir missing: {app}"
        missing = [p for p in (wb, pj) if not p or not os.path.isfile(p)]
        return not missing, "ok" if not missing else f"missing {missing[0]}"

    def phase_auth_token(self):
        from cursor_acc_info import get_token
        token = get_token()
        if not token:
            return True, "skip (no token)"
        if not (token.startswith("eyJ") and len(token) > 100):
            return False, f"bad token len={len(token)}"
        return True, f"jwt len={len(token)}"

    def phase_auth_membership(self):
        from config import get_config
        cfg = get_config()
        section = "WindowsPaths" if sys.platform == "win32" else "MacPaths" if sys.platform == "darwin" else "LinuxPaths"
        db = cfg.get(section, "sqlite_path", fallback="")
        if not db or not os.path.isfile(db):
            return True, "skip (no db)"
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        pro = cur.execute(
            "SELECT value FROM ItemTable WHERE key='cursorAuth/stripeMembershipType'"
        ).fetchone()
        active = cur.execute(
            "SELECT value FROM ItemTable WHERE key='cursorAuth/stripeSubscriptionStatus'"
        ).fetchone()
        conn.close()
        if not pro or pro[0] != "pro":
            return False, f"membership={pro[0] if pro else 'missing'}"
        if not active or active[0] != "active":
            return False, f"status={active[0] if active else 'missing'}"
        return True, "pro/active"

    def phase_e2e_smoke(self):
        r = subprocess.run(
            [sys.executable, "scripts/e2e_smoke_test.py", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if r.returncode != 0:
            return False, r.stdout.strip() or r.stderr.strip()[:120]
        data = json.loads(r.stdout.strip().splitlines()[-1])
        failed = data.get("failed", [])
        return not failed, f"{data.get('passed')}/{data.get('total')}"

    def phase_antirevert(self):
        r = subprocess.run(
            [sys.executable, "scripts/verify_antirevert.py", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        data = json.loads(r.stdout.strip())
        return data.get("ok"), f"{data.get('total') - len(data.get('failed', []))}/{data.get('total')}"

    def phase_sync_block(self):
        r = subprocess.run(
            [sys.executable, "scripts/verify_sync_block.py", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        data = json.loads(r.stdout.strip())
        return data.get("ok"), f"{data.get('total') - len(data.get('failed', []))}/{data.get('total')}"

    def phase_patches_complete(self):
        from utils import get_cursor_workbench_path, get_resolved_cursor_app_path
        from workbench_patches import count_pending_patches
        wb = get_cursor_workbench_path(get_resolved_cursor_app_path())
        content = Path(wb).read_text(encoding="utf-8", errors="ignore")
        pending = count_pending_patches(content)
        return pending == 0, f"pending={pending}"

    def phase_translator_keys(self):
        from main import Translator
        t = Translator()
        t.current_language = "vi"
        t.load_translations()
        missing = [k for k in LOCALE_KEYS if t.get(k) == k]
        return not missing, "ok" if not missing else f"missing {missing[:3]}"


def apply_fixes(failed_phases: list[str]) -> list[str]:
    applied = []
    fixable = {"07_auth_membership", "09_antirevert", "10_sync_block", "11_patches_complete"}
    if fixable & set(failed_phases):
        from main import translator
        import vip_activate
        _quiet_run(lambda: vip_activate.activate_vip_membership(translator))
        applied.append("vip_membership")
        try:
            _quiet_run(lambda: vip_activate.patch_workbench_vip(translator))
            applied.append("workbench_patch")
        except PermissionError:
            applied.append("workbench_locked")
        except Exception as e:
            applied.append(f"workbench_error:{e}")
    if "04_config" in failed_phases:
        from config import get_config
        get_config()
        applied.append("config_resync")
    return applied


def run_all(verbose: bool) -> tuple[bool, dict]:
    runner = PhaseRunner(verbose=verbose)
    for phase in PHASES:
        runner.run_phase(phase)
    failed = [p for p, (ok, _) in runner.results.items() if not ok]
    return not failed, runner.results


def main():
    parser = argparse.ArgumentParser(description="12-phase fix loop")
    parser.add_argument("--fix", action="store_true", help="Auto-fix failed phases")
    parser.add_argument("--loop", action="store_true", help="Repeat until clean (requires --fix)")
    parser.add_argument("--max-rounds", type=int, default=8)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    round_num = 0
    last_results = {}
    while True:
        round_num += 1
        ok, results = run_all(args.verbose)
        last_results = results

        if ok:
            if args.json:
                print(json.dumps({"ok": True, "rounds": round_num, "phases": {k: v[1] for k, v in results.items()}}, ensure_ascii=False))
            else:
                print(f"phase_loop OK 12/12 round={round_num}")
            return 0

        failed = [p for p, (o, _) in results.items() if not o]
        if args.fix:
            fixes = apply_fixes(failed)
            if args.verbose:
                print(f"round {round_num} fixes: {fixes}")
            if args.loop and round_num < args.max_rounds:
                continue

        if args.json:
            print(json.dumps({
                "ok": False,
                "rounds": round_num,
                "failed": failed,
                "details": {k: {"ok": v[0], "msg": v[1]} for k, v in results.items()},
            }, ensure_ascii=False))
        else:
            print(f"phase_loop FAIL {12 - len(failed)}/12 round={round_num}")
            for p in failed:
                print(f"  - {p}: {results[p][1]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
