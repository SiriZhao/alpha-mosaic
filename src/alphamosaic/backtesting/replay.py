"""Daily next-open paper execution with explicit cash, actions and unfilled orders."""

import math
from datetime import date, timedelta

import exchange_calendars as xcals

from alphamosaic.backtesting.models import (
    CashEntry,
    EquityPoint,
    Fill,
    LedgerEvent,
    OrderAdjustment,
    OrderEvent,
    ReplayConfig,
    ReplayDataset,
    ReplayResult,
    SignalEvent,
    TargetAllocation,
)
from alphamosaic.backtesting.strategies import Strategy
from alphamosaic.core.contracts import DataQuality, HistoricalBar
from alphamosaic.portfolio.construction import constrain_weights


def validate_dataset(data: ReplayDataset) -> list[str]:
    if not data.bars or any(len(bars) < 2 for bars in data.bars.values()):
        raise ValueError("at least two bars per security required")
    calendar = xcals.get_calendar("XNYS")
    reference = next(iter(data.bars.values()))
    sessions = [bar.session for bar in reference]
    expected = [s.date() for s in calendar.sessions_in_range(sessions[0], sessions[-1])]
    if sessions != expected:
        raise ValueError("unique, complete chronological exchange sessions required")
    qualities = set()
    for symbol, bars in data.bars.items():
        for bar in bars:
            HistoricalBar.model_validate(bar.model_dump())
        identity = data.identities.get(symbol)
        if identity is None or identity.symbol != symbol or identity.currency != "USD":
            raise ValueError("security identity/currency mismatch")
        if identity.as_of > data.cutoff or identity.exchange.upper().split("-")[0] not in {
            "NASDAQ",
            "NYSE",
            "AMEX",
            "NYSEARCA",
        }:
            raise ValueError("unsupported exchange or future identity")
        if (
            data.mode == "STRICT_PIT"
            and identity.as_of > calendar.session_open(sessions[0]).to_pydatetime()
        ):
            raise ValueError("historical security identity unavailable")
        if not identity.active or not identity.identity_verified:
            # Current ETF benchmarks are diagnostic only; never quietly certify identity.
            if data.mode == "STRICT_PIT":
                raise ValueError("security identity not verified")
        if [bar.session for bar in bars] != sessions:
            raise ValueError("unaligned or missing security sessions")
        if len({bar.adjustment_policy for bar in bars}) != 1:
            raise ValueError("mixed adjustment policy")
        for bar in bars:
            if bar.symbol != symbol or bar.currency != identity.currency:
                raise ValueError("bar identity mismatch")
            if bar.known_at > data.cutoff or bar.observed_at > data.cutoff:
                raise ValueError("future information after dataset cutoff")
            if bar.known_at < bar.observed_at:
                raise ValueError("bar availability precedes observation")
            if bar.observed_at != calendar.session_close(bar.session).to_pydatetime():
                raise ValueError("bar observation must match session close")
            if data.mode == "STRICT_PIT" and (
                bar.pit_status != "VERIFIED"
                or bar.known_at
                > calendar.session_open(calendar.next_session(bar.session)).to_pydatetime()
            ):
                raise ValueError("historical bar is not certified PIT")
            qualities.add(bar.data_quality)
    if qualities - {
        DataQuality.FIXTURE,
        DataQuality.HISTORICAL,
        DataQuality.REAL,
        DataQuality.DELAYED,
    }:
        raise ValueError("model/missing observations cannot be replay prices")
    if DataQuality.FIXTURE in qualities and len(qualities) != 1:
        raise ValueError("fixture and real data cannot be mixed")
    if data.mode == "STRICT_PIT":
        if any(
            bar.adjustment_policy in {"UNKNOWN", "NOT_APPLICABLE"}
            for rows in data.bars.values()
            for bar in rows
        ):
            raise ValueError("strict replay requires an explicit price adjustment policy")
        if qualities != {DataQuality.FIXTURE} and (
            not data.historical_universe_verified or not data.corporate_actions_complete
        ):
            raise ValueError(
                "strict real replay requires verified universe and corporate-action coverage"
            )
    action_keys = [(a.symbol, a.action, a.effective_date) for a in data.actions]
    if len(action_keys) != len(set(action_keys)):
        raise ValueError("duplicate corporate actions require consolidation")
    if any(s.symbol not in data.bars or s.known_at > data.cutoff for s in data.signals):
        raise ValueError("signal identity or cutoff mismatch")
    if any(s.data_quality == "FIXTURE" for s in data.signals) and qualities != {
        DataQuality.FIXTURE
    }:
        raise ValueError("fixture signals cannot augment real history")
    for action in data.actions:
        if action.symbol not in data.bars or action.known_at > data.cutoff:
            raise ValueError("corporate action identity or cutoff mismatch")
        if action.action not in {"SPLIT", "DIVIDEND"}:
            raise ValueError("unsupported action needs reviewed delisting/symbol-change data")
        if action.currency != "USD" or action.effective_date not in sessions:
            raise ValueError("action currency or session mismatch")
        if action.data_quality == DataQuality.FIXTURE and qualities != {DataQuality.FIXTURE}:
            raise ValueError("fixture actions cannot augment real history")
        if action.action == "SPLIT" and action.ratio is None:
            raise ValueError("split ratio missing")
        if action.action == "DIVIDEND" and action.cash_amount is None:
            raise ValueError("dividend amount missing")
        if data.bars[action.symbol][0].adjustment_policy != "RAW":
            raise ValueError("actions require RAW prices to prevent double adjustment")
        if (
            data.mode == "STRICT_PIT"
            and action.known_at > calendar.session_open(action.effective_date).to_pydatetime()
        ):
            raise ValueError("late corporate action")
        if data.mode == "STRICT_PIT" and action.pit_status != "VERIFIED":
            raise ValueError("corporate action is not certified PIT")
    flags = []
    if any(bar.volume is None for bars in data.bars.values() for bar in bars):
        flags.append("MISSING_LIQUIDITY_ORDERS_WILL_NOT_FILL")
    if data.mode == "RECONSTRUCTED_DIAGNOSTIC":
        flags.append("RECONSTRUCTED_HISTORY_NOT_CERTIFIED_PIT")
    if not data.historical_universe_verified:
        flags.append("SURVIVORSHIP_DELISTING_COVERAGE_NOT_VERIFIED")
    if not data.corporate_actions_complete:
        flags.append("CORPORATE_ACTION_COVERAGE_NOT_VERIFIED")
    if any(bar.adjustment_policy == "UNKNOWN" for bars in data.bars.values() for bar in bars):
        flags.append("UNKNOWN_ADJUSTMENT_PRICE_RETURN_ONLY")
    if any(not identity.identity_verified for identity in data.identities.values()):
        flags.append("CURRENT_IDENTITY_NOT_VERIFIED")
    return flags


