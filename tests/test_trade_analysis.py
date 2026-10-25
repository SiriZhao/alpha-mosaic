"""Hand-worked FIFO results, corporate actions and independent NAV reconciliation."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import pytest
from test_backtesting import dataset

from alphamosaic.backtesting.models import (
    CashEntry,
    EquityPoint,
    Fill,
    LedgerEvent,
    OrderEvent,
    ReplayConfig,
    ReplayResult,
    SignalEvent,
    TargetAllocation,
)
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import CorporateAction
from alphamosaic.evaluation.trades import analyze_trades


def manual_result(entries: list[tuple[float, float, float]], *, close: float = 10, embedded_costs: bool = False) -> ReplayResult:
    """Independent fixed ledger fixture: (signed quantity, execution price, commission)."""
    dates = [day.date() for day in pd.bdate_range("2024-01-02", periods=len(entries) or 1)]
    cash, position = 1000.0, 0.0
    fills: list[Fill] = []
    events: list[LedgerEvent] = []
    orders: list[OrderEvent] = []
    signals: list[SignalEvent] = []
    ledger: list[CashEntry] = []
    equity: list[EquityPoint] = []

    def event(at: datetime, kind: Any, reference: str) -> None:
        events.append(LedgerEvent(event_id=f"e{len(events)}", at=at, kind=kind,
                                  reference=reference, cash=cash, positions={"AAA": position}))

    for i, day in enumerate(dates):
        opened = datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(hours=14)
        closed = opened + timedelta(hours=7)
        if entries:
            quantity, price, fee = entries[i]
            generated = datetime.combine(dates[i - 1], datetime.min.time(), tzinfo=UTC) + timedelta(hours=21) if i else opened - timedelta(days=1)
            signal = SignalEvent(signal_id=f"s{i}", observation_at=generated, generated_at=generated, weights={})
            order = OrderEvent(order_id=f"o{i}", signal_id=signal.signal_id, submitted_at=generated + timedelta(microseconds=1), eligible_at=opened, symbol="AAA", quantity=quantity)
            signals.append(signal)
            orders.append(order)
            event(generated, "SIGNAL", signal.signal_id)
            event(order.submitted_at, "ORDER", order.order_id)
        event(opened, "MARKET", str(day))
        if entries:
            quantity, price, fee = entries[i]
            fill = Fill(session=day, symbol="AAA", quantity=quantity, price=price, fee=fee,
                        slippage_cost=5 if embedded_costs else 0, spread_cost=2 if embedded_costs else 0,
                        order_id=f"o{i}", fill_id=f"f{i}", filled_at=opened)
            cash -= quantity * price + fee
            position += quantity
            fills.append(fill)
            ledger.append(CashEntry(event_id=fill.fill_id, at=opened, kind="FILL", symbol="AAA", amount=-quantity * price - fee, balance=cash))
            event(opened, "FILL", fill.fill_id)
        equity.append(EquityPoint(session=day, cash=cash, nav=cash + position * close,
                                  positions={"AAA": position} if position else {},
                                  market_values={"AAA": position * close} if position else {}))
        event(closed, "PORTFOLIO", str(day))
    return ReplayResult(strategy="manual-fixture", kind="HISTORICAL", acceptance="FIXTURE",
        config=ReplayConfig(initial_cash=1000), equity=equity, fills=fills, events=events,
        orders=orders, signals=signals, cash_ledger=ledger, applied_actions=[],
        unfilled_orders=[], turnover=0, fees=sum(f.fee for f in fills),
        slippage_cost=sum(f.slippage_cost for f in fills), spread_cost=sum(f.spread_cost for f in fills), diagnostics=[])


def test_hand_worked_multilot_fifo_partial_sales_and_holding_period() -> None:
    result = manual_result([(10, 10, 1), (5, 12, .6), (-12, 15, 1.8), (-3, 11, .3)])
    analysis = analyze_trades(result)
    assert analysis["status"] == "VERIFIED", analysis
    closed = analysis["closed_lots"]
    assert [row["quantity_at_exit"] for row in closed] == [10, 2, 3]
    assert [row["price_pnl_after_fees_usd"] for row in closed] == pytest.approx([47.5, 5.46, -3.66])
    assert [row["entry_fee_usd"] for row in closed] == pytest.approx([1, .24, .36])
    assert [row["exit_fee_usd"] for row in closed] == pytest.approx([1.5, .3, .3])
    assert analysis["metrics"]["trade_count"] == 3
    assert analysis["metrics"]["completed_round_trip_count"] == 1
    assert analysis["metrics"]["win_rate"] == pytest.approx(2 / 3)
    assert analysis["metrics"]["profit_factor"] == pytest.approx(52.96 / 3.66)
    assert analysis["metrics"]["average_holding_period_sessions"] == pytest.approx(298.96 / 161.6)
    assert analysis["asset_attribution"][0]["total_pnl_usd"] == pytest.approx(49.3)
    assert analysis["open_lots"] == []
    assert analysis["reconciliation"]["residual_usd"] == pytest.approx(0)


def test_changing_a_future_exit_cannot_rewrite_closed_fifo_matches() -> None:
    first = analyze_trades(manual_result([(10, 10, 1), (5, 12, .6), (-12, 15, 1.8), (-3, 11, .3)]))
    second = analyze_trades(manual_result([(10, 10, 1), (5, 12, .6), (-12, 15, 1.8), (-3, 3, .3)]))
    assert first["status"] == second["status"] == "VERIFIED"
    assert first["closed_lots"][:2] == second["closed_lots"][:2]
    assert first["closed_lots"][2] != second["closed_lots"][2]


def test_open_positions_are_not_closed_winners_and_costs_are_not_double_counted() -> None:
    result = manual_result([(10, 10, 1)], close=12, embedded_costs=True)
    analysis = analyze_trades(result)
    assert analysis["status"] == "VERIFIED"
    assert analysis["metrics"]["trade_count"] == 0
    assert analysis["metrics"]["win_rate"] is None
    assert analysis["metrics"]["profit_factor"] is None
    assert analysis["metrics"]["average_holding_period_sessions"] is None
    assert analysis["open_lots"][0]["unrealized_price_pnl_after_entry_fee_usd"] == pytest.approx(19)
    row = analysis["asset_attribution"][0]
    assert row["total_pnl_usd"] == pytest.approx(19)
    assert row["slippage_usd"] == 5 and row["spread_usd"] == 2
    closed = analyze_trades(manual_result([(10, 10, 1), (-10, 10, 1)], embedded_costs=True))
    assert closed["closed_lots"][0]["total_pnl_after_fees_usd"] == pytest.approx(-2)
    assert closed["metrics"]["profit_factor"] == 0


def test_no_fills_and_no_losses_have_explicit_undefined_ratios() -> None:
    empty = analyze_trades(manual_result([]))
    assert empty["status"] == "VERIFIED"
    assert empty["metrics"]["trade_count"] == 0
    assert empty["asset_attribution"][0]["total_pnl_usd"] == 0
    win = analyze_trades(manual_result([(10, 10, 0), (-10, 11, 0)]))
    assert win["status"] == "VERIFIED"
    assert win["metrics"]["win_rate"] == 1
    assert win["metrics"]["profit_factor"] is None
    breakeven = analyze_trades(manual_result([(10, 10, 0), (-10, 10, 0)]))
    assert breakeven["metrics"]["win_rate"] == 0
    assert breakeven["metrics"]["profit_factor"] is None


def test_borrowing_and_phantom_flat_asset_values_are_rejected() -> None:
    assert analyze_trades(manual_result([(20, 100, 0)]))["status"] == "BLOCKED"
    result = manual_result([])
    point = result.equity[0].model_copy(update={"market_values": {"AAA": 50}, "nav": 1050})
    result = result.model_copy(update={"equity": [point]})
    assert analyze_trades(result)["status"] == "BLOCKED"


def action_result() -> tuple[Any, ReplayResult]:
    data = dataset(8)
    for symbol, rows in data.bars.items():
        data.bars[symbol] = [b.model_copy(update={"open": 100.0 if i < 3 else 50.0 if i < 4 else 49.0,
            "close": 100.0 if i < 3 else 50.0 if i < 4 else 49.0,
            "high": 101.0 if i < 3 else 51.0, "low": 99.0 if i < 3 else 48.0}) for i, b in enumerate(rows)]
    rows = data.bars["AAA"]
    evidence = rows[0].model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    data = data.model_copy(update={"actions": [
        CorporateAction(**evidence, action="SPLIT", effective_date=rows[3].session, ratio=2),
        CorporateAction(**evidence, action="DIVIDEND", effective_date=rows[4].session, cash_amount=1)]})

    class BuyThenExit:
        def allocation(self, history, signals, at, config):
            return TargetAllocation(decision_at=at, weights={"AAA": .5} if len(history["AAA"]) <= 4 else {})

    result = PaperReplayEngine().run(data, BuyThenExit(), "manual-actions", ReplayConfig(
        initial_cash=10_000, fee_bps=0, slippage_bps=0, rebalance_sessions=1))
    return data, result


def test_split_dividend_economic_value_and_fifo_cost_are_preserved() -> None:
    data, result = action_result()
    analysis = analyze_trades(result, data)
    assert analysis["status"] == "VERIFIED", analysis
    assert analysis["reconciliation"]["actions_checked"] == 2
    assert analysis["reconciliation"]["portfolio_pnl_usd"] == pytest.approx(0)
    assert analysis["metrics"]["completed_round_trip_count"] == 1
    assert analysis["closed_lots"][0]["split_factor"] == 2
    assert analysis["closed_lots"][0]["entry_execution_basis_usd"] == 5000
    assert sum(row["dividend_income_usd"] for row in analysis["closed_lots"]) == 100
    assert sum(row["price_pnl_after_fees_usd"] for row in analysis["closed_lots"]) == -100
    assert analysis["metrics"]["win_rate"] == 0
    assert analysis["asset_attribution"][0]["dividend_income_usd"] == 100
    assert analyze_trades(result)["status"] == "BLOCKED"
    bad = data.model_copy(update={"actions": list(reversed(data.actions))})
    assert analyze_trades(result, bad)["status"] == "BLOCKED"


def test_partial_exit_allocates_posted_dividend_between_closed_and_open_lots() -> None:
    data, _ = action_result()

    class PartialExit:
        def allocation(self, history, signals, at, config):
            return TargetAllocation(decision_at=at, weights={"AAA": .5 if len(history["AAA"]) <= 4 else .25})

    result = PaperReplayEngine().run(data, PartialExit(), "partial-dividend", ReplayConfig(
        initial_cash=10_000, fee_bps=0, slippage_bps=0, rebalance_sessions=1))
    analysis = analyze_trades(result, data)
    assert analysis["status"] == "VERIFIED", analysis
    assert analysis["closed_lots"][0]["quantity_at_exit"] == 49
    assert analysis["closed_lots"][0]["dividend_income_usd"] == 49
    assert analysis["open_lots"][0]["quantity"] == 51
    assert analysis["open_lots"][0]["dividend_income_usd"] == 51
    assert analysis["metrics"]["completed_round_trip_count"] == 0
    assert analysis["reconciliation"]["allocated_dividends_usd"] == 100
    assert analysis["reconciliation"]["portfolio_pnl_usd"] == pytest.approx(0)


def test_reverse_split_open_lot_preserves_basis_and_separate_dividend_income() -> None:
    data = dataset(8)
    for symbol, bars in data.bars.items():
        data.bars[symbol] = [bar.model_copy(update={
            "open": 100.0 if symbol == "BBB" or i < 3 else 200.0 if i < 4 else 198.0,
            "close": 100.0 if symbol == "BBB" or i < 3 else 200.0 if i < 4 else 198.0,
            "high": 201.0, "low": 99.0}) for i, bar in enumerate(bars)]
    rows = data.bars["AAA"]
    evidence = rows[0].model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    data = data.model_copy(update={"actions": [
        CorporateAction(**evidence, action="SPLIT", effective_date=rows[3].session, ratio=.5),
        CorporateAction(**evidence, action="DIVIDEND", effective_date=rows[4].session, cash_amount=2)]})
    result = PaperReplayEngine().run(data, StrategyRegistry().get("buy_and_hold"), "buy_and_hold",
        ReplayConfig(initial_cash=10_000, fee_bps=0, slippage_bps=0))
    analysis = analyze_trades(result, data)
    assert analysis["status"] == "VERIFIED", analysis
    lot = next(row for row in analysis["open_lots"] if row["symbol"] == "AAA")
    assert lot["quantity"] == 25 and lot["entry_share_quantity"] == 50
    assert lot["split_factor"] == .5 and lot["cost_basis_usd"] == 5000
    assert lot["dividend_income_usd"] == 50
    assert lot["unrealized_price_pnl_after_entry_fee_usd"] == -50
    assert analysis["metrics"]["trade_count"] == 0
    assert analysis["reconciliation"]["portfolio_pnl_usd"] == pytest.approx(0)


def test_missing_exchange_session_cannot_shorten_holding_period() -> None:
    data, result = action_result()
    missing = result.equity[2].session
    shortened = result.model_copy(update={
        "equity": [point for point in result.equity if point.session != missing],
        "events": [event for event in result.events if event.at.date() != missing],
    })
    assert analyze_trades(result, data)["status"] == "VERIFIED"
    blocked = analyze_trades(shortened, data)
    assert blocked["status"] == "BLOCKED"
    assert "complete XNYS" in blocked["reason"]


def test_dataset_class_and_adjusted_cash_actions_cannot_be_relabeled() -> None:
    data, result = action_result()
    assert analyze_trades(result.model_copy(update={"acceptance": "REAL_PIT"}), data)["status"] == "BLOCKED"
    data.bars["AAA"] = [bar.model_copy(update={"adjustment_policy": "TOTAL_RETURN"}) for bar in data.bars["AAA"]]
    assert analyze_trades(result, data)["status"] == "BLOCKED"


@pytest.mark.parametrize("kind", ["SIGNAL", "ORDER"])
def test_missing_signal_or_order_audit_event_blocks_trace(kind: str) -> None:
    result = manual_result([(10, 10, 0), (-10, 11, 0)])
    result = result.model_copy(update={"events": [event for event in result.events if not(event.kind == kind and event.reference in {"s0", "o0"})]})
    assert analyze_trades(result)["status"] == "BLOCKED"


def test_replay_multiple_assets_reconcile_without_tax_or_factor_claim() -> None:
    data = dataset(180)
    for name in ("equal_weight", "momentum", "low_volatility", "volatility_targeting"):
        result = PaperReplayEngine().run(data, StrategyRegistry().get(name), name, ReplayConfig(rebalance_sessions=5))
        analysis = analyze_trades(result, data)
        assert analysis["status"] == "VERIFIED", (name, analysis)
        assert sum(row["total_pnl_usd"] for row in analysis["asset_attribution"]) == pytest.approx(result.equity[-1].nav - result.config.initial_cash)
        json.dumps(analysis, allow_nan=False)


@pytest.mark.parametrize("fault", ["cash", "position", "mark", "fee_total", "duplicate_fill", "missing_event", "missing_cash", "sell_exceeds", "naive_timestamp"])
def test_inconsistent_or_incomplete_evidence_blocks_all_trade_statistics(fault: str) -> None:
    result = manual_result([(10, 10, 1), (-10, 11, 1)])
    if fault in {"cash", "position", "mark"}:
        point = result.equity[-1]
        update = {"cash": point.cash + 1} if fault == "cash" else {"positions": {"AAA": 1}} if fault == "position" else {"market_values": {"AAA": 5}}
        result = result.model_copy(update={"equity": [*result.equity[:-1], point.model_copy(update=update)]})
    elif fault == "fee_total":
        result = result.model_copy(update={"fees": 99})
    elif fault == "duplicate_fill":
        result = result.model_copy(update={"fills": [*result.fills, result.fills[0]]})
    elif fault == "missing_event":
        result = result.model_copy(update={"events": [e for e in result.events if not(e.kind == "FILL" and e.reference == "f0")]})
    elif fault == "missing_cash":
        result = result.model_copy(update={"cash_ledger": result.cash_ledger[:-1]})
    elif fault == "sell_exceeds":
        result = result.model_copy(update={"fills": [result.fills[0], result.fills[1].model_copy(update={"quantity": -11})]})
    else:
        result = result.model_copy(update={"fills": [result.fills[0].model_copy(update={"filled_at": datetime(2024, 1, 2)}), result.fills[1]]})
    blocked = analyze_trades(result)
    assert blocked["status"] == "BLOCKED", fault
    assert blocked["metrics"]["trade_count"] is None
    assert blocked["closed_lots"] == blocked["open_lots"] == blocked["asset_attribution"] == []
