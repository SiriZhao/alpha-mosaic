"""Financial accounting and causality regressions with manually checkable fixtures."""

from datetime import timedelta

import pytest
from test_backtesting import dataset

from alphamosaic.backtesting.models import (
    DatedSignal,
    ReplayConfig,
    TargetAllocation,
    preset_config,
)
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import CorporateAction, DataQuality
from alphamosaic.portfolio.construction import constrain_weights


def flat_dataset(count=8):
    data = dataset(count)
    for symbol, bars in data.bars.items():
        data.bars[symbol] = [
            b.model_copy(update={"open": 100.0, "close": 100.0, "high": 101.0, "low": 99.0})
            for b in bars
        ]
    return data


def test_strategy_cannot_observe_future_signals():
    data = flat_dataset()
    future = DatedSignal(
        symbol="AAA",
        known_at=data.bars["AAA"][-1].known_at,
        source="fixture",
        evidence_id="future",
        value=9,
        metric="ai_rating",
        pit_verified=True,
        data_quality="FIXTURE",
        valid_until=data.cutoff,
    )
    data = data.model_copy(update={"signals": [future]})

    class Spy:
        def allocation(self, history, signals, at, config):
            assert all(s.known_at <= at <= s.valid_until for s in signals)
            return TargetAllocation(decision_at=at, weights={})

    PaperReplayEngine().run(data, Spy(), "spy", ReplayConfig(rebalance_sessions=1))


@pytest.mark.parametrize("volume", [None, 1])
def test_actual_liquidity_limits_simulated_fills(volume):
    data = flat_dataset()
    for symbol in data.bars:
        data.bars[symbol][1] = data.bars[symbol][1].model_copy(update={"volume": volume})
    result = PaperReplayEngine().run(
        data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", ReplayConfig()
    )
    first_day = data.bars["AAA"][1].session
    assert not [f for f in result.fills if f.session == first_day]


def test_ledger_trace_and_next_open_are_reconstructible():
    data = flat_dataset()
    result = PaperReplayEngine().run(
        data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", ReplayConfig()
    )
    running_cash = result.config.initial_cash
    for entry in result.cash_ledger:
        running_cash += entry.amount
        assert running_cash == pytest.approx(entry.balance)
    assert running_cash == pytest.approx(result.equity[-1].cash)
    orders = {o.order_id: o for o in result.orders}
    signals = {s.signal_id: s for s in result.signals}
    for fill in result.fills:
        order = orders[fill.order_id]
        signal = signals[order.signal_id]
        assert fill.filled_at is not None
        assert signal.generated_at <= order.submitted_at < fill.filled_at
        assert signal.observation_at < fill.filled_at
    for point in result.equity:
        assert point.cash + sum(point.market_values.values()) == pytest.approx(point.nav)


def test_observation_cannot_be_available_before_it_exists():
    data = flat_dataset()
    bar = data.bars["AAA"][0]
    data.bars["AAA"][0] = bar.model_copy(update={"known_at": bar.observed_at - timedelta(days=1)})
    with pytest.raises(ValueError, match="availability"):
        PaperReplayEngine().run(
            data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", ReplayConfig()
        )


def test_constant_price_round_trip_loses_only_recorded_costs():
    data = flat_dataset(5)

    class RoundTrip:
        def allocation(self, history, signals, at, config):
            return TargetAllocation(
                decision_at=at, weights={"AAA": 0.5} if len(history["AAA"]) == 1 else {}
            )

    result = PaperReplayEngine().run(
        data, RoundTrip(), "round_trip", ReplayConfig(rebalance_sessions=1)
    )
    assert len(result.fills) == 2
    assert result.equity[-1].nav < result.config.initial_cash
    assert result.equity[-1].nav == pytest.approx(
        result.config.initial_cash - result.fees - result.slippage_cost - result.spread_cost
    )


