"""Stable contracts for optional research and backtest engines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset, ReplayResult
from alphamosaic.backtesting.strategies import Strategy


@dataclass(frozen=True)
class EngineHealth:
    name: str
    adapter_present: bool
    dependency_installed: bool
    engine_started: bool
    computation_succeeded: bool
    validation_passed: bool
    status: str
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngineRun:
    engine: str
    result: ReplayResult | None
    metrics: dict[str, float | None]
    status: str
    diagnostics: tuple[str, ...] = ()


class BacktestEngineAdapter(Protocol):
    """Execution/analytics boundary shared by optional engines.

    An adapter must state whether it executes orders. Analytics-only adapters
    return ``execution_engine=False`` in ``health`` and never imply fills.
    """

    name: str
    execution_engine: bool

    def health(self) -> EngineHealth: ...

    def run(
        self,
        data: ReplayDataset,
        strategy: Strategy,
        strategy_name: str,
        config: ReplayConfig,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> EngineRun: ...


def engine_health_dict(health: EngineHealth) -> dict[str, Any]:
    return {
        "name": health.name,
        "adapter_present": health.adapter_present,
        "dependency_installed": health.dependency_installed,
        "engine_started": health.engine_started,
        "computation_succeeded": health.computation_succeeded,
        "validation_passed": health.validation_passed,
        "status": health.status,
        "diagnostics": list(health.diagnostics),
    }
