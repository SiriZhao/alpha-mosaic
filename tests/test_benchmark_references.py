from datetime import date

import exchange_calendars as xcals
import pytest
from test_independent_dividend_payment import fixture_data as dividend_fixture
from test_independent_dividend_payment import payment_config

from alphamosaic.backtesting.benchmarks import cash_zero_interest, equal_weight, run_benchmark
from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import DataQuality, HistoricalBar, SecurityIdentity


def fixture_data(prices=(100, 100), n=4):
    cal = xcals.get_calendar("XNYS")
    sessions = list(cal.sessions_in_range("2024-01-02", "2024-03-31"))[:n]
    bars, identities = {}, {}
    for symbol, price in zip(("AAA", "BBB"), prices, strict=True):
        identities[symbol] = SecurityIdentity(
            symbol=symbol, exchange="NYSE", currency="USD", active=True,
            identity_source="fixture", identity_verified=True,
            as_of=cal.session_open(sessions[0]).to_pydatetime(),
        )
        rows = []
        for session in sessions:
            at = cal.session_close(session).to_pydatetime()
            rows.append(HistoricalBar(
                symbol=symbol, source="fixture", source_url="https://example.invalid",
                observed_at=at, known_at=at, as_of=at, data_quality=DataQuality.FIXTURE,
                adjustment_policy="RAW", currency="USD", provenance={"test": "1"},
                license_scope="test", pit_status="VERIFIED", session=session.date(),
                open=price, high=price, low=price, close=price, volume=1_000_000,
            ))
        bars[symbol] = rows
    return ReplayDataset(
        bars=bars, identities=identities,
        cutoff=cal.session_close(sessions[-1]).to_pydatetime(),
    )


def test_cash_zero_interest_is_explicit_model_assumption():
    data = fixture_data()
    sessions = tuple(bar.session for bar in data.bars["AAA"])
    reference = run_benchmark(cash_zero_interest(sessions, initial_cash=2400))
    assert [point.nav for point in reference.points] == [2400] * len(sessions)
    assert all(point.return_value in (None, 0) for point in reference.points)
    assert reference.metrics == {"beta": None, "alpha": None, "correlation": None}


def test_existing_delayed_first_allocation_is_reproduced():
    data = fixture_data()
    config = ReplayConfig(
        initial_cash=2400, fee_bps=0, slippage_bps=0, spread_bps=0,
        max_volume_fraction=1, rebalance_sessions=1,
    )
    result = PaperReplayEngine().run(
        data, StrategyRegistry().get("equal_weight"), "equal_weight", config,
    )
    assert result.fills and result.fills[0].session == data.bars["AAA"][1].session


def test_explicit_schedule_policy_starts_at_first_eligible_open():
    data = fixture_data(n=30)
    config = ReplayConfig(
        initial_cash=2400, fee_bps=0, slippage_bps=0, spread_bps=0,
        max_volume_fraction=1,
    )
    strategy = StrategyRegistry().get("equal_weight")
    engine = PaperReplayEngine()
    default = engine.run(data, strategy, "equal_weight", config)
    explicit = engine.run(
        data, strategy, "equal_weight", config,
        schedule_policy="FIRST_ELIGIBLE_OPEN_THEN_INTERVAL",
    )
    assert default.fills[0].session == data.bars["AAA"][21].session
    assert explicit.fills[0].session == data.bars["AAA"][1].session


def test_equal_weight_freezes_symbols_and_weights():
    data = fixture_data()
    sessions = tuple(bar.session for bar in data.bars["AAA"])
    config = ReplayConfig(
        initial_cash=2400, fee_bps=0, slippage_bps=0, spread_bps=0,
        max_volume_fraction=1, rebalance_sessions=1,
    )
    reference = run_benchmark(
        equal_weight(("AAA", "BBB"), sessions, initial_cash=2400, replay_config=config),
        data,
    )
    assert {symbol for point in reference.points for symbol in point.positions} <= {"AAA", "BBB"}
    assert reference.points[1].positions == {"AAA": 12.0, "BBB": 12.0}
    with pytest.raises(ValueError):
        equal_weight(("AAA", "BBB"), sessions, initial_cash=2400,
                     replay_config=config.model_copy(update={"max_positions": 1}))
    with pytest.raises(ValueError):
        equal_weight(("CASH", "BBB"), sessions, initial_cash=2400, replay_config=config)


def test_benchmark_rejects_silent_cash_mismatch_non_session_and_market_bars():
    data = fixture_data()
    sessions = tuple(bar.session for bar in data.bars["AAA"])
    with pytest.raises(ValueError, match="conflicts"):
        cash_zero_interest(sessions, initial_cash=2400, replay_config=ReplayConfig(initial_cash=1000))
    with pytest.raises(ValueError, match="valid XNYS"):
        cash_zero_interest((sessions[0], date(2024, 1, 6)), initial_cash=2400)
    with pytest.raises(ValueError, match="does not consume"):
        run_benchmark(cash_zero_interest(sessions, initial_cash=2400), data)


def test_equal_weight_costs_reduce_cash_and_no_future_bar_changes_prior_fill():
    data = fixture_data(n=30)
    sessions = tuple(bar.session for bar in data.bars["AAA"])
    config = ReplayConfig(initial_cash=2400, fee_bps=10, slippage_bps=0, spread_bps=0,
        max_volume_fraction=1)
    reference = run_benchmark(equal_weight(("AAA", "BBB"), sessions, initial_cash=2400,
        replay_config=config), data)
    assert reference.replay_result is not None
    assert reference.replay_result.fees == pytest.approx(2.4)
    changed = data.model_copy(update={"bars": {symbol: [
        bar.model_copy(update={"close": bar.close + (100 if index >= 10 else 0),
            "open": bar.open + (100 if index >= 10 else 0),
            "high": bar.high + (100 if index >= 10 else 0),
            "low": bar.low + (100 if index >= 10 else 0)})
        for index, bar in enumerate(rows)] for symbol, rows in data.bars.items()}})
    altered = run_benchmark(equal_weight(("AAA", "BBB"), sessions, initial_cash=2400,
        replay_config=config), changed)
    assert altered.replay_result is not None
    assert altered.replay_result.fills[:2] == reference.replay_result.fills[:2]


def test_equal_weight_reuses_raw_split_and_dividend_ledger_without_double_income():
    data = dividend_fixture(split_ratio=2)
    sessions = tuple(bar.session for bar in data.bars["AAA"])
    config = payment_config(rebalance_sessions=1)
    reference = run_benchmark(equal_weight(("AAA",), sessions, initial_cash=1000,
        replay_config=config), data)
    assert reference.replay_result is not None
    result = reference.replay_result
    # The split occurs after the ex-date: the already-earned claim remains
    # tied to the ten pre-split shares and is not multiplied at payment.
    assert result.dividend_entitlements[0].entitled_quantity == 10
    assert result.dividend_entitlements[0].amount == 10
    assert sum(payment.amount for payment in result.dividend_payments) == 10
    assert all(point.nav == pytest.approx(1000) for point in result.equity)
    assert reference.diagnostics[-1].startswith("DIVIDEND_")
