@echo off
chcp 65001 >nul
title MiMo VIP - Reset MiMo Machine ID
cd /d "%~dp0\.."

where python >nul 2>&1
if errorlevel 1 (
    echo [X] Khong tim thay Python.
    pause
    exit /b 1
)

echo === Reset MiMo Machine ID (installation_id + registry) ===
echo Dong MiMo CLI truoc khi chay.
echo Can quyen Admin de doi Registry MachineGuid.
echo.
python reset_mimo_machine.py
pause
