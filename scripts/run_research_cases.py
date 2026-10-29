"""Reproduce fixed synthetic cases and sensitivity controls; never optimize results."""

import argparse
import cProfile
import json
import pstats
import time
import tracemalloc
from pathlib import Path
from uuid import uuid4

from alphamosaic.backtesting.models import preset_config
from alphamosaic.core.service import ApplicationService


def run(home: Path, sessions: int = 504) -> dict:
    service = ApplicationService(home)
    manifest = service.research_demo(sessions)
    data = service.experiment_runner().datasets.load(manifest["dataset_id"])
    dates = [b.session for b in data.bars["SPY"]]
    split = int(len(dates) * .7)
    common = {"dataset_id": manifest["dataset_id"], "benchmark": "SPY", "start": str(dates[80]), "end": str(dates[-1]), "question": "Can a fixed synthetic baseline reproduce under explicit costs and independent accounting checks?"}
    cases = [
        ("A_buy_hold", "buy_and_hold", ["SPY"], "realistic", 63, False),
        ("B_trend", "trend", ["SPY"], "realistic", 63, False),
        ("C_allocation", "low_volatility", ["SPY", "QQQM", "TLT"], "realistic", 63, False),
        ("cost_zero", "trend", ["SPY"], "zero", 63, False),
        ("cost_stress", "trend", ["SPY"], "stress", 63, False),
        ("parameter_42", "time_series_momentum", ["SPY"], "realistic", 42, False),
        ("parameter_84", "time_series_momentum", ["SPY"], "realistic", 84, False),
        ("declared_holdout", "trend", ["SPY"], "realistic", 63, True),
    ]
    runs = []
    for label, strategy, symbols, cost, lookback, holdout in cases:
        config = {**common, "strategy": strategy, "symbols": symbols, "replay": preset_config(cost).model_copy(update={"lookback": lookback}).model_dump(mode="json")}
        if holdout:
            config.update(start=str(dates[split]), validation="PREDECLARED_HOLDOUT")
        result = service.research_experiment(config)
        runs.append({"case": label, "experiment_id": result["experiment_id"], "status": result["status"], "acceptance": result.get("acceptance"), "error": result.get("error")})
    # Keep failed research visible, including a valid configuration with a missing dataset.
    failed = service.research_experiment({**common, "dataset_id": "0" * 64, "strategy": "trend", "symbols": ["SPY"]})
    rows = [service.research_result(row["experiment_id"]) for row in runs]
    comparison = service.research_comparison([row["experiment_id"] for row in runs[:3]])
    return {"acceptance": "FIXTURE", "market_performance_inference": "PROHIBITED", "dataset_id": manifest["dataset_id"], "cases": runs, "failed_control": {"experiment_id": failed["experiment_id"], "status": failed["status"]}, "comparison": comparison, "trials_attempted": len(cases), "selection": "ALL_PREDECLARED_CASES_RETAINED", "holdout": "Declared chronological synthetic evaluation only; no model fitting or independent market validation", "completed": sum(r["status"] == "COMPLETED" for r in runs), "metrics_available": all(bool(r.get("analysis")) for r in rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path("runtime/renaissance-demo"))
    parser.add_argument("--sessions", type=int, default=504)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    args.home.mkdir(parents=True, exist_ok=True)
    profiler = cProfile.Profile()
    tracemalloc.start()
    started = time.perf_counter()
    if args.profile:
        profiler.enable()
    summary = run(args.home, args.sessions)
    if args.profile:
        profiler.disable()
        with (args.home / ("profile-" + uuid4().hex + ".txt")).open("x") as stream:
            pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(25)
    summary["performance"] = {"elapsed_seconds": time.perf_counter() - started, "peak_traced_bytes": tracemalloc.get_traced_memory()[1], "includes": "dataset validation, replay, analytics, serialization and HTML chart generation", "optimization": "No optimization claimed; profile establishes baseline"}
    tracemalloc.stop()
    output = args.home / ("suite-" + uuid4().hex + ".json")
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"summary": str(output.resolve()), "completed": summary["completed"], "cases": summary["cases"], "performance": summary["performance"]}, indent=2))
    if summary["completed"] != 8 or summary["failed_control"]["status"] != "FAILED":
        raise SystemExit(1)
