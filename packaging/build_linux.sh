#!/usr/bin/env bash
# ============================================================
# Build RadScan Lite for Linux (PyInstaller + Streamlit)
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== RadScan Lite - Linux Build ==="

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Install: sudo apt install python3 python3-pip"
    exit 1
fi

echo "=== Installing build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[packaging]"

echo "=== Cleaning previous builds..."
rm -rf dist build

echo "=== Building executable..."
pyinstaller --clean \
    --name "RadScanLite" \
    --onefile \
    --windowed \
    --add-data "app.py:." \
    --add-data "radscan_lite:radscan_lite" \
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
    run_radscan.py

echo "=== Build complete!"
echo "Executable: $ROOT_DIR/dist/RadScanLite"
