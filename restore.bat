@echo off
chcp 65001 >nul
title Restore Cursor Workbench
cd /d "%~dp0"
echo.
echo [!!] Dong Cursor hoan toan truoc khi restore!
echo.
pause
python scripts/restore_workbench.py
echo.
pause
