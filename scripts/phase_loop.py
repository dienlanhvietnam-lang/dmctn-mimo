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
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("DMCTN_MIMO_LANG", "vi")
os.environ.setdefault("DMCTN_MIMO_KEEP_RUNNING", "1")

PHASES = [
    "01_syntax",
    "02_imports",
    "03_locales",
    "04_config",
    "05_mimo_cli",
    "06_mimo_bootstrap",
    "07_mimo_slots",
    "08_e2e_smoke",
    "09_ui_theme",
    "10_mimo_protected",
    "11_branding",
    "12_translator_keys",
    "13_context_vault",
]

CORE_MODULES = [
    "main", "config", "utils", "ui", "logo", "branding",
    "reset_mimo_machine", "totally_reset_mimo", "setup_mimo_auto", "mimo_auth",
    "mimo_account_slots", "mimo_platform_login", "mimo_manage_accounts", "chrome_profile",
    "mimo_paths", "mimo_context_paths", "mimo_context_vault", "mimo_manage_context",
]

LOCALE_KEYS = [
    "menu.mimo_platform_login",
    "menu.mimo_manage_accounts",
    "menu.deep_reset_mimo",
    "menu.manage_context",
    "mimo_slots.title",
    "mimo_login.title",
    "mimo_deep.title",
    "mimo_context.title",
    "mimo_reset.mode_preserve",
]


def _nested_get(data: dict, dotted: str):
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _quiet_run(fn):
    os.environ["DMCTN_MIMO_QUIET"] = "1"
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
        for path in sorted((ROOT / "locales").glob("*.json")):
            try:
                json.load(path.open(encoding="utf-8"))
            except Exception as e:
                errors.append(f"{path.name}:{e}")
        locale_files = {p.name for p in (ROOT / "locales").glob("*.json")}
        if locale_files != {"en.json", "vi.json"}:
            errors.append(f"expected en.json+vi.json only, got {sorted(locale_files)}")
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
        from branding import CONFIG_DIR_NAME

        cfg = get_config()
        if not cfg:
            return False, "get_config returned None"
        if not cfg.has_section("Utils"):
            return False, "missing Utils section"
        return True, f"config_dir={CONFIG_DIR_NAME}"

    def phase_mimo_cli(self):
        mimo_cmd = ROOT / "mimo" / "node_modules" / ".bin" / "mimo.cmd"
        if sys.platform == "win32":
            return mimo_cmd.is_file(), str(mimo_cmd.name if mimo_cmd.is_file() else mimo_cmd)
        mimo_bin = ROOT / "mimo" / "node_modules" / ".bin" / "mimo"
        return mimo_bin.is_file(), str(mimo_bin)

    def phase_mimo_bootstrap(self):
        from mimo_auth import verify_free_bootstrap

        data = verify_free_bootstrap()
        jwt = data.get("jwt", "")
        return bool(jwt), f"jwt len={len(jwt)}"

    def phase_mimo_slots(self):
        from mimo_paths import get_mimo_accounts_dir, get_mimo_manifest_path

        accounts = get_mimo_accounts_dir()
        manifest = get_mimo_manifest_path()
        return accounts.endswith("accounts") and manifest.endswith("manifest.json"), "ok"

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

    def phase_ui_theme(self):
        import ui

        assert callable(ui.panel)
        assert ui.box_width() >= ui.MIN_WIDTH
        return True, f"width={ui.box_width()}"

    def phase_mimo_protected(self):
        from mimo_context_paths import get_context_vault_dir
        from mimo_paths import get_dmctn_protected_paths, get_mimo_protected_dirs, get_mimo_wipe_dirs

        protected = get_mimo_protected_dirs()
        wipe = get_mimo_wipe_dirs()
        bad = [name for name in protected if any(p.endswith(name) for p in wipe)]
        vault = os.path.normcase(os.path.abspath(get_context_vault_dir()))
        wipe_abs = [os.path.normcase(os.path.abspath(p)) for p in wipe]
        if vault in wipe_abs:
            bad.append("context_vault")
        dmctn = [os.path.normcase(os.path.abspath(p)) for p in get_dmctn_protected_paths()]
        if vault not in dmctn:
            bad.append("dmctn_protected_missing")
        return not bad, "ok" if not bad else f"leak {bad}"

    def phase_branding(self):
        from branding import APP_NAME, CONFIG_DIR_NAME

        ok = APP_NAME == "MiMo FREE" and CONFIG_DIR_NAME == ".dmctn-mimo"
        return ok, APP_NAME

    def phase_translator_keys(self):
        from main import Translator

        t = Translator()
        t.current_language = "vi"
        t.load_translations()
        missing = [k for k in LOCALE_KEYS if t.get(k) == k]
        return not missing, "ok" if not missing else f"missing {missing[:3]}"

    def phase_context_vault(self):
        from mimo_context_paths import get_context_bundle_paths, get_context_vault_dir
        from mimo_context_vault import list_context_slots

        paths = get_context_bundle_paths()
        assert any("memory" in p.replace("\\", "/") for p in paths)
        vault = get_context_vault_dir()
        assert ".dmctn-mimo" in vault.replace("\\", "/") or "dmctn" in vault.lower()
        data = list_context_slots()
        assert "slots" in data and "count" in data
        return True, f"slots={data['count']}"


def apply_fixes(failed_phases: list[str]) -> list[str]:
    applied = []
    if "04_config" in failed_phases:
        from config import get_config

        get_config()
        applied.append("config_resync")
    if "06_mimo_bootstrap" in failed_phases:
        from setup_mimo_auto import apply_mimo_auto_config

        apply_mimo_auto_config()
        applied.append("mimo_auto_config")
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
