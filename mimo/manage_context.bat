@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python mimo_manage_context.py
exit /b %ERRORLEVEL%
