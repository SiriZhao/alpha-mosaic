"""Natural-week causality, manual returns, and weekly-rule boundary checks."""

from datetime import UTC, date, datetime, timedelta

import exchange_calendars as xcals
import pytest

from alphamosaic.backtesting.models import EquityPoint, ReplayConfig, ReplayDataset, ReplayResult
from alphamosaic.backtesting.weekly_strategy import WeeklyBaselineStrategy, WeeklyStrategyParameters
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar, SecurityIdentity
from alphamosaic.data.weekly import (
    aggregate_weekly,
    aggregate_weekly_bars,
    is_week_close,
    last_session_of_week,
)
from alphamosaic.evaluation.weekly import analyze_weekly, weekly_equity


def data_between(start: str = "2024-01-02", end: str = "2024-02-02") -> ReplayDataset:
    calendar = xcals.get_calendar("XNYS")
    sessions = list(calendar.sessions_in_range(start, end))
    bars = []
    for i, session in enumerate(sessions):
        at = calendar.session_close(session).to_pydatetime()
        bars.append(HistoricalBar(symbol="AAA", session=session.date(), open=100 + i,
            high=101 + i, low=99 + i, close=100.5 + i, volume=1000 + i,
            observed_at=at, known_at=at, as_of=at, source="fixture-weekly-v1",
            source_url="https://example.invalid/weekly", currency="USD",
            data_quality=DataQuality.FIXTURE, adjustment_policy="RAW",
            provenance={"provider_version": "1"}, pit_status="VERIFIED", license_scope="test-only"))
    identity = SecurityIdentity(symbol="AAA", exchange="NYSE", currency="USD", active=True,
        identity_verified=True, identity_source="fixture", as_of=calendar.session_open(sessions[0]).to_pydatetime())
    return ReplayDataset(bars={"AAA": bars}, identities={"AAA": identity}, cutoff=bars[-1].as_of,
        historical_universe_verified=True, corporate_actions_complete=True)


def equity_result(data: ReplayDataset, weekly_growth: float = 0) -> ReplayResult:
    weeks = []
    points = []
    for bar in data.bars["AAA"]:
        label = bar.session - timedelta(days=bar.session.weekday())
        if label not in weeks:
            weeks.append(label)
        nav = 100 * (1 + weekly_growth) ** (len(weeks) - 1)
        if is_week_close(bar.session):
            nav *= 1 + weekly_growth
        points.append(EquityPoint(session=bar.session, nav=nav, cash=nav, positions={}))
    return ReplayResult(strategy="fixture-equity", kind="HISTORICAL", acceptance="FIXTURE",
        config=ReplayConfig(initial_cash=100), equity=points, fills=[], unfilled_orders=[],
        applied_actions=[], turnover=0, fees=0, slippage_cost=0, diagnostics=[])


def test_good_friday_week_uses_four_sessions_and_thursday_close() -> None:
    data = data_between("2024-03-25", "2024-03-28")
    view = aggregate_weekly(data)
    assert is_week_close(date(2024, 3, 28))
    assert not is_week_close(date(2024, 3, 29))
    assert last_session_of_week(date(2024, 3, 29)) == date(2024, 3, 28)
    assert len(view.bars["AAA"]) == 1
    bar = view.bars["AAA"][0]
    assert bar.session_count == 4 and bar.first_session == date(2024, 3, 25)
    assert bar.last_session == date(2024, 3, 28)
    assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == (100, 104, 99, 103.5, 4006)
    assert bar.available_at == data.cutoff
    assert bar.frequency == "WEEKLY_XNYS" and view.periods_per_year == 52


def test_partial_boundaries_are_explicit_and_internal_missing_sessions_rejected() -> None:
    data = data_between("2024-01-03", "2024-01-17")
    view = aggregate_weekly(data)
    assert [b.week_start for b in view.bars["AAA"]] == [date(2024, 1, 8)]
    assert [x.reason for x in view.excluded_weeks["AAA"]] == ["PARTIAL_BOUNDARY_WEEK", "WEEK_NOT_CLOSED_AT_CUTOFF"]
    bad = data.model_copy(update={"bars": {"AAA": [b for b in data.bars["AAA"] if b.session != date(2024, 1, 10)]}})
    with pytest.raises(ValueError, match="complete chronological"):
        aggregate_weekly(bad)


