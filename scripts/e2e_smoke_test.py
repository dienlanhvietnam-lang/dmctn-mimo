"""Smoke/E2E runner for menu features.

Quiet by default to save agent/LLM tokens when run in a loop.
  python scripts/e2e_smoke_test.py           # summary only
  python scripts/e2e_smoke_test.py --json    # one-line JSON
  python scripts/e2e_smoke_test.py -v        # full module output
"""
import argparse
import io
import json
import os
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault("CURSOR_FREE_VIP_LANG", "vi")
os.environ.setdefault("CURSOR_FREE_VIP_KEEP_RUNNING", "1")

RESULTS = []


def run_case(name, fn, verbose=False):
    if verbose:
        print(f"\n{'='*60}\nTEST: {name}\n{'='*60}")
    try:
        if verbose:
            fn()
        else:
            os.environ["CURSOR_FREE_VIP_QUIET"] = "1"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                fn()
        RESULTS.append((name, "PASS", ""))
        if verbose:
            print(f"[PASS] {name}")
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        RESULTS.append((name, "FAIL", msg))
        if verbose:
            print(f"[FAIL] {name} -> {msg}")
            traceback.print_exc()
        else:
            print(f"[FAIL] {name} -> {msg}")


def test_9_disable_auto_update():
    from main import translator
    import disable_auto_update
    disabler = disable_auto_update.AutoUpdateDisabler(translator)
    assert disabler.disable_auto_update() is True


def test_12_print_config():
    from main import translator
    from config import get_config
    assert get_config(translator) is not None


def test_15_bypass_version_paths():
    from main import translator
    import bypass_version
    path = bypass_version.get_product_json_path(translator)
    assert os.path.isfile(path), path


def test_15_bypass_version_run():
    from main import translator
    import bypass_version
    assert bypass_version.main(translator) in (True, False)


def test_16_check_user_authorized():
    from main import translator
    import check_user_authorized
    from cursor_acc_info import get_token
    token = get_token()
    if not token:
        return
    ok = check_user_authorized.check_user_authorized(token, translator)
    assert ok in (True, False)


def test_17_bypass_token_limit_paths():
    from main import translator
    import bypass_token_limit
    path = bypass_token_limit.get_workbench_cursor_path(translator)
    assert os.path.isfile(path), path


def test_17_bypass_token_limit_run():
    from main import translator
    import bypass_token_limit
    path = bypass_token_limit.get_workbench_cursor_path(translator)
    assert bypass_token_limit.modify_workbench_js(path, translator) is True


def test_10_totally_reset_paths():
    from main import translator
    from reset_machine_manual import get_cursor_paths, get_workbench_cursor_path
    pkg_path, main_path = get_cursor_paths(translator)
    assert os.path.isfile(pkg_path), pkg_path
    assert os.path.isfile(main_path), main_path
    workbench = get_workbench_cursor_path(translator)
    assert os.path.isfile(workbench), workbench


def test_2_register_import():
    import cursor_register  # noqa: F401


def test_3_google_import():
    import cursor_register_google  # noqa: F401


def test_4_github_import():
    import cursor_register_github  # noqa: F401


def test_5_manual_import():
    import cursor_register_manual  # noqa: F401


def test_14_delete_google_import():
    import delete_cursor_google  # noqa: F401


def test_18_vip_activate():
    from main import translator
    import vip_activate
    assert vip_activate.activate_vip_membership(translator) is True


def main():
    parser = argparse.ArgumentParser(description="E2E smoke tests (quiet by default)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full module output")
    parser.add_argument("--json", action="store_true", help="Print one-line JSON summary only")
    args = parser.parse_args()

    cases = [
        ("9 disable_auto_update", test_9_disable_auto_update),
        ("12 print_config", test_12_print_config),
        ("15 bypass_version paths", test_15_bypass_version_paths),
        ("15 bypass_version run", test_15_bypass_version_run),
        ("16 check_user_authorized", test_16_check_user_authorized),
        ("17 bypass_token_limit paths", test_17_bypass_token_limit_paths),
        ("17 bypass_token_limit run", test_17_bypass_token_limit_run),
        ("10 totally_reset paths", test_10_totally_reset_paths),
        ("2 cursor_register import", test_2_register_import),
        ("3 cursor_register_google import", test_3_google_import),
        ("4 cursor_register_github import", test_4_github_import),
        ("5 cursor_register_manual import", test_5_manual_import),
        ("14 delete_cursor_google import", test_14_delete_google_import),
        ("18 vip_activate", test_18_vip_activate),
    ]

    for name, fn in cases:
        run_case(name, fn, verbose=args.verbose)

    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    failed = [{"name": n, "error": m} for n, s, m in RESULTS if s == "FAIL"]

    if args.json:
        print(json.dumps({"passed": passed, "total": len(RESULTS), "failed": failed}, ensure_ascii=False))
    elif args.verbose:
        print(f"\n{'='*60}\nSUMMARY\n{'='*60}")
        print(f"Passed: {passed}/{len(RESULTS)}")
        for name, status, msg in RESULTS:
            mark = "OK" if status == "PASS" else "XX"
            print(f"  [{mark}] {name}" + (f" - {msg}" if msg else ""))
    else:
        status = "PASS" if not failed else "FAIL"
        print(f"e2e {status} {passed}/{len(RESULTS)}")
        for item in failed:
            print(f"  - {item['name']}: {item['error']}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
