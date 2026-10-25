"""Independent fixed-amount dividend oracles; never market-performance evidence.

Ordinary entitlement follows the sourced ex-date, as described by SEC Investor.gov.
The payment convention below is the declared simulator assumption, not broker posting.
No production accrual, scheduling, allocation or payment helper supplies expected values.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, date, datetime, timedelta
from typing import Any

import exchange_calendars as xcals
import pytest

from alphamosaic.backtesting.models import (
    ReplayConfig,
    ReplayDataset,
    ReplayResult,
    TargetAllocation,
)
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar, SecurityIdentity
from alphamosaic.evaluation.analytics import analyze
from alphamosaic.evaluation.trades import analyze_trades
from alphamosaic.experiments.runner import compare_experiments

EX = date(2024, 1, 4)
PAY = date(2024, 1, 8)
AVAILABLE = date(2024, 1, 9)
ENTRY = date(2024, 1, 3)


class FixedTargets:
    """Predeclared dated allocations, independent of all future prices and payouts."""

    def __init__(self, changes: dict[date, dict[str, float]]) -> None:
        self.changes = sorted(changes.items())

    def allocation(self, history, signals, at, config) -> TargetAllocation:
        observed = next(iter(history.values()))[-1].session
        applicable = [weights for session, weights in self.changes if session <= observed]
        return TargetAllocation(decision_at=at, weights=applicable[-1] if applicable else {})


def payment_config(**changes: Any) -> ReplayConfig:
    return ReplayConfig.model_validate({
        "initial_cash": 1000, "fee_bps": 0, "slippage_bps": 0, "spread_bps": 0,
        "rebalance_sessions": 1, "max_volume_fraction": 1, "min_cash_buffer": 0,
        "accounting_schema_version": 2, "dividend_accounting": "PAY_DATE_RECEIVABLE",
        "payment_availability": "NEXT_XNYS_OPEN_AFTER_PAY_DATE", **changes,
    })


def fixture_data(
    *,
    through: str = "2024-01-12",
    split_ratio: float | None = None,
    second_asset: bool = False,
    dividend_changes: dict[str, Any] | None = None,
    legacy_terms: bool = False,
) -> ReplayDataset:
    """AAA is100 then99 at ex-date; BBB is1. Split marks preserve AAA value."""
    calendar = xcals.get_calendar("XNYS")
    sessions = list(calendar.sessions_in_range("2024-01-02", through))
    bars: dict[str, list[HistoricalBar]] = {}
    identities: dict[str, SecurityIdentity] = {}
    for symbol in (["AAA", "BBB"] if second_asset else ["AAA"]):
        identities[symbol] = SecurityIdentity(symbol=symbol, exchange="NYSE", currency="USD",
            security_type="STOCK", active=True, identity_source="independent-fixed-ledger-v1",
            identity_verified=True, as_of=calendar.session_open(sessions[0]).to_pydatetime())
        rows = []
        for session in sessions:
            day = session.date()
            price = 1.0 if symbol == "BBB" else 100.0 if day < EX else 99.0
            if symbol == "AAA" and split_ratio is not None and day >= date(2024, 1, 5):
                price /= split_ratio
            closed = calendar.session_close(session).to_pydatetime()
            rows.append(HistoricalBar(symbol=symbol, session=day, open=price, high=price,
                low=price, close=price, volume=100_000, observed_at=closed,
                known_at=closed, as_of=closed, currency="USD", data_quality=DataQuality.FIXTURE,
                source="independent-fixed-ledger-v1", source_url="https://example.invalid/dividend-payment-oracle",
                adjustment_policy="RAW", pit_status="VERIFIED", license_scope="Synthetic test-only",
                provenance={"generator": "explicit-hand-calculable-prices", "provider_version": "1"}))
        bars[symbol] = rows
    available = datetime(2024, 1, 2, tzinfo=UTC)
    evidence: dict[str, Any] = dict(symbol="AAA", source="independent-fixed-ledger-v1",
        source_url="https://example.invalid/ordinary-dividend-declaration", observed_at=available,
        known_at=available, as_of=available, currency="USD", data_quality=DataQuality.FIXTURE,
        adjustment_policy="RAW", pit_status="VERIFIED", license_scope="Synthetic test-only", provenance={"test": "independent-ledger"})
    terms: dict[str, Any] = {**evidence, "action": "DIVIDEND", "effective_date": EX, "cash_amount": 1}
    if not legacy_terms:
        terms.update(effective_date_role="EX_DATE", dividend_type="ORDINARY_CASH", payment_date=PAY,
            cash_amount_basis="EX_DATE_SHARES", source_action_id="ordinary-AAA-20240104-v1")
    dividend = CorporateAction.model_validate({**terms, **(dividend_changes or {})})
    actions = [dividend]
    if split_ratio is not None:
        actions.append(CorporateAction(**evidence, action="SPLIT", effective_date=date(2024, 1, 5), ratio=split_ratio))
    return ReplayDataset(bars=bars, identities=identities, actions=actions,
        cutoff=calendar.session_close(sessions[-1]).to_pydatetime(), mode="STRICT_PIT",
        historical_universe_verified=True, corporate_actions_complete=True)


def replay(
    data: ReplayDataset,
    targets: dict[date, dict[str, float]] | None = None,
    *,
    start: date | None = None,
    end: date | None = None,
) -> ReplayResult:
    return PaperReplayEngine().run(data, FixedTargets(targets or {date(2024, 1, 2): {"AAA": 1}}),
        "independent-frozen-targets", payment_config(), start, end)


def point(result: ReplayResult, session: date):
    return next(p for p in result.equity if p.session == session)


def claim(point_or_event) -> float:
    return math.fsum(point_or_event.receivables.values())


def independently_reconstruct(result: ReplayResult) -> None:
    """Rebuild balances only from public fills/accruals/payments and fixed identities."""
    cash = result.config.initial_cash
    outstanding: dict[str, float] = {}
    earned = paid = 0.0
    entitlements = {e.entitlement_id: e for e in result.dividend_entitlements}
    assert len(entitlements) == len(result.dividend_entitlements)
    payment_ids = {p.payment_id for p in result.dividend_payments}
    assert len(payment_ids) == len(result.dividend_payments)
    for p in result.equity:
        for entitlement in result.dividend_entitlements:
            if entitlement.ex_date == p.session:
                assert entitlement.amount == pytest.approx(entitlement.entitled_quantity * entitlement.cash_per_share)
                assert entitlement.source_action_id == "ordinary-AAA-20240104-v1"
                if entitlement.amount:
                    outstanding[entitlement.entitlement_id] = entitlement.amount
                earned += entitlement.amount
        for payment in result.dividend_payments:
            if payment.at.date() == p.session:
                entitlement = entitlements[payment.entitlement_id]
                assert payment.symbol == entitlement.symbol
                assert payment.amount == pytest.approx(entitlement.amount)
                assert payment.at.date() > entitlement.payment_date
                assert payment.entitlement_id in outstanding
                cash += payment.amount
                paid += payment.amount
                del outstanding[payment.entitlement_id]
        for fill in result.fills:
            if fill.session == p.session:
                cash -= fill.quantity * fill.price + fill.fee
        assert p.cash == pytest.approx(cash)
        assert p.receivables == pytest.approx(outstanding)
        assert p.nav == pytest.approx(cash + math.fsum(p.market_values.values()) + math.fsum(outstanding.values()))
        assert earned == pytest.approx(paid + math.fsum(outstanding.values()))
    cash_payments = [e for e in result.cash_ledger if e.kind == "DIVIDEND_PAYMENT"]
    assert math.fsum(e.amount for e in cash_payments) == pytest.approx(paid)
    assert not any(e.kind == "DIVIDEND" for e in result.cash_ledger)


def test_independent_ex_date_nav_and_later_payment_are_one_income_event() -> None:
    data = fixture_data()
    result = replay(data)
    assert point(result, ENTRY).positions == {"AAA": 10}
    ex = point(result, EX)
    assert (ex.cash, claim(ex), ex.market_values["AAA"], ex.nav) == pytest.approx((0, 10, 990, 1000))
    assert point(result, PAY).cash == 0 and claim(point(result, PAY)) == 10
    settled = point(result, AVAILABLE)
    assert (settled.cash, claim(settled), settled.nav) == pytest.approx((10, 0, 1000))
    assert len(result.dividend_payments) == 1
    assert result.dividend_payments[0].at == datetime(2024, 1, 9, 14, 30, tzinfo=UTC)
    assert all(p.nav == pytest.approx(1000) for p in result.equity)
    independently_reconstruct(result)
    trades = analyze_trades(result, data)
    assert trades["status"] == "VERIFIED"
    assert math.fsum(a["dividend_income_usd"] for a in trades["asset_attribution"]) == 10
    assert math.fsum(a["total_pnl_usd"] for a in trades["asset_attribution"]) == pytest.approx(0)


@pytest.mark.parametrize("sale_signal", [date(2024, 1, 3), date(2024, 1, 4)])
def test_ex_open_or_post_ex_seller_retains_frozen_right_after_full_exit(sale_signal: date) -> None:
    result = replay(fixture_data(), {date(2024, 1, 2): {"AAA": 1}, sale_signal: {}})
    sold = point(result, EX if sale_signal == date(2024, 1, 3) else date(2024, 1, 5))
    assert not sold.positions
    assert (sold.cash, claim(sold), sold.nav) == pytest.approx((990, 10, 1000))
    assert (point(result, AVAILABLE).cash, claim(point(result, AVAILABLE))) == pytest.approx((1000, 0))
    assert result.dividend_entitlements[0].entitled_quantity == 10
    independently_reconstruct(result)


def test_ex_open_buyer_receives_no_old_entitlement() -> None:
    result = replay(fixture_data(), {date(2024, 1, 2): {}, date(2024, 1, 3): {"AAA": 1}})
    assert next(f for f in result.fills if f.quantity > 0).session == EX
    assert (point(result, EX).cash, claim(point(result, EX))) == pytest.approx((10, 0))
    assert all(e.entitled_quantity == 0 and e.amount == 0 for e in result.dividend_entitlements)
    assert not result.dividend_payments
    independently_reconstruct(result)


def test_replacement_lot_does_not_inherit_old_dividend_right_or_income() -> None:
    data = fixture_data()
    result = replay(data, {date(2024, 1, 2): {"AAA": 1}, date(2024, 1, 4): {}, date(2024, 1, 5): {"AAA": 1}})
    assert [(f.session, f.quantity) for f in result.fills] == [(ENTRY, 10), (date(2024, 1, 5), -10), (date(2024, 1, 8), 10)]
    assert (point(result, date(2024, 1, 8)).cash, claim(point(result, date(2024, 1, 8)))) == pytest.approx((0, 10))
    trades = analyze_trades(result, data)
    assert trades["status"] == "VERIFIED"
    assert len(trades["closed_lots"]) == len(trades["open_lots"]) == 1
    closed, current = trades["closed_lots"][0], trades["open_lots"][0]
    assert (closed["price_pnl_after_fees_usd"], closed["dividend_income_usd"], closed["total_pnl_after_fees_usd"]) == pytest.approx((-10, 10, 0))
    assert current["dividend_income_usd"] == 0
    independently_reconstruct(result)


@pytest.mark.parametrize("ratio,quantity,price", [(2.0, 20.0, 49.5), (.5, 5.0, 198.0)])
def test_intervening_split_changes_shares_but_not_fixed_dollar_claim(ratio: float, quantity: float, price: float) -> None:
    result = replay(fixture_data(split_ratio=ratio))
    split = point(result, date(2024, 1, 5))
    assert split.positions["AAA"] == quantity
    assert (split.market_values["AAA"], claim(split), split.cash, split.nav) == pytest.approx((quantity * price, 10, 0, 1000))
    assert result.dividend_entitlements[0].entitled_quantity == 10
    assert result.dividend_entitlements[0].amount == 10
    assert result.dividend_payments[0].amount == 10
    independently_reconstruct(result)


def test_claim_cannot_fund_pre_payment_buys_but_paid_cash_can() -> None:
    result = replay(fixture_data(second_asset=True), {date(2024, 1, 2): {"AAA": 1}, date(2024, 1, 4): {"AAA": .99, "BBB": .01}})
    purchases = [f for f in result.fills if f.symbol == "BBB" and f.quantity > 0]
    assert purchases and purchases[0].session == AVAILABLE
    assert purchases[0].quantity == 10
    assert not any(f.symbol == "BBB" for f in result.fills if f.session < AVAILABLE)
    assert any(o["reason"] == "CASH_CONSTRAINT" for o in result.unfilled_orders)
    assert point(result, PAY).cash == 0 and claim(point(result, PAY)) == 10
    assert point(result, AVAILABLE).positions == {"AAA": 10, "BBB": 10}
    assert point(result, AVAILABLE).cash == 0
    independently_reconstruct(result)


def test_end_before_pay_retains_nonspendable_claim_and_extension_only_reclassifies() -> None:
    data = fixture_data()
    short = replay(data, end=date(2024, 1, 5))
    full = replay(data)
    end = short.equity[-1]
    assert (end.cash, claim(end), end.nav) == pytest.approx((0, 10, 1000))
    assert not short.dividend_payments
    assert short.dividend_entitlements[0].payment_date == PAY
    assert short.dividend_entitlements[0].available_at is None
    assert [p for p in full.equity if p.session <= end.session] == short.equity
    assert full.equity[-1].nav == end.nav
    independently_reconstruct(short)


def test_start_after_ex_has_no_inherited_right_from_warmup_history() -> None:
    result = replay(fixture_data(), start=date(2024, 1, 5))
    assert not result.dividend_entitlements
    assert not result.dividend_payments
    assert all(claim(p) == 0 for p in result.equity)
    independently_reconstruct(result)


@pytest.mark.parametrize("source_pay,available", [(date(2024, 1, 6), date(2024, 1, 8)), (date(2024, 1, 15), date(2024, 1, 16))])
def test_weekend_and_holiday_pay_dates_keep_source_date_and_conservative_availability(source_pay: date, available: date) -> None:
    data = fixture_data(through="2024-01-19", dividend_changes={"payment_date": source_pay})
    result = replay(data)
    assert result.dividend_entitlements[0].payment_date == source_pay
    assert result.dividend_payments[0].at.date() == available
    assert point(result, available).cash == 10
    independently_reconstruct(result)


def test_distant_source_pay_date_retains_claim_without_inventing_calendar_coverage() -> None:
    result = replay(fixture_data(dividend_changes={"payment_date": date(2100, 1, 1)}))
    assert not result.dividend_payments
    assert (result.equity[-1].cash, claim(result.equity[-1]), result.equity[-1].nav) == pytest.approx((0, 10, 1000))
    entitlement = result.dividend_entitlements[0]
    assert entitlement.payment_date == date(2100, 1, 1)
    assert entitlement.available_at is None
    independently_reconstruct(result)


def test_partial_exit_keeps_accrual_allocated_between_closed_and_open_lots() -> None:
    data = fixture_data()
    result = replay(data, {date(2024, 1, 2): {"AAA": 1}, date(2024, 1, 4): {"AAA": .5}}, end=date(2024, 1, 5))
    end = result.equity[-1]
    assert (end.cash, claim(end), end.market_values["AAA"], end.nav) == pytest.approx((495, 10, 495, 1000))
    trades = analyze_trades(result, data)
    assert trades["status"] == "VERIFIED"
    assert len(trades["closed_lots"]) == len(trades["open_lots"]) == 1
    assert trades["closed_lots"][0]["dividend_income_usd"] == 5
    assert trades["open_lots"][0]["dividend_income_usd"] == 5
    assert math.fsum(row["total_pnl_usd"] for row in trades["asset_attribution"]) == pytest.approx(0)
    independently_reconstruct(result)


def test_receivable_is_not_misreported_as_stock_market_exposure() -> None:
    result = replay(fixture_data())
    analysis = analyze(result)
    ex = next(row for row in analysis["exposures"] if row["session"] == EX.isoformat())
    assert ex["cash_weight"] == 0
    assert ex["receivable_weight"] == pytest.approx(.01)
    assert ex["market_weight"] == pytest.approx(.99)
    assert ex["concentration_hhi"] == pytest.approx(.99 ** 2)
    settled = next(row for row in analysis["exposures"] if row["session"] == AVAILABLE.isoformat())
    assert (settled["cash_weight"], settled["receivable_weight"], settled["market_weight"]) == pytest.approx((.01, 0, .99))


def test_equal_ex_and_pay_calendar_date_still_cannot_post_cash_at_ex_open() -> None:
    result = replay(fixture_data(dividend_changes={"payment_date": EX}))
    assert point(result, EX).cash == 0 and claim(point(result, EX)) == 10
    assert result.dividend_payments[0].at.date() == date(2024, 1, 5)
    independently_reconstruct(result)


def test_declared_zero_dividend_does_not_create_a_receivable_or_payment() -> None:
    data = fixture_data(dividend_changes={"cash_amount": 0})
    result = replay(data)
    assert all(claim(p) == 0 for p in result.equity)
    assert not result.dividend_payments
    assert all(e.amount == 0 for e in result.dividend_entitlements)
    assert result.equity[-1].nav == 990  # The fixture price decline remains a loss, not dividend income.
    trades = analyze_trades(result, data)
    assert trades["status"] == "VERIFIED"
    assert math.fsum(a["dividend_income_usd"] for a in trades["asset_attribution"]) == 0
    independently_reconstruct(result)


def test_unrepresentable_gross_entitlement_fails_before_nan_or_infinite_nav() -> None:
    with pytest.raises(ValueError):
        replay(fixture_data(dividend_changes={"cash_amount": 1e308}))


@pytest.mark.parametrize("corruption", ["missing_claim_snapshot", "double_payment", "unknown_claim", "amount_mismatch", "missing_payment_cash"])
def test_independent_lot_reconstruction_rejects_corrupted_payment_evidence(corruption: str) -> None:
    data = fixture_data()
    result = replay(data).model_copy(deep=True)
    if corruption == "missing_claim_snapshot":
        index = next(i for i, p in enumerate(result.equity) if p.session == EX)
        result.equity[index] = result.equity[index].model_copy(update={"receivables": {}})
    elif corruption == "double_payment":
        result.dividend_payments.append(result.dividend_payments[0])
    elif corruption == "unknown_claim":
        result.dividend_payments[0] = result.dividend_payments[0].model_copy(update={"entitlement_id": "unregistered-claim"})
    elif corruption == "amount_mismatch":
        result.dividend_payments[0] = result.dividend_payments[0].model_copy(update={"amount": 20})
    else:
        result = result.model_copy(update={"cash_ledger": [entry for entry in result.cash_ledger if entry.kind != "DIVIDEND_PAYMENT"]})
    assert analyze_trades(result, data)["status"] == "BLOCKED"


@pytest.mark.parametrize("changes", [
    {"payment_date": None}, {"payment_date": date(2024, 1, 3)},
    {"effective_date_role": None}, {"dividend_type": None},
    {"dividend_type": "SPECIAL"}, {"dividend_type": "SPECIAL_CASH"},
    {"dividend_type": "DUE_BILL"}, {"dividend_type": "UNKNOWN"},
    {"cash_amount_basis": None}, {"source_action_id": None}, {"source_action_id": ""},
    {"effective_date": date(2024, 1, 6)},
])
def test_missing_ambiguous_and_nonordinary_terms_fail_before_success(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        replay(fixture_data(dividend_changes=changes))


def test_late_known_terms_cannot_be_backdated_even_in_diagnostic_mode() -> None:
    ex_open = datetime(2024, 1, 4, 14, 30, tzinfo=UTC)
    data = fixture_data(dividend_changes={"known_at": ex_open + timedelta(microseconds=1), "as_of": ex_open + timedelta(microseconds=1)})
    for mode in ("STRICT_PIT", "RECONSTRUCTED_DIAGNOSTIC"):
        with pytest.raises(ValueError):
            replay(data.model_copy(update={"mode": mode}))


def test_same_day_split_and_ex_date_are_rejected_without_a_reviewed_unit_model() -> None:
    data = fixture_data()
    dividend = data.actions[0]
    evidence = dividend.model_dump(exclude={"action", "effective_date", "ratio", "cash_amount",
        "effective_date_role", "dividend_type", "payment_date", "cash_amount_basis", "source_action_id"})
    split = CorporateAction(**evidence, action="SPLIT", effective_date=EX, ratio=2)
    with pytest.raises(ValueError):
        replay(data.model_copy(update={"actions": [*data.actions, split]}))


def test_raw_action_on_total_return_prices_cannot_credit_dividend_twice() -> None:
    data = fixture_data()
    adjusted = data.model_copy(update={"bars": {symbol: [b.model_copy(update={"adjustment_policy": "TOTAL_RETURN"}) for b in rows] for symbol, rows in data.bars.items()}})
    with pytest.raises(ValueError):
        replay(adjusted)


def test_legacy_and_receivable_accounting_are_not_ordinary_comparison_peers() -> None:
    data = fixture_data()
    paid = replay(data)
    legacy_config = ReplayConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, rebalance_sessions=1, max_volume_fraction=1)
    legacy = PaperReplayEngine().run(data, FixedTargets({date(2024, 1, 2): {"AAA": 1}}), "independent-frozen-targets", legacy_config)
    dataset_hash = hashlib.sha256(json.dumps(data.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
    def item(result: ReplayResult, label: str) -> dict[str, Any]:
        return {"experiment_id": label, "status": "COMPLETED", "dataset_hash": dataset_hash,
            "acceptance": "FIXTURE", "return_basis": "RAW_WITH_CASH_ACTIONS",
            "reproducibility": {"source_hash": "independent-same-source-fixture"},
            "config": {"strategy": "independent-frozen-targets", "replay": result.config.model_dump(mode="json"),
                "validation": "EXPLORATORY", "benchmark": "AAA"}, "result": result.model_dump(mode="json"), "analysis": {"metrics": {}}}
    assert compare_experiments([item(paid, "new"), item(legacy, "legacy")])["status"] == "INCOMPATIBLE"


def test_no_dividend_economic_path_does_not_change_between_declared_models() -> None:
    data = fixture_data(legacy_terms=True).model_copy(update={"actions": []})
    targets: dict[date, dict[str, float]] = {date(2024, 1, 2): {"AAA": 1}}
    modern = replay(data, targets)
    legacy = PaperReplayEngine().run(data, FixedTargets(targets), "independent-frozen-targets",
        ReplayConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, rebalance_sessions=1, max_volume_fraction=1))
    assert modern.fills == legacy.fills
    assert [(p.session, p.cash, p.positions, p.nav) for p in modern.equity] == [(p.session, p.cash, p.positions, p.nav) for p in legacy.equity]
    assert not modern.dividend_entitlements and not modern.dividend_payments


def test_dividend_benchmark_uses_matching_entitlement_and_cash_availability_semantics() -> None:
    data = fixture_data()
    modern = replay(data)
    config = ReplayConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, rebalance_sessions=1, max_volume_fraction=1)
    legacy = PaperReplayEngine().run(data, FixedTargets({date(2024, 1, 2): {"AAA": 1}}), "independent-frozen-targets", config)
    compatible = analyze(modern, modern, return_basis="RAW_WITH_CASH_ACTIONS", benchmark_return_basis="RAW_WITH_CASH_ACTIONS")
    assert compatible["benchmark_status"] == "COMPARABLE_SIMULATED_RETURNS"
    incompatible = analyze(modern, legacy, return_basis="RAW_WITH_CASH_ACTIONS", benchmark_return_basis="RAW_WITH_CASH_ACTIONS")
    assert incompatible["benchmark_status"].startswith("BLOCKED")
    assert incompatible["metrics"]["beta"] is None
    assert incompatible["metrics"]["information_ratio"] is None
