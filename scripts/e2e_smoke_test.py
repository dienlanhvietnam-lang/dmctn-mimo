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
import shutil
import sys
import tempfile
import traceback
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault("MIMO_VIP_LANG", "vi")
os.environ.setdefault("MIMO_VIP_KEEP_RUNNING", "1")
os.environ.setdefault("MINO_VIP_LANG", os.environ["MIMO_VIP_LANG"])
os.environ.setdefault("MINO_VIP_KEEP_RUNNING", os.environ["MIMO_VIP_KEEP_RUNNING"])
os.environ.setdefault("CURSOR_FREE_VIP_LANG", os.environ["MIMO_VIP_LANG"])
os.environ.setdefault("CURSOR_FREE_VIP_KEEP_RUNNING", os.environ["MIMO_VIP_KEEP_RUNNING"])

RESULTS = []


def run_case(name, fn, verbose=False):
    if verbose:
        print(f"\n{'='*60}\nTEST: {name}\n{'='*60}")
    try:
        if verbose:
            fn()
        else:
            os.environ["MIMO_VIP_QUIET"] = "1"
            os.environ["MINO_VIP_QUIET"] = "1"
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


def test_chrome_profile_save_load():
    import configparser
    import tempfile
    import chrome_profile
    import config as config_mod
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_chrome_")
    orig_utils_dir = utils.get_app_config_dir
    orig_config_dir = config_mod.get_app_config_dir
    utils.get_app_config_dir = lambda: tmp
    config_mod.get_app_config_dir = lambda: tmp

    try:
        config_path = os.path.join(tmp, "config.ini")
        config = configparser.ConfigParser()
        config.add_section("Chrome")
        config.set("Chrome", "chromepath", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)

        orig_profiles = chrome_profile.get_available_profiles
        chrome_profile.get_available_profiles = lambda user_data_dir=None: [("Profile 5", "Work 1")]
        try:
            assert chrome_profile.save_selected_profile("Profile 5", "Work 1")
            loaded = chrome_profile.load_saved_profile()
            assert loaded == ("Profile 5", "Work 1")
        finally:
            chrome_profile.get_available_profiles = orig_profiles
    finally:
        utils.get_app_config_dir = orig_utils_dir
        config_mod.get_app_config_dir = orig_config_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_select_profile_prompt_uses_msg_fallback():
    from chrome_profile import _msg

    class T:
        def get(self, key, **kwargs):
            return "Choice ({choices})".format(**kwargs)

    text = _msg(T(), "menu.input_choice", "Please enter your choice ({choices})", choices="0-3")
    assert "0-3" in text


def test_mimo_slots_modules_import():
    import chrome_profile  # noqa: F401
    import mimo_account_slots  # noqa: F401
    import mimo_platform_login  # noqa: F401
    import mimo_manage_accounts  # noqa: F401
    import ui  # noqa: F401


def test_mimo_paths_accounts_dir():
    from mimo_paths import get_mimo_accounts_dir, get_mimo_manifest_path, get_mimo_protected_dirs

    assert get_mimo_accounts_dir().endswith(os.path.join("mimocode", "accounts"))
    assert get_mimo_manifest_path().endswith("manifest.json")
    assert "accounts" in get_mimo_protected_dirs()


def test_mimo_account_slots_crud():
    import mimo_account_slots as slots
    import mimo_paths

    tmp = tempfile.mkdtemp(prefix="mimo_slots_")
    data_dir = os.path.join(tmp, "mimocode")
    accounts_dir = os.path.join(data_dir, "accounts")
    os.makedirs(accounts_dir, exist_ok=True)
    auth_path = os.path.join(data_dir, "auth.json")
    auth_payload = {
        "xiaomi": {
            "type": "api",
            "key": "sk-test-key-abcdefghijklmnop",
            "metadata": {"uid": "1234567890", "base_url": "https://api.xiaomimimo.com/v1"},
        }
    }
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_payload, f)

    orig_data = mimo_paths.get_mimo_data_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    try:
        created = slots.create_slot_from_auth(
            auth_path,
            label="test-gmail",
            chrome_profile="Profile 5",
            chrome_display_name="Work 1",
        )
        assert created["slot_id"]
        entries = slots.list_slot_entries()
        assert len(entries) == 1
        assert entries[0]["label"] == "test-gmail"
        assert entries[0]["key_prefix"].startswith("sk-test")

        active = slots.activate_slot(created["slot_id"])
        assert os.path.isfile(active)
        with open(active, encoding="utf-8") as f:
            assert json.load(f)["xiaomi"]["key"] == auth_payload["xiaomi"]["key"]

        slots.rename_slot(created["slot_id"], "renamed")
        assert slots.load_manifest()["slots"][0]["label"] == "renamed"

        slots.delete_slot(created["slot_id"])
        assert slots.list_slot_entries() == []
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        shutil.rmtree(tmp, ignore_errors=True)


