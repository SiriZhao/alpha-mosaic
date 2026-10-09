"""Daily next-open paper execution with explicit cash, actions and unfilled orders."""

import math
from datetime import date

import exchange_calendars as xcals

from alphamosaic.backtesting.models import (
    EquityPoint,
    Fill,
    ReplayConfig,
    ReplayDataset,
    ReplayResult,
)
from alphamosaic.backtesting.strategies import Strategy
from alphamosaic.core.contracts import DataQuality, HistoricalBar


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


def _causal_history(data: ReplayDataset, index: int) -> dict[str, list[HistoricalBar]]:
    history = {s: bars[:index] for s, bars in data.bars.items()}
    prior = next(iter(data.bars.values()))[index].session if index else None
    # Split-adjust only the already observed history, never future corporate actions.
    for action in data.actions:
        if action.action != "SPLIT" or prior is None or action.effective_date > prior:
            continue
        ratio = float(action.ratio or 1)
        symbol = str(action.symbol)
        history[symbol] = [
            bar.model_copy(
                update={
                    "open": bar.open / ratio,
                    "high": bar.high / ratio,
                    "low": bar.low / ratio,
                    "close": bar.close / ratio,
                    "volume": bar.volume * ratio if bar.volume is not None else None,
                }
            )
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
        flags = validate_dataset(data)
        calendar = xcals.get_calendar("XNYS")
        sessions = [bar.session for bar in next(iter(data.bars.values()))]
        cash = config.initial_cash
        positions = dict.fromkeys(data.bars, 0.0)
        fills, equity, unfilled, applied = [], [], [], []
        turnover = 0.0
        elapsed = 0
        bought = False
        for index, session in enumerate(sessions):
            if (start and session < start) or (end and session > end):
                continue
            current = {s: bars[index] for s, bars in data.bars.items()}
            for action_index, action in enumerate(data.actions):
                if action.effective_date != session:
                    continue
                symbol = str(action.symbol)
                if action.action == "SPLIT":
                    positions[symbol] *= float(action.ratio or 1)
                elif action.action == "DIVIDEND":
                    cash += positions[symbol] * float(action.cash_amount or 0)
                applied.append(f"{action_index}:{symbol}:{action.action}:{session}")
            nav_open = cash + sum(positions[s] * bar.open for s, bar in current.items())
            rebalance = index > 0 and elapsed % config.rebalance_sessions == 0
            if name == "buy_and_hold":
                rebalance = index > 0 and not bought
            if rebalance:
                at = calendar.session_open(session).to_pydatetime()
                history = _causal_history(data, index)
                if data.mode == "STRICT_PIT" and any(
                    bar.known_at > at for bars in history.values() for bar in bars
                ):
                    raise ValueError("look-ahead: history not available at decision time")
                target = strategy.allocation(history, data.signals, at, config)
                if target.decision_at > at or set(target.weights) - set(current):
                    raise ValueError("future or unknown target allocation")
                if len(target.weights) > config.max_positions:
                    raise ValueError("position limit exceeded")
                # Share targets and liquidity use ONLY prior known observations. Next open
                # determines execution price; a gap can leave a cash-constrained order unfilled.
                nav_decision = cash + sum(positions[s] * history[s][-1].close for s in current)
                quantity = {
                    s: math.floor(nav_decision * target.weights.get(s, 0) / history[s][-1].close)
                    - positions[s]
                    for s in current
                }
                # Sales fund buys; alphabetical tie break makes replays reproducible.
                for s in sorted(quantity, key=lambda s: (quantity[s] >= 0, s)):
                    q, bar = quantity[s], current[s]
                    if not q:
                        continue
                    reason = None
                    prior_volume = history[s][-1].volume
                    capacity = (
                        math.floor(prior_volume * config.max_volume_fraction)
                        if prior_volume is not None
                        else 0
                    )
                    if bar.volume == 0:
                        capacity = 0  # Observed no trades: a submitted order cannot fill.
                    if capacity == 0:
                        reason = "NO_VERIFIED_LIQUIDITY"
                    clipped = math.copysign(min(abs(q), capacity), q)
                    if abs(clipped) < abs(q) and not reason:
                        reason = "VOLUME_CAP"
                    price = bar.open * (1 + math.copysign(config.slippage_bps / 10_000, q))
                    if clipped > 0:
                        affordable = math.floor(cash / (price * (1 + config.fee_bps / 10_000)))
                        if affordable < clipped:
                            clipped, reason = float(affordable), "CASH_CONSTRAINT"
                    if clipped < 0:
                        clipped = -min(abs(clipped), positions[s])
                    if abs(clipped) < abs(q):
                        unfilled.append(
                            {
                                "session": str(session),
                                "symbol": s,
                                "quantity": q - clipped,
                                "reason": reason or "POSITION_CONSTRAINT",
                            }
                        )
                    if clipped:
                        notional = abs(clipped * price)
                        fee = notional * config.fee_bps / 10_000
                        cash -= clipped * price + fee
                        positions[s] += clipped
                        turnover += notional / nav_open
                        fills.append(
                            Fill(
                                session=session,
                                symbol=s,
                                quantity=clipped,
                                price=price,
                                fee=fee,
                                slippage_cost=abs(clipped) * abs(price - bar.open),
                            )
                        )
                bought = bought or any(q > 0 for q in positions.values())
            if cash < -1e-7 or any(q < -1e-7 for q in positions.values()):
                raise ValueError("cash or position invariant violated")
            equity.append(
                EquityPoint(
                    session=session,
                    nav=cash + sum(positions[s] * bar.close for s, bar in current.items()),
                    cash=cash,
                    positions={s: q for s, q in positions.items() if q},
                )
            )
            elapsed += 1
        if len(equity) < 2:
            raise ValueError("insufficient replay sessions")
        fixture = all(
            bar.data_quality == DataQuality.FIXTURE for bars in data.bars.values() for bar in bars
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
            diagnostics=flags,
        )
