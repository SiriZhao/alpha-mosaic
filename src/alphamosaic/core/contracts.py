"""Evidence contracts. Missing financial values stay null; timestamps are aware UTC."""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class DataQuality(StrEnum):
    REAL = "REAL"
    DELAYED = "DELAYED"
    HISTORICAL = "HISTORICAL"
    FIXTURE = "FIXTURE"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    MISSING = "MISSING"


class Status(StrEnum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_INSTALLED = "NOT_INSTALLED"
    UNSUPPORTED = "UNSUPPORTED"
    EMPTY = "EMPTY"
    INVALID_DATA = "INVALID_DATA"
    STALE = "STALE"
    QUOTA = "QUOTA"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)


class SecurityIdentity(Contract):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,14}$")
    exchange: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    security_type: Literal["STOCK", "ETF"] = "STOCK"
    active: bool
    identity_source: str
    identity_verified: bool
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone required")
        return value.astimezone(UTC)


class Evidence(Contract):
    symbol: str | None = None
    source: str
    source_url: str
    observed_at: datetime
    published_at: datetime | None = None
    known_at: datetime
    as_of: datetime
    currency: str | None = None
    data_quality: DataQuality
    adjustment_policy: Literal["RAW", "SPLIT", "TOTAL_RETURN", "UNKNOWN", "NOT_APPLICABLE"]
    provenance: dict[str, str]
    license_scope: str
    pit_status: Literal["VERIFIED", "RECONSTRUCTED", "NOT_APPLICABLE"] = "RECONSTRUCTED"

    @field_validator("observed_at", "published_at", "known_at", "as_of")
    @classmethod
    def timestamps(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("timezone required")
            return value.astimezone(UTC)
        return value

    @model_validator(mode="after")
    def chronology(self) -> Self:
        if self.known_at > self.as_of:
            raise ValueError("known_at after as_of: future information")
        if self.published_at is not None and self.published_at > self.known_at:
            raise ValueError("publication after known_at")
        if self.observed_at > self.as_of:
            raise ValueError("observed_at after as_of")
        return self


class MarketObservation(Evidence):
    price: float | None = Field(default=None, gt=0)
    volume: float | None = Field(default=None, ge=0)
    identity: SecurityIdentity


class HistoricalBar(Evidence):
    session: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

    @model_validator(mode="after")
    def ohlc(self) -> Self:
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("invalid OHLC envelope")
        if self.low > self.high or self.session > self.as_of.date():
            raise ValueError("invalid bar date/range")
        return self


class CorporateAction(Evidence):
    action: Literal["SPLIT", "DIVIDEND", "DELISTING", "SYMBOL_CHANGE"]
    effective_date: date
    ratio: float | None = Field(default=None, gt=0)
    cash_amount: float | None = Field(default=None, ge=0)


class CompanyFundamentals(Evidence):
    fiscal_period: date | None = None
    revenue: float | None = None
    net_income: float | None = None
    equity: float | None = None
    debt: float | None = Field(default=None, ge=0)
    market_cap: float | None = Field(default=None, gt=0)
    pe_ratio: float | None = None
    return_on_equity: float | None = None
    missing_fields: list[str] = Field(default_factory=list)


class AnalystEstimate(Evidence):
    period: date
    metric: str
    value: float | None = None
    analyst_count: int | None = Field(default=None, ge=0)


class NewsEvent(Evidence):
    title: str
    event_type: str
    summary: str | None = None


class ProviderEvidence(Evidence):
    endpoint: str
    requested_at: datetime
    completed_at: datetime
    status: Status
    row_count: int = Field(ge=0)
    fields: list[str]
    diagnostics: list[str] = Field(default_factory=list)

    @field_validator("requested_at", "completed_at")
    @classmethod
    def aware_request(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timezone required")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def request_order(self) -> Self:
        if not self.requested_at <= self.completed_at <= self.as_of:
            raise ValueError("invalid request chronology")
        return self


class ProviderHealth(Contract):
    name: str
    status: Status
    checked_at: datetime
    capabilities: list[str]
    diagnostics: list[str]
    version: str | None = None


class SignalObservation(Evidence):
    factor: str
    value: float | None
    methodology: str
    validated_predictive_probability: bool = False


class OpportunityCandidate(Contract):
    ticker: str
    rank: int = Field(ge=1)
    score: float
    factors: dict[str, float | None]
    reasons: list[str]
    risks: list[str]
    data_timestamp: datetime
    source: str
    missing_fields: list[str]
    research_priority: Literal["HIGH", "NORMAL"]
    identity: SecurityIdentity
    data_quality: DataQuality
    score_type: Literal["HEURISTIC_PERCENTILE"] = "HEURISTIC_PERCENTILE"


class ResearchVerdict(Evidence):
    verdict: Literal["REVIEW", "INSUFFICIENT_EVIDENCE", "BLOCKED"]
    rationale: list[str]
    validated_alpha: bool = False


class RiskAssessment(Contract):
    symbol: str
    review_allowed: bool
    flags: list[str]
    maximum_review_weight: float = Field(ge=0, le=1)
    execution_allowed: Literal[False] = False


class DecisionProposal(Contract):
    symbol: str
    action: Literal["RESEARCH", "WATCH", "AVOID"]
    rationale: list[str]
    risk: RiskAssessment
    requires_human_review: Literal[True] = True
    broker_enabled: Literal[False] = False


class BacktestResult(Contract):
    kind: Literal["HISTORICAL", "OUT_OF_SAMPLE", "FORWARD_SIMULATION", "REAL_ACCOUNT"]
    methodology: str
    metrics: dict[str, float | None]
    benchmarks: dict[str, dict[str, float | None]]
    turnover: float = Field(ge=0)
    fees: float = Field(ge=0)
    signal_coverage: float = Field(ge=0, le=1)
    observations: int = Field(ge=0)
    limitations: list[str]
    validated_alpha: Literal[False] = False


class DataBatch(Contract):
    identity: SecurityIdentity | None = None
    bars: list[HistoricalBar] = Field(default_factory=list)
    fundamentals: CompanyFundamentals | None = None
    evidence: list[ProviderEvidence]
    status: Status


class ScanReport(Contract):
    run_id: str
    created_at: datetime
    cutoff: datetime
    status: Status
    universe_name: str
    universe_source: str
    universe_count: int
    eligible_count: int
    candidates: list[OpportunityCandidate]
    research_queue: list[str]
    decisions: list[DecisionProposal]
    evidence: list[ProviderEvidence]
    exclusions: dict[str, list[str]]
    evaluation: BacktestResult | None = None
    acceptance: Literal["REAL_DATA", "FIXTURE"]
    warnings: list[str]
    broker_enabled: Literal[False] = False
