"""Typed, versioned benchmark specifications.

Benchmarks are paper references only. Cash is an explicit model assumption,
never a fabricated market bar or a magic ``CASH`` ticker.
"""

from datetime import date
from typing import Literal, Self

import exchange_calendars as xcals
from pydantic import Field, model_validator

from alphamosaic.backtesting.models import ReplayConfig, ReplayResult
from alphamosaic.core.contracts import Contract

BenchmarkKind = Literal["CASH_ZERO_INTEREST", "EQUAL_WEIGHT"]
SchedulePolicy = Literal["FIRST_ELIGIBLE_OPEN_THEN_INTERVAL"]


class BenchmarkSpecV1(Contract):
    """A complete benchmark declaration, frozen before a replay starts."""

    schema_version: Literal[1] = 1
    kind: BenchmarkKind
    name: str = Field(min_length=1)
    currency: Literal["USD"] = "USD"
    initial_cash: float = Field(gt=0)
    sessions: tuple[date, ...] = Field(min_length=2)
    replay_config: ReplayConfig = Field(default_factory=ReplayConfig)
    schedule_policy: SchedulePolicy = "FIRST_ELIGIBLE_OPEN_THEN_INTERVAL"
    symbols: tuple[str, ...] = ()
    weights: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_spec(self) -> Self:
        if tuple(sorted(set(self.sessions))) != self.sessions:
            raise ValueError("benchmark sessions must be unique and chronological")
        if any(not xcals.get_calendar("XNYS").is_session(session) for session in self.sessions):
            raise ValueError("benchmark sessions must be valid XNYS sessions")
        if self.initial_cash != self.replay_config.initial_cash:
            raise ValueError("benchmark initial_cash must match replay_config.initial_cash")
        if self.kind == "CASH_ZERO_INTEREST":
            if self.symbols or self.weights:
                raise ValueError("cash benchmark cannot declare symbols or weights")
        else:
            if not self.symbols:
                raise ValueError("equal-weight benchmark requires explicit symbols")
            if any(symbol.upper() == "CASH" for symbol in self.symbols):
                raise ValueError("CASH is not a security symbol")
            if len(set(self.symbols)) != len(self.symbols):
                raise ValueError("equal-weight symbols must be unique")
            expected = {symbol: 1 / len(self.symbols) for symbol in self.symbols}
            if self.weights != expected:
                raise ValueError("equal-weight benchmark must freeze explicit equal weights")
            config = self.replay_config
            if config.decision_frequency != "DAILY":
                raise ValueError("equal-weight benchmark requires DAILY decisions")
            if config.max_positions < len(self.symbols):
                raise ValueError("max_positions truncates the equal-weight universe")
            if config.max_single_weight + 1e-12 < 1 / len(self.symbols):
                raise ValueError("max_single_weight conflicts with equal weights")
            if config.max_gross_exposure + 1e-12 < 1:
                raise ValueError("max_gross_exposure conflicts with equal weights")
            if config.min_cash_buffer > 1e-12:
                raise ValueError("min_cash_buffer truncates the equal-weight allocation")
        return self


class BenchmarkPoint(Contract):
    session: date
    nav: float = Field(gt=0)
    cash: float = Field(ge=0)
    positions: dict[str, float] = Field(default_factory=dict)
    return_value: float | None = None


class BenchmarkReference(Contract):
    """Immutable benchmark output with explicitly nullable analytics."""

    spec: BenchmarkSpecV1
    replay_result: ReplayResult | None = None
    points: tuple[BenchmarkPoint, ...]
    metrics: dict[str, float | None] = Field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()
