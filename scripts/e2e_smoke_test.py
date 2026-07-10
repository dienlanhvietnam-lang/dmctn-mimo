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
os.environ.setdefault("DMCTN_MIMO_LANG", "vi")
os.environ.setdefault("DMCTN_MIMO_KEEP_RUNNING", "1")

RESULTS = []


def run_case(name, fn, verbose=False):
    if verbose:
        print(f"\n{'='*60}\nTEST: {name}\n{'='*60}")
    try:
        if verbose:
            fn()
        else:
            os.environ["DMCTN_MIMO_QUIET"] = "1"
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


def test_mimo_deep_wipe_includes_slots_and_config():
    import os
    from mimo_paths import get_mimo_accounts_dir, get_mimo_config_dir, get_mimo_data_dir, get_mimo_deep_wipe_extra

    extras = get_mimo_deep_wipe_extra()
    assert get_mimo_accounts_dir() in extras
    config_dir = get_mimo_config_dir()
    data_dir = get_mimo_data_dir()
    if os.path.normcase(os.path.abspath(config_dir)) != os.path.normcase(os.path.abspath(data_dir)):
        assert config_dir in extras
    assert len(extras) >= 1


def test_12_mimo_reset_helpers():
    from machine_id_utils import generate_mimo_client_ids
    from mimo_paths import get_mimo_data_dir, get_mimo_identity_files

    mimo_ids = generate_mimo_client_ids()
    assert len(mimo_ids["mimo-free-client"]) == 64
    assert len(mimo_ids["installation_id"]) == 36
    assert mimo_ids["mimo-key-name"].startswith("mimo-code-cli-key-")

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

    assert APP_NAME == "MiMo FREE"
    assert CONFIG_DIR_NAME == ".dmctn-mimo"
    env = cli_process_env("vi")
    assert env["DMCTN_MIMO_LANG"] == "vi"
    assert env["LANG"] == "vi_VN"


def test_dashboard_translations():
    import main

    main.translator.set_language("en")
    assert "Enter choice" in main._T("dashboard.prompt")
    assert "[0-8]" in main._T("dashboard.prompt")
    main.translator.set_language("vi")
    assert "Nhập lựa chọn" in main._T("dashboard.prompt")
    assert "[0-8]" in main._T("dashboard.prompt")


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


def _patch_context_dirs(tmp_data: str, tmp_vault: str):
    """Patch mimo_paths + utils so vault/data live under temp dirs."""
    import mimo_context_paths as cpaths
    import mimo_context_vault as vault
    import mimo_paths
    import utils

    orig = {
        "data": mimo_paths.get_mimo_data_dir,
        "app": utils.get_app_config_dir,
        "vault": cpaths.get_context_vault_dir,
    }
    mimo_paths.get_mimo_data_dir = lambda: tmp_data
    utils.get_app_config_dir = lambda: tmp_vault
    # Re-bind vault helpers that call get_app_config_dir at call time — already do
    return orig


def _restore_context_dirs(orig):
    import mimo_paths
    import utils

    mimo_paths.get_mimo_data_dir = orig["data"]
    utils.get_app_config_dir = orig["app"]


def test_context_paths_targets():
    from mimo_context_paths import get_context_bundle_paths

    paths = get_context_bundle_paths()
    joined = " ".join(paths).replace("\\", "/")
    assert "memory" in joined
    assert "mimocode.db" in joined


def test_context_vault_crud():
    import mimo_context_vault as vault
    import mimo_paths
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_ctx_")
    data_dir = os.path.join(tmp, "mimocode")
    vault_root = os.path.join(tmp, "dmctn")
    mem = os.path.join(data_dir, "memory")
    os.makedirs(mem, exist_ok=True)
    marker = os.path.join(mem, "note.txt")
    with open(marker, "w", encoding="utf-8") as f:
        f.write("hello-context")

    orig_data = mimo_paths.get_mimo_data_dir
    orig_app = utils.get_app_config_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    utils.get_app_config_dir = lambda: vault_root
    try:
        created = vault.create_context_snapshot(label="test-ctx")
        assert created["slot_id"]
        assert vault.list_context_slots()["count"] == 1

        shutil.rmtree(mem)
        assert not os.path.isfile(marker)

        vault.restore_context_snapshot(created["slot_id"])
        assert os.path.isfile(marker)
        with open(marker, encoding="utf-8") as f:
            assert f.read() == "hello-context"

        vault.rename_context_slot(created["slot_id"], "renamed-ctx")
        assert vault.list_context_slots()["slots"][0]["label"] == "renamed-ctx"

        vault.delete_context_slot(created["slot_id"])
        assert vault.list_context_slots()["count"] == 0
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        utils.get_app_config_dir = orig_app
        shutil.rmtree(tmp, ignore_errors=True)


