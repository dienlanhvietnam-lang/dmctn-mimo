@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo === Deep Reset MiMo (slots + .config/mimocode + local data) ===
python -c "import totally_reset_mimo; totally_reset_mimo.run_deep()"
pause
