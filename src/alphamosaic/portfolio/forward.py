"""Initialize an isolated empty paper account; no inferred fills or returns."""

import sqlite3
from pathlib import Path
from typing import Any

from alphamosaic.core.contracts import utc_now


class ForwardPaperStore:
    def __init__(self, root: Path):
        self.path = root / "forward-paper.sqlite"

    def initialize(self, initial_cash: float = 100_000) -> dict[str, Any]:
        if not 0 < initial_cash <= 1_000_000_000:
            raise ValueError("finite positive paper cash required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
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
                "No trades, fills or returns inferred from initialization; no recording worker connected"
            ],
        }