def test_friday_bar_is_unavailable_until_close_and_late_known_at_is_respected() -> None:
    data = data_between("2024-01-02", "2024-01-05")
    just_before_close = data.cutoff - timedelta(seconds=1)
    assert not aggregate_weekly(data, just_before_close).bars["AAA"]
    delayed = data.bars["AAA"][-1].model_copy(update={"known_at": data.cutoff + timedelta(days=1), "as_of": data.cutoff + timedelta(days=1)})
    future = data.model_copy(update={"bars": {"AAA": [*data.bars["AAA"][:-1], delayed]}, "cutoff": data.cutoff + timedelta(days=1)})
    unavailable = aggregate_weekly(future, data.cutoff)
    assert unavailable.excluded_weeks["AAA"][0].reason == "DATA_NOT_AVAILABLE_AT_CUTOFF"
    available = aggregate_weekly(future)
    assert available.bars["AAA"][0].available_at == delayed.known_at


def test_future_price_perturbation_does_not_change_completed_week_view() -> None:
    data = data_between()
    cutoff = xcals.get_calendar("XNYS").session_close(date(2024, 1, 12)).to_pydatetime()
    altered = [b.model_copy(update={"open": b.open * 9, "high": b.high * 9, "low": b.low * 9, "close": b.close * 9}) if b.session > cutoff.date() else b for b in data.bars["AAA"]]
    future = data.model_copy(update={"bars": {"AAA": altered}})
    assert aggregate_weekly(data, cutoff) == aggregate_weekly(future, cutoff)


@pytest.mark.parametrize("changes", [
    {"source": "another-provider"}, {"source_url": "https://example.invalid/other"},
    {"currency": "GBP"}, {"adjustment_policy": "SPLIT"},
    {"provenance": {"provider_version": "2"}}, {"data_quality": DataQuality.HISTORICAL},
])
def test_mixed_weekly_metadata_never_silently_aggregates(changes: dict) -> None:
    data = data_between()
    rows = list(data.bars["AAA"])
    rows[2] = rows[2].model_copy(update=changes)
    with pytest.raises(ValueError, match="mixed weekly"):
        aggregate_weekly(data.model_copy(update={"bars": {"AAA": rows}}))


def test_raw_action_discontinuities_are_rejected_instead_of_skipping_a_week() -> None:
    data = data_between()
    row = data.bars["AAA"][4]
    evidence = row.model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    action = CorporateAction(**evidence, action="SPLIT", effective_date=row.session, ratio=2)
    with pytest.raises(ValueError, match="RAW_CORPORATE_ACTION"):
        aggregate_weekly(data.model_copy(update={"actions": [action]}))


def test_late_disclosed_effective_action_cannot_qualify_a_raw_weekly_view() -> None:
    data = data_between("2024-01-02", "2024-01-12")
    cutoff = data.cutoff
    known = cutoff + timedelta(days=4)
    rows = [b if i < 2 else b.model_copy(update={field: getattr(b, field) / 2 for field in ("open", "high", "low", "close")}) for i, b in enumerate(data.bars["AAA"])]
    evidence = rows[0].model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    evidence.update(known_at=known, as_of=known)
    action = CorporateAction(**evidence, action="SPLIT", effective_date=rows[2].session, ratio=2)
    revised = data.model_copy(update={"bars": {"AAA": rows}, "actions": [action],
        "cutoff": known, "mode": "RECONSTRUCTED_DIAGNOSTIC"})
    with pytest.raises(ValueError, match="RAW_CORPORATE_ACTION"):
        aggregate_weekly(revised, cutoff)