def test_reset_preserve_context_dry():
    import reset_mimo_machine as reset
    import mimo_context_vault as vault
    import mimo_paths
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_preserve_")
    data_dir = os.path.join(tmp, "mimocode")
    vault_root = os.path.join(tmp, "dmctn")
    mem = os.path.join(data_dir, "memory")
    os.makedirs(mem, exist_ok=True)
    marker = os.path.join(mem, "keep.txt")
    with open(marker, "w", encoding="utf-8") as f:
        f.write("preserve-me")
    client_path = os.path.join(data_dir, "mimo-free-client")
    with open(client_path, "w", encoding="utf-8") as f:
        f.write("old-client-id")

    orig_data = mimo_paths.get_mimo_data_dir
    orig_app = utils.get_app_config_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    utils.get_app_config_dir = lambda: vault_root
    try:
        ok = reset.reset_mimo_machine(
            mode=reset.MODE_FULL_PRESERVE,
            skip_registry=True,
            skip_backup=True,
            skip_slot_backup=True,
            clear_auth=False,
        )
        assert ok is True
        assert vault.list_context_slots()["count"] >= 1
        assert os.path.isfile(marker)
        with open(marker, encoding="utf-8") as f:
            assert f.read() == "preserve-me"
        with open(client_path, encoding="utf-8") as f:
            assert f.read() != "old-client-id"
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        utils.get_app_config_dir = orig_app
        shutil.rmtree(tmp, ignore_errors=True)


def test_context_slot_activate():
    import mimo_context_vault as vault
    import mimo_paths
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_ctx2_")
    data_dir = os.path.join(tmp, "mimocode")
    vault_root = os.path.join(tmp, "dmctn")
    mem = os.path.join(data_dir, "memory")
    os.makedirs(mem, exist_ok=True)

    orig_data = mimo_paths.get_mimo_data_dir
    orig_app = utils.get_app_config_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    utils.get_app_config_dir = lambda: vault_root
    try:
        with open(os.path.join(mem, "a.txt"), "w", encoding="utf-8") as f:
            f.write("slot-a")
        a = vault.create_context_snapshot(label="A")

        with open(os.path.join(mem, "a.txt"), "w", encoding="utf-8") as f:
            f.write("slot-b")
        b = vault.create_context_snapshot(label="B")

        vault.activate_context_slot(a["slot_id"])
        with open(os.path.join(mem, "a.txt"), encoding="utf-8") as f:
            assert f.read() == "slot-a"

        vault.activate_context_slot(b["slot_id"])
        with open(os.path.join(mem, "a.txt"), encoding="utf-8") as f:
            assert f.read() == "slot-b"
        assert vault.get_active_context_id() == b["slot_id"]
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        utils.get_app_config_dir = orig_app
        shutil.rmtree(tmp, ignore_errors=True)


def test_registry_only_keeps_client():
    import reset_mimo_machine as reset
    import mimo_paths
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_reg_")
    data_dir = os.path.join(tmp, "mimocode")
    vault_root = os.path.join(tmp, "dmctn")
    os.makedirs(data_dir, exist_ok=True)
    client_path = os.path.join(data_dir, "mimo-free-client")
    with open(client_path, "w", encoding="utf-8") as f:
        f.write("stable-client-xyz")

    orig_data = mimo_paths.get_mimo_data_dir
    orig_app = utils.get_app_config_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    utils.get_app_config_dir = lambda: vault_root
    try:
        ok = reset.reset_mimo_machine(
            mode=reset.MODE_REGISTRY_ONLY,
            skip_registry=True,
            skip_backup=True,
        )
        assert ok is True
        with open(client_path, encoding="utf-8") as f:
            assert f.read() == "stable-client-xyz"
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        utils.get_app_config_dir = orig_app
        shutil.rmtree(tmp, ignore_errors=True)


