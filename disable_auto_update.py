import os
import sys
import platform
import shutil
from colorama import Fore, Style, init
import subprocess
from config import get_config
import re
import tempfile
from utils import (
    get_resolved_cursor_app_path,
    get_cursor_product_json_path,
    get_cursor_paths_section,
    should_keep_cursor_running,
)

# Initialize colorama
init()

# Define emoji constants
EMOJI = {
    "PROCESS": "🔄",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "FOLDER": "📁",
    "FILE": "📄",
    "STOP": "🛑",
    "CHECK": "✔️"
}

class AutoUpdateDisabler:
    def __init__(self, translator=None):
        self.translator = translator
        self.system = platform.system()
        
        # Get path from configuration file
        config = get_config(translator)
        if config:
            section = get_cursor_paths_section()
            configured_app = config.get(section, 'cursor_path', fallback='') if config.has_section(section) else ''
            app_path = get_resolved_cursor_app_path(configured_app)
            if app_path:
                self.product_json_path = os.path.join(app_path, 'product.json')
                resources_dir = os.path.dirname(app_path)
                for name in ('app-update.yml', 'update.yml'):
                    update_yml = os.path.join(resources_dir, name)
                    if os.path.exists(update_yml) or name == 'app-update.yml':
                        self.update_yml_path = update_yml
                        break
            if self.system == "Windows":
                self.updater_path = config.get('WindowsPaths', 'updater_path', fallback=os.path.join(os.getenv("LOCALAPPDATA", ""), "cursor-updater"))
            elif self.system == "Darwin":
                self.updater_path = config.get('MacPaths', 'updater_path', fallback=os.path.expanduser("~/Library/Application Support/cursor-updater"))
            elif self.system == "Linux":
                self.updater_path = config.get('LinuxPaths', 'updater_path', fallback=os.path.expanduser("~/.config/cursor-updater"))

            if not app_path:
                if self.system == "Windows":
                    self.update_yml_path = config.get('WindowsPaths', 'update_yml_path', fallback=os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app-update.yml"))
                    self.product_json_path = config.get('WindowsPaths', 'product_json_path', fallback=os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "product.json"))
                elif self.system == "Darwin":
                    self.update_yml_path = config.get('MacPaths', 'update_yml_path', fallback="/Applications/Cursor.app/Contents/Resources/app-update.yml")
                    self.product_json_path = config.get('MacPaths', 'product_json_path', fallback="/Applications/Cursor.app/Contents/Resources/app/product.json")
                elif self.system == "Linux":
                    self.update_yml_path = config.get('LinuxPaths', 'update_yml_path', fallback=os.path.expanduser("~/.config/cursor/resources/app-update.yml"))
                    self.product_json_path = config.get('LinuxPaths', 'product_json_path', fallback=os.path.expanduser("~/.config/cursor/resources/app/product.json"))
        else:
            # If configuration loading fails, use default paths
            self.updater_paths = {
                "Windows": os.path.join(os.getenv("LOCALAPPDATA", ""), "cursor-updater"),
                "Darwin": os.path.expanduser("~/Library/Application Support/cursor-updater"),
                "Linux": os.path.expanduser("~/.config/cursor-updater")
            }
            self.updater_path = self.updater_paths.get(self.system)
            
            self.update_yml_paths = {
                "Windows": os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "update.yml"),
                "Darwin": "/Applications/Cursor.app/Contents/Resources/app-update.yml",
                "Linux": os.path.expanduser("~/.config/cursor/resources/app-update.yml")
            }
            self.update_yml_path = self.update_yml_paths.get(self.system)

            self.product_json_paths = {
                "Windows": os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "product.json"),
                "Darwin": "/Applications/Cursor.app/Contents/Resources/app/product.json",
                "Linux": os.path.expanduser("~/.config/cursor/resources/app/product.json")
            }
            self.product_json_path = self.product_json_paths.get(self.system)

    def _remove_update_url(self):
        """Remove update URL"""
        try:
            original_stat = os.stat(self.product_json_path)
            original_mode = original_stat.st_mode
            original_uid = original_stat.st_uid
            original_gid = original_stat.st_gid

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                with open(self.product_json_path, "r", encoding="utf-8") as product_json_file:
                    content = product_json_file.read()
                
                patterns = {
                    r"https://api2.cursor.sh/aiserver.v1.AuthService/DownloadUpdate": r"",
                    r"https://api2.cursor.sh/updates": r"",
                    r"http://cursorapi.com/updates": r"",
                }
                
                for pattern, replacement in patterns.items():
                    content = re.sub(pattern, replacement, content)

                tmp_file.write(content)
                tmp_path = tmp_file.name

            shutil.copy2(self.product_json_path, self.product_json_path + ".old")
            shutil.move(tmp_path, self.product_json_path)

            os.chmod(self.product_json_path, original_mode)
            if os.name != "nt":
                os.chown(self.product_json_path, original_uid, original_gid)

            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('reset.file_modified')}{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('reset.modify_file_failed', error=str(e))}{Style.RESET_ALL}")
            if "tmp_path" in locals():
                os.unlink(tmp_path)
            return False

    def _kill_cursor_processes(self):
        """End all Cursor processes unless keep-running mode is enabled."""
        if should_keep_cursor_running():
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('update.keep_cursor_running') if self.translator else 'Giữ Cursor đang chạy, bỏ qua bước tắt process.'}{Style.RESET_ALL}")
            return True
        try:
            print(f"{Fore.CYAN}{EMOJI['PROCESS']} {self.translator.get('update.killing_processes') if self.translator else '正在结束 Cursor 进程...'}{Style.RESET_ALL}")
            
            if self.system == "Windows":
                subprocess.run(['taskkill', '/F', '/IM', 'Cursor.exe', '/T'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'Cursor'], capture_output=True)
                
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('update.processes_killed') if self.translator else 'Cursor 进程已结束'}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('update.kill_process_failed', error=str(e)) if self.translator else f'结束进程失败: {e}'}{Style.RESET_ALL}")
            return False

    def _remove_updater_directory(self):
        """Delete updater directory"""
        try:
            updater_path = self.updater_path
            if not updater_path:
                raise OSError(self.translator.get('update.unsupported_os', system=self.system) if self.translator else f"不支持的操作系统: {self.system}")

            print(f"{Fore.CYAN}{EMOJI['FOLDER']} {self.translator.get('update.removing_directory') if self.translator else '正在删除更新程序目录...'}{Style.RESET_ALL}")
            
            if os.path.exists(updater_path):
                try:
                    if os.path.isdir(updater_path):
                        shutil.rmtree(updater_path)
                    else:
                        os.remove(updater_path)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('update.directory_removed') if self.translator else '更新程序目录已删除'}{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('update.directory_locked', path=updater_path) if self.translator else f'更新程序目录已被锁定，跳过删除: {updater_path}'}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('update.remove_directory_failed', error=str(e)) if self.translator else f'删除目录失败: {e}'}{Style.RESET_ALL}")
            return True
    
    def _clear_update_yml_file(self):
        """Clear update.yml file"""
        try:
            update_yml_path = self.update_yml_path
            if not update_yml_path:
                raise OSError(self.translator.get('update.unsupported_os', system=self.system) if self.translator else f"不支持的操作系统: {self.system}")
            
            print(f"{Fore.CYAN}{EMOJI['FILE']} {self.translator.get('update.clearing_update_yml') if self.translator else '正在清空更新配置文件...'}{Style.RESET_ALL}")
            
            if os.path.exists(update_yml_path):
                try:
                    with open(update_yml_path, 'w') as f:
                        f.write('')
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('update.update_yml_cleared') if self.translator else '更新配置文件已清空'}{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('update.yml_locked') if self.translator else '更新配置文件已被锁定，跳过清空'}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('update.update_yml_not_found') if self.translator else '更新配置文件不存在'}{Style.RESET_ALL}")
            return True
                
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('update.clear_update_yml_failed', error=str(e)) if self.translator else f'清空更新配置文件失败: {e}'}{Style.RESET_ALL}")
            return False

    def _create_blocking_file(self):
        """Create blocking files"""
        try:
            # 检查 updater_path
            updater_path = self.updater_path
            if not updater_path:
                raise OSError(self.translator.get('update.unsupported_os', system=self.system) if self.translator else f"不支持的操作系统: {self.system}")

            print(f"{Fore.CYAN}{EMOJI['FILE']} {self.translator.get('update.creating_block_file') if self.translator else '正在创建阻止文件...'}{Style.RESET_ALL}")
            
            # 创建 updater_path 阻止文件
            try:
                os.makedirs(os.path.dirname(updater_path), exist_ok=True)
                open(updater_path, 'w').close()
                
                # 设置 updater_path 为只读
                if self.system == "Windows":
                    os.system(f'attrib +r "{updater_path}"')
                else:
                    os.chmod(updater_path, 0o444)  # 设置为只读
                
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('update.block_file_created') if self.translator else '阻止文件已创建'}: {updater_path}{Style.RESET_ALL}")
            except PermissionError:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('update.block_file_locked') if self.translator else '阻止文件已被锁定，跳过创建'}{Style.RESET_ALL}")
            
            # 检查 update_yml_path
            update_yml_path = self.update_yml_path
            if update_yml_path and os.path.exists(os.path.dirname(update_yml_path)):
                try:
                    # 创建 update_yml_path 阻止文件
                    with open(update_yml_path, 'w') as f:
                        f.write('# This file is locked to prevent auto-updates\nversion: 0.0.0\n')
                    
                    # 设置 update_yml_path 为只读
                    if self.system == "Windows":
                        os.system(f'attrib +r "{update_yml_path}"')
                    else:
                        os.chmod(update_yml_path, 0o444)  # 设置为只读
                    
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('update.yml_locked') if self.translator else '更新配置文件已锁定'}: {update_yml_path}{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('update.yml_already_locked') if self.translator else '更新配置文件已被锁定，跳过修改'}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('update.create_block_file_failed', error=str(e)) if self.translator else f'创建阻止文件失败: {e}'}{Style.RESET_ALL}")
            return True  # 返回 True 以继续执行后续步骤

    def disable_auto_update(self):
        """Disable auto update"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('update.start_disable') if self.translator else '开始禁用自动更新...'}{Style.RESET_ALL}")
            
            # 1. End processes
            if not self._kill_cursor_processes():
                return False
                
            # 2. Delete directory - 即使失败也继续执行
            self._remove_updater_directory()
                
            # 3. Clear update.yml file
            if not self._clear_update_yml_file():
                return False
                
            # 4. Create blocking file
            if not self._create_blocking_file():
                return False
                
            # 5. Remove update URL from product.json
            if not self._remove_update_url():
                return False
                
            print(f"{Fore.GREEN}{EMOJI['CHECK']} {self.translator.get('update.disable_success') if self.translator else '自动更新已禁用'}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('update.disable_failed', error=str(e)) if self.translator else f'禁用自动更新失败: {e}'}{Style.RESET_ALL}")
            return False

def run(translator=None):
    """Convenient function for directly calling the disable function"""
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['STOP']} {translator.get('update.title') if translator else 'Disable Cursor Auto Update'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    disabler = AutoUpdateDisabler(translator)
    disabler.disable_auto_update()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {translator.get('update.press_enter') if translator else 'Press Enter to Continue...'}")

if __name__ == "__main__":
    from main import translator as main_translator
    run(main_translator) 