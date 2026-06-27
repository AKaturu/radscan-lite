#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# RadScan Lite — macOS/Linux Quick Install & Launch
# ============================================================

echo ""
echo "=== RadScan Lite — Installer ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found."
    echo "Install Python 3.11+ from your package manager:"
    echo "  macOS: brew install python"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

# Check Python version
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    echo "Python $PY_VER found."
else
    echo "ERROR: Python 3.11+ required. Found: $PY_VER"
    exit 1
fi

echo "Step 1: Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "Step 2: Installing dependencies..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install --editable .

echo "Step 3: Done!"
echo ""
echo "Starting RadScan Lite..."
echo "The app will open in your browser at http://localhost:8501"
echo ""
python3 run_radscan.py
