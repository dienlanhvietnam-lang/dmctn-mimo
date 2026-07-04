@echo off
chcp 65001 >nul
title Cursor Free VIP
cd /d "%~dp0"

set CURSOR_FREE_VIP_LANG=vi
set CURSOR_FREE_VIP_KEEP_RUNNING=1

where python >nul 2>&1
if errorlevel 1 (
    echo [X] Khong tim thay Python. Hay cai Python 3 va them vao PATH.
    pause
    exit /b 1
)

python main.py
if errorlevel 1 (
    echo.
    echo [X] Ung dung thoat voi loi.
)
pause
