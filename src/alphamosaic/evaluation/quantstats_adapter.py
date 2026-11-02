"""QuantStats analytics boundary: finite metrics only, no downloads."""

import importlib
import math

import pandas as pd


class QuantStatsAdapter:
    def metrics(self, returns: pd.Series) -> dict[str, float | None]:
        qs = importlib.import_module("quantstats")
        returns = pd.Series(returns.to_numpy(dtype=float), index=pd.date_range("2000-01-01", periods=len(returns), freq="B"))
        if returns.empty:
            return {"return": None, "cagr": None, "volatility": None, "max_drawdown": None, "sharpe": None, "sortino": None}
        if not all(math.isfinite(v) and v >= -1 for v in returns):
            raise ValueError("finite simple returns >= -1 required")
        variance = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
        raw = {
            "return": qs.stats.comp(returns),
            "cagr": qs.stats.cagr(returns, periods=252),
            "volatility": qs.stats.volatility(returns, periods=252),
            "max_drawdown": qs.stats.max_drawdown(returns),
            "sharpe": qs.stats.sharpe(returns, rf=0, periods=252) if variance > 1e-15 else None,
            "sortino": qs.stats.sortino(returns, rf=0, periods=252),
        }
        return {
            key: float(value) if value is not None and math.isfinite(float(value)) else None for key, value in raw.items()
        }