def test_future_price_perturbation_preserves_prior_signals_and_fills():
    original = dataset(100)
    changed = original.model_copy(deep=True)
    for symbol, bars in changed.bars.items():
        for i in range(80, len(bars)):
            changed.bars[symbol][i] = bars[i].model_copy(
                update={key: getattr(bars[i], key) * 2 for key in ("open", "high", "low", "close")}
            )
    config = ReplayConfig(rebalance_sessions=1)
    engine = PaperReplayEngine()
    a = engine.run(original, StrategyRegistry().get("momentum"), "momentum", config)
    b = engine.run(changed, StrategyRegistry().get("momentum"), "momentum", config)
    boundary = original.bars["AAA"][80].observed_at
    assert [s for s in a.signals if s.generated_at < boundary] == [
        s for s in b.signals if s.generated_at < boundary
    ]
    day = original.bars["AAA"][80].session
    assert [f for f in a.fills if f.session < day] == [f for f in b.fills if f.session < day]


def test_open_gap_cannot_bypass_single_asset_or_gross_buy_limits():
    data = flat_dataset(5)
    for symbol, bars in data.bars.items():
        data.bars[symbol] = [
            bars[0],
            *[
                b.model_copy(update={"open": 200.0, "close": 200.0, "high": 201.0, "low": 199.0})
                for b in bars[1:]
            ],
        ]
    config = ReplayConfig(max_single_weight=0.25, max_gross_exposure=0.4, min_cash_buffer=0.6)
    result = PaperReplayEngine().run(
        data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", config
    )
    assert result.fills
    for point in result.equity:
        assert all(v / point.nav <= 0.25 + 1e-10 for v in point.market_values.values())
        assert sum(point.market_values.values()) / point.nav <= 0.4 + 1e-10


def test_strict_real_requires_coverage_and_known_adjustment():
    data = flat_dataset()
    for symbol, bars in data.bars.items():
        data.bars[symbol] = [
            b.model_copy(update={"data_quality": DataQuality.HISTORICAL}) for b in bars
        ]
    with pytest.raises(ValueError, match="coverage"):
        PaperReplayEngine().run(
            data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", ReplayConfig()
        )
    data = data.model_copy(
        update={"historical_universe_verified": True, "corporate_actions_complete": True}
    )
    data.bars["AAA"] = [
        b.model_copy(update={"adjustment_policy": "UNKNOWN"}) for b in data.bars["AAA"]
    ]
    with pytest.raises(ValueError, match="adjustment"):
        PaperReplayEngine().run(
            data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", ReplayConfig()
        )


def test_split_adjusted_pending_order_keeps_append_only_amendment():
    data = flat_dataset(7)
    for i in range(2, 7):
        data.bars["AAA"][i] = data.bars["AAA"][i].model_copy(
            update={
                "open": 50.0,
                "close": 50.0,
                "high": 51.0,
                "low": 49.0,
            }
        )
    base = data.bars["AAA"][0].model_dump(
        exclude={"session", "open", "close", "high", "low", "volume"}
    )
    action = CorporateAction(
        **base, effective_date=data.bars["AAA"][2].session, action="SPLIT", ratio=2
    )
    data = data.model_copy(update={"actions": [action]})
    result = PaperReplayEngine().run(
        data,
        StrategyRegistry().get("buy_and_hold"),
        "buy_and_hold",
        ReplayConfig(order_delay_sessions=3, fee_bps=0, slippage_bps=0),
    )
    amendment = result.order_adjustments[0]
    order = next(o for o in result.orders if o.order_id == amendment.order_id)
    fill = next(f for f in result.fills if f.order_id == order.order_id)
    assert order.quantity == amendment.previous_quantity
    assert fill.quantity == amendment.adjusted_quantity == 2 * order.quantity
    assert all(point.nav == 100_000 for point in result.equity)


def test_trust_boundary_rejects_bypassed_action_validation():
    data = flat_dataset()
    base = data.bars["AAA"][0].model_dump(
        exclude={"session", "open", "close", "high", "low", "volume"}
    )
    split = CorporateAction(
        **base, effective_date=data.bars["AAA"][2].session, action="SPLIT", ratio=2
    )
    data = data.model_copy(update={"actions": [split.model_copy(update={"ratio": -2})]})
    with pytest.raises(ValueError):
        PaperReplayEngine().run(
            data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold", ReplayConfig()
        )


