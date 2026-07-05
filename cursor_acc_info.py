import os
import sys
import json
import requests
import sqlite3
from typing import Dict, Optional
import platform
from colorama import Fore, Style, init
import logging
import re

# Initialize colorama
init()

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define emoji constants
EMOJI = {
    "USER": "👤",
    "USAGE": "📊",
    "PREMIUM": "⭐",
    "BASIC": "📝",
    "SUBSCRIPTION": "💳",
    "INFO": "ℹ️",
    "ERROR": "❌",
    "SUCCESS": "✅",
    "WARNING": "⚠️",
    "TIME": "🕒"
}

class Config:
    """Config"""
    NAME_LOWER = "cursor"
    NAME_CAPITALIZE = "Cursor"
    BASE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

class UsageManager:
    """Usage Manager"""
    
    @staticmethod
    def get_proxy():
        """get proxy"""
        # from config import get_config
        proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
        if proxy:
            return {"http": proxy, "https": proxy}
        return None
    
    @staticmethod
    def get_usage(token: str) -> Optional[Dict]:
        """get usage"""
        url = f"https://www.{Config.NAME_LOWER}.com/api/usage"
        headers = Config.BASE_HEADERS.copy()
        headers.update({"Cookie": f"Workos{Config.NAME_CAPITALIZE}SessionToken=user_01OOOOOOOOOOOOOOOOOOOOOOOO%3A%3A{token}"})
        try:
            proxies = UsageManager.get_proxy()
            response = requests.get(url, headers=headers, timeout=10, proxies=proxies)
            response.raise_for_status()
            data = response.json()
            
            # get Premium usage and limit
            gpt4_data = data.get("gpt-4", {})
            premium_usage = gpt4_data.get("numRequestsTotal", 0)
            max_premium_usage = gpt4_data.get("maxRequestUsage", 999)
            
            # get Basic usage, but set limit to "No Limit"
            gpt35_data = data.get("gpt-3.5-turbo", {})
            basic_usage = gpt35_data.get("numRequestsTotal", 0)
            
            return {
                'premium_usage': premium_usage, 
                'max_premium_usage': max_premium_usage, 
                'basic_usage': basic_usage, 
                'max_basic_usage': "No Limit"  # set Basic limit to "No Limit"
            }
        except requests.RequestException as e:
            # only log error
            logger.error(f"Get usage info failed: {str(e)}")
            return None
        except Exception as e:
            # catch all other exceptions
            logger.error(f"Get usage info failed: {str(e)}")
            return None

    @staticmethod
    def get_stripe_profile(token: str) -> Optional[Dict]:
        """get user subscription info"""
        url = f"https://api2.{Config.NAME_LOWER}.sh/auth/full_stripe_profile"
        headers = Config.BASE_HEADERS.copy()
        headers.update({"Authorization": f"Bearer {token}"})
        try:
            proxies = UsageManager.get_proxy()
            response = requests.get(url, headers=headers, timeout=10, proxies=proxies)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get subscription info failed: {str(e)}")
            return None

def get_token_from_config():
    """get path info from config"""
    try:
        from config import get_config
        config = get_config()
        if not config:
            return None
            
        system = platform.system()
        if system == "Windows" and config.has_section('WindowsPaths'):
            return {
                'storage_path': config.get('WindowsPaths', 'storage_path'),
                'sqlite_path': config.get('WindowsPaths', 'sqlite_path'),
                'session_path': os.path.join(os.getenv("APPDATA"), "Cursor", "Session Storage")
            }
        elif system == "Darwin" and config.has_section('MacPaths'):  # macOS
            return {
                'storage_path': config.get('MacPaths', 'storage_path'),
                'sqlite_path': config.get('MacPaths', 'sqlite_path'),
                'session_path': os.path.expanduser("~/Library/Application Support/Cursor/Session Storage")
            }
        elif system == "Linux" and config.has_section('LinuxPaths'):
            return {
                'storage_path': config.get('LinuxPaths', 'storage_path'),
                'sqlite_path': config.get('LinuxPaths', 'sqlite_path'),
                'session_path': os.path.expanduser("~/.config/Cursor/Session Storage")
            }
    except Exception as e:
        logger.error(f"Get config path failed: {str(e)}")
    
    return None

def get_token_from_storage(storage_path):
    """get token from storage.json"""
    if not os.path.exists(storage_path):
        return None
        
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            token = data.get('cursorAuth/accessToken')
            if isinstance(token, str) and token.startswith('eyJ'):
                return token
            for key in ('cursorAuth/refreshToken',):
                value = data.get(key)
                if isinstance(value, str) and value.startswith('eyJ'):
                    return value
    except Exception as e:
        logger.error(f"get token from storage.json failed: {str(e)}")
    
    return None

