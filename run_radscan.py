from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).resolve().parent / "app.py"
    port = os.environ.get("RADSCAN_PORT", "8501")

    print(f"RadScan Lite — Starting on http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={port}",
        "--server.headless=true",
    ]
    proc = subprocess.run(cmd)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
