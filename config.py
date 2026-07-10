import os
import configparser
import shutil
import datetime

from colorama import Fore, Style
from branding import env_flag
from utils import get_default_chrome_path, get_app_config_dir
import icons as _icons

EMOJI = {
    "INFO": _icons.INFO,
    "WARNING": _icons.WARNING,
    "ERROR": _icons.ERROR,
    "SUCCESS": _icons.SUCCESS,
    "ADMIN": _icons.ADMIN,
    "ARROW": _icons.ARROW,
    "USER": _icons.INFO,
    "KEY": _icons.OAUTH,
    "SETTINGS": _icons.MENU,
}


def setup_config(translator=None):
    """Setup configuration file and return config object."""
    try:
        config_dir = get_app_config_dir()
        config_file = os.path.join(config_dir, "config.ini")
        os.makedirs(config_dir, exist_ok=True)

        config = configparser.ConfigParser()
        default_config = {
            "Chrome": {
                "chromepath": get_default_chrome_path(),
                "profile_directory": "",
                "profile_display_name": "",
            },
            "Turnstile": {
                "handle_turnstile_time": "2",
                "handle_turnstile_random_time": "1-3",
            },
            "Timing": {
                "min_random_time": "0.1",
                "max_random_time": "0.8",
                "page_load_wait": "0.1-0.8",
                "input_wait": "0.3-0.8",
                "submit_wait": "0.5-1.5",
                "verification_code_input": "0.1-0.3",
                "verification_success_wait": "2-3",
                "verification_retry_wait": "2-3",
                "email_check_initial_wait": "4-6",
                "email_refresh_wait": "2-4",
                "settings_page_load_wait": "1-2",
                "failed_retry_time": "0.5-1",
                "retry_interval": "8-12",
                "max_timeout": "160",
            },
            "Utils": {
                "enabled_update_check": "True",
                "enabled_force_update": "False",
                "enabled_account_info": "False",
                "language": "vi",
            },
        }

        if os.path.exists(config_file):
            config.read(config_file, encoding="utf-8")
            config_modified = False

            for section, options in default_config.items():
                if not config.has_section(section):
                    config.add_section(section)
                    config_modified = True
                for option, value in options.items():
                    if not config.has_option(section, option):
                        config.set(section, option, str(value))
                        config_modified = True
                        if translator:
                            print(
                                f"{Fore.YELLOW}{EMOJI['INFO']} "
                                f"{translator.get('config.config_option_added', option=f'{section}.{option}')}"
                                f"{Style.RESET_ALL}"
                            )

            if config_modified:
                with open(config_file, "w", encoding="utf-8") as f:
                    config.write(f)
                if translator:
                    print(
                        f"{Fore.GREEN}{EMOJI['SUCCESS']} "
                        f"{translator.get('config.config_updated')}"
                        f"{Style.RESET_ALL}"
                    )
        else:
            for section, options in default_config.items():
                config.add_section(section)
                for option, value in options.items():
                    config.set(section, option, str(value))

            with open(config_file, "w", encoding="utf-8") as f:
                config.write(f)
                if translator:
                    print(
                        f"{Fore.GREEN}{EMOJI['SUCCESS']} "
                        f"{translator.get('config.config_created', config_file=config_file)}"
                        f"{Style.RESET_ALL}"
                    )

        return config

    except Exception as e:
        if translator:
            print(
                f"{Fore.RED}{EMOJI['ERROR']} "
                f"{translator.get('config.config_setup_error', error=str(e))}"
                f"{Style.RESET_ALL}"
            )
        return None


def force_update_config(translator=None):
    """Force update configuration file with latest defaults if enabled."""
    try:
        config_dir = get_app_config_dir()
        config_file = os.path.join(config_dir, "config.ini")
        current_time = datetime.datetime.now()

        if os.path.exists(config_file):
            existing_config = configparser.ConfigParser()
            existing_config.read(config_file, encoding="utf-8")
            update_enabled = True
            if existing_config.has_section("Utils") and existing_config.has_option(
                "Utils", "enabled_force_update"
            ):
                update_enabled = existing_config.get("Utils", "enabled_force_update").strip().lower() in (
                    "true",
                    "yes",
                    "1",
                    "on",
                )

            if update_enabled:
                try:
                    backup_file = f"{config_file}.bak.{current_time.strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(config_file, backup_file)
                    if translator:
                        print(
                            f"\n{Fore.CYAN}{EMOJI['INFO']} "
                            f"{translator.get('config.backup_created', path=backup_file)}"
                            f"{Style.RESET_ALL}"
                        )
                    print(
                        f"\n{Fore.CYAN}{EMOJI['INFO']} "
                        f"{translator.get('config.config_force_update_enabled')}"
                        f"{Style.RESET_ALL}"
                    )
                    os.remove(config_file)
                    if translator:
                        print(
                            f"{Fore.CYAN}{EMOJI['INFO']} "
                            f"{translator.get('config.config_removed')}"
                            f"{Style.RESET_ALL}"
                        )
                except Exception as e:
                    if translator:
                        print(
                            f"{Fore.RED}{EMOJI['ERROR']} "
                            f"{translator.get('config.backup_failed', error=str(e))}"
                            f"{Style.RESET_ALL}"
                        )
            elif translator and not env_flag("QUIET", legacy_env="DMCTN_MIMO_QUIET"):
                print(
                    f"\n{Fore.CYAN}{EMOJI['INFO']} "
                    f"{translator.get('config.config_force_update_disabled')}"
                    f"{Style.RESET_ALL}"
                )

        return setup_config(translator)

    except Exception as e:
        if translator:
            print(
                f"{Fore.RED}{EMOJI['ERROR']} "
                f"{translator.get('config.force_update_failed', error=str(e))}"
                f"{Style.RESET_ALL}"
            )
        return None


def get_config(translator=None):
    """Get existing config or create new one."""
    return setup_config(translator)


def save_user_language(lang_code: str) -> bool:
    """Persist UI language choice to config.ini (Utils.language)."""
    try:
        config_dir = get_app_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.ini")
        config = configparser.ConfigParser()
        if os.path.isfile(config_file):
            config.read(config_file, encoding="utf-8")
        if not config.has_section("Utils"):
            config.add_section("Utils")
        config.set("Utils", "language", lang_code.strip().lower())
        with open(config_file, "w", encoding="utf-8") as f:
            config.write(f)
        return True
    except OSError:
        return False
