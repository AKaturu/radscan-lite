#!/usr/bin/env bash
# ============================================================
# Build RadScan Lite for Linux (PyInstaller + Streamlit)
# ============================================================
set -euo pipefail

echo "=== RadScan Lite — Linux Build ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Install: sudo apt install python3 python3-pip"
    exit 1
fi

# Install build dependencies
echo "=== Installing build dependencies..."
pip3 install --upgrade pip
pip3 install pyinstaller streamlit pydicom numpy pandas Pillow pydantic

# Clean previous builds
echo "=== Cleaning previous builds..."
rm -rf ../dist ../build

# Run PyInstaller
echo "=== Building executable..."
pyinstaller --clean \
    --name "RadScanLite" \
    --onefile \
    --windowed \
    --add-data "../app.py:." \
    --add-data "../radscan_lite:radscan_lite" \
    --hidden-import pydicom \
    --hidden-import pydicom.datadict \
    --hidden-import pydicom.tag \
    --hidden-import pydicom.errors \
    --hidden-import streamlit \
    --hidden-import streamlit.web.cli \
    --hidden-import numpy \
    --hidden-import pandas \
    --hidden-import PIL \
    --hidden-import pydantic \
    ../run_radscan.py

echo "=== Build complete!"
echo "Executable: $(pwd)/dist/RadScanLite"
