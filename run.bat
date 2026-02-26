@echo off
cd /d "%~dp0"
python --version >nul 2>&1 || (echo Python not found. Install Python 3.8+ && pause && exit /b 1)
python "%~dp0api_switcher.py"
