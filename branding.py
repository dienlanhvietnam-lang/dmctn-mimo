"""MiMo VIP branding, config paths, and environment helpers."""
import os
import shutil

APP_NAME = "MiMo VIP"
APP_NAME_SLUG = "mimo-vip"
CONFIG_DIR_NAME = ".mimo-vip"
LEGACY_CONFIG_DIR_NAMES = (".mino-vip", ".cursor-free-vip")
GITHUB_REPO = "mino-vip/mino-vip"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_ISSUES_URL = f"{GITHUB_URL}/issues"
LEGACY_GITHUB_REPO = "hovanhoa/cursor-free-vip"
LEGACY_GITHUB_URL = f"https://github.com/{LEGACY_GITHUB_REPO}"


def resolve_config_dir(documents_path):
    """Return MiMo VIP config directory, migrating legacy folders when needed."""
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


def env_flag(name, legacy_env=None):
    for prefix in ("MIMO_VIP_", "MINO_VIP_"):
        value = os.getenv(f"{prefix}{name}", "").strip().lower()
        if value in ("1", "true", "yes", "on"):
            return True
    if legacy_env:
        value = os.getenv(legacy_env, "").strip().lower()
        return value in ("1", "true", "yes", "on")
    return False


def env_get(name, default="", legacy_env=None):
    for prefix in ("MIMO_VIP_", "MINO_VIP_"):
        value = os.getenv(f"{prefix}{name}", "").strip()
        if value:
            return value
    if legacy_env:
        return os.getenv(legacy_env, default).strip()
    return default


CLI_LOCALE_MAP = {
    "vi": "vi_VN",
    "en": "en_US",
    "zh_cn": "zh_CN",
    "zh_tw": "zh_TW",
    "de": "de_DE",
    "fr": "fr_FR",
    "es": "es_ES",
    "pt": "pt_PT",
    "ru": "ru_RU",
    "nl": "nl_NL",
    "tr": "tr_TR",
    "bg": "bg_BG",
}


def cli_process_env(lang_code: str | None = None) -> dict:
    """Environment for MiMo CLI subprocesses, synced with dashboard language."""
    env = os.environ.copy()
    code = (lang_code or env_get("LANG", legacy_env="CURSOR_FREE_VIP_LANG") or "en").strip().lower()
    env["MIMO_VIP_LANG"] = code
    env["MINO_VIP_LANG"] = code
    locale_name = CLI_LOCALE_MAP.get(code, "en_US")
    env["LANG"] = locale_name
    env["LC_ALL"] = locale_name
    return env
