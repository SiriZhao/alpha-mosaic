"""Fixed weekly baselines; a daily simulator still owns fills and accounting."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Literal

from alphamosaic.backtesting.models import (
    DatedSignal,
    ReplayConfig,
    TargetAllocation,
    WeeklyStrategyParameters,
)
from alphamosaic.core.contracts import HistoricalBar
from alphamosaic.data.weekly import aggregate_weekly_bars, aware_utc
from alphamosaic.portfolio.construction import constrain_weights


class WeeklyBaselineStrategy:
    """Use only completed, available natural-week observations at decision time.

    The caller must schedule WEEKLY decisions at actual XNYS week-end closes and
    provide raw corporate-action qualification before invoking this history-only API.
    No daily lookback/rebalance parameter is reinterpreted as a weekly parameter.
    """

    decision_frequency = "WEEKLY"

    def __init__(
        self,
        name: Literal["weekly_momentum", "weekly_trend", "weekly_equal_weight"],
        parameters: WeeklyStrategyParameters | None = None,
    ) -> None:
        if name not in {"weekly_momentum", "weekly_trend", "weekly_equal_weight"}:
            raise ValueError("unknown weekly baseline strategy")
        self.name = name
        self.parameters = WeeklyStrategyParameters.model_validate(parameters.model_dump()) if parameters else None

    def allocation(
        self,
        history: dict[str, list[HistoricalBar]],
        signals: list[DatedSignal],
        at: datetime,
        config: ReplayConfig,
    ) -> TargetAllocation:
        at = aware_utc(at)
        config = ReplayConfig.model_validate(config.model_dump())
        if self.parameters is not None and self.parameters != config.weekly_parameters:
            raise ValueError("weekly constructor parameters differ from the recorded replay configuration")
        parameters = self.parameters or config.weekly_parameters
        scores: dict[str, float] = {}
        aligned: tuple | None = None
        evidence_ids: list[str] = []
        for symbol, daily in history.items():
            if not daily:
                continue
            view = aggregate_weekly_bars(daily, cutoff=at)
            rows = view.bars
            if any(b.symbol != symbol or b.available_at > at for b in rows):
                raise ValueError("weekly strategy received unavailable or mismatched history")
            weeks = tuple(b.week_start for b in rows)
            if any(a + timedelta(days=7) != b for a, b in zip(weeks, weeks[1:], strict=False)):
                raise ValueError("weekly strategy requires consecutive complete available weeks")
            if aligned is None:
                aligned = weeks
            elif weeks != aligned:
                raise ValueError("weekly strategy assets have unaligned available weeks")
            if not rows:
                continue
            prices = [b.close for b in rows]
            if self.name == "weekly_equal_weight":
                scores[symbol] = 1
            elif self.name == "weekly_momentum" and len(prices) >= parameters.lookback_weeks + 1:
                momentum = prices[-1] / prices[-parameters.lookback_weeks - 1] - 1
                if not math.isfinite(momentum):
                    raise ValueError("non-finite weekly momentum")
                if momentum > 0:
                    scores[symbol] = momentum
            elif self.name == "weekly_trend" and len(prices) >= parameters.trend_long_weeks:
                scale = max(prices[-parameters.trend_long_weeks:])
                short = math.fsum(p / scale for p in prices[-parameters.trend_short_weeks:]) / parameters.trend_short_weeks
                long = math.fsum(p / scale for p in prices[-parameters.trend_long_weeks:]) / parameters.trend_long_weeks
                if short > long and prices[-1] / scale > long:
                    scores[symbol] = short / long - 1
            if symbol in scores:
                evidence_ids.extend(b.source_hash for b in rows[-max(parameters.lookback_weeks + 1, parameters.trend_long_weeks):])
        selected = sorted(scores, key=lambda s: (-scores[s], s))[:config.max_positions]
        weights = {s: 1 / len(selected) for s in selected} if selected else {}
        weights, _ = constrain_weights(weights, config)
        return TargetAllocation(decision_at=at, weights=weights, evidence_ids=sorted(set(evidence_ids)))