def test_mimo_wipe_protects_accounts():
    from mimo_paths import get_mimo_protected_dirs, get_mimo_wipe_dirs

    protected = get_mimo_protected_dirs()
    wipe_dirs = get_mimo_wipe_dirs()
    for name in protected:
        assert not any(p.endswith(name) for p in wipe_dirs), f"{name} must not be wiped"


def test_12_mimo_reset_helpers():
    from machine_id_utils import generate_mimo_client_ids, generate_telemetry_ids
    from mimo_paths import get_mimo_data_dir, get_mimo_identity_files

    mimo_ids = generate_mimo_client_ids()
    assert len(mimo_ids["mimo-free-client"]) == 64
    assert len(mimo_ids["installation_id"]) == 36
    assert mimo_ids["mimo-key-name"].startswith("mimo-code-cli-key-")

    telemetry = generate_telemetry_ids()
    assert len(telemetry["telemetry.machineId"]) == 64

    files = get_mimo_identity_files()
    assert "installation_id" in files
    assert get_mimo_data_dir()


def test_13_mimo_total_helpers():
    from mimo_paths import get_mimo_database_files, get_mimo_wipe_dirs, get_mimo_wipe_files
    import totally_reset_mimo

    assert any(p.endswith("mimocode.db") for p in get_mimo_database_files())
    assert any(p.endswith("memory") for p in get_mimo_wipe_dirs())
    assert callable(totally_reset_mimo.totally_reset_mimo)


def test_mimo_auto_setup():
    from setup_mimo_auto import apply_mimo_auto_config, build_auto_provider_config
    from mimo_auth import verify_free_bootstrap

    cfg = build_auto_provider_config()
    assert "mimo" not in cfg.get("provider", {})
    assert cfg["agent"]["build"]["model"] == "mimo/mimo-auto"
    path = apply_mimo_auto_config()
    assert os.path.isfile(path)
    verify_free_bootstrap()


def test_branding_mimo():
    from branding import APP_NAME, CONFIG_DIR_NAME, cli_process_env

    assert APP_NAME == "MiMo VIP"
    assert CONFIG_DIR_NAME == ".mimo-vip"
    env = cli_process_env("vi")
    assert env["MIMO_VIP_LANG"] == "vi"
    assert env["LANG"] == "vi_VN"


def test_dashboard_translations():
    import main

    main.translator.set_language("en")
    assert "Enter choice" in main._T("dashboard.prompt")
    main.translator.set_language("vi")
    assert "Nhập lựa chọn" in main._T("dashboard.prompt")


def test_save_user_language():
    import configparser
    import config as config_mod
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_lang_")
    orig = utils.get_app_config_dir
    utils.get_app_config_dir = lambda: tmp
    config_mod.get_app_config_dir = lambda: tmp
    try:
        assert config_mod.save_user_language("en")
        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(tmp, "config.ini"), encoding="utf-8")
        assert cfg.get("Utils", "language") == "en"
    finally:
        utils.get_app_config_dir = orig
        config_mod.get_app_config_dir = orig
        shutil.rmtree(tmp, ignore_errors=True)


