import os
import sys
import platform
import random
import shutil

from branding import resolve_config_dir, env_flag


def get_app_config_dir():
    """Return MiMo FREE config directory under Documents."""
    return resolve_config_dir(get_user_documents_path())


def get_user_documents_path():
    """Get user documents path."""
    if platform.system() == "Windows":
        return os.path.expanduser("~\\Documents")
    return os.path.expanduser("~/Documents")


def get_default_chrome_path():
    """Get default Chrome path."""
    if os.name == "nt":
        try:
            chrome_in_path = shutil.which("chrome")
            if chrome_in_path:
                return chrome_in_path
        except OSError:
            pass
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return "/usr/bin/google-chrome"


def should_keep_chrome_running():
    return env_flag("KEEP_RUNNING", legacy_env="DMCTN_MIMO_KEEP_RUNNING")


def get_random_wait_time(config, timing_key):
    """Get random wait time based on configuration timing settings."""
    try:
        timing = config.get("Timing", {}).get(timing_key)
        if not timing:
            return random.uniform(0.5, 1.5)

        if isinstance(timing, str):
            if "-" in timing:
                min_time, max_time = map(float, timing.split("-"))
            elif "," in timing:
                min_time, max_time = map(float, timing.split(","))
            else:
                min_time = max_time = float(timing)
        else:
            min_time = max_time = float(timing)

        return random.uniform(min_time, max_time)
    except (ValueError, TypeError, AttributeError):
        return random.uniform(0.5, 1.5)
