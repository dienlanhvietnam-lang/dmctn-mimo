@echo off
chcp 65001 >nul
title MiMo VIP - Totally Reset MiMo
cd /d "%~dp0\.."

where python >nul 2>&1
if errorlevel 1 (
    echo [X] Khong tim thay Python.
    pause
    exit /b 1
)

echo === Totally Reset MiMo (DB + memory + session + machine ID) ===
echo Dong MiMo CLI truoc khi chay.
echo.
python totally_reset_mimo.py
pause
