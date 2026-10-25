"""Auditable daily-return analytics, independent of optional analytics vendors."""

from __future__ import annotations

import math
from collections.abc import Sequence
from numbers import Integral
from typing import Any

import numpy as np

from alphamosaic.backtesting.models import ReplayResult, dividend_accounting_signature


def _finite(value: float | np.floating[Any]) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _returns(values: Sequence[float] | np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or not np.isfinite(result).all() or (result < -1).any():
        raise ValueError("finite one-dimensional simple returns >= -1 required")
    return result


def _annualization(value: int | np.integer[Any]) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or not 0 < value <= 1_000_000:
        raise ValueError("annualization must be an integer in 1..1000000")
    return int(value)


def _scaled_moments(values: np.ndarray) -> tuple[float, float, float, np.ndarray]:
    """Normalize before computing mean/squares so finite representable moments survive."""
    scale = float(np.max(np.abs(values))) or 1.0
    normalized = values / scale
    mean = float(normalized.mean())
    centered = normalized - mean
    deviation = math.sqrt(float(np.dot(centered, centered)) / (len(values) - 1)) if len(values) > 1 else 0.0
    return scale, mean, deviation, centered


def _scaled_ratio(numerators: tuple[float, ...], denominators: tuple[float, ...] = ()) -> float | None:
    """Multiply/divide mantissas before restoring exponents, avoiding intermediate overflow."""
    if any(value == 0 for value in denominators):
        return None
    if any(value == 0 for value in numerators):
        return 0.0
    mantissa, exponent = 1.0, 0
    for values, direction in ((numerators, 1), (denominators, -1)):
        for value in values:
            part, power = math.frexp(value)
            mantissa = mantissa * part if direction == 1 else mantissa / part
            exponent += direction * power
            mantissa, adjustment = math.frexp(mantissa)
            exponent += adjustment
    try:
        return _finite(math.ldexp(mantissa, exponent))
    except OverflowError:
        return None


def returns_metrics(
    returns: Sequence[float] | np.ndarray,
    periods_per_year: int | np.integer[Any] = 252,
    risk_free_annual: float = 0,
) -> dict[str, float | None]:
    """Use trading-period annualization and include starting capital in drawdown."""
    periods_per_year = _annualization(periods_per_year)
    if not math.isfinite(risk_free_annual) or risk_free_annual <= -1:
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
        scale, _, deviation, _ = _scaled_moments(x)
        excess_scale, excess_mean, _, _ = _scaled_moments(excess)
        downside = np.minimum(excess, 0)
        downside_scale = float(np.max(np.abs(downside))) or 1.0
        downside_deviation = float(np.sqrt(np.mean((downside / downside_scale) ** 2)))
        std = _scaled_ratio((deviation, scale))
        downside_std = _scaled_ratio((downside_deviation, downside_scale))
        annual_root = math.sqrt(periods_per_year)
        result = {
            "return": _finite(wealth[-1] - 1),
            "cagr": _finite(cagr),
            "volatility": _scaled_ratio((deviation, scale, annual_root)) if len(x) > 1 else None,
            "sharpe": _scaled_ratio((excess_mean, excess_scale, annual_root), (deviation, scale)) if std is not None and std > 1e-15 else None,
            "sortino": _scaled_ratio((excess_mean, excess_scale, annual_root), (downside_deviation, downside_scale)) if downside_std is not None and downside_std > 1e-15 else None,
            "calmar": _finite(cagr / abs(max_dd)) if max_dd < -1e-15 else None,
            "max_drawdown": _finite(max_dd),
            "drawdown_duration_sessions": float(longest),
        }
    return result


def benchmark_metrics(
    returns: Sequence[float] | np.ndarray,
    benchmark_returns: Sequence[float] | np.ndarray,
    periods_per_year: int | np.integer[Any] = 252,
) -> dict[str, float | None]:
    """OLS daily excess-return intercept times annual periods, with zero RF."""
    periods_per_year = _annualization(periods_per_year)
    x, b = _returns(returns), _returns(benchmark_returns)
    if len(x) != len(b):
        raise ValueError("equal aligned return lengths and positive annualization required")
    names = ("beta", "alpha_annualized_arithmetic", "tracking_error", "information_ratio", "correlation")
    if len(x) < 2:
        return dict.fromkeys(names)
    active = x - b
    sx, mx, dx, cx = _scaled_moments(x)
    sb, mb, db, cb = _scaled_moments(b)
    sa, ma, da, _ = _scaled_moments(active)
    tracking = _scaled_ratio((sa, da))
    benchmark_std = _scaled_ratio((sb, db))
    strategy_std = _scaled_ratio((sx, dx))
    covariance = float(np.dot(cx, cb)) / (len(x) - 1)
    variance = float(np.dot(cb, cb)) / (len(x) - 1)
    beta = _scaled_ratio((covariance, sx), (variance, sb)) if benchmark_std is not None and benchmark_std > 1e-15 else None
    mean_x = _scaled_ratio((sx, mx))
    fitted_mean = _scaled_ratio((beta, sb, mb)) if beta is not None else None
    alpha = _scaled_ratio((mean_x - fitted_mean, float(periods_per_year))) if mean_x is not None and fitted_mean is not None else None
    correlation = _scaled_ratio((covariance,), (dx, db)) if benchmark_std is not None and benchmark_std > 1e-15 and strategy_std is not None and strategy_std > 1e-15 else None
    annual_root = math.sqrt(periods_per_year)
    return {
        "beta": beta,
        "alpha_annualized_arithmetic": alpha,
        "tracking_error": _scaled_ratio((sa, da, annual_root)),
        "information_ratio": _scaled_ratio((ma, annual_root), (da,)) if tracking is None or tracking > 1e-15 else None,
        "correlation": max(-1.0, min(1.0, correlation)) if correlation is not None else None,
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
        "market_exposure": None,
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
        elif dividend_accounting_signature(result.config) != dividend_accounting_signature(benchmark_result.config):
            benchmark_status = "BLOCKED_ACCOUNTING_MODEL_MISMATCH"
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
        payment_mode = result.config.accounting_schema_version >= 2
        cash_weight = _finite(point.cash / point.nav)
        if cash_weight is not None and not 0 <= cash_weight <= 1:
            cash_weight = None
        marks = point.market_values
        weights = [float(value) / point.nav for value in marks.values()]
        active = {symbol for symbol, quantity in point.positions.items() if quantity != 0}
        marked = {symbol for symbol, value in marks.items() if value != 0}
        receivable_weight = _finite(math.fsum(point.receivables.values()) / point.nav)
        if any(amount < 0 for amount in point.receivables.values()) or receivable_weight is None or not 0 <= receivable_weight <= 1:
            receivable_weight = None
        qualified = (
            cash_weight is not None and active == marked
            and (not payment_mode or receivable_weight is not None)
            and all(quantity >= 0 for quantity in point.positions.values())
            and all(math.isfinite(weight) and 0 <= weight <= 1 + 1e-10 for weight in weights)
            and math.isclose(math.fsum(weights) + cash_weight + (receivable_weight or 0 if payment_mode else 0), 1, rel_tol=1e-10, abs_tol=1e-10)
        )
        exposures.append({"session": str(point.session),
                          "concentration_hhi": math.fsum(w * w for w in weights) if qualified else None,
                          "cash_weight": cash_weight})
        if payment_mode:
            exposures[-1].update({"market_weight": math.fsum(weights) if qualified else None,
                                 "receivable_weight": receivable_weight})
    if result.config.accounting_schema_version >= 2:
        if all(row["market_weight"] is not None for row in exposures):
            metrics["market_exposure"] = math.fsum(row["market_weight"] for row in exposures) / len(exposures)
    elif all(row["cash_weight"] is not None for row in exposures):
        metrics["market_exposure"] = math.fsum(1 - row["cash_weight"] for row in exposures) / len(exposures)
    missing_concentration = sum(row["concentration_hhi"] is None for row in exposures)
    if missing_concentration:
        warnings.append(f"Asset concentration unavailable in {missing_concentration} sessions: missing or inconsistent position marks; gaps retained.")
    return {
        "metrics": metrics,
        "rolling": rolling,
        "drawdown_episodes": episodes,
        "exposures": exposures,
        "benchmark_status": benchmark_status,
        "attribution": {"fees_usd": result.fees, "slippage_usd": result.slippage_cost, "spread_usd": float(getattr(result, "spread_cost", 0)), "asset_pnl": None, "cash_interest": None},
        "warnings": warnings,
        "conventions": {"periods_per_year": periods_per_year, "rolling_window_sessions": rolling_window, "frequency": "DAILY_EXCHANGE_SESSION", "risk_free_annual": 0, "cagr": "geometric trading-period annualization", "return_basis": return_basis, "alpha": "OLS arithmetic daily intercept times annual periods; risk free zero", "sample_start": str(result.equity[0].session), "sample_end": str(result.equity[-1].session), "acceptance": result.acceptance},
    }
