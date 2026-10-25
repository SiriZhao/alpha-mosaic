"""Fixed weekly baselines; a daily simulator still owns fills and accounting."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import Field, model_validator

from alphamosaic.backtesting.models import DatedSignal, ReplayConfig, TargetAllocation
from alphamosaic.core.contracts import Contract, HistoricalBar
from alphamosaic.data.weekly import aggregate_weekly_bars, aware_utc
from alphamosaic.portfolio.construction import constrain_weights


class WeeklyStrategyParameters(Contract):
    lookback_weeks: int = Field(default=12, ge=2, le=104)
    trend_short_weeks: int = Field(default=4, ge=2, le=103)
    trend_long_weeks: int = Field(default=12, ge=3, le=104)

    @model_validator(mode="after")
    def windows(self) -> Self:
        if self.trend_short_weeks >= self.trend_long_weeks:
            raise ValueError("weekly trend short window must precede long window")
        return self


class WeeklyBaselineStrategy:
    """Use only completed, available natural-week observations at decision time.

    The caller must schedule WEEKLY decisions at actual XNYS week-end closes and
    provide raw corporate-action qualification before invoking this history-only API.
    No daily lookback/rebalance parameter is reinterpreted as a weekly parameter.
    """

    def __init__(
        self,
        name: Literal["weekly_momentum", "weekly_trend", "weekly_equal_weight"],
        parameters: WeeklyStrategyParameters | None = None,
    ) -> None:
        if name not in {"weekly_momentum", "weekly_trend", "weekly_equal_weight"}:
            raise ValueError("unknown weekly baseline strategy")
        self.name = name
        self.parameters = WeeklyStrategyParameters.model_validate((parameters or WeeklyStrategyParameters()).model_dump())

    def allocation(
        self,
        history: dict[str, list[HistoricalBar]],
        signals: list[DatedSignal],
        at: datetime,
        config: ReplayConfig,
    ) -> TargetAllocation:
        at = aware_utc(at)
        config = ReplayConfig.model_validate(config.model_dump())
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
            elif self.name == "weekly_momentum" and len(prices) >= self.parameters.lookback_weeks + 1:
                momentum = prices[-1] / prices[-self.parameters.lookback_weeks - 1] - 1
                if not math.isfinite(momentum):
                    raise ValueError("non-finite weekly momentum")
                if momentum > 0:
                    scores[symbol] = momentum
            elif self.name == "weekly_trend" and len(prices) >= self.parameters.trend_long_weeks:
                scale = max(prices[-self.parameters.trend_long_weeks:])
                short = math.fsum(p / scale for p in prices[-self.parameters.trend_short_weeks:]) / self.parameters.trend_short_weeks
                long = math.fsum(p / scale for p in prices[-self.parameters.trend_long_weeks:]) / self.parameters.trend_long_weeks
                if short > long and prices[-1] / scale > long:
                    scores[symbol] = short / long - 1
            if symbol in scores:
                evidence_ids.extend(b.source_hash for b in rows[-max(self.parameters.lookback_weeks + 1, self.parameters.trend_long_weeks):])
        selected = sorted(scores, key=lambda s: (-scores[s], s))[:config.max_positions]
        weights = {s: 1 / len(selected) for s in selected} if selected else {}
        weights, _ = constrain_weights(weights, config)
        return TargetAllocation(decision_at=at, weights=weights, evidence_ids=sorted(set(evidence_ids)))
