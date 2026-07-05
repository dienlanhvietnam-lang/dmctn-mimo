@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python mimo_platform_login.py
exit /b %ERRORLEVEL%
