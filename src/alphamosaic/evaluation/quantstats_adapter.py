"""QuantStats analytics boundary: finite metrics only, no downloads."""

import importlib
import math

import pandas as pd


class QuantStatsAdapter:
    def metrics(self, returns: pd.Series) -> dict[str, float | None]:
        qs = importlib.import_module("quantstats")
        raw = {
            "return": qs.stats.comp(returns),
            "volatility": qs.stats.volatility(returns, periods=252),
            "max_drawdown": qs.stats.max_drawdown(returns),
            "sharpe": qs.stats.sharpe(returns, rf=0, periods=252),
            "sortino": qs.stats.sortino(returns, rf=0, periods=252),
        }
        return {
            key: float(value) if math.isfinite(float(value)) else None for key, value in raw.items()
        }