def test_unknown_volume_stays_null_and_naive_cutoff_rejected() -> None:
    data = data_between()
    rows = list(data.bars["AAA"])
    rows[0] = rows[0].model_copy(update={"volume": None})
    view = aggregate_weekly_bars(rows, cutoff=data.cutoff)
    assert view.bars[0].volume is None
    assert "MISSING_DAILY_VOLUME_WEEKLY_VOLUME_WITHHELD" in view.warnings
    with pytest.raises(ValueError, match="aware"):
        aggregate_weekly(data, datetime(2024, 2, 2))
    with pytest.raises(ValueError, match="cannot exceed"):
        aggregate_weekly(data, data.cutoff + timedelta(seconds=1))


def test_weekly_equity_keeps_first_return_and_uses_fifty_two_periods() -> None:
    data = data_between("2024-01-02", "2024-01-12")
    result = equity_result(data, .1)
    series = weekly_equity(result)
    assert len(series.points) == 2 and not series.partial_intervals
    assert [p.return_value for p in series.points] == pytest.approx([.1, .1])
    analysis = analyze_weekly(result)
    assert analysis["metrics"]["return"] == pytest.approx(.21)
    assert analysis["metrics"]["cagr"] == pytest.approx(1.1 ** 52 - 1)
    assert analysis["metrics"]["drawdown_duration_weeks"] == 0
    assert "drawdown_duration_sessions" not in analysis["metrics"]
    assert series.inception_return_through_last_completed_week == pytest.approx(.21)


def test_partial_initial_nav_interval_remains_visible_without_wrong_annualization() -> None:
    data = data_between("2024-01-03", "2024-01-17")
    result = equity_result(data, .1)
    analysis = analyze_weekly(result)
    series = analysis["weekly_equity"]
    assert analysis["conventions"]["observations"] == 1
    assert analysis["metrics"]["return"] == pytest.approx(.1)
    assert series["partial_intervals"][0]["return_value"] == pytest.approx(.1)
    assert series["inception_return_through_last_completed_week"] == pytest.approx(.21)
    assert series["observed_total_return"] == pytest.approx(.21)
    assert len(series["partial_intervals"]) == 2


def test_constant_nav_has_zero_return_and_benchmark_basis_is_checked() -> None:
    result = equity_result(data_between())
    analysis = analyze_weekly(result, benchmark_result=result, return_basis="RAW_WITH_CASH_ACTIONS", benchmark_return_basis="RAW_WITH_CASH_ACTIONS")
    assert analysis["metrics"]["return"] == 0
    assert analysis["metrics"]["volatility"] == 0
    assert analysis["metrics"]["sharpe"] is None
    assert analysis["benchmark_status"] == "COMPARABLE_SIMULATED_WEEKLY_RETURNS"
    assert analyze_weekly(result, benchmark_result=result)["benchmark_status"] == "BLOCKED_UNKNOWN_RETURN_BASIS"
    assert analyze_weekly(result, benchmark_result=result, return_basis="PRICE", benchmark_return_basis="TOTAL_RETURN")["benchmark_status"] == "BLOCKED_RETURN_BASIS_MISMATCH"


def test_future_nav_cannot_change_historical_weekly_analytics() -> None:
    data = data_between()
    result = equity_result(data, .02)
    cutoff = xcals.get_calendar("XNYS").session_close(date(2024, 1, 12)).to_pydatetime()
    changed = result.model_copy(update={"equity": [p.model_copy(update={"nav": p.nav * 100}) if p.session > cutoff.date() else p for p in result.equity]})
    assert analyze_weekly(result, cutoff) == analyze_weekly(changed, cutoff)


def test_missing_daily_nav_and_nonfinite_values_are_rejected() -> None:
    result = equity_result(data_between())
    with pytest.raises(ValueError, match="complete chronological"):
        weekly_equity(result.model_copy(update={"equity": [*result.equity[:5], *result.equity[6:]]}))
    points = list(result.equity)
    points[3] = points[3].model_copy(update={"nav": float("inf")})
    with pytest.raises(ValueError, match="positive finite"):
        weekly_equity(result.model_copy(update={"equity": points}))


