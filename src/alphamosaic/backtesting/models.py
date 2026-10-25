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


class WeeklyStrategyParameters(Contract):
    lookback_weeks: int = Field(default=12, ge=2, le=104)
    trend_short_weeks: int = Field(default=4, ge=2, le=103)
    trend_long_weeks: int = Field(default=12, ge=3, le=104)

    @model_validator(mode="after")
    def windows(self) -> Self:
        if self.trend_short_weeks >= self.trend_long_weeks:
            raise ValueError("weekly trend short window must precede long window")
        return self


class ReplayConfig(Contract):
    accounting_schema_version: Literal[1, 2] = 1
    dividend_accounting: Literal["LEGACY_EX_DATE_CASH", "PAY_DATE_RECEIVABLE"] = "LEGACY_EX_DATE_CASH"
    payment_availability: Literal["NEXT_XNYS_OPEN_AFTER_PAY_DATE"] = "NEXT_XNYS_OPEN_AFTER_PAY_DATE"
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
    decision_frequency: Literal["DAILY", "WEEKLY"] = "DAILY"
    weekly_parameters: WeeklyStrategyParameters = Field(default_factory=WeeklyStrategyParameters)
    seed: int = 42

    @model_validator(mode="after")
    def accounting_model(self) -> Self:
        expected = "LEGACY_EX_DATE_CASH" if self.accounting_schema_version == 1 else "PAY_DATE_RECEIVABLE"
        if self.dividend_accounting != expected:
            raise ValueError("accounting schema and dividend model are contradictory")
        return self


def payment_replay_config(**kwargs: object) -> ReplayConfig:
    """New research uses explicit payment accounting; missing old fields stay legacy."""
    if {"accounting_schema_version", "dividend_accounting", "payment_availability"} & kwargs.keys():
        raise ValueError("payment configuration model cannot be overridden")
    return ReplayConfig.model_validate({"accounting_schema_version": 2,
        "dividend_accounting": "PAY_DATE_RECEIVABLE", **kwargs})


def dividend_accounting_signature(config: ReplayConfig) -> tuple[int, str, str]:
    """Resolve the declared balance-sheet and dividend availability conventions."""
    validated = ReplayConfig.model_validate(config.model_dump())
    return validated.accounting_schema_version, validated.dividend_accounting, validated.payment_availability


def preset_config(name: str) -> ReplayConfig:
    """Explicit scenario defaults; zero costs are only a control experiment."""
    if name == "zero":
        return payment_replay_config(fee_bps=0, slippage_bps=0, spread_bps=0)
    if name == "realistic":
        return payment_replay_config(fee_bps=10, slippage_bps=5, spread_bps=2, min_cash_buffer=0.02)
    if name == "stress":
        return payment_replay_config(
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
    kind: Literal["FILL", "DIVIDEND", "DIVIDEND_PAYMENT"]
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
    kind: Literal["MARKET", "SIGNAL", "ORDER", "FILL", "CORPORATE_ACTION", "PORTFOLIO", "DIVIDEND_PAYMENT"]
    reference: str
    cash: float
    positions: dict[str, float]
    receivables: dict[str, float] = Field(default_factory=dict)


class EquityPoint(Contract):
    session: date
    nav: float
    cash: float
    positions: dict[str, float]
    average_costs: dict[str, float] = Field(default_factory=dict)
    market_values: dict[str, float] = Field(default_factory=dict)
    receivables: dict[str, float] = Field(default_factory=dict)


class DividendEntitlement(Contract):
    entitlement_id: str
    action_reference: str
    source_action_id: str
    symbol: str
    ex_date: date
    payment_date: date
    accrued_at: datetime
    entitled_quantity: float = Field(ge=0)
    cash_per_share: float = Field(ge=0)
    amount: float = Field(ge=0)
    available_at: datetime | None = None
    schedule_status: Literal["SCHEDULED", "AFTER_EVALUATION_END"]

    @field_validator("accrued_at", "available_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("aware dividend timestamp required")
            return value.astimezone(UTC)
        return value

    @model_validator(mode="after")
    def chronology(self) -> Self:
        if self.payment_date < self.ex_date or self.accrued_at.date() != self.ex_date:
            raise ValueError("invalid ordinary dividend dates")
        if (self.schedule_status == "SCHEDULED") != (self.available_at is not None):
            raise ValueError("dividend schedule status and availability disagree")
        if self.available_at is not None and self.available_at <= self.accrued_at:
            raise ValueError("dividend payment availability must follow accrual")
        return self


class DividendPayment(Contract):
    payment_id: str
    entitlement_id: str
    action_reference: str
    symbol: str
    at: datetime
    amount: float = Field(gt=0)

    @field_validator("at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("aware dividend payment timestamp required")
        return value.astimezone(UTC)


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
    dividend_entitlements: list[DividendEntitlement] = Field(default_factory=list)
    dividend_payments: list[DividendPayment] = Field(default_factory=list)
    metrics: dict[str, float | None] = Field(default_factory=dict)
    benchmarks: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    diagnostics: list[str]
    validated_alpha: Literal[False] = False
    broker_enabled: Literal[False] = False
