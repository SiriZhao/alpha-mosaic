"""Isolated, bounded OpenBB V5 Fetcher SDK bridge; JSON stdin/stdout only.

No ambient OpenBB credentials/configuration are read. OpenBB 2.0.1 still uses
module-level paths; set these in this disposable worker before provider imports.
"""

import asyncio
import contextlib
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, cast


def initialize(runtime: Path) -> None:
    directory = runtime.resolve() / "openbb-v5"
    directory.mkdir(parents=True, exist_ok=True)
    constants = cast(Any, importlib.import_module("openbb_core.app.constants"))
    constants.OPENBB_DIRECTORY = directory
    constants.USER_SETTINGS_PATH = directory / "user_settings.json"
    constants.SYSTEM_SETTINGS_PATH = directory / "system_settings.json"
    # The official service respects user cache/data preferences. Both are local.
    settings = {
        "credentials": {},
        "preferences": {"data_directory": str(directory / "data"), "cache_directory": str(directory / "cache")},
        "defaults": {"commands": {}},
    }
    if not constants.USER_SETTINGS_PATH.exists():
        constants.USER_SETTINGS_PATH.write_text(json.dumps(settings), encoding="utf-8")
    if not constants.SYSTEM_SETTINGS_PATH.exists():
        constants.SYSTEM_SETTINGS_PATH.write_text("{}", encoding="utf-8")
    os.environ["OPENBB_AUTO_BUILD"] = "false"


async def fetch(model: str, name: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    module = importlib.import_module(f"openbb_nasdaq.models.{model}")
    fetcher = getattr(module, name)
    results = await fetcher.fetch_data(params=params, credentials={})
    if hasattr(results, "result"):
        results = results.result
    return [row.model_dump(mode="json") for row in results]


async def execute(request: dict[str, Any]) -> dict[str, Any]:
    operation = request["operation"]
    if operation == "universe":
        rows: list[dict[str, Any]] = []
        for exchange in ("nasdaq", "nyse", "amex"):
            data = await fetch(
                "equity_screener", "NasdaqEquityScreenerFetcher", {"exchange": exchange}
            )
            rows.extend([{**row, "exchange": exchange.upper()} for row in data])
        return {"rows": rows}
    if operation == "history":
        symbol = request["symbol"]
        etf = symbol in {"SPY", "QQQM"}
        history = await fetch(
            "etf_historical" if etf else "equity_historical",
            "NasdaqEtfHistoricalFetcher" if etf else "NasdaqEquityHistoricalFetcher",
            {"symbol": symbol, "start_date": request["start"], "end_date": request["end"]},
        )
        profile = await fetch(
            "etf_info" if etf else "equity_info",
            "NasdaqEtfInfoFetcher" if etf else "NasdaqEquityInfoFetcher",
            {"symbol": symbol},
        )
        fundamental: dict[str, Any] = {}
        errors: list[str] = []
        if request.get("fundamentals") and not etf:
            for model, name in (
                ("income_statement", "NasdaqIncomeStatementFetcher"),
                ("financial_ratios", "NasdaqFinancialRatiosFetcher"),
            ):
                try:
                    rows = await fetch(
                        model, name, {"symbol": symbol, "limit": 1, "period": "annual"}
                    )
                    if rows:
                        if model == "income_statement":
                            fundamental = rows[0]
                        elif fundamental.get("date") and rows[0].get("date") == fundamental["date"]:
                            fundamental.update(rows[0])
                        else:
                            errors.append("financial_ratios: PERIOD_ALIGNMENT_NOT_VERIFIED; not merged")
                except Exception as exc:
                    errors.append(f"{model}: {type(exc).__name__}")
        return {
            "rows": history,
            "profile": profile,
            "fundamentals": fundamental,
            "diagnostics": errors,
        }
    if operation == "index":
        return {
            "rows": await fetch(
                "index_historical", "NasdaqIndexHistoricalFetcher", request["params"]
            )
        }
    raise ValueError("unsupported worker operation")


def main() -> None:
    request = json.load(sys.stdin)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            initialize(Path(request["runtime"]))
            result = asyncio.run(asyncio.wait_for(execute(request), timeout=request["timeout"]))
        response = {"status": "OK", **result}
    except Exception as exc:
        response = {"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc)[:1000]}
    print(json.dumps(response, allow_nan=False))


if __name__ == "__main__":
    main()