def test_extract_oauth_url():
    from mimo_platform_login import extract_oauth_url

    sample = [
        "INFO Starting OAuth flow\n",
        "INFO Open: https://platform.xiaomimimo.com/authorize?pk=abc&redirect_uri=http%3A%2F%2F127.0.0.1%3A3847\n",
    ]
    url = extract_oauth_url(sample)
    assert url is not None
    assert url.startswith("https://platform.xiaomimimo.com/authorize?")
    assert "redirect_uri=" in url

    assert extract_oauth_url(["no url here\n"]) is None
    assert extract_oauth_url(["callback http://127.0.0.1:3847/callback\n"]) is None


def test_run_providers_login_returns_early_on_url(monkeypatch=None):
    """Mock CLI stdout so run_providers_login returns when URL appears (no 120s wait)."""
    import mimo_platform_login as login

    class FakeProc:
        returncode = None

        def poll(self):
            return None

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    oauth_line = (
        "INFO https://platform.xiaomimimo.com/authorize?pk=test&redirect_uri=http%3A%2F%2F127.0.0.1%3A9999\n"
    )

    class FakeStdout:
        _done = False

        def readline(self):
            if self._done:
                return ""
            self._done = True
            return oauth_line

        def close(self):
            pass

    fake_proc = FakeProc()
    fake_proc.stdout = FakeStdout()

    orig_popen = login.subprocess.Popen

    def fake_popen(*args, **kwargs):
        return fake_proc

    login.subprocess.Popen = fake_popen
    try:
        t0 = __import__("time").time()
        url, code, lines = login.run_providers_login(timeout=5, verbose=False)
        elapsed = __import__("time").time() - t0
        assert url is not None
        assert "platform.xiaomimimo.com/authorize" in url
        assert elapsed < 3
    finally:
        login.subprocess.Popen = orig_popen


def test_open_url_via_subprocess_args():
    import chrome_profile

    calls = []

    def fake_popen(args, **kwargs):
        calls.append(args)
        class P:
            pid = 1
        return P()

    orig = chrome_profile.subprocess.Popen
    orig_path = chrome_profile.get_browser_path
    orig_user = chrome_profile.get_user_data_directory
    chrome_profile.subprocess.Popen = fake_popen
    chrome_profile.get_browser_path = lambda: "C:\\Chrome\\chrome.exe"
    chrome_profile.get_user_data_directory = lambda: "C:\\Users\\x\\AppData\\Local\\Google\\Chrome\\User Data"
    try:
        ok = chrome_profile.open_url_via_subprocess(
            "https://platform.xiaomimimo.com/authorize?pk=x",
            "Profile 5",
        )
        assert ok is True
        assert len(calls) == 1
        args = calls[0]
        assert args[0] == "C:\\Chrome\\chrome.exe"
        assert any(a.startswith("--profile-directory=Profile 5") for a in args)
        assert args[-1].startswith("https://platform.xiaomimimo.com/")
    finally:
        chrome_profile.subprocess.Popen = orig
        chrome_profile.get_browser_path = orig_path
        chrome_profile.get_user_data_directory = orig_user


def main():
    parser = argparse.ArgumentParser(description="E2E smoke tests (quiet by default)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full module output")
    parser.add_argument("--json", action="store_true", help="Print one-line JSON summary only")
    args = parser.parse_args()

    cases = [
        ("mimo slots modules import", test_mimo_slots_modules_import),
        ("chrome profile save load", test_chrome_profile_save_load),
        ("select_profile msg fallback", test_select_profile_prompt_uses_msg_fallback),
        ("mimo_paths accounts dir", test_mimo_paths_accounts_dir),
        ("mimo_account_slots crud", test_mimo_account_slots_crud),
        ("mimo wipe protects accounts", test_mimo_wipe_protects_accounts),
        ("12 mimo_reset helpers", test_12_mimo_reset_helpers),
        ("13 mimo_total helpers", test_13_mimo_total_helpers),
        ("mimo_auto setup", test_mimo_auto_setup),
        ("branding MiMo VIP", test_branding_mimo),
        ("dashboard translations", test_dashboard_translations),
        ("save user language", test_save_user_language),
        ("extract oauth url", test_extract_oauth_url),
        ("providers login early return", test_run_providers_login_returns_early_on_url),
        ("open url subprocess args", test_open_url_via_subprocess_args),
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
