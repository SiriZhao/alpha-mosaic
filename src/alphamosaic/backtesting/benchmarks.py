"""Deterministic paper benchmark references.

This module deliberately keeps cash outside the market-data universe. The
equal-weight reference delegates fills, actions and accounting to the canonical
paper replay engine with a frozen target allocation.
"""

from datetime import date
from typing import Any

from alphamosaic.backtesting.models import (
    ReplayConfig,
    ReplayDataset,
    ReplayResult,
    TargetAllocation,
)
from alphamosaic.backtesting.replay import PaperReplayEngine, validate_dataset
from alphamosaic.core.benchmark_contracts import BenchmarkPoint, BenchmarkReference, BenchmarkSpecV1


class _FrozenEqualWeightStrategy:
    def __init__(self, symbols: tuple[str, ...], weights: dict[str, float]) -> None:
        self._symbols = symbols
        self._weights = weights

    def allocation(self, history: Any, signals: Any, at: Any, config: ReplayConfig) -> TargetAllocation:
        if tuple(history) != self._symbols:
            raise ValueError("equal-weight universe changed during replay")
        return TargetAllocation(decision_at=at, weights=dict(self._weights))


def cash_zero_interest(
    sessions: tuple[date, ...] | list[date],
    *,
    initial_cash: float = 100_000,
    replay_config: ReplayConfig | None = None,
    name: str = "cash_zero_interest",
) -> BenchmarkSpecV1:
    """Create a constant zero-interest cash reference on an explicit session grid."""

    config = replay_config or ReplayConfig(initial_cash=initial_cash)
    if config.initial_cash != initial_cash:
        raise ValueError("cash benchmark initial_cash conflicts with replay_config")
    return BenchmarkSpecV1(
        kind="CASH_ZERO_INTEREST",
        name=name,
        initial_cash=initial_cash,
        sessions=tuple(sessions),
        replay_config=config,
    )


def equal_weight(
    symbols: tuple[str, ...] | list[str],
    sessions: tuple[date, ...] | list[date],
    *,
    initial_cash: float = 100_000,
    replay_config: ReplayConfig | None = None,
    name: str = "equal_weight",
) -> BenchmarkSpecV1:
    """Create a frozen equal-weight benchmark declaration."""

    frozen_symbols = tuple(symbols)
    config = replay_config or ReplayConfig(initial_cash=initial_cash)
    if config.initial_cash != initial_cash:
        raise ValueError("equal-weight benchmark initial_cash conflicts with replay_config")
    weights = {symbol: 1 / len(frozen_symbols) for symbol in frozen_symbols} if frozen_symbols else {}
    return BenchmarkSpecV1(
        kind="EQUAL_WEIGHT",
        name=name,
        initial_cash=initial_cash,
        sessions=tuple(sessions),
        symbols=frozen_symbols,
        weights=weights,
        replay_config=config,
    )


def _cash_reference(spec: BenchmarkSpecV1) -> BenchmarkReference:
    points = tuple(
        BenchmarkPoint(
            session=session,
            nav=spec.initial_cash,
            cash=spec.initial_cash,
            return_value=None if index == 0 else 0.0,
        )
        for index, session in enumerate(spec.sessions)
    )
    return BenchmarkReference(
        spec=spec,
        points=points,
        metrics={"beta": None, "alpha": None, "correlation": None},
        diagnostics=("MODEL_ASSUMPTION_ZERO_INTEREST_CASH",),
    )


def _result_points(result: ReplayResult) -> tuple[BenchmarkPoint, ...]:
    previous: float | None = None
    points: list[BenchmarkPoint] = []
    for point in result.equity:
        change = None if previous is None else point.nav / previous - 1
        points.append(
            BenchmarkPoint(
                session=point.session,
                nav=point.nav,
                cash=point.cash,
                positions=point.positions,
                return_value=change,
            )
        )
        previous = point.nav
    return tuple(points)


def run_benchmark(spec: BenchmarkSpecV1, data: ReplayDataset | None = None) -> BenchmarkReference:
    """Run a typed benchmark without broker access or synthetic market data."""

    spec = BenchmarkSpecV1.model_validate(spec.model_dump())
    if spec.kind == "CASH_ZERO_INTEREST":
        if data is not None:
            raise ValueError("cash benchmark does not consume market bars")
        return _cash_reference(spec)
    if data is None:
        raise ValueError("equal-weight benchmark requires a replay dataset")
    if set(data.bars) != set(spec.symbols):
        raise ValueError("equal-weight benchmark refuses universe truncation or expansion")
    if any(symbol.upper() == "CASH" for symbol in data.bars):
        raise ValueError("CASH is not a security symbol")
    sessions = tuple(next(iter(data.bars.values()))[i].session for i in range(len(next(iter(data.bars.values())))))
    if sessions != spec.sessions:
        raise ValueError("equal-weight benchmark requires the exact qualified session grid")
    validate_dataset(data)
    strategy = _FrozenEqualWeightStrategy(spec.symbols, spec.weights)
    result = PaperReplayEngine().run(
        data,
        strategy,
        "equal_weight",
        spec.replay_config,
        schedule_policy=spec.schedule_policy,
    )
    if tuple(point.session for point in result.equity) != spec.sessions:
        raise ValueError("replay did not produce the exact qualified session grid")
    return BenchmarkReference(
        spec=spec,
        replay_result=result,
        points=_result_points(result),
        metrics={"beta": None, "alpha": None, "correlation": None},
        diagnostics=tuple(result.diagnostics),
    )


def build_benchmark(spec: BenchmarkSpecV1, data: ReplayDataset | None = None) -> BenchmarkReference:
    """Compatibility alias for :func:`run_benchmark`."""

    return run_benchmark(spec, data)
