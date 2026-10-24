"""Opt-in browser QA of an operator-started localhost research terminal."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from playwright.sync_api import sync_playwright


def check(url: str, output: Path) -> dict:
    parsed = urlparse(url)
    if parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.scheme != "http":
        raise ValueError("local HTTP terminal only")
    output.mkdir(parents=True, exist_ok=True)
    pages = ["Research Overview", "Data Explorer", "Strategy Lab", "Backtest Results", "Experiment Comparison", "Risk Lab", "AI Research", "Reports"]
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1080})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        page.get_by_role("heading", name="Research Overview", exact=True).wait_for(timeout=45000)
        for index, label in enumerate(pages):
            page.get_by_text(label, exact=True).first.click()
            page.get_by_role("heading", name=label, exact=True).wait_for()
            page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'", timeout=45000)
            if label in {"Backtest Results", "Risk Lab"}:
                page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').wait_for(timeout=30000)
            if label in {"Research Overview", "Data Explorer", "Strategy Lab", "Backtest Results"}:
                page.locator('[data-testid="stDataFrame"] canvas').first.wait_for(timeout=30000)
            if page.locator('[data-testid="stException"]').count():
                errors.append(label + ": " + page.locator('[data-testid="stException"]').inner_text())
            page.screenshot(path=str(output / f"{index + 1:02d}-{label.lower().replace(' ', '-')}.png"), full_page=True)
        collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
        if collapse.is_visible():
            collapse.click()
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(300)
        page.screenshot(path=str(output / "09-mobile-reports.png"), full_page=True)
        browser.close()
    result = {"status": "PASSED" if not errors else "FAILED", "pages": pages, "browser_errors": errors, "screenshots": 9, "scope": "Navigation, render, populated local fixture reports and mobile degradation; not every interactive action"}
    (output / "browser-qa.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8518")
    parser.add_argument("--output", type=Path, default=Path("runtime/terminal-qa"))
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--home", type=Path, default=Path("runtime/renaissance-demo"))
    args = parser.parse_args()
    process = None
    try:
        if args.start_server:
            parsed = urlparse(args.url)
            if parsed.hostname not in {"localhost", "127.0.0.1"} or not parsed.port:
                parser.error("explicit localhost port required")
            app = Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"
            process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(app), "--server.headless", "true", "--server.address", "127.0.0.1", "--server.port", str(parsed.port), "--browser.gatherUsageStats", "false", "--theme.base", "dark"], env={**os.environ, "ALPHAMOSAIC_HOME": str(args.home.resolve())}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            deadline = time.monotonic() + 30
            while True:
                try:
                    response = httpx.get(args.url + "/_stcore/health", timeout=1)
                    response.raise_for_status()
                    break
                except httpx.HTTPError:
                    if time.monotonic() > deadline or process.poll() is not None:
                        raise RuntimeError("local terminal failed startup health check") from None
                    time.sleep(.2)
        result = check(args.url, args.output)
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
    print(json.dumps(result))
    if result["status"] != "PASSED":
        raise SystemExit(1)
