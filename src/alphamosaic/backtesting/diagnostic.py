"""Chronological, two-session-lag diagnostic. This does not validate the scanner."""

import hashlib

import numpy as np
import pandas as pd

from alphamosaic.core.contracts import BacktestResult, HistoricalBar
from alphamosaic.evaluation.quantstats_adapter import QuantStatsAdapter


def trend_diagnostic(
    bars: list[HistoricalBar],
    benchmarks: dict[str, list[HistoricalBar]],
    fee_bps: float = 10,
    out_of_sample: bool = False,
    slippage_bps: float = 5,
) -> BacktestResult:
    if len(bars) < 65 or not 0 <= fee_bps <= 100:
        raise ValueError("65 bars and fee_bps in 0..100 required")
    if len({bar.session for bar in bars}) != len(bars) or any(
        a.session >= b.session for a, b in zip(bars, bars[1:], strict=False)
    ):
        raise ValueError("unique chronological bars required")
    series = pd.Series(
        [bar.close for bar in bars],
        index=pd.to_datetime([bar.session for bar in bars]),
        dtype=float,
    )
    average = pd.Series(series.rolling(20).mean(), index=series.index)
    valid_signal = average.notna()
    signal = (series > average).astype(float).where(valid_signal).shift(2)
    gross = series.pct_change() * signal
    turnover = signal.fillna(0).diff().abs().fillna(0)
    if not 0 <= slippage_bps <= 100:
        raise ValueError("slippage_bps in 0..100 required")
    cost = turnover * (fee_bps + slippage_bps) / 10_000
    net = (gross - cost).dropna()
    if out_of_sample:
        # Fixed 70/30 chronology, no fitting or optimization on the holdout.
        net = net.loc[series.index[int(len(series) * 0.7)] :]
    if len(net) < 10:
        raise ValueError("insufficient evaluation observations")
    adapter = QuantStatsAdapter()
    comparisons = {}
    for symbol, reference in benchmarks.items():
        benchmark = pd.Series(
            [bar.close for bar in reference],
            index=pd.to_datetime([bar.session for bar in reference]),
            dtype=float,
        )
        if not benchmark.index.is_unique or not benchmark.index.is_monotonic_increasing:
            continue
        aligned = benchmark.pct_change(fill_method=None).reindex(net.index)
        if not aligned.isna().any():
            comparisons[symbol] = adapter.metrics(aligned)
    metrics = adapter.metrics(net)
    metrics["exposure"] = float(signal.reindex(net.index).mean())
    metrics["slippage_return_deduction"] = float((turnover * slippage_bps / 10_000).reindex(net.index).sum())
    for symbol, values in comparisons.items():
        if values["return"] is not None and metrics["return"] is not None:
            metrics[f"excess_return_{symbol}"] = metrics["return"] - values["return"]
    return BacktestResult(
        dataset_fingerprint=hashlib.sha256("".join(bar.model_dump_json() for bar in bars).encode()).hexdigest(),
        kind="OUT_OF_SAMPLE" if out_of_sample else "HISTORICAL",
        methodology=f"Fixed SMA20 long/cash; signal lagged two sessions; close-to-close price returns; fee {fee_bps}bp and slippage {slippage_bps}bp per unit turnover; no fitting",
        metrics=metrics,
        benchmarks=comparisons,
        turnover=float(turnover.reindex(net.index).sum()),
        fees=float((turnover * fee_bps / 10_000).reindex(net.index).sum()),
        signal_coverage=float(np.mean(valid_signal.shift(2, fill_value=False).astype(bool))),
        observations=len(net),
        limitations=[
            "Research implementation diagnostic; not evidence of scanner profitability",
            "Zero risk-free rate; no spread/impact/financing model",
            "Historical bars are retrieved/revised now, not PIT certified",
            "Current surviving security; no delisting return coverage",
            "Provider adjustment unknown: price returns may contain corporate actions",
            "OUT_OF_SAMPLE means fixed chronological holdout only, not independent prospective validation",
            "Fees are summed return deductions, not dollar account fees",
        ],
    )
