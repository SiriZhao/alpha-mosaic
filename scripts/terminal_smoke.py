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
from playwright.sync_api import expect, sync_playwright

from alphamosaic.experiments.runner import source_manifest


def check(url: str, output: Path, compare_ids: list[str] | None = None, experiment_id: str | None = None) -> dict:
    source_hash = source_manifest()["source_hash"]
    parsed = urlparse(url)
    if parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.scheme != "http":
        raise ValueError("local HTTP terminal only")
    output.mkdir(parents=True, exist_ok=True)
    pages = ["Research Overview", "Data Explorer", "Strategy Lab", "Backtest Results", "Experiment Comparison", "Risk Lab", "AI Research", "Reports"]
    errors = []
    extra_screenshots = 0
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
            if experiment_id and label in {"Backtest Results", "Risk Lab", "Reports"}:
                selection = page.get_by_role("combobox", name="Experiment", exact=True)
                if selection.input_value() != experiment_id:
                    selection.click()
                    if selection.is_editable():
                        selection.fill(experiment_id)
                    page.get_by_role("option", name=experiment_id, exact=True).click()
                expect(selection).to_have_value(experiment_id, timeout=30000)
                page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'", timeout=45000)
                if label != "Reports":
                    page.get_by_test_id("stCaptionContainer").filter(has_text="experiment " + experiment_id).first.wait_for(timeout=45000)
            if label == "Experiment Comparison" and compare_ids:
                for comparison_id in compare_ids:
                    selection = page.locator('[data-testid="stMultiSelect"] input').first
                    selection.fill(comparison_id)
                    page.get_by_role("option", name=comparison_id, exact=True).click()
                    page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'", timeout=45000)
                page.keyboard.press("Escape")
                page.get_by_role("heading", name=label, exact=True).click()
                page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').first.wait_for(timeout=30000)
            if label in {"Backtest Results", "Risk Lab"}:
                page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').first.wait_for(timeout=30000)
            if label in {"Research Overview", "Data Explorer", "Strategy Lab", "Backtest Results"}:
                page.locator('[data-testid="stDataFrame"] canvas').first.wait_for(timeout=30000)
            if page.locator('[data-testid="stException"]').count():
                errors.append(label + ": " + page.locator('[data-testid="stException"]').inner_text())
            page.screenshot(path=str(output / f"{index + 1:02d}-{label.lower().replace(' ', '-')}.png"), full_page=True)
            if label == "Experiment Comparison" and compare_ids:
                page.locator('[data-testid="stPlotlyChart"]').first.scroll_into_view_if_needed()
                page.screenshot(path=str(output / "10-qualified-comparison-curve.png"), full_page=True)
                extra_screenshots += 1
            if label == "Risk Lab" and page.get_by_role("heading", name="Persisted risk evidence").count():
                visible = page.locator('[data-testid="stPlotlyChart"]').filter(visible=True)
                visible.last.scroll_into_view_if_needed()
                page.screenshot(path=str(output / "11-rolling-risk-evidence.png"), full_page=True)
                extra_screenshots += 1
            if label == "Backtest Results" and experiment_id:
                tab = page.get_by_role("tab", name="Dividend accounting", exact=True)
                tab.click()
                expect(tab).to_have_attribute("aria-selected", "true")
                page.get_by_role("heading", name="Dividend rights and cash availability", exact=True).wait_for()
                page.get_by_text("Unpaid dividend claims", exact=True).scroll_into_view_if_needed()
                page.screenshot(path=str(output / "12-dividend-accounting.png"), full_page=True)
                extra_screenshots += 1
            if label == "Risk Lab" and experiment_id:
                page.get_by_role("tab", name="Exposure and concentration", exact=True).click()
                page.locator('[data-testid="stPlotlyChart"]').filter(visible=True).nth(1).scroll_into_view_if_needed()
                page.screenshot(path=str(output / "13-cash-market-receivable-weights.png"), full_page=True)
                extra_screenshots += 1
        collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
        if collapse.is_visible():
            collapse.click()
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(300)
        page.screenshot(path=str(output / "09-mobile-reports.png"), full_page=True)
        browser.close()
    if source_manifest()["source_hash"] != source_hash:
        errors.append("Source changed during browser verification")
    result = {"status": "PASSED" if not errors else "FAILED", "viewer_source_hash": source_hash, "pages": pages, "browser_errors": errors, "screenshots": 9 + extra_screenshots, "comparison_selection": compare_ids or [], "result_selection": experiment_id, "scope": "Navigation, render, populated local fixture reports, selected qualified comparison and result when requested, and mobile degradation; scrolled viewports where needed; not every interactive action"}
    (output / "browser-qa.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8518")
    parser.add_argument("--output", type=Path, default=Path("runtime/terminal-qa"))
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--home", type=Path, default=Path("runtime/renaissance-demo"))
    parser.add_argument("--compare", nargs="+", help="Actual comparable local experiment IDs to select in the browser")
    parser.add_argument("--experiment", help="Actual completed local experiment ID for results, risk and reports")
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
        result = check(args.url, args.output, args.compare, args.experiment)
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
    print(json.dumps(result))
    if result["status"] != "PASSED":
        raise SystemExit(1)