def test_weekly_momentum_uses_week_window_and_only_completed_available_values() -> None:
    data = data_between("2024-01-02", "2024-02-02")
    strategy = WeeklyBaselineStrategy("weekly_momentum", WeeklyStrategyParameters(lookback_weeks=2))
    config = ReplayConfig(max_single_weight=.4, min_cash_buffer=.1, weekly_parameters=WeeklyStrategyParameters(lookback_weeks=2))
    decision = strategy.allocation(data.bars, [], data.cutoff, config)
    assert decision.weights == {"AAA": .4}
    assert len(decision.evidence_ids) >= 3
    # A giant current partial-week price cannot manufacture a new completed-week signal.
    partial = data_between("2024-01-02", "2024-01-10")
    assert not strategy.allocation(partial.bars, [], partial.cutoff, config).weights
    changed = [b.model_copy(update={"open": b.open * 100, "close": b.close * 100, "high": b.high * 100, "low": b.low * 100}) if b.session >= date(2024, 1, 8) else b for b in partial.bars["AAA"]]
    assert not strategy.allocation({"AAA": changed}, [], partial.cutoff, config).weights


def test_weekly_strategy_rejects_internal_unavailable_weeks_and_invalid_parameters() -> None:
    data = data_between()
    rows = list(data.bars["AAA"])
    rows[5] = rows[5].model_copy(update={"known_at": data.cutoff + timedelta(days=1), "as_of": data.cutoff + timedelta(days=1)})
    strategy = WeeklyBaselineStrategy("weekly_equal_weight")
    with pytest.raises(ValueError, match="consecutive"):
        strategy.allocation({"AAA": rows}, [], data.cutoff, ReplayConfig())
    with pytest.raises(ValueError, match="short window"):
        WeeklyStrategyParameters(trend_short_weeks=12, trend_long_weeks=4)


def test_weekly_trend_warmup_is_weeks_not_daily_lookback() -> None:
    data = data_between("2024-01-02", "2024-02-02")
    strategy = WeeklyBaselineStrategy("weekly_trend", WeeklyStrategyParameters(trend_short_weeks=2, trend_long_weeks=3))
    decision = strategy.allocation(data.bars, [], data.cutoff, ReplayConfig(lookback=252, weekly_parameters=WeeklyStrategyParameters(trend_short_weeks=2, trend_long_weeks=3)))
    assert decision.weights == {"AAA": 1}
    assert decision.decision_at.tzinfo == UTC


def test_strict_unknown_adjustment_or_unverified_historical_identity_rejected() -> None:
    data = data_between()
    unknown = data.model_copy(update={"bars": {"AAA": [b.model_copy(update={"adjustment_policy": "UNKNOWN"}) for b in data.bars["AAA"]]}})
    with pytest.raises(ValueError, match="explicit adjustment"):
        aggregate_weekly(unknown)
    identity = data.identities["AAA"].model_copy(update={"as_of": data.bars["AAA"][0].known_at})
    with pytest.raises(ValueError, match="historical identity"):
        aggregate_weekly(data.model_copy(update={"identities": {"AAA": identity}}))


def test_different_providers_are_explicit_across_assets_but_fixture_real_mix_fails() -> None:
    data = data_between()
    other = [b.model_copy(update={"symbol": "BBB", "source": "another-fixture-provider"}) for b in data.bars["AAA"]]
    identity = data.identities["AAA"].model_copy(update={"symbol": "BBB"})
    two = data.model_copy(update={"bars": {**data.bars, "BBB": other}, "identities": {**data.identities, "BBB": identity}})
    assert "MIXED_WEEKLY_ASSET_PROVIDERS_REVIEW_REQUIRED" in aggregate_weekly(two).warnings
    real = [b.model_copy(update={"data_quality": DataQuality.HISTORICAL}) for b in other]
    with pytest.raises(ValueError, match="fixture and real weekly"):
        aggregate_weekly(two.model_copy(update={"bars": {**data.bars, "BBB": real}}))


def test_unaligned_assets_and_duplicate_sessions_fail_closed() -> None:
    data = data_between()
    identity = data.identities["AAA"].model_copy(update={"symbol": "BBB"})
    other = [b.model_copy(update={"symbol": "BBB"}) for b in data.bars["AAA"][:-5]]
    with pytest.raises(ValueError, match="unaligned"):
        aggregate_weekly(data.model_copy(update={"bars": {**data.bars, "BBB": other}, "identities": {**data.identities, "BBB": identity}}))
    with pytest.raises(ValueError, match="complete chronological"):
        aggregate_weekly_bars([data.bars["AAA"][0], *data.bars["AAA"]], cutoff=data.cutoff)


