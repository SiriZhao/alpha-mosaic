"""Engine adapters: deterministic execution plus an explicit QuantStats boundary."""

from __future__ import annotations

import importlib.util
from datetime import date

import pandas as pd

from alphamosaic.backtesting.adapters import EngineHealth, EngineRun
from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import Strategy
from alphamosaic.evaluation.quantstats_adapter import QuantStatsAdapter
from alphamosaic.evaluation.validation import returns_of


class PaperReplayAdapter:
    name = "alphamosaic-paper-replay"
    execution_engine = True

    def __init__(self) -> None:
        self._last: EngineHealth | None = None

    def health(self) -> EngineHealth:
        return self._last or EngineHealth(
            self.name,
            True,
            True,
            True,
            False,
            False,
            "READY",
            ("deterministic local execution engine; computation not run",),
        )

    def run(
        self,
        data: ReplayDataset,
        strategy: Strategy,
        strategy_name: str,
        config: ReplayConfig,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> EngineRun:
        try:
            result = PaperReplayEngine().run(data, strategy, strategy_name, config, start, end)
            metrics = QuantStatsAdapter().metrics(returns_of(result))
            self._last = EngineHealth(
                self.name,
                True,
                True,
                True,
                True,
                False,
                "COMPUTED",
                ("validation is evidence-gated separately",),
            )
            return EngineRun(self.name, result, metrics, "COMPUTED")
        except (ImportError, ValueError) as exc:
            self._last = EngineHealth(
                self.name, True, True, True, False, False, "BLOCKED", (str(exc),)
            )
            return EngineRun(self.name, None, {}, "BLOCKED", (str(exc),))


class QuantStatsAdapterEngine:
    """QuantStats is an independent statistics implementation, not an order engine."""

    name = "quantstats-analytics"
    execution_engine = False

    def health(self) -> EngineHealth:
        installed = importlib.util.find_spec("quantstats") is not None
        return EngineHealth(
            self.name,
            True,
            installed,
            installed,
            False,
            False,
            "READY" if installed else "NOT_CONFIGURED",
            ("analytics only; it does not model orders, cash, fills, or corporate actions",)
            if installed
            else ("install optional analytics extra",),
        )

    def run(
        self,
        data: ReplayDataset,
        strategy: Strategy,
        strategy_name: str,
        config: ReplayConfig,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> EngineRun:
        # Run the canonical replay supplied by the caller's same data/strategy, then
        # calculate metrics through the independently maintained QuantStats package.
        replay = PaperReplayAdapter().run(
            data, strategy, strategy_name, config, start=start, end=end
        )
        if replay.result is None:
            return EngineRun(self.name, None, {}, "BLOCKED", replay.diagnostics)
        metrics = QuantStatsAdapter().metrics(pd.Series(returns_of(replay.result)))
        return EngineRun(
            self.name,
            replay.result,
            metrics,
            "COMPUTED",
            ("execution_fills are owned by alphamosaic-paper-replay",),
        )
