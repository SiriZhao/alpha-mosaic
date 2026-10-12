"""Comparison of execution and independent statistics paths."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from alphamosaic.backtesting.engines import PaperReplayAdapter, QuantStatsAdapterEngine
from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.evaluation.validation import returns_of


def dataset_fingerprint(data: ReplayDataset) -> str:
    payload = data.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def compare_engine_paths(
    data: ReplayDataset, strategy_name: str = "momentum", config: ReplayConfig | None = None
) -> dict[str, Any]:
    config = config or ReplayConfig()
    strategy = StrategyRegistry().get(strategy_name)
    execution = PaperReplayAdapter().run(data, strategy, strategy_name, config)
    analytics = QuantStatsAdapterEngine().run(data, strategy, strategy_name, config)
    if execution.result is None or analytics.result is None:
        return {
            "status": "BLOCKED",
            "source_fingerprint": dataset_fingerprint(data),
            "execution": execution.status,
            "analytics": analytics.status,
            "diagnostics": list(execution.diagnostics + analytics.diagnostics),
        }
    left, right = execution.result, analytics.result
    nav_left = [p.nav for p in left.equity]
    nav_right = [p.nav for p in right.equity]
    nav_diff = max((abs(a - b) for a, b in zip(nav_left, nav_right, strict=True)), default=0.0)
    metrics_diff: dict[str, float | None] = {}
    for key, left_value in execution.metrics.items():
        right_value = analytics.metrics.get(key)
        metrics_diff[key] = (
            float(left_value) - float(right_value)
            if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float))
            else None
        )
    return {
        "status": "COMPUTED",
        "source_fingerprint": dataset_fingerprint(data),
        "execution_engine": execution.engine,
        "analytics_engine": analytics.engine,
        "independent_execution_engine": False,
        "same_strategy": True,
        "same_cost_config": left.config.model_dump(mode="json")
        == right.config.model_dump(mode="json"),
        "same_sessions": [p.session for p in left.equity] == [p.session for p in right.equity],
        "same_fills": len(left.fills) == len(right.fills),
        "same_cash": all(a.cash == b.cash for a, b in zip(left.equity, right.equity, strict=True)),
        "nav_max_absolute_difference": nav_diff,
        "metrics_execution": execution.metrics,
        "metrics_quantstats": analytics.metrics,
        "metric_differences": metrics_diff,
        "difference_reasons": [
            "QuantStats receives the canonical equity return series and does not execute orders",
            "order, cash, fee, slippage, corporate-action and calendar fields are owned by PaperReplay",
        ],
        "fees": left.fees,
        "slippage_cost": left.slippage_cost,
        "fill_count": len(left.fills),
        "observations": len(returns_of(left)),
        "validation": "NO_ALPHA_CERTIFICATION",
    }
