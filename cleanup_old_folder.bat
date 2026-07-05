@echo off
chcp 65001 >nul
title Xoa thu muc cu cursor-free-vip
cd /d "%~dp0"

if /i "%~dp0" NEQ "D:\CURORVIP\mino-vip\" (
    echo [X] Chay file nay tu D:\CURORVIP\mino-vip
    pause
    exit /b 1
)

if not exist "D:\CURORVIP\cursor-free-vip" (
    echo [OK] Thu muc cu da khong con.
    pause
    exit /b 0
)

echo Dong Cursor / terminal dang mo thu muc cursor-free-vip truoc khi xoa.
echo Se xoa: D:\CURORVIP\cursor-free-vip
pause

rd /s /q "D:\CURORVIP\cursor-free-vip" 2>nul
if exist "D:\CURORVIP\cursor-free-vip" (
    echo [X] Khong xoa duoc - thu muc dang duoc su dung.
    echo Mo workspace moi: D:\CURORVIP\mino-vip roi chay lai file nay.
    pause
    exit /b 1
)

echo [OK] Da xoa thu muc cu.
pause
exit /b 0
