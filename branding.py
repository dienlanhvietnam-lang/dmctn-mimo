"""DMCTN / MiMo FREE branding, config paths, and environment helpers."""
import os
import shutil

APP_NAME = "MiMo FREE"
APP_AUTHOR = "DMCTN"
APP_NAME_SLUG = "dmctn-mimo"
CONFIG_DIR_NAME = ".dmctn-mimo"
# Legacy config folders on disk (migration only — not displayed as product name)
LEGACY_CONFIG_DIR_NAMES = (".mimo-vip", ".mino-vip", ".cursor-free-vip")
GITHUB_ORG = "dienlanhvietnam-lang"
GITHUB_REPO = f"{GITHUB_ORG}/{APP_NAME_SLUG}"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_ORG_URL = f"https://github.com/{GITHUB_ORG}"
GITHUB_ISSUES_URL = f"{GITHUB_URL}/issues"

ENV_PREFIX = "DMCTN_MIMO_"
# Read old env names silently when migrating user setups (do not set these in new code)
_LEGACY_ENV_PREFIXES = ("MIMO_VIP_", "MINO_VIP_")
_LEGACY_ENV_FULL = {
    "LANG": ("CURSOR_FREE_VIP_LANG",),
    "KEEP_RUNNING": ("CURSOR_FREE_VIP_KEEP_RUNNING",),
    "QUIET": ("CURSOR_FREE_VIP_QUIET",),
}


def resolve_config_dir(documents_path):
    """Return DMCTN MiMo config directory, migrating legacy folders when needed."""
    new_dir = os.path.join(documents_path, CONFIG_DIR_NAME)
    if os.path.isdir(new_dir):
        return new_dir
    for legacy_name in LEGACY_CONFIG_DIR_NAMES:
        legacy_dir = os.path.join(documents_path, legacy_name)
        if os.path.isdir(legacy_dir):
            try:
                shutil.copytree(legacy_dir, new_dir)
                return new_dir
            except OSError:
                return legacy_dir
    return new_dir


def _legacy_env_values(name: str) -> tuple[str, ...]:
    keys = _LEGACY_ENV_FULL.get(name, ())
    return keys


def env_flag(name, legacy_env=None) -> bool:
    value = os.getenv(f"{ENV_PREFIX}{name}", "").strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    for prefix in _LEGACY_ENV_PREFIXES:
        value = os.getenv(f"{prefix}{name}", "").strip().lower()
        if value in ("1", "true", "yes", "on"):
            return True
    for key in _legacy_env_values(name):
        value = os.getenv(key, "").strip().lower()
        if value in ("1", "true", "yes", "on"):
            return True
    if legacy_env:
        value = os.getenv(legacy_env, "").strip().lower()
        return value in ("1", "true", "yes", "on")
    return False


def env_get(name, default="", legacy_env=None) -> str:
    value = os.getenv(f"{ENV_PREFIX}{name}", "").strip()
    if value:
        return value
    for prefix in _LEGACY_ENV_PREFIXES:
        value = os.getenv(f"{prefix}{name}", "").strip()
        if value:
            return value
    for key in _legacy_env_values(name):
        value = os.getenv(key, "").strip()
        if value:
            return value
    if legacy_env:
        return os.getenv(legacy_env, default).strip()
    return default


CLI_LOCALE_MAP = {
    "vi": "vi_VN",
    "en": "en_US",
}


def cli_process_env(lang_code: str | None = None) -> dict:
    """Environment for MiMo CLI subprocesses, synced with dashboard language."""
    env = os.environ.copy()
    code = (lang_code or env_get("LANG") or "en").strip().lower()
    env[f"{ENV_PREFIX}LANG"] = code
    locale_name = CLI_LOCALE_MAP.get(code, "en_US")
    env["LANG"] = locale_name
    env["LC_ALL"] = locale_name
    return env
