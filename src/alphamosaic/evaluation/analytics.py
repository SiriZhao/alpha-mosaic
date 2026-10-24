"""Auditable daily-return analytics, independent of optional analytics vendors."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from alphamosaic.backtesting.models import ReplayResult


def _finite(value: float | np.floating[Any]) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _returns(values: Sequence[float] | np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or not np.isfinite(result).all() or (result < -1).any():
        raise ValueError("finite one-dimensional simple returns >= -1 required")
    return result


def returns_metrics(
    returns: Sequence[float] | np.ndarray,
    periods_per_year: int = 252,
    risk_free_annual: float = 0,
) -> dict[str, float | None]:
    """Use trading-period annualization and include starting capital in drawdown."""
    if periods_per_year <= 0 or not math.isfinite(risk_free_annual) or risk_free_annual <= -1:
        raise ValueError("positive annualization and finite risk-free rate > -1 required")
    x = _returns(returns)
    names = ("return", "cagr", "volatility", "sharpe", "sortino", "calmar", "max_drawdown", "drawdown_duration_sessions")
    if not len(x):
        return dict.fromkeys(names)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        wealth = np.cumprod(1 + x)
        if not np.isfinite(wealth).all():
            raise ValueError("non-finite compounded wealth")
        peaks = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
        drawdowns = wealth / peaks - 1
        max_dd = float(drawdowns.min())
        duration = longest = 0
        for dd in drawdowns:
            duration = duration + 1 if dd < -1e-12 else 0
            longest = max(longest, duration)
        cagr = float(wealth[-1] ** (periods_per_year / len(x)) - 1)
        rf = (1 + risk_free_annual) ** (1 / periods_per_year) - 1
        excess = x - rf
        std = float(x.std(ddof=1)) if len(x) > 1 else 0.0
        downside = float(np.sqrt(np.mean(np.minimum(excess, 0) ** 2)))
        result = {
            "return": _finite(wealth[-1] - 1),
            "cagr": _finite(cagr),
            "volatility": _finite(std * np.sqrt(periods_per_year)) if len(x) > 1 else None,
            "sharpe": _finite(excess.mean() / std * np.sqrt(periods_per_year)) if std > 1e-15 else None,
            "sortino": _finite(excess.mean() / downside * np.sqrt(periods_per_year)) if downside > 1e-15 else None,
            "calmar": _finite(cagr / abs(max_dd)) if max_dd < -1e-15 else None,
            "max_drawdown": _finite(max_dd),
            "drawdown_duration_sessions": float(longest),
        }
    return result


def benchmark_metrics(
    returns: Sequence[float] | np.ndarray,
    benchmark_returns: Sequence[float] | np.ndarray,
    periods_per_year: int = 252,
) -> dict[str, float | None]:
    """OLS daily excess-return intercept times annual periods, with zero RF."""
    x, b = _returns(returns), _returns(benchmark_returns)
    if len(x) != len(b) or periods_per_year <= 0:
        raise ValueError("equal aligned return lengths and positive annualization required")
    names = ("beta", "alpha_annualized_arithmetic", "tracking_error", "information_ratio", "correlation")
    if len(x) < 2:
        return dict.fromkeys(names)
    active = x - b
    tracking = float(active.std(ddof=1))
    variance = float(b.var(ddof=1))
    beta = float(np.cov(x, b, ddof=1)[0, 1] / variance) if variance > 1e-30 else None
    return {
        "beta": _finite(beta) if beta is not None else None,
        "alpha_annualized_arithmetic": _finite((x.mean() - beta * b.mean()) * periods_per_year) if beta is not None else None,
        "tracking_error": _finite(tracking * np.sqrt(periods_per_year)),
        "information_ratio": _finite(active.mean() / tracking * np.sqrt(periods_per_year)) if tracking > 1e-15 else None,
        "correlation": _finite(np.corrcoef(x, b)[0, 1]) if variance > 1e-30 and x.var(ddof=1) > 1e-30 else None,
    }


def _result_returns(result: ReplayResult) -> np.ndarray:
    if not result.equity:
        raise ValueError("nonempty equity history required")
    dates = [point.session for point in result.equity]
    if dates != sorted(set(dates)):
        raise ValueError("unique chronological equity sessions required")
    nav = np.asarray([result.config.initial_cash, *[point.nav for point in result.equity]], dtype=float)
    if not np.isfinite(nav).all() or (nav <= 0).any():
        raise ValueError("strictly positive finite portfolio NAV required")
    return nav[1:] / nav[:-1] - 1


def analyze(
    result: ReplayResult,
    benchmark_result: ReplayResult | None = None,
    *,
    return_basis: str | None = None,
    benchmark_return_basis: str | None = None,
    periods_per_year: int = 252,
    rolling_window: int = 21,
) -> dict[str, Any]:
    """Produce JSON-compatible analytics; refuse incomparable benchmark series."""
    if rolling_window < 2:
        raise ValueError("rolling window must contain at least two sessions")
    returns = _result_returns(result)
    metrics = returns_metrics(returns, periods_per_year)
    metrics.update(benchmark_metrics([], [], periods_per_year))
    metrics.update({
        "turnover": result.turnover,
        "fill_count": float(len(result.fills)),
        "trade_count": None,
        "win_rate": None,
        "profit_factor": None,
        "average_holding_period_sessions": None,
        "market_exposure": float(np.mean([1 - point.cash / point.nav for point in result.equity])),
        "transaction_cost_drag_initial_capital": (result.fees + result.slippage_cost + float(getattr(result, "spread_cost", 0))) / result.config.initial_cash,
    })
    warnings = list(result.diagnostics) + [
        "Trade statistics requiring matched closed lots are unavailable; fill_count counts execution records and trade_count is null.",
        "Cost drag is explicit simulated costs divided by initial capital, not a counterfactual return difference.",
        "Regression alpha is descriptive association, not causal attribution or demonstrated alpha.",
    ]
    benchmark_status = "NOT_PROVIDED"
    benchmark_returns = None
    allowed_basis = {"PRICE", "TOTAL_RETURN", "RAW_WITH_CASH_ACTIONS"}
    if benchmark_result is not None:
        if return_basis not in allowed_basis or benchmark_return_basis not in allowed_basis:
            benchmark_status = "BLOCKED_UNKNOWN_RETURN_BASIS"
        elif return_basis != benchmark_return_basis:
            benchmark_status = "BLOCKED_RETURN_BASIS_MISMATCH"
        elif [point.session for point in result.equity] != [point.session for point in benchmark_result.equity]:
            benchmark_status = "BLOCKED_UNALIGNED_SESSIONS"
        elif result.acceptance != benchmark_result.acceptance:
            benchmark_status = "BLOCKED_EVIDENCE_CLASS_MISMATCH"
        else:
            benchmark_returns = _result_returns(benchmark_result)
            metrics.update(benchmark_metrics(returns, benchmark_returns, periods_per_year))
            benchmark_status = "COMPARABLE_SIMULATED_RETURNS"
            if result.config != benchmark_result.config:
                warnings.append("Benchmark and strategy simulation configurations differ; inspect execution and cost assumptions.")
        if benchmark_status.startswith("BLOCKED"):
            warnings.append(benchmark_status)
    nav = np.asarray([result.config.initial_cash, *[point.nav for point in result.equity]])
    peaks = np.maximum.accumulate(nav)
    dd = nav[1:] / peaks[1:] - 1
    rolling = []
    for i, point in enumerate(result.equity):
        row: dict[str, Any] = {"session": str(point.session), "return": float(returns[i]), "drawdown": float(dd[i])}
        if i + 1 >= rolling_window:
            window = returns[i + 1 - rolling_window:i + 1]
            values = returns_metrics(window, periods_per_year)
            row.update({"volatility": values["volatility"], "sharpe": values["sharpe"]})
            if benchmark_returns is not None:
                row.update(benchmark_metrics(window, benchmark_returns[i + 1 - rolling_window:i + 1], periods_per_year))
        rolling.append(row)
    episodes = []
    start = None
    trough = 0.0
    for i, value in enumerate(dd):
        if value < -1e-12:
            start = i if start is None else start
            trough = min(trough, float(value))
        elif start is not None:
            episodes.append({"start": str(result.equity[start].session), "recovery": str(result.equity[i].session), "underwater_sessions": i - start, "maximum_drawdown": trough})
            start, trough = None, 0.0
    if start is not None:
        episodes.append({"start": str(result.equity[start].session), "recovery": None, "underwater_sessions": len(dd) - start, "maximum_drawdown": trough})
    exposures = []
    for point in result.equity:
        market_values = getattr(point, "market_values", None)
        if market_values:
            weights = [float(value) / point.nav for value in market_values.values()]
            exposures.append({"session": str(point.session), "concentration_hhi": sum(w * w for w in weights), "cash_weight": point.cash / point.nav})
    return {
        "metrics": metrics,
        "rolling": rolling,
        "drawdown_episodes": episodes,
        "exposures": exposures,
        "benchmark_status": benchmark_status,
        "attribution": {"fees_usd": result.fees, "slippage_usd": result.slippage_cost, "spread_usd": float(getattr(result, "spread_cost", 0)), "asset_pnl": None, "cash_interest": None},
        "warnings": warnings,
        "conventions": {"periods_per_year": periods_per_year, "frequency": "DAILY_EXCHANGE_SESSION", "risk_free_annual": 0, "cagr": "geometric trading-period annualization", "return_basis": return_basis, "alpha": "OLS arithmetic daily intercept times annual periods; risk free zero", "sample_start": str(result.equity[0].session), "sample_end": str(result.equity[-1].session), "acceptance": result.acceptance},
    }
