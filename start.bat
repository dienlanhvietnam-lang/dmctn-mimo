@echo off
chcp 65001 >nul
title MiMo FREE
cd /d "%~dp0"

set DMCTN_MIMO_KEEP_RUNNING=1

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