@pytest.mark.parametrize("name", ["zero", "realistic", "stress"])
def test_cost_scenarios_and_same_path_cost_accounting(name):
    config = preset_config(name).model_copy(update={"min_cash_buffer": 0})
    data = flat_dataset(5)

    class RoundTrip:
        def allocation(self, history, signals, at, config):
            return TargetAllocation(
                decision_at=at, weights={"AAA": 0.2} if len(history["AAA"]) == 1 else {}
            )

    result = PaperReplayEngine().run(
        data, RoundTrip(), "fixed_path", config.model_copy(update={"rebalance_sessions": 1})
    )
    assert [f.quantity for f in result.fills] == [200, -200]
    assert result.equity[-1].nav == pytest.approx(
        100_000 - result.fees - result.slippage_cost - result.spread_cost
    )


def test_all_baselines_produce_constrained_allocations():
    data = dataset(90)
    at = data.bars["AAA"][-1].known_at
    config = ReplayConfig(max_single_weight=0.3, max_gross_exposure=0.5)
    for item in StrategyRegistry().list():
        strategy = StrategyRegistry().get(item["name"])
        target = strategy.allocation(data.bars, [], at, config)
        assert sum(target.weights.values()) <= 0.5 + 1e-10
        assert all(0 < w <= 0.3 for w in target.weights.values())
    assert (
        StrategyRegistry().get("volatility_targeting").allocation(data.bars, [], at, config).weights
    )
    assert constrain_weights({"AAA": 0.8, "BBB": 0.2}, config)[1]


def test_delayed_overlapping_sells_cannot_short_and_record_position_rejections():
    data = flat_dataset(12)

    class Liquidate:
        def allocation(self, history, signals, at, config):
            return TargetAllocation(
                decision_at=at, weights={"AAA": 0.5} if len(history["AAA"]) < 5 else {}
            )

    result = PaperReplayEngine().run(
        data,
        Liquidate(),
        "liquidate",
        ReplayConfig(
            order_delay_sessions=3,
            rebalance_sessions=1,
            fee_bps=0,
            slippage_bps=0,
        ),
    )
    assert any(o["reason"] == "POSITION_CONSTRAINT" for o in result.unfilled_orders)
    assert all(q >= 0 for point in result.equity for q in point.positions.values())
    assert result.equity[-1].positions == {}
    assert all(point.nav == 100_000 for point in result.equity)


def test_raw_ex_dividend_drop_conserves_equity_and_cash_is_credited_once():
    data = flat_dataset(6)
    for i in range(3, 6):
        data.bars["AAA"][i] = data.bars["AAA"][i].model_copy(
            update={
                "open": 99.0,
                "close": 99.0,
                "high": 100.0,
                "low": 98.0,
            }
        )
    base = data.bars["AAA"][0].model_dump(
        exclude={"session", "open", "close", "high", "low", "volume"}
    )
    dividend = CorporateAction(
        **base, effective_date=data.bars["AAA"][3].session, action="DIVIDEND", cash_amount=1
    )
    data = data.model_copy(update={"actions": [dividend]})
    result = PaperReplayEngine().run(
        data,
        StrategyRegistry().get("buy_and_hold"),
        "buy_and_hold",
        ReplayConfig(fee_bps=0, slippage_bps=0),
    )
    assert all(point.nav == 100_000 for point in result.equity)
    payments = [e for e in result.cash_ledger if e.kind == "DIVIDEND"]
    assert len(payments) == 1 and payments[0].amount == 500
    assert "DIVIDEND_CASH_CREDITED_AT_EFFECTIVE_OPEN_PAYMENT_LAG_NOT_MODELED" in result.diagnostics


def test_ensemble_is_fixed_average_of_three_strategy_sleeves():
    data = dataset(90)
    registry = StrategyRegistry()
    at = data.bars["AAA"][-1].known_at
    config = ReplayConfig()
    components = [
        registry.get(name).allocation(data.bars, [], at, config).weights
        for name in ("time_series_momentum", "trend", "low_volatility")
    ]
    ensemble = registry.get("ensemble").allocation(data.bars, [], at, config)
    for symbol in data.bars:
        assert ensemble.weights.get(symbol, 0) == pytest.approx(
            sum(w.get(symbol, 0) for w in components) / 3
        )
