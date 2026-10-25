"""FIFO lot research statistics and additive, independently reconciled asset P&L.

This is an execution-ledger analysis, not tax-lot accounting or causal factor attribution.
Fill prices already include spread/slippage. Only commission is separately debited.
"""

from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import exchange_calendars as xcals

from alphamosaic.backtesting.models import Fill, ReplayDataset, ReplayResult
from alphamosaic.core.contracts import DataQuality

_NULL_METRICS = {
    "trade_count": None,
    "closed_lot_match_count": None,
    "completed_round_trip_count": None,
    "win_rate": None,
    "profit_factor": None,
    "average_holding_period_sessions": None,
}


def _equal(actual: float, expected: float, label: str) -> None:
    if not math.isfinite(actual) or not math.isfinite(expected) or not math.isclose(
        actual, expected, rel_tol=1e-10, abs_tol=1e-7
    ):
        raise ValueError(f"{label} does not reconcile")


@dataclass
class _Lot:
    fill: Fill
    quantity: float
    execution_basis: float
    fee: float
    slippage: float
    spread: float
    dividends: float = 0.0
    split_factor: float = 1.0
    dividend_rights: dict[str, float] = field(default_factory=dict)


def _analyze(result: ReplayResult, dataset: ReplayDataset | None) -> dict[str, Any]:
    if not result.equity or not result.events:
        raise ValueError("complete equity and ordered audit events required")
    sessions = [point.session for point in result.equity]
    if sessions != sorted(set(sessions)):
        raise ValueError("unique chronological equity sessions required")
    expected_sessions = [day.date() for day in xcals.get_calendar("XNYS").sessions_in_range(sessions[0], sessions[-1])]
    if sessions != expected_sessions:
        raise ValueError("complete XNYS equity sessions required for holding periods")
    session_index = {session: i for i, session in enumerate(sessions)}
    payment_mode = result.config.dividend_accounting == "PAY_DATE_RECEIVABLE"
    entitlements = {item.entitlement_id: item for item in result.dividend_entitlements}
    entitlements_by_action = {item.action_reference: item for item in result.dividend_entitlements}
    payments = {item.payment_id: item for item in result.dividend_payments}
    if len(entitlements) != len(result.dividend_entitlements) or len(entitlements_by_action) != len(entitlements) or len(payments) != len(result.dividend_payments):
        raise ValueError("duplicate dividend entitlement or payment identity")
    if not payment_mode and (entitlements or payments):
        raise ValueError("legacy accounting cannot contain payment-model records")
    symbols = set().union(*(set(event.positions) for event in result.events))
    symbols |= {fill.symbol for fill in result.fills}
    if dataset is not None:
        if not dataset.bars or any(not rows for rows in dataset.bars.values()):
            raise ValueError("nonempty dataset histories required")
        if symbols - set(dataset.bars):
            raise ValueError("dataset identity mismatch")
        if any(bar.currency != "USD" for rows in dataset.bars.values() for bar in rows):
            raise ValueError("USD price evidence required for USD P&L")
        marks = {s: {bar.session: bar.close for bar in bars} for s, bars in dataset.bars.items()}
        if any(len(marks[s]) != len(rows) for s, rows in dataset.bars.items()):
            raise ValueError("duplicate dataset sessions")
        qualities = {bar.data_quality for rows in dataset.bars.values() for bar in rows}
        if not qualities <= {DataQuality.FIXTURE, DataQuality.REAL, DataQuality.HISTORICAL, DataQuality.DELAYED}:
            raise ValueError("observed market or explicit fixture price evidence required")
        for action in dataset.actions:
            if action.data_quality not in {DataQuality.FIXTURE, DataQuality.REAL, DataQuality.HISTORICAL, DataQuality.DELAYED}:
                raise ValueError("corporate action evidence cannot be inference or missing")
            if (action.data_quality == DataQuality.FIXTURE) != (qualities == {DataQuality.FIXTURE}):
                raise ValueError("fixture and observed corporate action evidence cannot be mixed")
        expected_class = "FIXTURE" if qualities == {DataQuality.FIXTURE} else "REAL_PIT" if dataset.mode == "STRICT_PIT" else "REAL_RECONSTRUCTED"
        if DataQuality.FIXTURE in qualities and qualities != {DataQuality.FIXTURE} or result.acceptance != expected_class:
            raise ValueError("dataset and result evidence class mismatch")
    else:
        marks = {}
    if result.applied_actions and dataset is None:
        raise ValueError("dataset actions required for applied corporate-action references")
    if len(set(result.applied_actions)) != len(result.applied_actions):
        raise ValueError("duplicate applied corporate-action reference")
    fills = {fill.fill_id: fill for fill in result.fills}
    if len(fills) != len(result.fills) or any(not key for key in fills):
        raise ValueError("unique nonempty fill identifiers required")
    orders = {order.order_id: order for order in result.orders}
    signals = {signal.signal_id: signal for signal in result.signals}
    if len(orders) != len(result.orders) or len(signals) != len(result.signals):
        raise ValueError("duplicate order or signal identifier")
    if len({event.event_id for event in result.events}) != len(result.events):
        raise ValueError("duplicate audit event identifier")
    timestamps = [event.at for event in result.events]
    if any(at.tzinfo is None or at.utcoffset() is None for at in timestamps):
        raise ValueError("aware audit timestamps required")
    if timestamps != sorted(timestamps):
        raise ValueError("audit event order must be chronological")
    for fill in result.fills:
        if fill.quantity == 0 or fill.price <= 0 or min(fill.fee, fill.slippage_cost, fill.spread_cost) < 0:
            raise ValueError("positive fill prices, nonzero quantities and nonnegative costs required")
        if fill.filled_at is None or fill.filled_at.tzinfo is None or fill.filled_at.utcoffset() is None:
            raise ValueError("aware execution timestamp required")
        if fill.session not in session_index or fill.filled_at.date() != fill.session:
            raise ValueError("fill outside evaluated sessions")
        order = orders.get(fill.order_id)
        signal = signals.get(order.signal_id) if order is not None else None
        if order is None or signal is None or order.symbol != fill.symbol:
            raise ValueError("fill must trace to matching order and signal")
        if not signal.generated_at <= order.submitted_at < fill.filled_at or order.eligible_at > fill.filled_at:
            raise ValueError("noncausal execution trace")
    for key in ("fee", "slippage_cost", "spread_cost"):
        expected = result.fees if key == "fee" else getattr(result, key)
        _equal(math.fsum(getattr(fill, key) for fill in result.fills), expected, f"aggregate {key}")
    lots: dict[str, deque[_Lot]] = {symbol: deque() for symbol in symbols}
    positions = dict.fromkeys(symbols, 0.0)
    cash = result.config.initial_cash
    ledger_index = 0
    closed: list[dict[str, Any]] = []
    processed_fills: list[str] = []
    processed_actions: list[str] = []
    processed_signals: list[str] = []
    processed_orders: list[str] = []
    processed_entitlements: list[str] = []
    processed_payments: list[str] = []
    receivables: dict[str, float] = {}
    paid_entitlements: set[str] = set()
    valued_sessions = []
    round_trips = 0
    contribution = {symbol: {"realized_price_pnl_usd": 0.0, "dividend_income_usd": 0.0,
                             "fees_usd": 0.0, "slippage_usd": 0.0, "spread_usd": 0.0} for symbol in symbols}
    if payment_mode:
        for row in contribution.values():
            row["paid_dividends_usd"] = 0.0

    def check_receivables(actual: dict[str, float], label: str) -> None:
        if set(actual) != set(receivables):
            raise ValueError(f"{label} receivable identities do not reconcile")
        for key, amount in receivables.items():
            _equal(actual[key], amount, f"{label} receivable amount")

    def cash_entry(reference: str, kind: str, symbol: str, at: datetime, amount: float) -> None:
        nonlocal ledger_index, cash
        if ledger_index >= len(result.cash_ledger):
            raise ValueError("cash ledger entry missing")
        entry = result.cash_ledger[ledger_index]
        if (entry.event_id, entry.kind, entry.symbol, entry.at) != (reference, kind, symbol, at):
            raise ValueError("cash ledger order or identity mismatch")
        _equal(entry.amount, amount, "cash entry amount")
        cash += amount
        if cash < -1e-7:
            raise ValueError("negative cash violates the cash-funded account")
        _equal(entry.balance, cash, "cash entry balance")
        ledger_index += 1

    points = {point.session: point for point in result.equity}
    for event in result.events:
        if set(event.positions) - symbols or any(value < 0 for value in event.positions.values()):
            raise ValueError("negative or unknown event position")
        if event.kind == "DIVIDEND_PAYMENT":
            payment = payments.get(event.reference)
            if not payment_mode or payment is None or event.reference in processed_payments:
                raise ValueError("unknown, duplicate or legacy-model dividend payment")
            entitlement = entitlements.get(payment.entitlement_id)
            if entitlement is None or payment.entitlement_id not in processed_entitlements or payment.entitlement_id in paid_entitlements:
                raise ValueError("payment lacks a unique accrued entitlement")
            if (payment.action_reference, payment.symbol, payment.at, event.at) != (
                entitlement.action_reference, entitlement.symbol, entitlement.available_at, entitlement.available_at
            ):
                raise ValueError("dividend payment trace or availability mismatch")
            amount = receivables.get(payment.entitlement_id)
            if amount is None:
                raise ValueError("payment lacks an outstanding positive receivable")
            _equal(payment.amount, amount, "dividend payment frozen amount")
            cash_entry(payment.payment_id, "DIVIDEND_PAYMENT", payment.symbol, payment.at, amount)
            del receivables[payment.entitlement_id]
            contribution[payment.symbol]["paid_dividends_usd"] += amount
            paid_entitlements.add(payment.entitlement_id)
            processed_payments.append(payment.payment_id)
        elif event.kind == "SIGNAL":
            signal = signals.get(event.reference)
            if signal is None or event.reference in processed_signals or event.at != signal.generated_at:
                raise ValueError("signal audit identity, time or duplication mismatch")
            if signal.observation_at > signal.generated_at or any(weight < 0 for weight in signal.weights.values()) or sum(signal.weights.values()) > 1 + 1e-10:
                raise ValueError("future observation or non-cash-funded signal")
            processed_signals.append(event.reference)
        elif event.kind == "ORDER":
            order = orders.get(event.reference)
            if order is None or event.reference in processed_orders or order.signal_id not in processed_signals or event.at != order.submitted_at:
                raise ValueError("order audit identity, trace or duplication mismatch")
            if order.eligible_at <= order.submitted_at:
                raise ValueError("order must be submitted before execution eligibility")
            processed_orders.append(event.reference)
        elif event.kind == "CORPORATE_ACTION":
            if dataset is None:
                raise ValueError("corporate-action event requires the dataset")
            try:
                action_index, symbol, action_name, day = event.reference.split(":")
                index = int(action_index)
                if index < 0:
                    raise ValueError("negative action index")
                action = dataset.actions[index]
            except (ValueError, IndexError) as exc:
                raise ValueError("invalid corporate-action reference") from exc
            if (str(action.symbol), action.action, action.effective_date.isoformat()) != (symbol, action_name, day):
                raise ValueError("dataset corporate-action identity mismatch")
            if symbol not in symbols or event.at.date() != action.effective_date or event.reference in processed_actions:
                raise ValueError("corporate-action date, symbol or duplicate mismatch")
            if action.currency != "USD" or any(bar.adjustment_policy != "RAW" for bar in dataset.bars[symbol]):
                raise ValueError("cash corporate actions require matching raw USD prices")
            if action.action == "SPLIT":
                if action.ratio is None or action.ratio <= 0:
                    raise ValueError("positive split ratio required")
                for lot in lots[symbol]:
                    lot.quantity *= action.ratio
                    lot.split_factor *= action.ratio
                    if not math.isfinite(lot.quantity) or lot.quantity <= 0 or not math.isfinite(lot.split_factor) or lot.split_factor <= 0:
                        raise ValueError("split quantity overflow or underflow")
                positions[symbol] *= action.ratio
            elif action.action == "DIVIDEND":
                if action.cash_amount is None:
                    raise ValueError("cash dividend amount required")
                amount = positions[symbol] * action.cash_amount
                entitlement = None
                if payment_mode:
                    entitlement = entitlements_by_action.get(event.reference)
                    if entitlement is None or entitlement.entitlement_id in processed_entitlements:
                        raise ValueError("ordinary dividend lacks a unique entitlement record")
                    if (action.dividend_type, action.effective_date_role, action.cash_amount_basis) != ("ORDINARY_CASH", "EX_DATE", "EX_DATE_SHARES") or action.payment_date is None or action.source_action_id is None:
                        raise ValueError("unqualified ordinary dividend payment terms")
                    if action.known_at > event.at or action.payment_date < action.effective_date:
                        raise ValueError("late or invalid ordinary dividend terms")
                    if any(other.action == "SPLIT" and other.symbol == symbol and other.effective_date == action.effective_date for other in dataset.actions):
                        raise ValueError("ambiguous same-date split and dividend")
                    if (entitlement.symbol, entitlement.ex_date, entitlement.payment_date, entitlement.accrued_at, entitlement.source_action_id) != (
                        symbol, action.effective_date, action.payment_date, event.at, action.source_action_id
                    ):
                        raise ValueError("entitlement source identity or accrual timestamp mismatch")
                    _equal(entitlement.entitled_quantity, positions[symbol], "dividend entitled shares")
                    _equal(entitlement.cash_per_share, action.cash_amount, "dividend per-share amount")
                    _equal(entitlement.amount, amount, "dividend frozen gross amount")
                    # Derive availability from the independent evaluated session grid,
                    # rather than the replay's scheduling helper or a current share count.
                    candidates = [day for day in sessions if day > action.payment_date]
                    expected_at = xcals.get_calendar("XNYS").session_open(candidates[0]).to_pydatetime() if candidates else None
                    expected_status = "SCHEDULED" if expected_at is not None else "AFTER_EVALUATION_END"
                    if entitlement.available_at != expected_at or entitlement.schedule_status != expected_status:
                        raise ValueError("dividend payment availability convention mismatch")
                    if amount > 0:
                        receivables[entitlement.entitlement_id] = amount
                    processed_entitlements.append(entitlement.entitlement_id)
                else:
                    cash_entry(event.reference, "DIVIDEND", symbol, event.at, amount)
                for lot in lots[symbol]:
                    lot.dividends += lot.quantity * action.cash_amount
                    if entitlement is not None:
                        lot.dividend_rights[entitlement.entitlement_id] = lot.quantity * action.cash_amount
                contribution[symbol]["dividend_income_usd"] += amount
            else:
                raise ValueError("unsupported corporate-action economics")
            processed_actions.append(event.reference)
        elif event.kind == "FILL":
            fill = fills.get(event.reference)
            if fill is None or event.reference in processed_fills or fill.filled_at != event.at or fill.order_id not in processed_orders:
                raise ValueError("fill event identity, time or duplication mismatch")
            symbol = fill.symbol
            cash_entry(fill.fill_id, "FILL", symbol, event.at, -fill.quantity * fill.price - fill.fee)
            if fill.quantity > 0:
                lots[symbol].append(_Lot(fill, fill.quantity, fill.quantity * fill.price, fill.fee,
                                         fill.slippage_cost, fill.spread_cost))
            else:
                quantity = -fill.quantity
                if quantity > positions[symbol] and not math.isclose(quantity, positions[symbol], rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError("sell exceeds available long position")
                available = math.fsum(lot.quantity for lot in lots[symbol])
                _equal(available, positions[symbol], "FIFO lot quantity before sell")
                remaining = quantity
                while remaining > 0 and lots[symbol]:
                    lot = lots[symbol][0]
                    matched = min(remaining, lot.quantity)
                    fraction = matched / lot.quantity
                    sale_fraction = matched / quantity
                    execution_basis = lot.execution_basis * fraction
                    buy_fee = lot.fee * fraction
                    dividend = lot.dividends * fraction
                    sale_fee = fill.fee * sale_fraction
                    basis = execution_basis + buy_fee
                    price_pnl = matched * fill.price - sale_fee - basis
                    holding = session_index[fill.session] - session_index[lot.fill.session]
                    closed.append({"symbol": symbol, "entry_fill_id": lot.fill.fill_id,
                        "exit_fill_id": fill.fill_id, "entry_order_id": lot.fill.order_id,
                        "exit_order_id": fill.order_id, "entry_session": lot.fill.session.isoformat(),
                        "exit_session": fill.session.isoformat(), "quantity_at_exit": matched,
                        "entry_share_quantity": matched / lot.split_factor, "split_factor": lot.split_factor,
                        "entry_execution_basis_usd": execution_basis, "entry_fee_usd": buy_fee,
                        "exit_fee_usd": sale_fee, "cost_basis_usd": basis,
                        "net_sale_proceeds_usd": matched * fill.price - sale_fee,
                        "price_pnl_after_fees_usd": price_pnl, "dividend_income_usd": dividend,
                        "total_pnl_after_fees_usd": price_pnl + dividend,
                        "slippage_usd": lot.slippage * fraction + fill.slippage_cost * sale_fraction,
                        "spread_usd": lot.spread * fraction + fill.spread_cost * sale_fraction,
                        "holding_sessions": holding, "holding_calendar_days": (fill.session - lot.fill.session).days})
                    if payment_mode:
                        closed[-1]["dividend_entitlement_allocations"] = {key: value * fraction for key, value in lot.dividend_rights.items()}
                    contribution[symbol]["realized_price_pnl_usd"] += price_pnl
                    lot.quantity -= matched
                    for field in ("execution_basis", "fee", "slippage", "spread", "dividends"):
                        setattr(lot, field, getattr(lot, field) * (1 - fraction))
                    lot.dividend_rights = {key: value * (1 - fraction) for key, value in lot.dividend_rights.items()}
                    remaining -= matched
                    if lot.quantity == 0:
                        lots[symbol].popleft()
                _equal(remaining * fill.price, 0, "unmatched sell notional")
                if math.isclose(quantity, positions[symbol], rel_tol=1e-12, abs_tol=1e-12):
                    round_trips += 1
            positions[symbol] += fill.quantity
            contribution[symbol]["fees_usd"] += fill.fee
            contribution[symbol]["slippage_usd"] += fill.slippage_cost
            contribution[symbol]["spread_usd"] += fill.spread_cost
            processed_fills.append(fill.fill_id)
        _equal(event.cash, cash, "audit snapshot cash")
        check_receivables(event.receivables, "audit snapshot")
        for symbol in symbols:
            _equal(event.positions.get(symbol, 0), positions[symbol], "audit snapshot position")
        if event.kind == "PORTFOLIO":
            try:
                point = points[event.at.date()]
            except KeyError as exc:
                raise ValueError("portfolio snapshot outside equity history") from exc
            if event.reference != point.session.isoformat():
                raise ValueError("portfolio snapshot session mismatch")
            valued_sessions.append(point.session)
            if point.nav <= 0 or any(value < 0 for value in point.market_values.values()):
                raise ValueError("positive NAV and nonnegative market values required")
            _equal(point.cash, cash, "equity point cash")
            check_receivables(point.receivables, "equity point")
            for symbol in symbols:
                _equal(point.positions.get(symbol, 0), positions[symbol], "equity point position")
                _equal(math.fsum(lot.quantity for lot in lots[symbol]), positions[symbol], "FIFO position")
                if positions[symbol] > 0 and symbol not in point.market_values:
                    raise ValueError("open position lacks market value")
                if positions[symbol] > 0 and point.market_values.get(symbol, 0) <= 0:
                    raise ValueError("positive position requires positive market value")
                if positions[symbol] == 0:
                    _equal(point.market_values.get(symbol, 0), 0, "flat asset has phantom market value")
                if dataset is not None:
                    try:
                        value = positions[symbol] * marks[symbol][point.session]
                    except KeyError as exc:
                        raise ValueError("dataset missing matching valuation") from exc
                    _equal(point.market_values.get(symbol, 0), value, "dataset mark")
            if set(point.market_values) - symbols:
                raise ValueError("unknown market-value identity")
            _equal(point.nav, cash + math.fsum(point.market_values.values()) + math.fsum(receivables.values()), "equity accounting")
    if processed_fills != [fill.fill_id for fill in result.fills] or processed_actions != result.applied_actions:
        raise ValueError("fill or corporate-action audit coverage mismatch")
    if processed_signals != [signal.signal_id for signal in result.signals] or processed_orders != [order.order_id for order in result.orders]:
        raise ValueError("incomplete signal or order audit coverage")
    if processed_entitlements != [item.entitlement_id for item in result.dividend_entitlements] or processed_payments != [item.payment_id for item in result.dividend_payments]:
        raise ValueError("incomplete dividend accrual or payment audit coverage")
    expected_paid = {item.entitlement_id for item in result.dividend_entitlements if item.amount > 0 and item.available_at is not None}
    if expected_paid != paid_entitlements:
        raise ValueError("due dividend payments are missing or unexpected")
    if dataset is not None:
        expected_actions = [
            f"{i}:{action.symbol}:{action.action}:{action.effective_date}"
            for i, action in sorted(enumerate(dataset.actions), key=lambda item: (
                item[1].effective_date, item[1].action != "SPLIT", str(item[1].symbol)))
            if sessions[0] <= action.effective_date <= sessions[-1]
        ]
        if processed_actions != expected_actions:
            raise ValueError("dataset applied-action coverage mismatch")
    if valued_sessions != sessions or ledger_index != len(result.cash_ledger):
        raise ValueError("incomplete equity or cash audit coverage")
    final = result.equity[-1]
    open_rows = []
    asset_rows = []
    for symbol in sorted(symbols):
        quantity = math.fsum(lot.quantity for lot in lots[symbol])
        market_value = final.market_values.get(symbol, 0)
        basis = math.fsum(lot.execution_basis + lot.fee for lot in lots[symbol])
        for lot in lots[symbol]:
            value = market_value * lot.quantity / quantity if quantity else 0
            open_rows.append({"symbol": symbol, "entry_fill_id": lot.fill.fill_id,
                "entry_session": lot.fill.session.isoformat(), "quantity": lot.quantity,
                "entry_share_quantity": lot.quantity / lot.split_factor, "split_factor": lot.split_factor,
                "cost_basis_usd": lot.execution_basis + lot.fee, "market_value_usd": value,
                "unrealized_price_pnl_after_entry_fee_usd": value - lot.execution_basis - lot.fee,
                "dividend_income_usd": lot.dividends, "entry_fee_usd": lot.fee,
                "slippage_usd": lot.slippage, "spread_usd": lot.spread,
                "holding_sessions": session_index[final.session] - session_index[lot.fill.session]})
            if payment_mode:
                open_rows[-1]["dividend_entitlement_allocations"] = dict(lot.dividend_rights)
        row: dict[str, Any] = {"symbol": symbol, **contribution[symbol], "unrealized_price_pnl_usd": market_value - basis,
               "open_cost_basis_usd": basis, "ending_quantity": quantity, "ending_market_value_usd": market_value}
        row["total_pnl_usd"] = row["realized_price_pnl_usd"] + row["unrealized_price_pnl_usd"] + row["dividend_income_usd"]
        if payment_mode:
            row["outstanding_dividend_receivables_usd"] = math.fsum(amount for key, amount in receivables.items() if entitlements[key].symbol == symbol)
        row["contribution_to_initial_capital"] = row["total_pnl_usd"] / result.config.initial_cash
        asset_rows.append(row)
    attributed = math.fsum(row["total_pnl_usd"] for row in asset_rows)
    portfolio_pnl = final.nav - result.config.initial_cash
    _equal(attributed, portfolio_pnl, "asset P&L to portfolio NAV")
    allocated_fees = math.fsum(row["entry_fee_usd"] + row["exit_fee_usd"] for row in closed) + math.fsum(row["entry_fee_usd"] for row in open_rows)
    allocated_dividends = math.fsum(row["dividend_income_usd"] for row in [*closed, *open_rows])
    _equal(allocated_fees, result.fees, "FIFO commission allocation")
    _equal(allocated_dividends, math.fsum(row["dividend_income_usd"] for row in asset_rows), "FIFO dividend allocation")
    if payment_mode:
        for row in [*closed, *open_rows]:
            allocations = row["dividend_entitlement_allocations"]
            row["dividend_cash_received_usd"] = math.fsum(amount for key, amount in allocations.items() if key in paid_entitlements)
            row["dividend_receivable_usd"] = math.fsum(amount for key, amount in allocations.items() if key not in paid_entitlements)
            _equal(row["dividend_income_usd"], row["dividend_cash_received_usd"] + row["dividend_receivable_usd"], "lot earned versus paid dividend")
        _equal(allocated_dividends, math.fsum(item.amount for item in result.dividend_payments) + math.fsum(receivables.values()), "paid plus outstanding dividend identity")
    for field, total in (("slippage_usd", result.slippage_cost), ("spread_usd", result.spread_cost)):
        _equal(math.fsum(row[field] for row in [*closed, *open_rows]), total, f"FIFO {field} allocation")
    profits = math.fsum(max(0, row["total_pnl_after_fees_usd"]) for row in closed)
    losses = -math.fsum(min(0, row["total_pnl_after_fees_usd"]) for row in closed)
    closed_basis = math.fsum(row["cost_basis_usd"] for row in closed)
    metrics = {"trade_count": len(closed), "closed_lot_match_count": len(closed),
        "completed_round_trip_count": round_trips,
        "win_rate": sum(row["total_pnl_after_fees_usd"] > 0 for row in closed) / len(closed) if closed else None,
        "profit_factor": profits / losses if losses > 0 else None,
        "average_holding_period_sessions": math.fsum(row["cost_basis_usd"] * row["holding_sessions"] for row in closed) / closed_basis if closed_basis else None}
    output = {"status": "VERIFIED", "closed_lots": closed, "open_lots": open_rows,
        "metrics": metrics, "asset_attribution": asset_rows,
        "reconciliation": {"status": "PASSED", "initial_cash_usd": result.config.initial_cash,
            "ending_cash_usd": final.cash, "ending_nav_usd": final.nav,
            "portfolio_pnl_usd": portfolio_pnl, "attributed_pnl_usd": attributed,
            "allocated_commission_usd": allocated_fees, "allocated_dividends_usd": allocated_dividends,
            "residual_usd": portfolio_pnl - attributed, "fill_count_checked": len(processed_fills),
            "actions_checked": len(processed_actions), "equity_points_checked": len(valued_sessions),
            "absolute_tolerance_usd": 1e-7, "relative_tolerance": 1e-10},
        "warnings": ["FIFO matching segments are not independent trades or tax lots",
            "Dividend income is credited under the replay effective-open convention; payment-date lag is not modeled",
            "Cash interest, taxes and external funding are not modeled; no factor-causality or alpha claim",
            "Ledger reconciliation does not independently certify original dataset identity, source adjustment claims or PIT authenticity"],
        "conventions": {"matching": "FIFO", "trade_count": "Each sell-to-entry-lot matching segment; not flat-to-flat episodes",
            "completed_round_trip_count": "Position transitions from positive to flat per symbol",
            "win_rate": "Fraction of closed matching segments with positive net execution P&L plus allocated posted dividends; breakeven is not a win",
            "profit_factor": "Sum positive closed-segment total P&L / absolute sum negative P&L; null if no losses",
            "average_holding_period_sessions": "Entry-cost-basis-weighted exchange sessions for closed matching segments only",
            "costs": "Execution prices already embed spread/slippage; commission counted once in cost basis/proceeds",
            "attribution": "Additive accounting P&L by held asset divided by initial capital; not a factor regression",
            "market_values": "Checked against supplied dataset prices" if dataset is not None else "Internal ledger marks only; no dataset supplied",
            "evidence_class": result.acceptance}}
    if payment_mode:
        output["reconciliation"].update({"paid_dividends_usd": math.fsum(item.amount for item in result.dividend_payments),
            "outstanding_dividend_receivables_usd": math.fsum(receivables.values()),
            "dividend_payments_checked": len(processed_payments), "dividend_entitlements_checked": len(processed_entitlements)})
        output["warnings"][1] = "Ordinary dividend income accrues at ex-open; cash is available only at the first XNYS open strictly after the sourced pay date; unpaid claims assume full collection without taxes/default/impairment"
        output["conventions"].update({"dividend_accounting": result.config.dividend_accounting,
            "payment_availability": result.config.payment_availability,
            "win_rate": "Closed matching-segment economic P&L includes earned dividends, including unpaid receivables; this is not cash-realized profit",
            "dividend_income_usd": "Earned accrual; cash received and unpaid receivable are disclosed separately"})
    return output


def analyze_trades(result: ReplayResult, dataset: ReplayDataset | None = None) -> dict[str, Any]:
    """Return validated FIFO evidence or BLOCKED without partial/imagined statistics."""
    try:
        checked = ReplayResult.model_validate(result.model_dump())
        data = ReplayDataset.model_validate(dataset.model_dump()) if dataset is not None else None
        output = _analyze(checked, data)
        json.dumps(output, allow_nan=False)
        return output
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return {"status": "BLOCKED", "reason": str(exc), "closed_lots": [], "open_lots": [],
                "metrics": dict(_NULL_METRICS), "asset_attribution": [],
                "reconciliation": {"status": "NOT_VERIFIED"},
                "warnings": ["Incomplete or inconsistent execution evidence; return-series analytics are separate"]}
