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
    NOT_CONFIGURED = "NOT_CONFIGURED"
    RATE_LIMITED = "RATE_LIMITED"


class ResearchJobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


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
    lifecycle: dict[str, str] = Field(default_factory=dict)
    last_test: dict[str, str] = Field(default_factory=dict)
    installed: bool = False
    configured: bool = False
    connected: bool = False
    data_validated: bool = False
    research_ready: bool = False
    last_test_at: datetime | None = None
    last_test_status: Status | None = None


class DanelfinScore(Contract):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,14}$")
    score: float = Field(ge=1, le=10)
    technical_score: float | None = Field(default=None, ge=1, le=10)
    fundamental_score: float | None = Field(default=None, ge=1, le=10)
    sentiment_score: float | None = Field(default=None, ge=1, le=10)
    low_risk_score: float | None = Field(default=None, ge=1, le=10)
    rating_date: date
    observed_at: datetime
    known_at: datetime
    valid_until: datetime | None = None
    source_url: str
    evidence_ids: list[str] = Field(default_factory=list)
    identity_verified: bool = False
    diagnostics: list[str] = Field(default_factory=list)


class SignalObservation(Evidence):
    factor: str
    value: float | None
    methodology: str
    validated_predictive_probability: bool = False


class DanelfinScoreObservation(SignalObservation):
    """Strict, point-in-time representation of a Danelfin score response."""

    ai_score: float = Field(ge=1, le=10)
    sub_scores: dict[str, float | None] = Field(default_factory=dict)
    score_date: date
    valid_until: datetime
    identity_match: bool
    capability: Literal["STOCK_SCORE", "ETF_SCORE", "SCORE_HISTORY"]
    response_id: str | None = None
    content_fingerprint: str

    @model_validator(mode="after")
    def validity(self) -> Self:
        if self.valid_until is not None and self.valid_until < self.known_at:
            raise ValueError("score validity ends before it is known")
        if self.score_date > self.as_of.date():
            raise ValueError("rating date is after research cutoff")
        for name, value in self.sub_scores.items():
            if value is not None and not 1 <= value <= 10:
                raise ValueError(f"sub-score {name} must be between 1 and 10")
        return self


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
    archetypes: list[str] = Field(default_factory=list)


class ResearchVerdict(Evidence):
    verdict: Literal[
        "BULLISH",
        "BEARISH",
        "NEUTRAL",
        "CONFLICTED",
        "REVIEW",
        "INSUFFICIENT_EVIDENCE",
        "BLOCKED",
    ]
    rationale: list[str]
    validated_alpha: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    time_horizon: str | None = None
    investment_thesis: list[str] = Field(default_factory=list)
    counterarguments: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    model_information: dict[str, str] = Field(default_factory=dict)
    cost_usd: float | None = Field(default=None, ge=0)


class ResearchOutcome(Contract):
    symbol: str
    status: Status
    verdict: ResearchVerdict | None = None
    source: str
    cost_profile: Literal["FAST", "BALANCED", "DEEP"] | None = None
    diagnostics: list[str] = Field(default_factory=list)
    requested_at: datetime
    completed_at: datetime
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    danelfin_score: DanelfinScore | None = None
    observation: DanelfinScoreObservation | None = None
    execution: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class SignalDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class FusionSignal(Contract):
    source: str
    symbol: str
    direction: SignalDirection
    strength: float | None = Field(default=None, ge=0, le=1)
    horizon: str | None = None
    reliability: float | None = Field(default=None, ge=0, le=1)
    data_quality: DataQuality
    evidence_ids: list[str] = Field(default_factory=list)
    observed_at: datetime
    known_at: datetime
    rationale: list[str] = Field(default_factory=list)
    dependency_keys: list[str] = Field(default_factory=list)
    content_fingerprint: str | None = None
    derived_from: list[str] = Field(default_factory=list)


