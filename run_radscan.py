from __future__ import annotations

import os
import sys
import threading
import webbrowser
from pathlib import Path


def _app_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "app.py"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent / "app.py"


def main() -> None:
    app_path = _app_path()
    if "--self-check" in sys.argv:
        if not app_path.exists():
            print(f"Missing Streamlit app: {app_path}", file=sys.stderr)
            raise SystemExit(1)
        print("RadScan Lite desktop launcher OK")
        raise SystemExit(0)

    from streamlit.web import cli as stcli

    port = os.environ.get("RADSCAN_PORT", "8501")
    print(f"RadScan Lite - Starting on http://localhost:{port}")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
