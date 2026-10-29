"""Opt-in primary-source framework metadata capture; no source code is executed."""

import argparse
import base64
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

PROJECTS = {
    "qlib": ("microsoft/qlib", "pyqlib"),
    "lean": ("QuantConnect/Lean", None),
    "vectorbt": ("polakowo/vectorbt", "vectorbt"),
    "zipline-reloaded": ("stefan-jansen/zipline-reloaded", "zipline-reloaded"),
    "backtesting.py": ("kernc/backtesting.py", "backtesting"),
}


def capture() -> dict:
    rows = {}
    with httpx.Client(timeout=25, follow_redirects=True) as client:
        for name, (repo, package) in PROJECTS.items():
            item: dict[str, Any] = {"repository": f"https://github.com/{repo}"}
            for label, url in {
                "repository_metadata": f"https://api.github.com/repos/{repo}",
                "release": f"https://api.github.com/repos/{repo}/releases/latest",
                "license": f"https://api.github.com/repos/{repo}/license",
                **({"package": f"https://pypi.org/pypi/{package}/json"} if package else {}),
            }.items():
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    payload = response.json()
                    if label == "license":
                        text = base64.b64decode(payload["content"]).decode()
                        value = {"spdx": payload["license"]["spdx_id"], "url": payload["html_url"], "sha256": hashlib.sha256(text.encode()).hexdigest(), "text": text}
                    elif label == "repository_metadata":
                        value = {k: payload.get(k) for k in ("pushed_at", "archived", "default_branch", "language", "license")}
                    elif label == "release":
                        value = {k: payload.get(k) for k in ("tag_name", "published_at", "html_url", "target_commitish")}
                    else:
                        info = payload["info"]
                        value = {k: info.get(k) for k in ("version", "requires_python", "license_expression", "classifiers")}
                    item[label] = {"source": url, "status": "OK", "value": value}
                except (httpx.HTTPError, ValueError, KeyError) as exc:
                    item[label] = {"source": url, "status": type(exc).__name__, "http_status": exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None}
            branch, filename = ("main", "LICENSE") if name in {"qlib", "zipline-reloaded"} else ("master", "LICENSE.md" if name in {"vectorbt", "backtesting.py"} else "LICENSE")
            raw = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
            try:
                response = client.get(raw)
                response.raise_for_status()
                item["license_primary_text"] = {"source": raw, "status": "OK", "sha256": hashlib.sha256(response.content).hexdigest(), "text": response.text}
            except httpx.HTTPError as exc:
                item["license_primary_text"] = {"source": raw, "status": type(exc).__name__}
            rows[name] = item
    return {"captured_at": datetime.now(UTC).isoformat(), "primary_sources": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.allow_network:
        parser.error("network capture requires --allow-network")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(capture(), stream, indent=2)