class FusedSignal(Contract):
    symbol: str
    direction: SignalDirection
    research_confidence: float | None = Field(default=None, ge=0, le=1)
    rationale: list[str]
    conflicts: list[str]
    sources: list[str]
    horizon: str | None = None
    risk_flags: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    price_plan: dict[str, float | str] | None = None


class IntegrationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    READY_UNCONFIGURED = "READY_UNCONFIGURED"
    EXPERIMENTAL = "EXPERIMENTAL"
    LICENSE_BLOCKED = "LICENSE_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"
    DEPRECATED = "DEPRECATED"


class IntegrationRecord(Contract):
    name: str
    official_url: str
    version: str | None
    license: str | None
    interface: str
    authentication: str
    runtime_cost: str
    data_limits: str
    capabilities: list[str]
    status: IntegrationStatus
    connection_status: Status
    test_status: str
    diagnostics: list[str] = Field(default_factory=list)


class ResearchDecision(Contract):
    symbol: str
    candidate_reason: list[str]
    upside_drivers: list[str]
    fundamental_support: str
    valuation_view: str
    trend_view: str
    catalysts: list[str]
    downside_risks: list[str]
    invalidation_conditions: list[str]
    action: Literal["OBSERVE", "DEEP_RESEARCH", "AVOID"]
    trigger_conditions: list[str]
    entry_reference_price: float | None = None
    entry_trigger: float | None = None
    invalidation_level: float | None = None
    risk_budget: float | None = Field(default=None, ge=0, le=1)
    holding_horizon: str | None = None
    fused_signal: FusedSignal
    outcomes: list[ResearchOutcome]
    broker_enabled: Literal[False] = False


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


class ResearchJob(Contract):
    job_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    status: ResearchJobStatus
    created_at: datetime
    cutoff: datetime
    progress: float = Field(ge=0, le=1)
    completed_at: datetime | None = None
    result_ref: str | None = None
    provider_status: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    request_fingerprint: str | None = None


class OpportunityArchetype(StrEnum):
    QUALITY_GROWTH = "QUALITY_GROWTH"
    EARNINGS_REVISION = "EARNINGS_REVISION"
    VALUATION_DISLOCATION = "VALUATION_DISLOCATION"
    MOMENTUM_BREAKOUT = "MOMENTUM_BREAKOUT"
    EVENT_CATALYST = "EVENT_CATALYST"
    MEAN_REVERSION = "MEAN_REVERSION"


class OpportunityArchetypeSpec(Contract):
    archetype: OpportunityArchetype
    suitable_regimes: list[str]
    required_data: list[str]
    prerequisites: list[str]
    failure_risks: list[str]
    typical_holding_period: str
    default_priority: Literal["HIGH", "NORMAL", "LOW"]


class OpportunitySummary(Contract):
    symbol: str
    initial_rank: int
    deep_rank: int | None = None
    archetypes: list[OpportunityArchetype]
    business_drivers: list[str]
    thesis: list[str]
    expectations: list[str]
    overlooked_factors: list[str]
    valuation_risks: list[str]
    catalysts: list[str]
    trend_view: str
    scenarios: dict[str, str]
    holding_period: str
    invalidation_conditions: list[str]
    observation_range: str
    evidence_ids: list[str]
    provider_statuses: dict[str, Status]
    no_action_reasons: list[str] = Field(default_factory=list)
    rerank_reason: str | None = None


class OpportunityPipelineReport(Contract):
    run_id: str
    mode: Literal["FAST", "DEEP"]
    started_at: datetime
    completed_at: datetime
    cutoff: datetime
    universe_name: str
    universe_source: str
    universe_count: int = Field(ge=0)
    data_success_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    preliminary_candidate_count: int = Field(ge=0)
    deep_research_count: int = Field(ge=0)
    elapsed_seconds: float = Field(ge=0)
    initial_run_id: str
    initial_cutoff: datetime
    summaries: list[OpportunitySummary]
    provider_health: list[ProviderHealth]
    warnings: list[str]
    final_status: Literal["READY", "DEGRADED", "NO_ACTION"]
    broker_enabled: Literal[False] = False
