@echo off
chcp 65001 >nul
title MiMo FREE - Setup MiMo Auto + E2E
cd /d "%~dp0\.."

where python >nul 2>&1
if errorlevel 1 (
    echo [X] Khong tim thay Python.
    pause
    exit /b 1
)

python setup_mimo_auto.py
set ERR=%ERRORLEVEL%
pause
exit /b %ERR%
