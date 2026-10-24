"""Reproducible, long-only paper replay contracts."""

import math
from datetime import UTC, date, datetime
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from alphamosaic.core.contracts import Contract, CorporateAction, HistoricalBar, SecurityIdentity


class DatedSignal(Contract):
    symbol: str
    known_at: datetime
    source: str
    evidence_id: str
    value: float
    metric: Literal["quality", "value", "ai_rating", "consensus"]
    pit_verified: bool = False
    data_quality: str = "MISSING"
    license_scope: str = "NOT_VERIFIED"
    valid_until: datetime

    @field_validator("known_at", "valid_until")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("aware timestamp required")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def chronology(self) -> Self:
        if self.valid_until < self.known_at:
            raise ValueError("signal validity before availability")
        return self


class ReplayDataset(Contract):
    bars: dict[str, list[HistoricalBar]]
    identities: dict[str, SecurityIdentity]
    actions: list[CorporateAction] = Field(default_factory=list)
    signals: list[DatedSignal] = Field(default_factory=list)
    cutoff: datetime
    mode: Literal["STRICT_PIT", "RECONSTRUCTED_DIAGNOSTIC"] = "STRICT_PIT"
    historical_universe_verified: bool = False
    corporate_actions_complete: bool = False

    @field_validator("cutoff")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("aware cutoff required")
        return value.astimezone(UTC)


class ReplayConfig(Contract):
    initial_cash: float = Field(default=100_000, gt=0)
    fee_bps: float = Field(default=10, ge=0, le=1000)
    slippage_bps: float = Field(default=5, ge=0, le=1000)
    spread_bps: float = Field(default=0, ge=0, le=1000)
    order_delay_sessions: int = Field(default=1, ge=1, le=20)
    lot_size: int = Field(default=1, ge=1, le=1000)
    max_single_weight: float = Field(default=1, gt=0, le=1)
    max_gross_exposure: float = Field(default=1, gt=0, le=1)
    min_cash_buffer: float = Field(default=0, ge=0, lt=1)
    max_turnover: float = Field(default=2, gt=0, le=2)
    volatility_target: float = Field(default=0.15, gt=0, le=1)
    max_positions: int = Field(default=10, ge=1, le=100)
    max_volume_fraction: float = Field(default=0.01, gt=0, le=1)
    lookback: int = Field(default=63, ge=20, le=252)
    rebalance_sessions: int = Field(default=21, ge=1, le=252)
    seed: int = 42


def preset_config(name: str) -> ReplayConfig:
    """Explicit scenario defaults; zero costs are only a control experiment."""
    if name == "zero":
        return ReplayConfig(fee_bps=0, slippage_bps=0, spread_bps=0)
    if name == "realistic":
        return ReplayConfig(fee_bps=10, slippage_bps=5, spread_bps=2, min_cash_buffer=0.02)
    if name == "stress":
        return ReplayConfig(
            fee_bps=25,
            slippage_bps=25,
            spread_bps=10,
            min_cash_buffer=0.05,
            max_volume_fraction=0.005,
        )
    raise ValueError("unknown cost scenario")


class TargetAllocation(Contract):
    decision_at: datetime
    weights: dict[str, float]
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid(self) -> Self:
        if self.decision_at.tzinfo is None or any(
            not math.isfinite(w) or w <= 0 for w in self.weights.values()
        ):
            raise ValueError("aware time and long-only weights required")
        if sum(self.weights.values()) > 1 + 1e-10:
            raise ValueError("cash-funded allocation required")
        return self


class Fill(Contract):
    session: date
    symbol: str
    quantity: float
    price: float
    fee: float
    slippage_cost: float
    spread_cost: float = 0
    order_id: str = ""
    fill_id: str = ""
    filled_at: datetime | None = None


class SignalEvent(Contract):
    signal_id: str
    observation_at: datetime
    generated_at: datetime
    weights: dict[str, float]
    evidence_ids: list[str] = Field(default_factory=list)


class OrderEvent(Contract):
    order_id: str
    signal_id: str
    submitted_at: datetime
    eligible_at: datetime
    symbol: str
    quantity: float


class CashEntry(Contract):
    event_id: str
    at: datetime
    kind: Literal["FILL", "DIVIDEND"]
    symbol: str
    amount: float
    balance: float


class OrderAdjustment(Contract):
    order_id: str
    action_reference: str
    at: datetime
    previous_quantity: float
    adjusted_quantity: float


class LedgerEvent(Contract):
    event_id: str
    at: datetime
    kind: Literal["MARKET", "SIGNAL", "ORDER", "FILL", "CORPORATE_ACTION", "PORTFOLIO"]
    reference: str
    cash: float
    positions: dict[str, float]


class EquityPoint(Contract):
    session: date
    nav: float
    cash: float
    positions: dict[str, float]
    average_costs: dict[str, float] = Field(default_factory=dict)
    market_values: dict[str, float] = Field(default_factory=dict)


class ReplayResult(Contract):
    strategy: str
    kind: Literal["HISTORICAL", "OUT_OF_SAMPLE"]
    acceptance: Literal["FIXTURE", "REAL_RECONSTRUCTED", "REAL_PIT"]
    config: ReplayConfig
    equity: list[EquityPoint]
    fills: list[Fill]
    unfilled_orders: list[dict[str, str | float]]
    applied_actions: list[str]
    turnover: float
    fees: float
    slippage_cost: float
    spread_cost: float = 0
    signals: list[SignalEvent] = Field(default_factory=list)
    orders: list[OrderEvent] = Field(default_factory=list)
    order_adjustments: list[OrderAdjustment] = Field(default_factory=list)
    events: list[LedgerEvent] = Field(default_factory=list)
    cash_ledger: list[CashEntry] = Field(default_factory=list)
    metrics: dict[str, float | None] = Field(default_factory=dict)
    benchmarks: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    diagnostics: list[str]
    validated_alpha: Literal[False] = False
    broker_enabled: Literal[False] = False