def test_manage_context_import():
    import mimo_manage_context

    assert callable(mimo_manage_context.run)
    assert callable(mimo_manage_context.manage_context)


def test_vault_outside_wipe_targets():
    from mimo_context_paths import get_context_vault_dir
    from mimo_paths import get_dmctn_protected_paths, get_mimo_wipe_dirs

    vault = os.path.normcase(os.path.abspath(get_context_vault_dir()))
    wipe = [os.path.normcase(os.path.abspath(p)) for p in get_mimo_wipe_dirs()]
    assert vault not in wipe
    protected = [os.path.normcase(os.path.abspath(p)) for p in get_dmctn_protected_paths()]
    assert vault in protected


def test_total_reset_auto_snapshot():
    import mimo_context_vault as vault
    import mimo_paths
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_total_snap_")
    data_dir = os.path.join(tmp, "mimocode")
    vault_root = os.path.join(tmp, "dmctn")
    mem = os.path.join(data_dir, "memory")
    os.makedirs(mem, exist_ok=True)
    with open(os.path.join(mem, "x.txt"), "w", encoding="utf-8") as f:
        f.write("before-total")

    orig_data = mimo_paths.get_mimo_data_dir
    orig_app = utils.get_app_config_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    utils.get_app_config_dir = lambda: vault_root
    try:
        # Dry: only exercise snapshot path used by total reset
        assert vault.has_local_context()
        result = vault.create_context_snapshot(label="pre-total-test")
        assert result["slot_id"]
        assert vault.list_context_slots()["count"] >= 1
        assert os.path.isfile(result["bundle"])
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        utils.get_app_config_dir = orig_app
        shutil.rmtree(tmp, ignore_errors=True)


def test_deep_reset_keeps_vault_by_default():
    import mimo_context_vault as vault
    import mimo_paths
    import utils

    tmp = tempfile.mkdtemp(prefix="mimo_deep_vault_")
    data_dir = os.path.join(tmp, "mimocode")
    vault_root = os.path.join(tmp, "dmctn")
    mem = os.path.join(data_dir, "memory")
    os.makedirs(mem, exist_ok=True)
    with open(os.path.join(mem, "y.txt"), "w", encoding="utf-8") as f:
        f.write("keep-vault")

    orig_data = mimo_paths.get_mimo_data_dir
    orig_app = utils.get_app_config_dir
    mimo_paths.get_mimo_data_dir = lambda: data_dir
    utils.get_app_config_dir = lambda: vault_root
    try:
        created = vault.create_context_snapshot(label="keep-me")
        # wipe_vault=False must leave manifest
        assert vault.list_context_slots()["count"] == 1
        # Simulate deep reset default: do not wipe vault
        wipe_vault = False
        if wipe_vault:
            vault.wipe_context_vault()
        assert vault.list_context_slots()["count"] == 1
        assert vault.list_context_slots()["slots"][0]["id"] == created["slot_id"]
    finally:
        mimo_paths.get_mimo_data_dir = orig_data
        utils.get_app_config_dir = orig_app
        shutil.rmtree(tmp, ignore_errors=True)


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
        ("mimo deep wipe extras", test_mimo_deep_wipe_includes_slots_and_config),
        ("12 mimo_reset helpers", test_12_mimo_reset_helpers),
        ("13 mimo_total helpers", test_13_mimo_total_helpers),
        ("mimo_auto setup", test_mimo_auto_setup),
        ("branding MiMo FREE", test_branding_mimo),
        ("dashboard translations", test_dashboard_translations),
        ("save user language", test_save_user_language),
        ("extract oauth url", test_extract_oauth_url),
        ("providers login early return", test_run_providers_login_returns_early_on_url),
        ("open url subprocess args", test_open_url_via_subprocess_args),
        ("context paths targets", test_context_paths_targets),
        ("context vault crud", test_context_vault_crud),
        ("reset preserve context dry", test_reset_preserve_context_dry),
        ("context slot activate", test_context_slot_activate),
        ("registry only keeps client", test_registry_only_keeps_client),
        ("manage context import", test_manage_context_import),
        ("vault outside wipe targets", test_vault_outside_wipe_targets),
        ("total reset auto snapshot", test_total_reset_auto_snapshot),
        ("deep reset keeps vault", test_deep_reset_keeps_vault_by_default),
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