def get_token_from_sqlite(sqlite_path):
    """get token from sqlite"""
    if not os.path.exists(sqlite_path):
        return None
        
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        for key in ('cursorAuth/accessToken', 'cursorAuth/refreshToken'):
            cursor.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and isinstance(row[0], str) and row[0].startswith('eyJ'):
                conn.close()
                return row[0]
        conn.close()
    except Exception as e:
        logger.error(f"get token from sqlite failed: {str(e)}")
    
    return None

def get_token_from_session(session_path):
    """get token from session"""
    if not os.path.exists(session_path):
        return None
        
    try:
        # try to find all possible session files
        for file in os.listdir(session_path):
            if file.endswith('.log'):
                file_path = os.path.join(session_path, file)
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        # find token pattern
                        token_match = re.search(r'"token":"([^"]+)"', content)
                        if token_match:
                            return token_match.group(1)
                except:
                    continue
    except Exception as e:
        logger.error(f"get token from session failed: {str(e)}")
    
    return None

def get_token():
    """get Cursor token"""
    # get path from config
    paths = get_token_from_config()
    if not paths:
        return None
    
    # try to get token from different locations
    token = get_token_from_storage(paths['storage_path'])
    if token:
        return token
        
    token = get_token_from_sqlite(paths['sqlite_path'])
    if token:
        return token
        
    token = get_token_from_session(paths['session_path'])
    if token:
        return token
    
    return None

def format_subscription_type(subscription_data: Dict) -> str:
    """format subscription type"""
    if not subscription_data:
        return "Free"
    
    # handle new API response format
    if "membershipType" in subscription_data:
        membership_type = subscription_data.get("membershipType", "").lower()
        subscription_status = subscription_data.get("subscriptionStatus", "").lower()
        
        if subscription_status == "active":
            if membership_type == "pro":
                return "Pro"
            elif membership_type == "free_trial":
                return "Free Trial"
            elif membership_type == "pro_trial":
                return "Pro Trial"
            elif membership_type == "team":
                return "Team"
            elif membership_type == "enterprise":
                return "Enterprise"
            elif membership_type:
                return membership_type.capitalize()
            else:
                return "Active Subscription"
        elif subscription_status:
            return f"{membership_type.capitalize()} ({subscription_status})"
    
    # compatible with old API response format
    subscription = subscription_data.get("subscription")
    if subscription:
        plan = subscription.get("plan", {}).get("nickname", "Unknown")
        status = subscription.get("status", "unknown")
        
        if status == "active":
            if "pro" in plan.lower():
                return "Pro"
            elif "pro_trial" in plan.lower():
                return "Pro Trial"
            elif "free_trial" in plan.lower():
                return "Free Trial"
            elif "team" in plan.lower():
                return "Team"
            elif "enterprise" in plan.lower():
                return "Enterprise"
            else:
                return plan
        else:
            return f"{plan} ({status})"
    
    return "Free"

def get_email_from_storage(storage_path):
    """get email from storage.json"""
    if not os.path.exists(storage_path):
        return None
        
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # try to get email
            if 'cursorAuth/cachedEmail' in data:
                return data['cursorAuth/cachedEmail']
            
            # try other possible keys
            for key in data:
                if 'email' in key.lower() and isinstance(data[key], str) and '@' in data[key]:
                    return data[key]
    except Exception as e:
        logger.error(f"get email from storage.json failed: {str(e)}")
    
    return None

def get_email_from_sqlite(sqlite_path):
    """get email from sqlite"""
    if not os.path.exists(sqlite_path):
        return None
        
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM ItemTable WHERE key = ?", ('cursorAuth/cachedEmail',))
        row = cursor.fetchone()
        conn.close()
        if row and isinstance(row[0], str) and '@' in row[0]:
            return row[0]
    except Exception as e:
        logger.error(f"get email from sqlite failed: {str(e)}")
    
    return None

def _acc_t(translator):
    """Return a lookup that falls back to a literal when the key is missing."""
    def _t(key, fallback):
        if translator:
            value = translator.get(key)
            if value and value != key:
                return value
        return fallback
    return _t


