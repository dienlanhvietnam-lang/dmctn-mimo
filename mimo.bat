@echo off
chcp 65001 >nul
set "MIMO_HOME=%~dp0"
set "MIMO_DIR=%MIMO_HOME%mimo"
set "MIMO_CMD=%MIMO_DIR%\node_modules\.bin\mimo.cmd"

if not exist "%MIMO_CMD%" (
    pushd "%MIMO_DIR%"
    where node >nul 2>&1
    if errorlevel 1 (
        echo [X] Khong tim thay Node.js.
        popd
        exit /b 1
    )
    echo Dang cai @mimo-ai/cli...
    call npm install
    popd
    if errorlevel 1 exit /b 1
)

if not exist "%MIMO_CMD%" (
    echo [X] Khong cai duoc MiMo CLI.
    exit /b 1
)

call "%MIMO_CMD%" %*
exit /b %ERRORLEVEL%
