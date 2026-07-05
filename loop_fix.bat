@echo off
chcp 65001 >nul
title MiMo FREE - Fix Loop
cd /d "%~dp0"

set DMCTN_MIMO_LANG=vi
set DMCTN_MIMO_KEEP_RUNNING=1

where python >nul 2>&1
if errorlevel 1 (
    echo [X] Khong tim thay Python.
    pause
    exit /b 1
)

echo === 12 Phase Fix Loop ===
python scripts/phase_loop.py --fix --loop
set ERR=%ERRORLEVEL%
echo.
if %ERR%==0 (
    echo [OK] Tat ca 12 phase PASS.
) else (
    echo [X] Con loi - xem chi tiet phia tren.
)
pause
exit /b %ERR%
