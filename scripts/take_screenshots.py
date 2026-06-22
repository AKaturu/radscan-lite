from __future__ import annotations

import os
import time

from playwright.sync_api import sync_playwright


def take_screenshots():
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_assets")
    os.makedirs(out, exist_ok=True)

    # Also save the synthetic data for upload
    data_zip = os.path.join(out, "demo_data.zip")
    if not os.path.exists(data_zip):
        print("Generating ZIP from synthetic data...")
        import shutil
        import tempfile
        import zipfile
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))
        from generate_synthetic_data import generate_dataset
        td = tempfile.mkdtemp()
        generate_dataset(td)
        with zipfile.ZipFile(data_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(td):
                for fn in files:
                    fp = os.path.join(root, fn)
                    zf.write(fp, os.path.relpath(fp, td))
        shutil.rmtree(td)
        print(f"ZIP saved: {data_zip}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        page.goto("http://127.0.0.1:8591", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(out, "01_empty_app.png"), full_page=True)
        print("Screenshot 1: empty app")

        # Upload the ZIP file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(data_zip)
        time.sleep(15)

        page.screenshot(path=os.path.join(out, "02_scan_results.png"), full_page=True)
        print("Screenshot 2: scan results")

        # Scroll to findings
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)
        page.screenshot(path=os.path.join(out, "03_findings.png"), full_page=True)
        print("Screenshot 3: findings")

        # Scroll to privacy warnings
        page.evaluate("window.scrollTo(0, 2000)")
        time.sleep(1)
        page.screenshot(path=os.path.join(out, "04_privacy_warnings.png"), full_page=True)
        print("Screenshot 4: privacy warnings")

        browser.close()

    print(f"\nScreenshots saved to: {out}")


if __name__ == "__main__":
    import sys
    take_screenshots()
