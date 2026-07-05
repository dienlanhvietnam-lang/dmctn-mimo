import os
import sys
import platform
import random
import shutil
import configparser

from branding import resolve_config_dir, env_flag

def get_app_config_dir():
    """Return MiMo VIP config directory under Documents."""
    return resolve_config_dir(get_user_documents_path())


def get_user_documents_path():
    """Get user documents path"""
    if platform.system() == "Windows":
        return os.path.expanduser("~\\Documents")
    else:
        return os.path.expanduser("~/Documents")

def get_default_chrome_path():
    """Get default Chrome path"""
    if sys.platform == "win32":
        #  Trying to find chrome in PATH
        try:
            import shutil
            chrome_in_path = shutil.which("chrome")
            if chrome_in_path:
                return chrome_in_path
        except:
            pass
        # Going to default path
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    elif sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else:
        return "/usr/bin/google-chrome"

def get_linux_cursor_path():
    """Get Linux Cursor path"""
    possible_paths = [
        "/opt/Cursor/resources/app",
        "/usr/share/cursor/resources/app",
        "/opt/cursor-bin/resources/app",
        "/usr/lib/cursor/resources/app",
        os.path.expanduser("~/.local/share/cursor/resources/app")
    ]
    
    # return the first path that exists
    return next((path for path in possible_paths if os.path.exists(path)), possible_paths[0])

def _is_valid_cursor_app_path(path):
    return path and os.path.isfile(os.path.join(path, "package.json"))

def resolve_cursor_app_path(configured_path=None):
    """Find Cursor resources/app directory, preferring a valid configured path."""
    if _is_valid_cursor_app_path(configured_path):
        return os.path.normpath(configured_path)

    candidates = []
    if sys.platform == "win32":
        for name in ("cursor", "cursor.cmd"):
            cursor_bin = shutil.which(name)
            if cursor_bin:
                candidates.append(os.path.normpath(os.path.join(os.path.dirname(cursor_bin), "..")))
        localappdata = os.getenv("LOCALAPPDATA", "")
        candidates.extend([
            os.path.join(localappdata, "Programs", "Cursor", "resources", "app"),
            os.path.join(localappdata, "Programs", "cursor", "resources", "app"),
            r"C:\Program Files\Cursor\resources\app",
        ])
    elif sys.platform == "darwin":
        candidates.append("/Applications/Cursor.app/Contents/Resources/app")
    else:
        candidates.extend([
            get_linux_cursor_path(),
            "/opt/Cursor/resources/app",
            "/usr/share/cursor/resources/app",
            os.path.expanduser("~/.local/share/cursor/resources/app"),
        ])

    seen = set()
    for path in candidates:
        path = os.path.normpath(path)
        if path in seen:
            continue
        seen.add(path)
        if _is_valid_cursor_app_path(path):
            return path

    return os.path.normpath(configured_path) if configured_path else None

def get_cursor_paths_section():
    if sys.platform == "win32":
        return "WindowsPaths"
    if sys.platform == "darwin":
        return "MacPaths"
    return "LinuxPaths"

def persist_cursor_app_path(app_path):
    """Save resolved Cursor app path and related paths to config.ini."""
    if not app_path:
        return
    config_dir = get_app_config_dir()
    config_file = os.path.join(config_dir, "config.ini")
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file, encoding="utf-8")
    section = get_cursor_paths_section()
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, "cursor_path", app_path)
    config.set(section, "product_json_path", os.path.join(app_path, "product.json"))
    resources_dir = os.path.dirname(app_path)
    for name in ("app-update.yml", "update.yml"):
        update_yml = os.path.join(resources_dir, name)
        if os.path.exists(update_yml) or name == "app-update.yml":
            config.set(section, "update_yml_path", update_yml)
            break
    os.makedirs(config_dir, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        config.write(f)

def get_configured_cursor_app_path():
    config_dir = get_app_config_dir()
    config_file = os.path.join(config_dir, "config.ini")
    configured = None
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")
        section = get_cursor_paths_section()
        if config.has_section(section) and config.has_option(section, "cursor_path"):
            configured = config.get(section, "cursor_path")
    return configured

def get_resolved_cursor_app_path(configured_path=None):
    """Resolve Cursor app path and persist when auto-detected."""
    if configured_path is None:
        configured_path = get_configured_cursor_app_path()
    resolved = resolve_cursor_app_path(configured_path)
    if resolved and resolved != configured_path:
        persist_cursor_app_path(resolved)
    elif resolved and not configured_path:
        persist_cursor_app_path(resolved)
    return resolved

def get_cursor_product_json_path(configured_path=None):
    app_path = get_resolved_cursor_app_path(configured_path)
    if not app_path:
        return None
    path = os.path.join(app_path, "product.json")
    return path if os.path.isfile(path) else None

def get_cursor_main_js_path(configured_path=None):
    app_path = get_resolved_cursor_app_path(configured_path)
    if not app_path:
        return None
    path = os.path.join(app_path, "out", "main.js")
    return path if os.path.isfile(path) else None

def get_cursor_workbench_path(app_path=None):
    """Return path to workbench.desktop.main.js."""
    base = app_path or get_resolved_cursor_app_path()
    if not base:
        return None
    main = os.path.join(base, "out", "vs", "workbench", "workbench.desktop.main.js")
    return main if os.path.isfile(main) else None

def should_keep_cursor_running():
    return env_flag("KEEP_RUNNING", legacy_env="CURSOR_FREE_VIP_KEEP_RUNNING")

def get_random_wait_time(config, timing_key):
    """Get random wait time based on configuration timing settings
    
    Args:
        config (dict): Configuration dictionary containing timing settings
        timing_key (str): Key to look up in the timing settings
        
    Returns:
        float: Random wait time in seconds
    """
    try:
        # Get timing value from config
        timing = config.get('Timing', {}).get(timing_key)
        if not timing:
            # Default to 0.5-1.5 seconds if timing not found
            return random.uniform(0.5, 1.5)
            
        # Check if timing is a range (e.g., "0.5-1.5" or "0.5,1.5")
        if isinstance(timing, str):
            if '-' in timing:
                min_time, max_time = map(float, timing.split('-'))
            elif ',' in timing:
                min_time, max_time = map(float, timing.split(','))
            else:
                # Single value, use it as both min and max
                min_time = max_time = float(timing)
        else:
            # If timing is a number, use it as both min and max
            min_time = max_time = float(timing)
            
        return random.uniform(min_time, max_time)
        
    except (ValueError, TypeError, AttributeError):
        # Return default value if any error occurs
        return random.uniform(0.5, 1.5) 