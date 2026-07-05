import os
from colorama import Fore, Style, init
import time
import random
import webbrowser
import sys
import json
from DrissionPage import ChromiumPage
from cursor_auth import CursorAuth
from utils import get_random_wait_time, should_keep_cursor_running
from config import get_config
import platform

from chrome_profile import (
    configure_browser_options,
    get_available_profiles,
    get_browser_path,
    get_user_data_directory,
    kill_browser_processes,
    select_profile as chrome_select_profile,
)

# Initialize colorama
init()

# Define emoji constants
EMOJI = {
    'START': '🚀',
    'OAUTH': '🔑',
    'SUCCESS': '✅',
    'ERROR': '❌',
    'WAIT': '⏳',
    'INFO': 'ℹ️',
    'WARNING': '⚠️'
}

class OAuthHandler:
    def __init__(self, translator=None, auth_type=None):
        self.translator = translator
        self.config = get_config(translator)
        self.auth_type = auth_type  # make sure the auth_type is not None
        os.environ['BROWSER_HEADLESS'] = 'False'
        self.browser = None
        self.selected_profile = None
        
    def _get_available_profiles(self, user_data_dir):
        return get_available_profiles(user_data_dir)

    def _select_profile(self):
        picked = chrome_select_profile(self.translator)
        if not picked:
            return False
        self.selected_profile = picked[0]
        return True
        
    def setup_browser(self):
        """Setup browser for OAuth flow using selected profile"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.initializing_browser_setup') if self.translator else 'Initializing browser setup...'}{Style.RESET_ALL}")
            
            # Platform-specific initialization
            platform_name = platform.system().lower()
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.detected_platform', platform=platform_name) if self.translator else f'Detected platform: {platform_name}'}{Style.RESET_ALL}")
            
            # Get browser paths and user data directory
            user_data_dir = self._get_user_data_directory()
            chrome_path = self._get_browser_path()
            
            if not chrome_path:
                raise Exception(f"{self.translator.get('oauth.no_compatible_browser_found') if self.translator else 'No compatible browser found. Please install Google Chrome or Chromium.'}\n{self.translator.get('oauth.supported_browsers', platform=platform_name)}\n" + 
                              "- Windows: Google Chrome, Chromium\n" +
                              "- macOS: Google Chrome, Chromium\n" +
                              "- Linux: Google Chrome, Chromium, chromium-browser")
            
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.found_browser_data_directory', path=user_data_dir) if self.translator else f'Found browser data directory: {user_data_dir}'}{Style.RESET_ALL}")
            
            # Show warning about closing Chrome first
            if should_keep_cursor_running():
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.keep_chrome_running') if self.translator else 'Giữ Chrome/Cursor đang chạy, bỏ qua bước đóng trình duyệt.'}{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.YELLOW}{EMOJI['WARNING']} {self.translator.get('chrome_profile.warning_chrome_close') if self.translator else 'Warning: This will close all running Chrome processes'}{Style.RESET_ALL}")
                choice = input(f"{Fore.YELLOW} {self.translator.get('menu.continue_prompt', choices='y/N')} {Style.RESET_ALL}").lower()
                if choice != 'y':
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('menu.operation_cancelled_by_user') if self.translator else 'Operation cancelled by user'}{Style.RESET_ALL}")
                    return False
                self._kill_browser_processes()
            
            # Let user select a profile
            if not self._select_profile():
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('menu.operation_cancelled_by_user') if self.translator else 'Operation cancelled by user'}{Style.RESET_ALL}")
                return False
            
            # Configure browser options
            co = self._configure_browser_options(chrome_path, user_data_dir, self.selected_profile)
            
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.starting_browser', path=chrome_path) if self.translator else f'Starting browser at: {chrome_path}'}{Style.RESET_ALL}")
            self.browser = ChromiumPage(co)
            
            # Verify browser launched successfully
            if not self.browser:
                raise Exception(f"{self.translator.get('oauth.browser_failed_to_start') if self.translator else 'Failed to initialize browser instance'}")
            
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.browser_setup_completed') if self.translator else 'Browser setup completed successfully'}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.browser_setup_failed', error=str(e)) if self.translator else f'Browser setup failed: {str(e)}'}{Style.RESET_ALL}")
            if "DevToolsActivePort file doesn't exist" in str(e):
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.try_running_without_sudo_admin') if self.translator else 'Try running without sudo/administrator privileges'}{Style.RESET_ALL}")
            elif "Chrome failed to start" in str(e):
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.make_sure_chrome_chromium_is_properly_installed') if self.translator else 'Make sure Chrome/Chromium is properly installed'}{Style.RESET_ALL}")
                if platform_name == 'linux':
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.try_install_chromium') if self.translator else 'Try: sudo apt install chromium-browser'}{Style.RESET_ALL}")
            return False

    def _kill_browser_processes(self):
        kill_browser_processes()

    def _get_user_data_directory(self):
        return get_user_data_directory()

    def _get_browser_path(self):
        return get_browser_path()

    def _configure_browser_options(self, chrome_path, user_data_dir, active_profile):
        return configure_browser_options(chrome_path, user_data_dir, active_profile)

    def handle_google_auth(self):
        """Handle Google OAuth authentication"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.google_start') if self.translator else 'Starting Google OAuth authentication...'}{Style.RESET_ALL}")
            
            # Setup browser
            if not self.setup_browser():
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.browser_failed') if self.translator else 'Browser failed to initialize'}{Style.RESET_ALL}")
                return False, None
            
            # Navigate to auth URL
            try:
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.navigating_to_authentication_page') if self.translator else 'Navigating to authentication page...'}{Style.RESET_ALL}")
                self.browser.get("https://authenticator.cursor.sh/sign-up")
                time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
                
                # Look for Google auth button
                selectors = [
                    "//a[contains(@href,'GoogleOAuth')]",
                    "//a[contains(@class,'auth-method-button') and contains(@href,'GoogleOAuth')]",
                    "(//a[contains(@class,'auth-method-button')])[1]"  # First auth button as fallback
                ]
                
                auth_btn = None
                for selector in selectors:
                    try:
                        auth_btn = self.browser.ele(f"xpath:{selector}", timeout=2)
                        if auth_btn and auth_btn.is_displayed():
                            break
                    except:
                        continue
                
                if not auth_btn:
                    raise Exception("Could not find Google authentication button")
                
                # Click the button and wait for page load
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.starting_google_authentication') if self.translator else 'Starting Google authentication...'}{Style.RESET_ALL}")
                auth_btn.click()
                time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
                
                # Check if we're on account selection page
                if "accounts.google.com" in self.browser.url:
                    print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.please_select_your_google_account_to_continue') if self.translator else 'Please select your Google account to continue...'}{Style.RESET_ALL}")
                    alert_message = self.translator.get('oauth.please_select_your_google_account_to_continue') if self.translator else 'Please select your Google account to continue with Cursor authentication'
                    try:
                        self.browser.run_js(f"""
                        alert('{alert_message}');
                        """)
                    except:
                        pass  # Alert is optional
                
                # Wait for authentication to complete
                auth_info = self._wait_for_auth()
                if not auth_info:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.timeout') if self.translator else 'Timeout'}{Style.RESET_ALL}")
                    return False, None
                
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.success') if self.translator else 'Success'}{Style.RESET_ALL}")
                return True, auth_info
                
            except Exception as e:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.authentication_error', error=str(e)) if self.translator else f'Authentication error: {str(e)}'}{Style.RESET_ALL}")
                return False, None
            finally:
                try:
                    if self.browser:
                        self.browser.quit()
                except:
                    pass
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed', error=str(e))}{Style.RESET_ALL}")
            return False, None

    def _wait_for_auth(self):
        """Wait for authentication to complete and extract auth info"""
        try:
            max_wait = 300  # 5 minutes
            start_time = time.time()
            check_interval = 2  # Check every 2 seconds
            
            print(f"{Fore.CYAN}{EMOJI['WAIT']} {self.translator.get('oauth.waiting_for_authentication', timeout='5 minutes') if self.translator else 'Waiting for authentication (timeout: 5 minutes)'}{Style.RESET_ALL}")
            
            while time.time() - start_time < max_wait:
                try:
                    # Check for authentication cookies
                    cookies = self.browser.cookies()
                    
                    for cookie in cookies:
                        if cookie.get("name") == "WorkosCursorSessionToken":
                            value = cookie.get("value", "")
                            token = None
                            
                            if "::" in value:
                                token = value.split("::")[-1]
                            elif "%3A%3A" in value:
                                token = value.split("%3A%3A")[-1]
                            
                            if token:
                                # Get email from settings page
                                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.authentication_successful_getting_account_info') if self.translator else 'Authentication successful, getting account info...'}{Style.RESET_ALL}")
                                self.browser.get("https://www.cursor.com/settings")
                                time.sleep(3)
                                
                                email = None
                                try:
                                    email_element = self.browser.ele("css:div[class='flex w-full flex-col gap-2'] div:nth-child(2) p:nth-child(2)")
                                    if email_element:
                                        email = email_element.text
                                        print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.found_email', email=email) if self.translator else f'Found email: {email}'}{Style.RESET_ALL}")
                                except:
                                    email = "user@cursor.sh"  # Fallback email
                                
                                # Check usage count
                                try:
                                    usage_element = self.browser.ele("css:div[class='flex flex-col gap-4 lg:flex-row'] div:nth-child(1) div:nth-child(1) span:nth-child(2)")
                                    if usage_element:
                                        usage_text = usage_element.text
                                        print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.usage_count', usage=usage_text) if self.translator else f'Usage count: {usage_text}'}{Style.RESET_ALL}")
                                        
                                        def check_usage_limits(usage_str):
                                            try:
                                                parts = usage_str.split('/')
                                                if len(parts) != 2:
                                                    return False
                                                current = int(parts[0].strip())
                                                limit = int(parts[1].strip())
                                                return (limit == 50 and current >= 50) or (limit == 150 and current >= 150)
                                            except:
                                                return False

                                        if check_usage_limits(usage_text):
                                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.account_has_reached_maximum_usage', deleting='deleting') if self.translator else 'Account has reached maximum usage, deleting...'}{Style.RESET_ALL}")
                                            
                                            if self._delete_current_account():
                                                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.starting_new_authentication_process') if self.translator else 'Starting new authentication process...'}{Style.RESET_ALL}")
                                                if self.auth_type == "google":
                                                    return self.handle_google_auth()
                                                else:
                                                    return self.handle_github_auth()
                                            else:
                                                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed_to_delete_expired_account') if self.translator else 'Failed to delete expired account'}{Style.RESET_ALL}")
                                        else:
                                            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.account_is_still_valid', usage=usage_text) if self.translator else f'Account is still valid (Usage: {usage_text})'}{Style.RESET_ALL}")
                                except Exception as e:
                                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.could_not_check_usage_count', error=str(e)) if self.translator else f'Could not check usage count: {str(e)}'}{Style.RESET_ALL}")
                                
                                return {"email": email, "token": token}
                    
                    # Also check URL as backup
                    if "cursor.com/settings" in self.browser.url:
                        print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.detected_successful_login') if self.translator else 'Detected successful login'}{Style.RESET_ALL}")
                    
                except Exception as e:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.waiting_for_authentication', error=str(e)) if self.translator else f'Waiting for authentication... ({str(e)})'}{Style.RESET_ALL}")
                
                time.sleep(check_interval)
            
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.authentication_timeout') if self.translator else 'Authentication timeout'}{Style.RESET_ALL}")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.error_waiting_for_authentication', error=str(e)) if self.translator else f'Error while waiting for authentication: {str(e)}'}{Style.RESET_ALL}")
            return None
        
    def handle_github_auth(self):
        """Handle GitHub OAuth authentication"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.github_start')}{Style.RESET_ALL}")
            
            # Setup browser
            if not self.setup_browser():
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.browser_failed')}{Style.RESET_ALL}")
                return False, None
            
            # Navigate to auth URL
            try:
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.navigating_to_authentication_page') if self.translator else 'Navigating to authentication page...'}{Style.RESET_ALL}")
                self.browser.get("https://authenticator.cursor.sh/sign-up")
                time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
                
                # Look for GitHub auth button
                selectors = [
                    "//a[contains(@href,'GitHubOAuth')]",
                    "//a[contains(@class,'auth-method-button') and contains(@href,'GitHubOAuth')]",
                    "(//a[contains(@class,'auth-method-button')])[2]"  # Second auth button as fallback
                ]
                
                auth_btn = None
                for selector in selectors:
                    try:
                        auth_btn = self.browser.ele(f"xpath:{selector}", timeout=2)
                        if auth_btn and auth_btn.is_displayed():
                            break
                    except:
                        continue
                
                if not auth_btn:
                    raise Exception("Could not find GitHub authentication button")
                
                # Click the button and wait for page load
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.starting_github_authentication') if self.translator else 'Starting GitHub authentication...'}{Style.RESET_ALL}")
                auth_btn.click()
                time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
                
                # Wait for authentication to complete
                auth_info = self._wait_for_auth()
                if not auth_info:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.timeout') if self.translator else 'Timeout'}{Style.RESET_ALL}")
                    return False, None
                
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.success')}{Style.RESET_ALL}")
                return True, auth_info
                
            except Exception as e:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.authentication_error', error=str(e)) if self.translator else f'Authentication error: {str(e)}'}{Style.RESET_ALL}")
                return False, None
            finally:
                try:
                    if self.browser:
                        self.browser.quit()
                except:
                    pass
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed', error=str(e))}{Style.RESET_ALL}")
            return False, None
        
    def _handle_oauth(self, auth_type):
        """Handle OAuth authentication for both Google and GitHub
        
        Args:
            auth_type (str): Type of authentication ('google' or 'github')
        """
        try:
            if not self.setup_browser():
                return False, None
                
            # Navigate to auth URL
            self.browser.get("https://authenticator.cursor.sh/sign-up")
            time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
            
            # Set selectors based on auth type
            if auth_type == "google":
                selectors = [
                    "//a[@class='rt-reset rt-BaseButton rt-r-size-3 rt-variant-surface rt-high-contrast rt-Button auth-method-button_AuthMethodButton__irESX'][contains(@href,'GoogleOAuth')]",
                    "(//a[@class='rt-reset rt-BaseButton rt-r-size-3 rt-variant-surface rt-high-contrast rt-Button auth-method-button_AuthMethodButton__irESX'])[1]"
                ]
            else:  # github
                selectors = [
                    "(//a[@class='rt-reset rt-BaseButton rt-r-size-3 rt-variant-surface rt-high-contrast rt-Button auth-method-button_AuthMethodButton__irESX'])[2]"
                ]
            
            # Wait for the button to be available
            auth_btn = None
            max_button_wait = 30  # 30 seconds
            button_start_time = time.time()
            
            while time.time() - button_start_time < max_button_wait:
                for selector in selectors:
                    try:
                        auth_btn = self.browser.ele(f"xpath:{selector}", timeout=1)
                        if auth_btn and auth_btn.is_displayed():
                            break
                    except:
                        continue
                if auth_btn:
                    break
                time.sleep(1)
            
            if auth_btn:
                # Click the button and wait for page load
                auth_btn.click()
                time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
                
                # Check if we're on account selection page
                if auth_type == "google" and "accounts.google.com" in self.browser.url:
                    alert_message = self.translator.get('oauth.please_select_your_google_account_to_continue') if self.translator else 'Please select your Google account to continue with Cursor authentication'
                    try:
                        self.browser.run_js(f"""
                        alert('{alert_message}');
                        """)
                    except Exception as e:
                        print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.alert_display_failed', error=str(e)) if self.translator else f'Alert display failed: {str(e)}'}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.please_select_your_google_account_manually_to_continue_with_cursor_authentication') if self.translator else 'Please select your Google account manually to continue with Cursor authentication...'}{Style.RESET_ALL}")
                
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.waiting_for_authentication_to_complete') if self.translator else 'Waiting for authentication to complete...'}{Style.RESET_ALL}")
                
                # Wait for authentication to complete
                max_wait = 300  # 5 minutes
                start_time = time.time()
                last_url = self.browser.url
                
                print(f"{Fore.CYAN}{EMOJI['WAIT']} {self.translator.get('oauth.checking_authentication_status') if self.translator else 'Checking authentication status...'}{Style.RESET_ALL}")
                
                while time.time() - start_time < max_wait:
                    try:
                        # Check for authentication cookies
                        cookies = self.browser.cookies()
                        
                        for cookie in cookies:
                            if cookie.get("name") == "WorkosCursorSessionToken":
                                value = cookie.get("value", "")
                                if "::" in value:
                                    token = value.split("::")[-1]
                                elif "%3A%3A" in value:
                                    token = value.split("%3A%3A")[-1]
                                
                                if token:
                                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.authentication_successful') if self.translator else 'Authentication successful!'}{Style.RESET_ALL}")
                                    # Navigate to settings page
                                    print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.navigating_to_settings_page') if self.translator else 'Navigating to settings page...'}{Style.RESET_ALL}")
                                    self.browser.get("https://www.cursor.com/settings")
                                    time.sleep(3)  # Wait for settings page to load
                                    
                                    # Get email from settings page
                                    try:
                                        email_element = self.browser.ele("css:div[class='flex w-full flex-col gap-2'] div:nth-child(2) p:nth-child(2)")
                                        if email_element:
                                            actual_email = email_element.text
                                            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.found_email', email=actual_email) if self.translator else f'Found email: {actual_email}'}{Style.RESET_ALL}")
                                    except Exception as e:
                                        print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.could_not_find_email', error=str(e)) if self.translator else f'Could not find email: {str(e)}'}{Style.RESET_ALL}")
                                        actual_email = "user@cursor.sh"
                                    
                                    # Check usage count
                                    try:
                                        usage_element = self.browser.ele("css:div[class='flex flex-col gap-4 lg:flex-row'] div:nth-child(1) div:nth-child(1) span:nth-child(2)")
                                        if usage_element:
                                            usage_text = usage_element.text
                                            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.usage_count', usage=usage_text) if self.translator else f'Usage count: {usage_text}'}{Style.RESET_ALL}")
                                            
                                            def check_usage_limits(usage_str):
                                                try:
                                                    parts = usage_str.split('/')
                                                    if len(parts) != 2:
                                                        return False
                                                    current = int(parts[0].strip())
                                                    limit = int(parts[1].strip())
                                                    return (limit == 50 and current >= 50) or (limit == 150 and current >= 150)
                                                except:
                                                    return False

                                            if check_usage_limits(usage_text):
                                                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.account_has_reached_maximum_usage', deleting='deleting') if self.translator else 'Account has reached maximum usage, deleting...'}{Style.RESET_ALL}")
                                                
                                                if self._delete_current_account():
                                                    print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.starting_new_authentication_process') if self.translator else 'Starting new authentication process...'}{Style.RESET_ALL}")
                                                    if self.auth_type == "google":
                                                        return self.handle_google_auth()
                                                    else:
                                                        return self.handle_github_auth()
                                                else:
                                                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed_to_delete_expired_account') if self.translator else 'Failed to delete expired account'}{Style.RESET_ALL}")
                                            else:
                                                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.account_is_still_valid', usage=usage_text) if self.translator else f'Account is still valid (Usage: {usage_text})'}{Style.RESET_ALL}")
                                    except Exception as e:
                                        print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.could_not_check_usage_count', error=str(e)) if self.translator else f'Could not check usage count: {str(e)}'}{Style.RESET_ALL}")
                                    
                                    # Remove the browser stay open prompt and input wait
                                    return True, {"email": actual_email, "token": token}
                        
                        # Also check URL as backup
                        current_url = self.browser.url
                        if "cursor.com/settings" in current_url:
                            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.already_on_settings_page') if self.translator else 'Already on settings page!'}{Style.RESET_ALL}")
                            time.sleep(1)
                            cookies = self.browser.cookies()
                            for cookie in cookies:
                                if cookie.get("name") == "WorkosCursorSessionToken":
                                    value = cookie.get("value", "")
                                    if "::" in value:
                                        token = value.split("::")[-1]
                                    elif "%3A%3A" in value:
                                        token = value.split("%3A%3A")[-1]
                                    if token:
                                        # Get email and check usage here too
                                        try:
                                            email_element = self.browser.ele("css:div[class='flex w-full flex-col gap-2'] div:nth-child(2) p:nth-child(2)")
                                            if email_element:
                                                actual_email = email_element.text
                                                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.found_email', email=actual_email) if self.translator else f'Found email: {actual_email}'}{Style.RESET_ALL}")
                                        except Exception as e:
                                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.could_not_find_email', error=str(e)) if self.translator else f'Could not find email: {str(e)}'}{Style.RESET_ALL}")
                                            actual_email = "user@cursor.sh"
                                        
                                        # Check usage count
                                        try:
                                            usage_element = self.browser.ele("css:div[class='flex flex-col gap-4 lg:flex-row'] div:nth-child(1) div:nth-child(1) span:nth-child(2)")
                                            if usage_element:
                                                usage_text = usage_element.text
                                                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.usage_count', usage=usage_text) if self.translator else f'Usage count: {usage_text}'}{Style.RESET_ALL}")
                                                
                                                def check_usage_limits(usage_str):
                                                    try:
                                                        parts = usage_str.split('/')
                                                        if len(parts) != 2:
                                                            return False
                                                        current = int(parts[0].strip())
                                                        limit = int(parts[1].strip())
                                                        return (limit == 50 and current >= 50) or (limit == 150 and current >= 150)
                                                    except:
                                                        return False

                                                if check_usage_limits(usage_text):
                                                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.account_has_reached_maximum_usage', deleting='deleting') if self.translator else 'Account has reached maximum usage, deleting...'}{Style.RESET_ALL}")
                                                    
                                                    if self._delete_current_account():
                                                        print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.starting_new_authentication_process') if self.translator else 'Starting new authentication process...'}{Style.RESET_ALL}")
                                                        if self.auth_type == "google":
                                                            return self.handle_google_auth()
                                                        else:
                                                            return self.handle_github_auth()
                                                    else:
                                                        print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed_to_delete_expired_account') if self.translator else 'Failed to delete expired account'}{Style.RESET_ALL}")
                                                else:
                                                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.account_is_still_valid', usage=usage_text) if self.translator else f'Account is still valid (Usage: {usage_text})'}{Style.RESET_ALL}")
                                        except Exception as e:
                                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.could_not_check_usage_count', error=str(e)) if self.translator else f'Could not check usage count: {str(e)}'}{Style.RESET_ALL}")
                                        
                                        # Remove the browser stay open prompt and input wait
                                        return True, {"email": actual_email, "token": token}
                        elif current_url != last_url:
                            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.page_changed_checking_auth') if self.translator else 'Page changed, checking auth...'}{Style.RESET_ALL}")
                            last_url = current_url
                            time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
                    except Exception as e:
                        print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.status_check_error', error=str(e)) if self.translator else f'Status check error: {str(e)}'}{Style.RESET_ALL}")
                        time.sleep(1)
                        continue
                    time.sleep(1)
                    
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.authentication_timeout') if self.translator else 'Authentication timeout'}{Style.RESET_ALL}")
                return False, None
                
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.authentication_button_not_found') if self.translator else 'Authentication button not found'}{Style.RESET_ALL}")
            return False, None
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.authentication_failed', error=str(e)) if self.translator else f'Authentication failed: {str(e)}'}{Style.RESET_ALL}")
            return False, None
        finally:
            if self.browser:
                self.browser.quit()

    def _extract_auth_info(self):
        """Extract authentication information after successful OAuth"""
        try:
            # Get cookies with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cookies = self.browser.cookies()
                    if cookies:
                        break
                    time.sleep(1)
                except:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(1)
            
            # Debug cookie information
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.found_cookies', count=len(cookies)) if self.translator else f'Found {len(cookies)} cookies'}{Style.RESET_ALL}")
            
            email = None
            token = None
            
            for cookie in cookies:
                name = cookie.get("name", "")
                if name == "WorkosCursorSessionToken":
                    try:
                        value = cookie.get("value", "")
                        if "::" in value:
                            token = value.split("::")[-1]
                        elif "%3A%3A" in value:
                            token = value.split("%3A%3A")[-1]
                    except Exception as e:
                        print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('oauth.token_extraction_error', error=str(e)) if self.translator else f'Token extraction error: {str(e)}'}{Style.RESET_ALL}")
                elif name == "cursor_email":
                    email = cookie.get("value")
                    
            if email and token:
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('oauth.authentication_successful', email=email) if self.translator else f'Authentication successful - Email: {email}'}{Style.RESET_ALL}")
                return True, {"email": email, "token": token}
            else:
                missing = []
                if not email:
                    missing.append("email")
                if not token:
                    missing.append("token")
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.missing_authentication_data', data=', '.join(missing)) if self.translator else f'Missing authentication data: {", ".join(missing)}'}{Style.RESET_ALL}")
                return False, None
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed_to_extract_auth_info', error=str(e)) if self.translator else f'Failed to extract auth info: {str(e)}'}{Style.RESET_ALL}")
            return False, None

    def _delete_current_account(self):
        """Delete the current account using the API"""
        try:
            delete_js = """
            function deleteAccount() {
                return new Promise((resolve, reject) => {
                    fetch('https://www.cursor.com/api/dashboard/delete-account', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        credentials: 'include'
                    })
                    .then(response => {
                        if (response.status === 200) {
                            resolve('Account deleted successfully');
                        } else {
                            reject('Failed to delete account: ' + response.status);
                        }
                    })
                    .catch(error => {
                        reject('Error: ' + error);
                    });
                });
            }
            return deleteAccount();
            """
            
            result = self.browser.run_js(delete_js)
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Delete account result: {result}{Style.RESET_ALL}")
            
            # Navigate back to auth page
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('oauth.redirecting_to_authenticator_cursor_sh') if self.translator else 'Redirecting to authenticator.cursor.sh...'}{Style.RESET_ALL}")
            self.browser.get("https://authenticator.cursor.sh/sign-up")
            time.sleep(get_random_wait_time(self.config, 'page_load_wait'))
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('oauth.failed_to_delete_account', error=str(e)) if self.translator else f'Failed to delete account: {str(e)}'}{Style.RESET_ALL}")
            return False

def main(auth_type, translator=None):
    """Main function to handle OAuth authentication
    
    Args:
        auth_type (str): Type of authentication ('google' or 'github')
        translator: Translator instance for internationalization
    """
    handler = OAuthHandler(translator, auth_type)
    
    if auth_type.lower() == 'google':
        print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('oauth.google_start') if translator else 'Google start'}{Style.RESET_ALL}")
        success, auth_info = handler.handle_google_auth()
    elif auth_type.lower() == 'github':
        print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('oauth.github_start') if translator else 'Github start'}{Style.RESET_ALL}")
        success, auth_info = handler.handle_github_auth()
    else:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('oauth.invalid_authentication_type') if translator else 'Invalid authentication type'}{Style.RESET_ALL}")
        return False
        
    if success and auth_info:
        # Update Cursor authentication
        auth_manager = CursorAuth(translator)
        if auth_manager.update_auth(
            email=auth_info["email"],
            access_token=auth_info["token"],
            refresh_token=auth_info["token"]
        ):
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('oauth.auth_update_success') if translator else 'Auth update success'}{Style.RESET_ALL}")
            try:
                from cursor_membership import patch_workbench_vip
                patch_workbench_vip(translator)
            except Exception as e:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {translator.get('vip.patch_skipped', error=str(e)) if translator else f'VIP UI patch skipped: {e}'}{Style.RESET_ALL}")
            # Close the browser after successful authentication
            if handler.browser:
                handler.browser.quit()
                print(f"{Fore.CYAN}{EMOJI['INFO']} {translator.get('oauth.browser_closed') if translator else 'Browser closed'}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('oauth.auth_update_failed') if translator else 'Auth update failed'}{Style.RESET_ALL}")
            
    return False 