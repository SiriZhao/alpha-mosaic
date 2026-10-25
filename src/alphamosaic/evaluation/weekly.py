"""Complete-week NAV analysis with explicit initial/final partial intervals."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Literal

import exchange_calendars as xcals

from alphamosaic.backtesting.models import EquityPoint, ReplayResult
from alphamosaic.core.contracts import Contract
from alphamosaic.data.weekly import aware_utc, sessions_of_week, week_start
from alphamosaic.evaluation.analytics import benchmark_metrics, returns_metrics


class WeeklyEquityPoint(Contract):
    week_start: date
    first_session: date
    last_session: date
    session_count: int
    starting_nav: float
    nav: float
    return_value: float
    available_at: datetime


class PartialEquityInterval(Contract):
    week_start: date
    first_session: date
    last_session: date
    starting_nav: float
    nav: float
    return_value: float
    reason: Literal["PARTIAL_EVALUATION_BOUNDARY", "WEEK_NOT_CLOSED_AT_CUTOFF"]


class WeeklyEquitySeries(Contract):
    points: list[WeeklyEquityPoint]
    partial_intervals: list[PartialEquityInterval]
    initial_cash: float
    source_start: date | None
    last_observed_session: date | None
    observed_total_return: float | None
    inception_return_through_last_completed_week: float | None
    cutoff: datetime
    frequency: Literal["WEEKLY_XNYS"] = "WEEKLY_XNYS"
    periods_per_year: Literal[52] = 52


def weekly_equity(result: ReplayResult, cutoff: datetime | None = None) -> WeeklyEquitySeries:
    """Retain the initial-capital interval; never annualize a partial week as a week.

    Complete weeks use the preceding observed NAV, or initial_cash at inception.
    Partial boundary returns remain separately visible and reconcile to observed total
    return. The inception-through-completed-week total includes any initial partial week.
    """
    if not result.equity:
        raise ValueError("nonempty daily equity required for weekly analysis")
    calendar = xcals.get_calendar("XNYS")
    at = aware_utc(cutoff if cutoff is not None else calendar.session_close(result.equity[-1].session).to_pydatetime())
    selected = []
    for point in result.equity:
        if point.session > at.date():
            continue
        if not calendar.is_session(point.session):
            raise ValueError("weekly NAV contains a non-session date")
        if calendar.session_close(point.session).to_pydatetime() <= at:
            if not math.isfinite(point.nav) or point.nav <= 0:
                raise ValueError("positive finite daily NAV required")
            selected.append(point)
    if not math.isfinite(result.config.initial_cash) or result.config.initial_cash <= 0:
        raise ValueError("positive finite initial NAV required")
    if not selected:
        return WeeklyEquitySeries(points=[], partial_intervals=[], initial_cash=result.config.initial_cash,
            source_start=None, last_observed_session=None, observed_total_return=None,
            inception_return_through_last_completed_week=None, cutoff=at)
    dates = [p.session for p in selected]
    expected = [s.date() for s in calendar.sessions_in_range(dates[0], dates[-1])]
    if dates != expected:
        raise ValueError("unique complete chronological daily NAV sessions required")
    groups: dict[date, list[EquityPoint]] = {}
    for point in selected:
        groups.setdefault(week_start(point.session), []).append(point)
    points: list[WeeklyEquityPoint] = []
    partial: list[PartialEquityInterval] = []
    previous = result.config.initial_cash
    for monday, rows in groups.items():
        expected_week = sessions_of_week(monday)
        available_at = calendar.session_close(expected_week[-1]).to_pydatetime()
        change = rows[-1].nav / previous - 1
        if not math.isfinite(change):
            raise ValueError("non-finite weekly return")
        if tuple(p.session for p in rows) == expected_week and available_at <= at:
            points.append(WeeklyEquityPoint(week_start=monday, first_session=rows[0].session,
                last_session=rows[-1].session, starting_nav=previous, nav=rows[-1].nav,
                return_value=change, session_count=len(rows), available_at=available_at))
        else:
            partial.append(PartialEquityInterval(week_start=monday, first_session=rows[0].session,
                last_session=rows[-1].session, starting_nav=previous, nav=rows[-1].nav,
                return_value=change, reason="WEEK_NOT_CLOSED_AT_CUTOFF" if available_at > at else "PARTIAL_EVALUATION_BOUNDARY"))
        previous = rows[-1].nav
    return WeeklyEquitySeries(points=points, partial_intervals=partial,
        initial_cash=result.config.initial_cash, source_start=dates[0],
        last_observed_session=dates[-1], observed_total_return=selected[-1].nav / result.config.initial_cash - 1,
        inception_return_through_last_completed_week=points[-1].nav / result.config.initial_cash - 1 if points else None,
        cutoff=at)


def analyze_weekly(
    result: ReplayResult,
    cutoff: datetime | None = None,
    benchmark_result: ReplayResult | None = None,
    *,
    return_basis: str | None = None,
    benchmark_return_basis: str | None = None,
    rolling_weeks: int = 13,
) -> dict[str, Any]:
    """Describe a daily replay at weekly frequency; not a weekly strategy claim."""
    if rolling_weeks < 2:
        raise ValueError("rolling weekly window must contain at least two weeks")
    series = weekly_equity(result, cutoff)
    values = [p.return_value for p in series.points]
    metrics = returns_metrics(values, periods_per_year=52)
    metrics["drawdown_duration_weeks"] = metrics.pop("drawdown_duration_sessions")
    metrics.update(benchmark_metrics([], [], periods_per_year=52))
    status = "NOT_PROVIDED"
    reference: list[float] | None = None
    warnings = [*result.diagnostics,
        "Weekly analysis aggregates the supplied daily replay; it does not turn a daily decision rule into a weekly strategy.",
        "Annualization uses 52 complete exchange-calendar weeks, not 252 sessions or five-day blocks.",
        "Partial initial/final intervals remain separate and are excluded from annualized weekly metrics.",
        "Week-end sampled drawdown and volatility do not capture all intraweek daily losses; retain the daily risk report.",
    ]
    if benchmark_result is not None:
        benchmark = weekly_equity(benchmark_result, series.cutoff)
        allowed = {"PRICE", "TOTAL_RETURN", "RAW_WITH_CASH_ACTIONS"}
        if return_basis not in allowed or benchmark_return_basis not in allowed:
            status = "BLOCKED_UNKNOWN_RETURN_BASIS"
        elif return_basis != benchmark_return_basis:
            status = "BLOCKED_RETURN_BASIS_MISMATCH"
        elif result.acceptance != benchmark_result.acceptance:
            status = "BLOCKED_EVIDENCE_CLASS_MISMATCH"
        elif series.source_start != benchmark.source_start or series.last_observed_session != benchmark.last_observed_session:
            status = "BLOCKED_EVALUATION_BOUNDARY_MISMATCH"
        elif [(p.week_start, p.first_session, p.last_session) for p in series.points] != [(p.week_start, p.first_session, p.last_session) for p in benchmark.points]:
            status = "BLOCKED_UNALIGNED_WEEKS"
        else:
            reference = [p.return_value for p in benchmark.points]
            metrics.update(benchmark_metrics(values, reference, periods_per_year=52))
            status = "COMPARABLE_SIMULATED_WEEKLY_RETURNS"
            if result.config != benchmark_result.config:
                warnings.append("Benchmark and strategy execution/cost configurations differ.")
        if status.startswith("BLOCKED"):
            warnings.append(status)
    rolling = []
    for i, point in enumerate(series.points):
        row: dict[str, Any] = {"week_start": point.week_start.isoformat(), "last_session": point.last_session.isoformat(), "return": point.return_value}
        if i + 1 >= rolling_weeks:
            window = values[i + 1 - rolling_weeks:i + 1]
            window_metrics = returns_metrics(window, periods_per_year=52)
            row.update(volatility=window_metrics["volatility"], sharpe=window_metrics["sharpe"])
            if reference is not None:
                row.update(benchmark_metrics(window, reference[i + 1 - rolling_weeks:i + 1], periods_per_year=52))
        rolling.append(row)
    return {"status": "COMPLETE_WEEKS_AVAILABLE" if values else "INSUFFICIENT_COMPLETE_WEEKS",
        "metrics": metrics, "weekly_equity": series.model_dump(mode="json"),
        "rolling": rolling, "benchmark_status": status, "warnings": list(dict.fromkeys(warnings)),
        "conventions": {"frequency": "WEEKLY_XNYS", "periods_per_year": 52,
            "metrics_scope": "COMPLETE_CALENDAR_WEEKS_ONLY", "risk_free_annual": 0,
            "observations": len(values), "partial_intervals": len(series.partial_intervals),
            "acceptance": result.acceptance, "return_basis": return_basis,
            "decision_frequency": "NOT_INFERRED_FROM_RETURN_SAMPLING"}}