def _plan_and_status(subscription_info):
    """Extract (plan, status_code, is_active) from a stripe/profile payload."""
    if not subscription_info:
        return "Free", None, True
    if "membershipType" in subscription_info:
        membership = (subscription_info.get("membershipType") or "").strip()
        status = (subscription_info.get("subscriptionStatus") or "").strip()
        plan = membership.replace("_", " ").title() if membership else "Free"
        return plan, (status or None), (status.lower() == "active")
    subscription = subscription_info.get("subscription")
    if subscription:
        plan = subscription.get("plan", {}).get("nickname", "Unknown")
        status = (subscription.get("status") or "").strip()
        return plan, (status or None), (status.lower() == "active")
    return "Free", None, True


_STATUS_VI = {
    "active": "Đang hoạt động",
    "past_due": "Quá hạn",
    "trialing": "Dùng thử",
    "canceled": "Đã hủy",
    "unpaid": "Chưa thanh toán",
    "incomplete": "Chưa hoàn tất",
}


def display_account_info(translator=None):
    """Render the account summary panel (03)."""
    import ui

    T = _acc_t(translator)
    is_vi = bool(translator and getattr(translator, "current_language", "") == "vi")

    # get token + config path
    token = get_token()
    paths = get_token_from_config() if token else None
    acc_title = "TÓM TẮT TÀI KHOẢN" if is_vi else T("account_info.title", "Account Summary")
    if not token or not paths:
        ui.panel(
            [f"{ui.WARN}{T('account_info.token_not_found', 'Chưa đăng nhập Cursor (không tìm thấy token)')}{ui.RESET}"],
            number="03",
            title=acc_title.upper(),
            icon=ui.ICON_WARN,
        )
        return
    
    # get email info - try multiple sources
    email = get_email_from_storage(paths['storage_path'])
    
    # if not found in storage, try from sqlite
    if not email:
        email = get_email_from_sqlite(paths['sqlite_path'])
    
    # subscription (used for plan/status + email fallback)
    try:
        subscription_info = UsageManager.get_stripe_profile(token)
    except Exception as e:
        logger.debug(f"Get subscription info failed: {str(e)}")
        subscription_info = None

    if not email and subscription_info:
        if 'customer' in subscription_info and 'email' in subscription_info['customer']:
            email = subscription_info['customer']['email']

    # usage (401 when auth expired — shown inline, not logged loudly)
    try:
        usage_info = UsageManager.get_usage(token)
    except Exception as e:
        logger.debug(f"Get usage info failed: {str(e)}")
        usage_info = None

    plan, status_code, is_active = _plan_and_status(subscription_info)

    labels = [
        T("account_info.email", "Email"),
        T("account_info.subscription", "Gói dịch vụ" if is_vi else "Subscription"),
        "Trạng thái thanh toán" if is_vi else "Payment status",
        "API sử dụng" if is_vi else "API usage",
    ]
    label_w = max(ui.display_width(x) for x in labels)

    rows = []
    rows.append(ui.kv(labels[0], email or T("account_info.email_not_found", "Không tìm thấy"),
                      label_w, value_color=ui.TEXT if email else ui.WARN))

    plan_ok = plan.lower().split()[0] in ("pro", "team", "enterprise", "business", "ultra")
    rows.append(ui.kv(labels[1], plan, label_w, value_color=ui.OK if plan_ok else ui.TEXT))

    if status_code:
        status_label = _STATUS_VI.get(status_code.lower(), status_code.replace("_", " ").title()) if is_vi \
            else status_code.replace("_", " ").title()
        rows.append(ui.kv(labels[2], status_label, label_w, value_color=ui.OK if is_active else ui.WARN))

    if usage_info:
        premium = usage_info.get("premium_usage", 0) or 0
        max_premium = usage_info.get("max_premium_usage", "No Limit")
        rows.append(ui.kv(labels[3], f"{premium}/{max_premium}", label_w, value_color=ui.OK))
        icon = ui.ICON_OK if is_active else ui.ICON_WARN
    else:
        unauth = "Chưa xác thực / 401" if is_vi else "Unauthorized / 401"
        rows.append(ui.kv(labels[3], unauth, label_w, value_color=ui.ERR))
        icon = ui.ICON_WARN if is_active else ui.ICON_ERROR

    rows.append(ui.hint(("Đăng nhập lại hoặc kiểm tra tài khoản" if is_vi
                         else "Re-login or check the account") if not usage_info else ""))
    if not rows[-1].strip():
        rows.pop()

    ui.panel(rows, number="03", title=acc_title.upper(), icon=icon)

def main(translator=None):
    """main function"""
    try:
        display_account_info(translator)
    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('account_info.error') if translator else 'Error'}: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 