def _split_history_bar(bar: HistoricalBar, ratio: float) -> HistoricalBar:
    try:
        return HistoricalBar.model_validate({
            **bar.model_dump(),
            "open": bar.open / ratio,
            "high": bar.high / ratio,
            "low": bar.low / ratio,
            "close": bar.close / ratio,
            "volume": bar.volume * ratio if bar.volume is not None else None,
        })
    except (ValueError, ArithmeticError) as exc:
        raise ValueError("split-adjusted history has unrepresentable price or volume") from exc


def _causal_history(data: ReplayDataset, index: int) -> dict[str, list[HistoricalBar]]:
    history = {s: bars[:index] for s, bars in data.bars.items()}
    prior = next(iter(data.bars.values()))[index - 1].session if index else None
    # Split-adjust only the already observed history, never future corporate actions.
    for action in data.actions:
        if action.action != "SPLIT" or prior is None or action.effective_date > prior:
            continue
        ratio = float(action.ratio or 1)
        symbol = str(action.symbol)
        history[symbol] = [
            _split_history_bar(bar, ratio)
            if bar.session < action.effective_date
            else bar
            for bar in history[symbol]
        ]
    return history


class PaperReplayEngine:
    name = "AlphaMosaic deterministic daily paper replay"

    def run(
        self,
        data: ReplayDataset,
        strategy: Strategy,
        name: str,
        config: ReplayConfig,
        start: date | None = None,
        end: date | None = None,
    ) -> ReplayResult:
        # Revalidate copies at the trust boundary: model_copy deliberately skips validation.
        config = ReplayConfig.model_validate(config.model_dump())
        data = ReplayDataset.model_validate(data.model_dump())
        flags = validate_dataset(data)
        flags.append("DAILY_OPEN_FILL_APPROXIMATION_NO_AUCTION_OR_ORDER_BOOK_DATA")
        flags.append("SAME_DAY_VOLUME_IS_EX_POST_CAPACITY_CAP_NOT_OPEN_KNOWN_LIQUIDITY")
        if data.mode == "RECONSTRUCTED_DIAGNOSTIC":
            flags.append("REVISED_BARS_NOT_KNOWN_AT_HISTORICAL_DECISION_UNTRUSTED")
        if any(a.action == "DIVIDEND" for a in data.actions):
            flags.append("DIVIDEND_CASH_CREDITED_AT_EFFECTIVE_OPEN_PAYMENT_LAG_NOT_MODELED")
        calendar = xcals.get_calendar("XNYS")
        sessions = [bar.session for bar in next(iter(data.bars.values()))]
        selected = [
            i for i, s in enumerate(sessions) if (not start or s >= start) and (not end or s <= end)
        ]
        if len(selected) < 2:
            raise ValueError("insufficient replay sessions")
        first, last = selected[0], selected[-1]
        cash = config.initial_cash
        positions = dict.fromkeys(data.bars, 0.0)
        average_costs = dict.fromkeys(data.bars, 0.0)
        fills: list[Fill] = []
        equity: list[EquityPoint] = []
        unfilled: list[dict[str, str | float]] = []
        applied: list[str] = []
        signals: list[SignalEvent] = []
        orders: list[OrderEvent] = []
        order_adjustments: list[OrderAdjustment] = []
        events: list[LedgerEvent] = []
        cash_ledger: list[CashEntry] = []
        pending: dict[int, list[tuple[OrderEvent, float]]] = {}
        turnover = 0.0
        bought = False

        def event(at, kind, reference):
            events.append(
                LedgerEvent(
                    event_id=f"event-{len(events):06d}",
                    at=at,
                    kind=kind,
                    reference=reference,
                    cash=cash,
                    positions=dict(positions),
                )
            )

        # Decisions before the evaluation window may use warmup history, but carry no positions.
        for index in range(max(0, first - config.order_delay_sessions), last + 1):
            session = sessions[index]
            current = {s: bars[index] for s, bars in data.bars.items()}
            opened = calendar.session_open(session).to_pydatetime()
            closed = calendar.session_close(session).to_pydatetime()
            if index >= first:
                event(opened, "MARKET", str(session))
                actions = sorted(
                    [(j, a) for j, a in enumerate(data.actions) if a.effective_date == session],
                    key=lambda item: (item[1].action != "SPLIT", str(item[1].symbol)),
                )
                for action_index, action in actions:
                    symbol = str(action.symbol)
                    reference = f"{action_index}:{symbol}:{action.action}:{session}"
                    if action.action == "SPLIT":
                        ratio = float(action.ratio or 1)
                        positions[symbol] *= ratio
                        average_costs[symbol] /= ratio
                        for due, entries in pending.items():
                            if due >= index:
                                order_adjustments.extend(
                                    OrderAdjustment(
                                        order_id=o.order_id,
                                        action_reference=reference,
                                        at=opened,
                                        previous_quantity=o.quantity,
                                        adjusted_quantity=o.quantity * ratio,
                                    )
                                    for o, _ in entries
                                    if o.symbol == symbol
                                )
                                pending[due] = [
                                    (
                                        o.model_copy(update={"quantity": o.quantity * ratio}),
                                        v * ratio,
                                    )
                                    if o.symbol == symbol
                                    else (o, v)
                                    for o, v in entries
                                ]
                        if positions[symbol] % config.lot_size:
                            flags.append("SPLIT_FRACTIONAL_SHARES_RETAINED_NO_CASH_IN_LIEU_MODEL")
                    else:
                        amount = positions[symbol] * float(action.cash_amount or 0)
                        cash += amount
                        cash_ledger.append(
                            CashEntry(
                                event_id=reference,
                                at=opened,
                                kind="DIVIDEND",
                                symbol=symbol,
                                amount=amount,
                                balance=cash,
                            )
                        )
                    applied.append(reference)
                    event(opened, "CORPORATE_ACTION", reference)
                nav_open = cash + sum(positions[s] * bar.open for s, bar in current.items())
                if not math.isfinite(nav_open) or nav_open <= 0:
                    raise ValueError("invalid portfolio equity")
                day_turnover = 0.0
                for order, prior_volume in sorted(
                    pending.pop(index, []), key=lambda item: (item[0].quantity >= 0, item[0].symbol)
                ):
                    symbol, q = order.symbol, order.quantity
                    bar = current[symbol]
                    lot = config.lot_size
                    actual_volume = bar.volume or 0.0
                    capacity = (
                        math.floor(
                            min(prior_volume, actual_volume) * config.max_volume_fraction / lot
                        )
                        * lot
                    )
                    reason = "NO_VERIFIED_LIQUIDITY" if capacity <= 0 else "VOLUME_CAP"
                    clipped = math.copysign(min(abs(q), capacity), q)
                    sign = math.copysign(1, q)
                    spread_per_share = bar.open * config.spread_bps / 20_000
                    slippage_per_share = bar.open * config.slippage_bps / 10_000
                    price = bar.open + sign * (slippage_per_share + spread_per_share)
                    turnover_capacity = (
                        math.floor(
                            max(0, config.max_turnover - day_turnover) * nav_open / price / lot
                        )
                        * lot
                    )
                    if abs(clipped) > turnover_capacity:
                        clipped = math.copysign(turnover_capacity, q)
                        reason = "TURNOVER_CONSTRAINT"
                    if clipped > 0:
                        reserve = nav_open * config.min_cash_buffer
                        affordable = (
                            math.floor(
                                max(0, cash - reserve)
                                / (price * (1 + config.fee_bps / 10_000))
                                / lot
                            )
                            * lot
                        )
                        if affordable < clipped:
                            clipped, reason = float(affordable), "CASH_CONSTRAINT"
                        # Enforce buy limits using open marks and post-cost equity, so gaps
                        # cannot turn a constrained close target into an oversized purchase.
                        marked = sum(positions[s] * b.open for s, b in current.items())
                        equity_before = cash + marked
                        cost_per_share = price - bar.open + price * config.fee_bps / 10_000
                        single_capacity = max(
                            0.0,
                            (
                                config.max_single_weight * equity_before
                                - positions[symbol] * bar.open
                            )
                            / (bar.open + config.max_single_weight * cost_per_share),
                        )
                        gross_limit = min(config.max_gross_exposure, 1 - config.min_cash_buffer)
                        gross_capacity = max(
                            0.0,
                            (gross_limit * equity_before - marked)
                            / (bar.open + gross_limit * cost_per_share),
                        )
                        constrained = math.floor(min(single_capacity, gross_capacity) / lot) * lot
                        if (
                            positions[symbol] == 0
                            and sum(q > 0 for q in positions.values()) >= config.max_positions
                        ):
                            constrained = 0
                        if constrained < clipped:
                            clipped, reason = float(constrained), "EXPOSURE_CONSTRAINT"
                    if clipped < 0:
                        if abs(clipped) > positions[symbol]:
                            clipped, reason = -positions[symbol], "POSITION_CONSTRAINT"
                    if clipped > 0 and clipped % lot:
                        clipped = float(math.floor(clipped / lot) * lot)
                        reason = "LOT_SIZE_CONSTRAINT"
                    if abs(clipped) < abs(q):
                        unfilled.append(
                            {
                                "session": str(session),
                                "symbol": symbol,
                                "quantity": q - clipped,
                                "reason": reason,
                                "order_id": order.order_id,
                            }
                        )
                    if not clipped:
                        continue
                    notional = abs(clipped * price)
                    fee = notional * config.fee_bps / 10_000
                    amount = -clipped * price - fee
                    cash += amount
                    if clipped > 0:
                        average_costs[symbol] = (
                            positions[symbol] * average_costs[symbol] + notional + fee
                        ) / (positions[symbol] + clipped)
                    positions[symbol] += clipped
                    if positions[symbol] == 0:
                        average_costs[symbol] = 0
                    day_turnover += notional / nav_open
                    fill = Fill(
                        session=session,
                        symbol=symbol,
                        quantity=clipped,
                        price=price,
                        fee=fee,
                        slippage_cost=abs(clipped) * slippage_per_share,
                        spread_cost=abs(clipped) * spread_per_share,
                        order_id=order.order_id,
                        fill_id=f"fill-{len(fills):06d}",
                        filled_at=opened,
                    )
                    fills.append(fill)
                    cash_ledger.append(
                        CashEntry(
                            event_id=fill.fill_id,
                            at=opened,
                            kind="FILL",
                            symbol=symbol,
                            amount=amount,
                            balance=cash,
                        )
                    )
                    event(opened, "FILL", fill.fill_id)
                turnover += day_turnover
                bought = bought or any(q > 0 for q in positions.values())
                if cash < -1e-7 or any(q < -1e-7 for q in positions.values()):
                    raise ValueError("cash or position invariant violated")
                values = {s: q * current[s].close for s, q in positions.items() if q}
                nav_close = cash + sum(values.values())
                if any(
                    value / nav_close > config.max_single_weight + 1e-10
                    for value in values.values()
                ):
                    flags.append("SINGLE_ASSET_WEIGHT_DRIFT_BETWEEN_REBALANCES")
                if (
                    sum(values.values()) / nav_close
                    > min(config.max_gross_exposure, 1 - config.min_cash_buffer) + 1e-10
                ):
                    flags.append("GROSS_WEIGHT_DRIFT_BETWEEN_REBALANCES")
                equity.append(
                    EquityPoint(
                        session=session,
                        nav=cash + sum(values.values()),
                        cash=cash,
                        positions={s: q for s, q in positions.items() if q},
                        average_costs={s: average_costs[s] for s in values},
                        market_values=values,
                    )
                )
                event(closed, "PORTFOLIO", str(session))

            due = index + config.order_delay_sessions
            if due > last or due < first:
                continue
            rebalance = (due - first) % config.rebalance_sessions == 0
            if name == "buy_and_hold":
                # First partial purchase completes the single attempt; rejected attempts retry.
                rebalance = not bought and not any(pending.values())
            if not rebalance:
                continue
            history = _causal_history(data, index + 1)
            at = closed
            if data.mode == "STRICT_PIT":
                at = max([closed, *[b.known_at for rows in history.values() for b in rows]])
            submitted = at + timedelta(microseconds=1)
            eligible = calendar.session_open(sessions[due]).to_pydatetime()
            if submitted >= eligible:
                raise ValueError("look-ahead: history not available before execution")
            available_signals = [s for s in data.signals if s.known_at <= at <= s.valid_until]
            target = strategy.allocation(history, available_signals, at, config)
            target = TargetAllocation.model_validate(target.model_dump())
            if target.decision_at > at or set(target.weights) - set(current):
                raise ValueError("future or unknown target allocation")
            weights, constraint_flags = constrain_weights(target.weights, config)
            flags.extend(constraint_flags)
            signal_id = f"signal-{len(signals):06d}"
            signals.append(
                SignalEvent(
                    signal_id=signal_id,
                    observation_at=closed,
                    generated_at=at,
                    weights=weights,
                    evidence_ids=target.evidence_ids,
                )
            )
            event(at, "SIGNAL", signal_id)
            nav_decision = cash + sum(positions[s] * current[s].close for s in current)
            for symbol in sorted(current):
                target_shares = (
                    math.floor(
                        nav_decision
                        * weights.get(symbol, 0)
                        / current[symbol].close
                        / config.lot_size
                    )
                    * config.lot_size
                )
                quantity = target_shares - positions[symbol]
                if not quantity:
                    continue
                order = OrderEvent(
                    order_id=f"order-{len(orders):06d}",
                    signal_id=signal_id,
                    submitted_at=submitted,
                    eligible_at=eligible,
                    symbol=symbol,
                    quantity=quantity,
                )
                orders.append(order)
                pending.setdefault(due, []).append((order, current[symbol].volume or 0.0))
                event(submitted, "ORDER", order.order_id)
        fixture = all(
            bar.data_quality == DataQuality.FIXTURE for rows in data.bars.values() for bar in rows
        )
        return ReplayResult(
            strategy=name,
            kind="OUT_OF_SAMPLE" if start else "HISTORICAL",
            acceptance="FIXTURE"
            if fixture
            else "REAL_PIT"
            if data.mode == "STRICT_PIT"
            else "REAL_RECONSTRUCTED",
            config=config,
            equity=equity,
            fills=fills,
            unfilled_orders=unfilled,
            applied_actions=applied,
            turnover=turnover,
            fees=sum(f.fee for f in fills),
            slippage_cost=sum(f.slippage_cost for f in fills),
            spread_cost=sum(f.spread_cost for f in fills),
            signals=signals,
            orders=orders,
            events=events,
            order_adjustments=order_adjustments,
            cash_ledger=cash_ledger,
            diagnostics=list(dict.fromkeys(flags)),
        )
