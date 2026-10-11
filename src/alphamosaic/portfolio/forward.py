"""Immutable forward-paper signal evidence and horizon evaluation.

This store records research observations only. It never submits orders and never
converts an observation into a real-account return.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from alphamosaic.core.contracts import HistoricalBar, utc_now

_HORIZONS = (5, 20, 60)


def _iso(value: datetime | date | str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if value.tzinfo is None:
        raise ValueError("aware timestamp required")
    return value.astimezone(UTC).isoformat()


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ForwardPaperStore:
    def __init__(self, root: Path):
        self.path = root / "forward-paper.sqlite"

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self, initial_cash: float = 100_000) -> dict[str, Any]:
        if not 0 < initial_cash <= 1_000_000_000:
            raise ValueError("finite positive paper cash required")
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), created_at TEXT NOT NULL, cash REAL NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS signals (id TEXT PRIMARY KEY, symbol TEXT NOT NULL, known_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS outcomes (id TEXT PRIMARY KEY, signal_id TEXT NOT NULL, qualified INTEGER NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO account VALUES (1, ?, ?)",
                (utc_now().isoformat(), initial_cash),
            )
        return self.status()

    def status(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "status": "NOT_CONFIGURED",
                "broker_enabled": False,
                "observations": [],
                "diagnostics": ["paper account not initialized"],
            }
        with sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True) as connection:
            account = connection.execute(
                "SELECT created_at, cash FROM account WHERE id=1"
            ).fetchone()
            signals = connection.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
            outcomes = connection.execute(
                "SELECT COUNT(*) FROM outcomes WHERE qualified=1"
            ).fetchone()[0]
        if account is None:
            return {
                "status": "BLOCKED",
                "broker_enabled": False,
                "diagnostics": ["account row missing"],
            }
        return {
            "status": "READY",
            "account_state": "INITIALIZED_EMPTY" if not signals else "FORWARD_TESTING",
            "kind": "FORWARD_PAPER",
            "created_at": account[0],
            "initial_cash_usd": account[1],
            "signal_count": signals,
            "qualified_observations": outcomes,
            "return": None,
            "observations": [],
            "broker_enabled": False,
            "diagnostics": [
                "Research signal tracking only; no trades, fills or real-account returns"
            ],
        }

    def freeze_signal(
        self,
        *,
        symbol: str,
        price_reference: float,
        research_horizon: str = "T+5/T+20/T+60",
        signal_id: str | None = None,
        issued_at: datetime | None = None,
        as_of: datetime | None = None,
        source_hash: str | None = None,
        model_version: str = "alphamosaic-unknown",
        signal_direction: str = "NEUTRAL",
        entry_conditions: dict[str, Any] | None = None,
        invalidation_conditions: dict[str, Any] | None = None,
        benchmark: str = "SPY",
        fees_assumption: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert an immutable signal; reusing an id requires byte-identical payload."""
        if not symbol or price_reference <= 0:
            raise ValueError("symbol and positive price_reference required")
        issued_at = issued_at or utc_now()
        as_of = as_of or issued_at
        if issued_at.tzinfo is None or as_of.tzinfo is None or as_of > issued_at:
            raise ValueError("aware as_of must not be after issued_at")
        signal_id = signal_id or uuid4().hex
        payload: dict[str, Any] = {
            "signal_id": signal_id,
            "symbol": symbol.upper(),
            "issued_at": _iso(issued_at),
            "as_of": _iso(as_of),
            "price_reference": float(price_reference),
            "research_horizon": research_horizon,
            "model_version": model_version,
            "signal_direction": signal_direction,
            "entry_conditions": entry_conditions or {},
            "invalidation_conditions": invalidation_conditions or {},
            "benchmark": benchmark,
            "fees_assumption": fees_assumption or {},
            "broker_enabled": False,
        }
        payload["source_hash"] = source_hash or _payload_hash(payload)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        self.initialize()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT payload FROM signals WHERE id=?", (signal_id,)
            ).fetchone()
            if existing is not None:
                if existing[0] != raw:
                    raise ValueError("immutable signal id already contains different evidence")
                return payload
            connection.execute(
                "INSERT INTO signals(id, symbol, known_at, payload) VALUES (?, ?, ?, ?)",
                (signal_id, payload["symbol"], payload["as_of"], raw),
            )
        return payload

    # Explicit alias used by integrations and tests.
    record_signal = freeze_signal

    def signals(self, symbol: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True) as connection:
            rows = connection.execute(
                "SELECT payload FROM signals ORDER BY known_at, id"
            ).fetchall()
        values = [json.loads(row[0]) for row in rows]
        return [item for item in values if symbol is None or item["symbol"] == symbol.upper()]

    @staticmethod
    def _validate_bars(bars: list[HistoricalBar], symbol: str) -> None:
        if not bars or any(bar.symbol != symbol for bar in bars):
            raise ValueError("missing or mismatched forward bars")
        sessions = [bar.session for bar in bars]
        if sessions != sorted(set(sessions)):
            raise ValueError("forward bars must be unique and chronological")

    def evaluate(
        self,
        signal_id: str,
        bars: list[HistoricalBar],
        benchmark_bars: list[HistoricalBar] | None = None,
        horizons: tuple[int, ...] = _HORIZONS,
    ) -> list[dict[str, Any]]:
        if not self.path.exists():
            raise ValueError("paper account not initialized")
        with sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True) as connection:
            row = connection.execute(
                "SELECT payload FROM signals WHERE id=?", (signal_id,)
            ).fetchone()
        if row is None:
            raise KeyError(signal_id)
        signal = json.loads(row[0])
        signal_symbol = str(signal["symbol"])
        self._validate_bars(bars, signal_symbol)
        if benchmark_bars:
            self._validate_bars(benchmark_bars, str(benchmark_bars[0].symbol))
        as_of = datetime.fromisoformat(signal["as_of"])
        forward = [bar for bar in bars if bar.session > as_of.date()]
        entry = signal["entry_conditions"]
        trigger_price = entry.get("trigger_price")
        direction = signal["signal_direction"]
        triggered_index: int | None = None
        for index, bar in enumerate(forward):
            if (
                trigger_price is None
                or (direction == "BULLISH" and bar.high >= trigger_price)
                or (direction == "BEARISH" and bar.low <= trigger_price)
            ):
                triggered_index = index
                break
        outcomes: list[dict[str, Any]] = []
        fees = signal["fees_assumption"]
        fee_bps = float(fees.get("fee_bps", 0) or 0)
        slippage_bps = float(fees.get("slippage_bps", 0) or 0)
        if not 0 <= fee_bps <= 1000 or not 0 <= slippage_bps <= 1000:
            raise ValueError("fees_assumption bps must be in 0..1000")
        for horizon in horizons:
            if horizon not in _HORIZONS:
                raise ValueError("only T+5, T+20 and T+60 are supported")
            if triggered_index is None:
                outcome = {
                    "signal_id": signal_id,
                    "horizon": f"T+{horizon}",
                    "status": "NOT_TRIGGERED",
                    "qualified": False,
                    "broker_enabled": False,
                }
            elif len(forward) <= triggered_index + horizon - 1:
                outcome = {
                    "signal_id": signal_id,
                    "horizon": f"T+{horizon}",
                    "status": "HOLDING" if forward else "INSUFFICIENT_DATA",
                    "qualified": False,
                    "broker_enabled": False,
                }
            else:
                target = forward[triggered_index + horizon - 1]
                entry_bar = forward[triggered_index]
                entry_price = float(trigger_price or signal["price_reference"])
                direction_sign = 1 if direction != "BEARISH" else -1
                entry_price *= 1 + direction_sign * slippage_bps / 10_000
                exit_price = target.close * (1 - direction_sign * slippage_bps / 10_000)
                gross = direction_sign * (exit_price / entry_price - 1)
                net = gross - 2 * fee_bps / 10_000
                benchmark_return = None
                if benchmark_bars:
                    matching = {bar.session: bar for bar in benchmark_bars}
                    b_entry = matching.get(entry_bar.session)
                    b_target = matching.get(target.session)
                    if b_entry and b_target:
                        benchmark_return = b_target.close / b_entry.close - 1
                outcome = {
                    "signal_id": signal_id,
                    "horizon": f"T+{horizon}",
                    "status": "AT_HORIZON",
                    "qualified": True,
                    "entry_session": str(entry_bar.session),
                    "target_session": str(target.session),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_return": gross,
                    "fees_assumption": fees,
                    "net_return": net,
                    "benchmark": signal["benchmark"],
                    "benchmark_return": benchmark_return,
                    "excess_return": None if benchmark_return is None else net - benchmark_return,
                    "broker_enabled": False,
                }
            outcome = {**outcome, "source_hash": signal["source_hash"]}
            raw = json.dumps(outcome, sort_keys=True, separators=(",", ":"), allow_nan=False)
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT payload FROM outcomes WHERE id=?", (f"{signal_id}:{horizon}",)
                ).fetchone()
                if existing and existing[0] != raw:
                    raise ValueError("immutable outcome conflict")
                if not existing:
                    connection.execute(
                        "INSERT INTO outcomes(id, signal_id, qualified, payload) VALUES (?, ?, ?, ?)",
                        (f"{signal_id}:{horizon}", signal_id, int(outcome["qualified"]), raw),
                    )
            outcomes.append(outcome)
        return outcomes

    def outcomes(self, signal_id: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True) as connection:
            rows = connection.execute("SELECT payload FROM outcomes ORDER BY id").fetchall()
        values = [json.loads(item[0]) for item in rows]
        return [item for item in values if signal_id is None or item["signal_id"] == signal_id]
