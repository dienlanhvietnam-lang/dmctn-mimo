# -*- mode: python ; coding: utf-8 -*-

import os
import platform

from dotenv import load_dotenv

load_dotenv()
version = os.getenv("VERSION", "2.0.0")

system = platform.system().lower()
if system == "windows":
    os_type = "windows"
elif system == "linux":
    os_type = "linux"
else:
    os_type = "mac"

output_name = f"DmctnMimo_{version}_{os_type}"

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("locales", "locales"),
        ("chrome_profile.py", "."),
        ("reset_mimo_machine.py", "."),
        ("totally_reset_mimo.py", "."),
        ("setup_mimo_auto.py", "."),
        ("mimo_account_slots.py", "."),
        ("mimo_platform_login.py", "."),
        ("mimo_manage_accounts.py", "."),
        ("mimo_paths.py", "."),
        ("mimo_auth.py", "."),
        ("machine_id_utils.py", "."),
        ("config.py", "."),
        ("branding.py", "."),
        ("utils.py", "."),
        (".env", "."),
    ],
    hiddenimports=[
        "chrome_profile",
        "reset_mimo_machine",
        "totally_reset_mimo",
        "setup_mimo_auto",
        "mimo_account_slots",
        "mimo_platform_login",
        "mimo_manage_accounts",
        "mimo_paths",
        "mimo_auth",
        "machine_id_utils",
        "config",
        "branding",
        "ui",
        "utils",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

target_arch = os.environ.get("TARGET_ARCH", None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=output_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
