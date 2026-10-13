"""Recompute persisted factors without fetching or substituting market data."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from alphamosaic.core.contracts import DataBatch
from alphamosaic.data.validation import validate_batch
from alphamosaic.factors.engine import FactorEngine
from alphamosaic.reporting.store import ReportStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    store = ReportStore(args.home / "reports")
    report = store.get(args.run_id)
    if report is None or not report.source_batches:
        raise ValueError("no persisted source snapshots to recompute")
    batches = {symbol: DataBatch.model_validate(value) for symbol, value in report.source_batches.items()}
    benchmark_bars = {}
    for symbol in ("SPY", "QQQM"):
        batch = batches.get(symbol)
        flags = validate_batch(batch.identity, batch.bars, report.cutoff, purpose="PRICE_BENCHMARK") if batch else ["MISSING"]
        benchmark_bars[symbol] = batch.bars if batch and not flags and batch.status.value == "OK" else []
    for candidate in report.candidates:
        batch = batches[candidate.ticker]
        recomputed = FactorEngine().calculate(batch.bars, benchmark_bars["SPY"], batch.fundamentals, benchmark_bars["QQQM"], report.cutoff)
        for key, value in candidate.factors.items():
            actual = recomputed.get(key)
            if value is None and actual is None:
                continue
            if value is None or actual is None or not math.isclose(value, actual, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"factor replay mismatch: {candidate.ticker}/{key}")
    generated = store.finalize(report.run_id)
    if generated != store.finalize(report.run_id):
        raise ValueError("nonreproducible daily report")
    print(json.dumps({"run_id": report.run_id, "factor_replay": "PASSED", "candidates_checked": len(report.candidates), "cutoff": report.cutoff.isoformat(), "input_sha256": hashlib.sha256((store.root / report.run_id / "report.json").read_bytes()).hexdigest(), "generated": str(generated), "investment_action": "NO_ACTION"}, indent=2))


if __name__ == "__main__":
    main()
