"""Calendar-week decisions remain causal under the canonical daily fill engine."""

from datetime import timedelta

import exchange_calendars as xcals
import pytest

from alphamosaic.backtesting.models import ReplayConfig, WeeklyStrategyParameters
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.backtesting.weekly_strategy import WeeklyBaselineStrategy
from alphamosaic.core.contracts import CorporateAction
from alphamosaic.data.datasets import synthetic_demo
from alphamosaic.data.weekly import is_week_close


def test_weekly_signals_use_actual_calendar_close_and_next_session_open() -> None:
    data = synthetic_demo(100)
    config = ReplayConfig(decision_frequency="WEEKLY", rebalance_sessions=7)
    result = PaperReplayEngine().run(data, StrategyRegistry().get("weekly_equal_weight"), "weekly_equal_weight", config)
    calendar = xcals.get_calendar("XNYS")
    signals = {signal.signal_id: signal for signal in result.signals}
    assert result.fills
    for signal in result.signals:
        assert is_week_close(signal.observation_at.date())
        assert signal.generated_at >= calendar.session_close(signal.observation_at.date()).to_pydatetime()
    for order in result.orders:
        signal = signals[order.signal_id]
        expected = calendar.next_session(signal.observation_at.date())
        assert order.eligible_at == calendar.session_open(expected).to_pydatetime()
        assert signal.generated_at < order.eligible_at
    # Good Friday 2016 is closed: Thursday, not an arbitrary five-session block.
    assert any(s.observation_at.date().isoformat() == "2016-03-24" for s in result.signals)


def test_daily_rebalance_parameter_does_not_redefine_weekly_cadence() -> None:
    data = synthetic_demo(80)
    engine = PaperReplayEngine()
    def replay(interval: int):
        return engine.run(data, StrategyRegistry().get("weekly_equal_weight"), "weekly_equal_weight", ReplayConfig(decision_frequency="WEEKLY", rebalance_sessions=interval))
    left, right = replay(1), replay(21)
    assert left.signals == right.signals and left.fills == right.fills and left.equity == right.equity


def test_weekly_frequency_mismatches_are_rejected() -> None:
    data = synthetic_demo(80)
    with pytest.raises(ValueError, match="explicit WEEKLY"):
        PaperReplayEngine().run(data, StrategyRegistry().get("weekly_trend"), "weekly_trend", ReplayConfig())
    with pytest.raises(ValueError, match="registered weekly"):
        PaperReplayEngine().run(data, StrategyRegistry().get("trend"), "trend", ReplayConfig(decision_frequency="WEEKLY"))


def test_unrecorded_constructor_windows_cannot_change_a_replay() -> None:
    data = synthetic_demo(100)
    parameters = WeeklyStrategyParameters(lookback_weeks=2)
    strategy = WeeklyBaselineStrategy("weekly_momentum", parameters)
    with pytest.raises(ValueError, match="recorded replay configuration"):
        PaperReplayEngine().run(data, strategy, "weekly_momentum", ReplayConfig(decision_frequency="WEEKLY"))
    config = ReplayConfig(decision_frequency="WEEKLY", weekly_parameters=parameters)
    result = PaperReplayEngine().run(data, strategy, "weekly_momentum", config)
    assert result.config.weekly_parameters.lookback_weeks == 2
    assert result.fills == PaperReplayEngine().run(data, StrategyRegistry().get("weekly_momentum"), "weekly_momentum", config).fills


def test_weekly_raw_actions_require_an_explicit_reviewed_adjustment_model() -> None:
    data = synthetic_demo(80)
    bar = data.bars["SPY"][20]
    known = xcals.get_calendar("XNYS").session_open(bar.session).to_pydatetime() - timedelta(days=1)
    evidence = bar.model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    evidence.update(observed_at=known, known_at=known, as_of=known)
    data = data.model_copy(update={"actions": [CorporateAction(**evidence, action="DIVIDEND", effective_date=bar.session, cash_amount=1)]})
    with pytest.raises(ValueError, match="weekly RAW corporate-action"):
        PaperReplayEngine().run(data, StrategyRegistry().get("weekly_equal_weight"), "weekly_equal_weight", ReplayConfig(decision_frequency="WEEKLY"))


def test_future_week_changes_cannot_rewrite_past_signals_or_fills() -> None:
    original = synthetic_demo(100)
    boundary = original.bars["SPY"][70].session
    changed = original.model_copy(update={"bars": {symbol: [
        bar if bar.session <= boundary else bar.model_copy(update={field: getattr(bar, field) * 1.2 for field in ("open", "high", "low", "close")})
        for bar in rows] for symbol, rows in original.bars.items()}})
    config = ReplayConfig(decision_frequency="WEEKLY")
    def replay(data):
        return PaperReplayEngine().run(data, StrategyRegistry().get("weekly_momentum"), "weekly_momentum", config)
    left, right = replay(original), replay(changed)
    assert [f for f in left.fills if f.session <= boundary] == [f for f in right.fills if f.session <= boundary]
    assert [s for s in left.signals if s.observation_at.date() <= boundary] == [s for s in right.signals if s.observation_at.date() <= boundary]
