"""Fixed baseline signals; strategy calculation has no execution authority."""

from datetime import datetime
from typing import Protocol

import numpy as np

from alphamosaic.backtesting.models import DatedSignal, ReplayConfig, TargetAllocation
from alphamosaic.core.contracts import HistoricalBar


class Strategy(Protocol):
    def allocation(
        self,
        history: dict[str, list[HistoricalBar]],
        signals: list[DatedSignal],
        at: datetime,
        config: ReplayConfig,
    ) -> TargetAllocation: ...


STRATEGIES = {
    "buy_and_hold": "Equal weight, first eligible session then hold; cash-funded",
    "momentum": "Positive trailing 63-session price return; rank and equal weight",
    "trend": "SMA20 > SMA60 and close > SMA60; equal weight",
    "quality": "Positive sourced PIT ROE quality signal; rank and equal weight",
    "value": "Positive sourced PIT earnings yield; rank and equal weight",
    "multi_factor": "Mean cross-sectional ranks of momentum, trend and inverse volatility",
    "ai_rating": "Sourced PIT AI rating >=7/10; no reconstruction of past ratings",
    "signal_consensus": "Positive sourced PIT consensus; no LLM promotion",
}


class BaselineStrategy:
    def __init__(self, name: str, ablate: str | None = None):
        if name not in STRATEGIES:
            raise ValueError("unknown strategy")
        if ablate not in {None, "trend", "volatility"}:
            raise ValueError("unknown ablation")
        self.name, self.ablate = name, ablate

    def allocation(
        self,
        history: dict[str, list[HistoricalBar]],
        signals: list[DatedSignal],
        at: datetime,
        config: ReplayConfig,
    ) -> TargetAllocation:
        scores: dict[str, float] = {}
        rows: dict[str, dict[str, float]] = {}
        evidence: list[str] = []
        required = {
            "quality": "quality",
            "value": "value",
            "ai_rating": "ai_rating",
            "signal_consensus": "consensus",
        }.get(self.name)
        for symbol, bars in history.items():
            if not bars:
                continue
            prices = np.array([bar.close for bar in bars])
            if self.name == "buy_and_hold":
                scores[symbol] = 1
                continue
            if required:
                eligible = [
                    s
                    for s in signals
                    if s.symbol == symbol
                    and s.metric == required
                    and s.known_at <= at <= s.valid_until
                    and s.pit_verified
                ]
                if not eligible:
                    continue
                signal = max(eligible, key=lambda s: s.known_at)
                if signal.value >= 7 if self.name == "ai_rating" else signal.value > 0:
                    scores[symbol] = signal.value
                    evidence.append(signal.evidence_id)
                continue
            if len(prices) < max(60, config.lookback + 1):
                continue
            momentum = float(prices[-1] / prices[-config.lookback - 1] - 1)
            trend = float(np.mean(prices[-20:]) / np.mean(prices[-60:]) - 1)
            volatility = float(np.std(prices[1:] / prices[:-1] - 1, ddof=1))
            if self.name == "momentum" and momentum > 0:
                scores[symbol] = momentum
            elif self.name == "trend" and trend > 0 and prices[-1] > np.mean(prices[-60:]):
                scores[symbol] = trend
            elif self.name == "multi_factor" and momentum > 0:
                rows[symbol] = {"momentum": momentum, "trend": trend, "volatility": -volatility}
        if rows:
            # Fixed ranks, no fitted weights or best-result selection.
            names = [name for name in ("momentum", "trend", "volatility") if name != self.ablate]
            for symbol in rows:
                scores[symbol] = sum(
                    sum(row[name] <= rows[symbol][name] for row in rows.values()) / len(rows)
                    for name in names
                ) / len(names)
        selected = sorted(scores, key=lambda s: (-scores[s], s))[: config.max_positions]
        return TargetAllocation(
            decision_at=at, weights={s: 1 / len(selected) for s in selected}, evidence_ids=evidence
        )


class StrategyRegistry:
    def list(self) -> list[dict[str, str]]:
        return [
            {"name": name, "methodology": text, "state": "RESEARCH"}
            for name, text in STRATEGIES.items()
        ]

    def get(self, name: str, ablate: str | None = None) -> Strategy:
        return BaselineStrategy(name, ablate)
