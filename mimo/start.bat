@echo off
chcp 65001 >nul
title MiMo CLI
cd /d "%~dp0"

where node >nul 2>&1
if errorlevel 1 (
    echo [X] Khong tim thay Node.js.
    pause
    exit /b 1
)

if not exist "node_modules\.bin\mimo.cmd" (
    echo Dang cai @mimo-ai/cli...
    call npm install
)

call node_modules\.bin\mimo.cmd %*
