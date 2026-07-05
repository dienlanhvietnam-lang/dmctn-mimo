@echo off
chcp 65001 >nul
title Restore Cursor Original
cd /d "%~dp0"

echo === Khoi phuc Cursor ve nguyen ban (go patch) ===
echo Dong Cursor truoc khi chay!
echo.

python scripts/restore_cursor_original.py
set ERR=%ERRORLEVEL%
echo.
if %ERR%==0 (
    echo [OK] Da go patch. Mo lai Cursor.
) else (
    echo [X] Co loi hoac van con patch - xem phia tren.
)
pause
exit /b %ERR%
