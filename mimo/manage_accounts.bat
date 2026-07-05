@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python mimo_manage_accounts.py
exit /b %ERRORLEVEL%