def test_diagnostic_reconstructed_series_preserves_untrusted_availability() -> None:
    data = data_between()
    fetched = data.cutoff + timedelta(days=5)
    rows = [b.model_copy(update={"pit_status": "RECONSTRUCTED", "data_quality": DataQuality.HISTORICAL,
        "known_at": fetched, "as_of": fetched, "adjustment_policy": "UNKNOWN"}) for b in data.bars["AAA"]]
    diagnostic = data.model_copy(update={"bars": {"AAA": rows}, "mode": "RECONSTRUCTED_DIAGNOSTIC", "cutoff": fetched,
        "historical_universe_verified": False, "corporate_actions_complete": False})
    view = aggregate_weekly(diagnostic)
    assert view.bars["AAA"][0].available_at == fetched
    assert view.bars["AAA"][0].pit_status == "RECONSTRUCTED"
    assert "RECONSTRUCTED_WEEKLY_VALUES_NOT_CERTIFIED_HISTORICAL_SIGNAL_INPUT" in view.warnings
    assert all(not rows for rows in aggregate_weekly(diagnostic, data.cutoff).bars.values())


def test_only_partial_week_returns_have_no_annualized_week_metric() -> None:
    data = data_between("2024-01-03", "2024-01-04")
    result = equity_result(data)
    analysis = analyze_weekly(result)
    assert analysis["status"] == "INSUFFICIENT_COMPLETE_WEEKS"
    assert analysis["metrics"]["return"] is None and analysis["metrics"]["cagr"] is None
    assert analysis["weekly_equity"]["observed_total_return"] == 0
    assert len(analysis["weekly_equity"]["partial_intervals"]) == 1


def test_complete_and_partial_returns_reconcile_to_observed_initial_capital() -> None:
    result = equity_result(data_between("2024-01-03", "2024-01-17"), .02)
    series = weekly_equity(result)
    intervals = [*series.points, *series.partial_intervals]
    compounded = 1.0
    for interval in sorted(intervals, key=lambda p: p.week_start):
        compounded *= 1 + interval.return_value
    assert compounded - 1 == pytest.approx(series.observed_total_return)


def test_weekly_nav_extreme_ratio_and_weekly_volume_overflow_are_rejected() -> None:
    data = data_between("2024-01-02", "2024-01-05")
    rows = [b.model_copy(update={"volume": 1e308}) for b in data.bars["AAA"]]
    with pytest.raises(ValueError, match="non-finite aggregated"):
        aggregate_weekly_bars(rows, cutoff=data.cutoff)
    result = equity_result(data).model_copy(update={"config": ReplayConfig(initial_cash=1e-300)})
    points = [p.model_copy(update={"nav": 1e300}) for p in result.equity]
    with pytest.raises(ValueError, match="non-finite weekly"):
        weekly_equity(result.model_copy(update={"equity": points}))


def test_weekly_outputs_retain_source_risk_flags_and_material_identity_hashes() -> None:
    data = data_between()
    original = aggregate_weekly(data)
    changed = data.model_copy(update={"identities": {"AAA": data.identities["AAA"].model_copy(update={"identity_source": "reviewed-fixture-v2"})}})
    assert aggregate_weekly(changed).source_hash != original.source_hash
    result = equity_result(data).model_copy(update={"diagnostics": ["REVISED_BARS_NOT_KNOWN_AT_HISTORICAL_DECISION_UNTRUSTED"]})
    analysis = analyze_weekly(result)
    assert "REVISED_BARS_NOT_KNOWN_AT_HISTORICAL_DECISION_UNTRUSTED" in analysis["warnings"]
    assert analysis["conventions"]["nav_timestamp_semantics"] == "SIMULATED_VALUATION_TIME_NOT_PROVIDER_AVAILABILITY"
    assert analysis["conventions"]["pit_certification"] == "NOT_ESTABLISHED_BY_WEEKLY_NAV_AGGREGATION"
