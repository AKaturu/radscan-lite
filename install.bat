@echo off
REM ============================================================
REM RadScan Lite — Windows Quick Install & Launch
REM ============================================================
title RadScan Lite Installer
echo.
echo === RadScan Lite — Windows Installer ===
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found.
    echo Please install Python 3.11+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python 3.11+ is required. Current version:
    python --version
    echo Please upgrade from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Step 1: Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
)

echo Step 2: Installing dependencies...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install --editable .

echo Step 3: Done!
echo.
echo Starting RadScan Lite...
echo The app will open in your browser at http://localhost:8501
echo.
python run_radscan.py
pause
