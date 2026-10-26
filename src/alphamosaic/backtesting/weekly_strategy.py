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
from alphamosaic.core.weekly_features import DerivedWeeklyClose
from alphamosaic.data.weekly import WeeklyBar, aggregate_weekly_bars, aware_utc
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
        if config.weekly_feature_policy == "RAW_SPLIT_PRICE_ONLY_V1":
            raise ValueError("RAW price policy requires separately qualified derived feature input")
        weekly: dict[str, list[WeeklyBar] | list[DerivedWeeklyClose]] = {
            symbol: aggregate_weekly_bars(daily, cutoff=at).bars
            for symbol, daily in history.items() if daily
        }
        return self._allocate_weekly(weekly, at, config)

    def allocation_features(
        self, features: dict[str, list[DerivedWeeklyClose]], at: datetime, config: ReplayConfig,
    ) -> TargetAllocation:
        if config.weekly_feature_policy != "RAW_SPLIT_PRICE_ONLY_V1":
            raise ValueError("derived features require explicit RAW split price policy")
        weekly: dict[str, list[WeeklyBar] | list[DerivedWeeklyClose]] = {}
        for symbol, supplied in features.items():
            rows = [DerivedWeeklyClose.model_validate(row.model_dump()) for row in supplied]
            if any(row.decision_at != at or row.unit_anchor != rows[-1].last_session for row in rows):
                raise ValueError("derived weekly feature decision or anchor mismatch")
            weekly[symbol] = rows
        return self._allocate_weekly(weekly, at, config)

    def _allocate_weekly(
        self, weekly: dict[str, list[WeeklyBar] | list[DerivedWeeklyClose]],
        at: datetime, config: ReplayConfig,
    ) -> TargetAllocation:
        at = aware_utc(at)
        config = ReplayConfig.model_validate(config.model_dump())
        if self.parameters is not None and self.parameters != config.weekly_parameters:
            raise ValueError("weekly constructor parameters differ from the recorded replay configuration")
        parameters = self.parameters or config.weekly_parameters
        scores: dict[str, float] = {}
        aligned: tuple | None = None
        evidence_ids: list[str] = []
        feature_evidence: list[DerivedWeeklyClose] = []
        for symbol, rows in weekly.items():
            if any(b.symbol != symbol or (b.available_at if isinstance(b, WeeklyBar) else b.decision_at) > at for b in rows):
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
            # Record dependencies even when a negative price hypothesis leaves cash.
            if self.name != "weekly_equal_weight" or symbol in scores:
                for row in rows[-max(parameters.lookback_weeks + 1, parameters.trend_long_weeks):]:
                    if isinstance(row, DerivedWeeklyClose):
                        feature_evidence.append(row)
                        evidence_ids.append(row.dependency_fingerprint)
                    elif symbol in scores:
                        evidence_ids.append(row.source_hash)
        selected = sorted(scores, key=lambda s: (-scores[s], s))[:config.max_positions]
        weights = {s: 1 / len(selected) for s in selected} if selected else {}
        weights, _ = constrain_weights(weights, config)
        return TargetAllocation(decision_at=at, weights=weights, evidence_ids=sorted(set(evidence_ids)),
            feature_evidence=feature_evidence)
