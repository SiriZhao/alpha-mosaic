"""Fixed baseline signals; strategy calculation has no execution authority."""

from datetime import datetime
from typing import Literal, Protocol, cast

import numpy as np

from alphamosaic.backtesting.models import DatedSignal, ReplayConfig, TargetAllocation
from alphamosaic.backtesting.weekly_strategy import WeeklyBaselineStrategy
from alphamosaic.core.contracts import HistoricalBar
from alphamosaic.portfolio.construction import constrain_weights, inverse_volatility


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
    "equal_weight": "Periodic equal weight across the declared synchronized universe",
    "time_series_momentum": "Positive trailing lookback price return; equal weight",
    "cross_sectional_momentum": "Positive trailing returns; top half by rank, equal weight",
    "mean_reversion": "Close below trailing SMA20; rank percentage distance, equal weight",
    "volatility_targeting": "Equal weight scaled down to trailing annualized portfolio volatility target",
    "risk_adjusted_momentum": "Positive trailing price return divided by trailing daily volatility",
    "low_volatility": "Inverse trailing volatility allocation; zero-volatility assets excluded",
    "ensemble": "Equal capital sleeves of time-series momentum, trend and inverse volatility; unused capital remains cash",
    "weekly_equal_weight": "Complete XNYS natural-week equal weight; next eligible daily open execution",
    "weekly_momentum": "Positive trailing completed-week price return; independently configured weekly lookback",
    "weekly_trend": "Completed-week short/long SMA trend; weekly windows and calendar week-end decisions",
}


class BaselineStrategy:
    def __init__(self, name: str, ablate: str | None = None):
        if name not in STRATEGIES or name.startswith("weekly_"):
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
        if self.name == "ensemble":
            sleeves = [
                BaselineStrategy(name).allocation(history, signals, at, config)
                for name in ("time_series_momentum", "trend", "low_volatility")
            ]
            combined: dict[str, float] = {}
            for sleeve in sleeves:
                for symbol, weight in sleeve.weights.items():
                    combined[symbol] = combined.get(symbol, 0.0) + weight / len(sleeves)
            # A sleeve union may exceed the position budget; retain largest weights
            # deterministically without reallocating the removed exposure.
            selected = sorted(combined, key=lambda s: (-combined[s], s))[: config.max_positions]
            weights, _ = constrain_weights({s: combined[s] for s in selected}, config)
            return TargetAllocation(decision_at=at, weights=weights)
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
            if self.name in {"buy_and_hold", "equal_weight"}:
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
            needed = 20 if self.name == "mean_reversion" else max(60, config.lookback + 1)
            if len(prices) < needed:
                continue
            if self.name == "mean_reversion":
                distance = float(np.mean(prices[-20:]) / prices[-1] - 1)
                if distance > 0:
                    scores[symbol] = distance
                continue
            momentum = float(prices[-1] / prices[-config.lookback - 1] - 1)
            trend = float(np.mean(prices[-20:]) / np.mean(prices[-60:]) - 1)
            window = prices[-config.lookback - 1 :]
            volatility = float(np.std(window[1:] / window[:-1] - 1, ddof=1))
            if (
                self.name in {"momentum", "time_series_momentum", "cross_sectional_momentum"}
                and momentum > 0
            ):
                scores[symbol] = momentum
            elif self.name == "trend" and trend > 0 and prices[-1] > np.mean(prices[-60:]):
                scores[symbol] = trend
            elif self.name == "multi_factor" and momentum > 0:
                rows[symbol] = {"momentum": momentum, "trend": trend, "volatility": -volatility}
            elif self.name == "risk_adjusted_momentum" and momentum > 0 and volatility > 0:
                scores[symbol] = momentum / volatility
            elif self.name in {"low_volatility", "volatility_targeting"} and volatility > 0:
                scores[symbol] = 1 / volatility
        if rows:
            # Fixed ranks, no fitted weights or best-result selection.
            names = [name for name in ("momentum", "trend", "volatility") if name != self.ablate]
            for symbol in rows:
                scores[symbol] = sum(
                    sum(row[name] <= rows[symbol][name] for row in rows.values()) / len(rows)
                    for name in names
                ) / len(names)
        selected = sorted(scores, key=lambda s: (-scores[s], s))[: config.max_positions]
        if self.name == "cross_sectional_momentum":
            selected = selected[: max(1, (len(history) + 1) // 2)]
        weights = {s: 1 / len(selected) for s in selected}
        if self.name == "low_volatility":
            weights = inverse_volatility({s: 1 / scores[s] for s in selected})
        if self.name == "volatility_targeting" and selected:
            changes = np.array(
                [
                    np.diff([b.close for b in history[s][-config.lookback - 1 :]])
                    / np.array([b.close for b in history[s][-config.lookback - 1 : -1]])
                    for s in selected
                ]
            )
            # np.diff operates on the same explicit trailing window; covariance retained.
            portfolio_returns = changes.mean(axis=0)
            realized = float(np.std(portfolio_returns, ddof=1) * np.sqrt(252))
            scale = min(1.0, config.volatility_target / realized) if realized > 0 else 0.0
            weights = {s: w * scale for s, w in weights.items()}
        weights, _ = constrain_weights(weights, config)
        return TargetAllocation(decision_at=at, weights=weights, evidence_ids=evidence)


class StrategyRegistry:
    def list(self) -> list[dict[str, str]]:
        return [
            {"name": name, "methodology": text, "state": "RESEARCH"}
            for name, text in STRATEGIES.items()
        ]

    def get(self, name: str, ablate: str | None = None) -> Strategy:
        if name in {"weekly_equal_weight", "weekly_momentum", "weekly_trend"}:
            if ablate is not None:
                raise ValueError("weekly baselines do not support daily feature ablation")
            return WeeklyBaselineStrategy(cast(Literal["weekly_equal_weight", "weekly_momentum", "weekly_trend"], name))
        return BaselineStrategy(name, ablate)
