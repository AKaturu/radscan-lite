@echo off
REM ============================================================
REM Build RadScan Lite for Windows (PyInstaller + Streamlit)
REM ============================================================
echo.
echo === RadScan Lite — Windows Build ===
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install build dependencies
echo === Installing build dependencies...
pip install --upgrade pip
pip install pyinstaller streamlit pydicom numpy pandas Pillow pydantic

REM Clean previous builds
echo === Cleaning previous builds...
if exist "..\dist" rmdir /s /q "..\dist"
if exist "..\build" rmdir /s /q "..\build"

REM Run PyInstaller
echo === Building executable...
pyinstaller --clean ^
    --name "RadScanLite" ^
    --onefile ^
    --windowed ^
    --add-data "..\app.py;." ^
    --add-data "..\radscan_lite;radscan_lite" ^
    --hidden-import pydicom ^
    --hidden-import pydicom.datadict ^
    --hidden-import pydicom.tag ^
    --hidden-import pydicom.errors ^
    --hidden-import streamlit ^
    --hidden-import streamlit.web.cli ^
    --hidden-import numpy ^
    --hidden-import pandas ^
    --hidden-import PIL ^
    --hidden-import pydantic ^
    ..\run_radscan.py

if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo === Build complete!
echo Executable: %CD%\dist\RadScanLite.exe
echo.
pause
