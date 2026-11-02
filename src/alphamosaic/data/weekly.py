"""Causal XNYS natural-week views; these are never daily execution bars."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Literal, Self

import exchange_calendars as xcals
from pydantic import Field, field_validator, model_validator

from alphamosaic.backtesting.models import ReplayDataset
from alphamosaic.core.contracts import (
    Contract,
    CorporateAction,
    DataQuality,
    HistoricalBar,
    SecurityIdentity,
)


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("aware UTC-compatible cutoff required")
    return value.astimezone(UTC)


def week_start(day: date) -> date:
    """Monday label for the exchange session's civil week."""
    return day - timedelta(days=day.weekday())


def sessions_of_week(day: date) -> tuple[date, ...]:
    calendar = xcals.get_calendar("XNYS")
    monday = week_start(day)
    return tuple(s.date() for s in calendar.sessions_in_range(monday, monday + timedelta(days=4)))


def last_session_of_week(day: date) -> date:
    sessions = sessions_of_week(day)
    if not sessions:
        raise ValueError("week contains no exchange sessions")
    return sessions[-1]


def is_week_close(day: date) -> bool:
    """Good Friday/Thanksgiving and other holiday weeks use actual XNYS sessions."""
    return day == last_session_of_week(day)


class ExcludedWeek(Contract):
    week_start: date
    reason: Literal["PARTIAL_BOUNDARY_WEEK", "WEEK_NOT_CLOSED_AT_CUTOFF", "DATA_NOT_AVAILABLE_AT_CUTOFF"]
    observed_sessions: list[date]
    expected_sessions: list[date]


class WeeklyBar(Contract):
    symbol: str
    week_start: date
    first_session: date
    last_session: date
    session_count: int = Field(gt=0, le=5)
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float | None = Field(default=None, ge=0)
    observed_at: datetime
    available_at: datetime
    as_of: datetime
    source: str
    source_url: str
    source_versions: list[str]
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    currency: Literal["USD"] = "USD"
    adjustment_policy: Literal["RAW", "SPLIT", "TOTAL_RETURN", "UNKNOWN"]
    data_quality: DataQuality
    pit_status: Literal["VERIFIED", "RECONSTRUCTED", "NOT_APPLICABLE"]
    license_scope: str
    frequency: Literal["WEEKLY_XNYS"] = "WEEKLY_XNYS"

    @field_validator("observed_at", "available_at", "as_of")
    @classmethod
    def timestamps(cls, value: datetime) -> datetime:
        return aware_utc(value)

    @model_validator(mode="after")
    def valid(self) -> Self:
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("invalid weekly OHLC envelope")
        if not self.first_session <= self.last_session or self.week_start != week_start(self.first_session):
            raise ValueError("invalid weekly sessions")
        if not self.observed_at <= self.available_at <= self.as_of:
            raise ValueError("weekly availability chronology invalid")
        return self


class WeeklySeries(Contract):
    bars: list[WeeklyBar]
    excluded_weeks: list[ExcludedWeek]
    warnings: list[str]
    cutoff: datetime
    frequency: Literal["WEEKLY_XNYS"] = "WEEKLY_XNYS"


class WeeklyDataset(Contract):
    bars: dict[str, list[WeeklyBar]]
    identities: dict[str, SecurityIdentity]
    excluded_weeks: dict[str, list[ExcludedWeek]]
    warnings: list[str]
    cutoff: datetime
    mode: Literal["STRICT_PIT", "RECONSTRUCTED_DIAGNOSTIC"]
    historical_universe_verified: bool
    corporate_actions_complete: bool
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    calendar: Literal["XNYS"] = "XNYS"
    frequency: Literal["WEEKLY_XNYS"] = "WEEKLY_XNYS"
    periods_per_year: Literal[52] = 52


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def aggregate_weekly_bars(
    bars: Sequence[HistoricalBar],
    *,
    cutoff: datetime,
    actions: Sequence[CorporateAction] = (),
) -> WeeklySeries:
    """Aggregate complete available natural weeks without filling or repairing input.

    Boundary partial weeks are excluded explicitly. Missing interior exchange sessions,
    mixed provenance and RAW corporate-action price discontinuities are rejected.
    Volume is a sum of supplied daily volume, not opening liquidity or capacity.
    """
    cutoff = aware_utc(cutoff)
    calendar = xcals.get_calendar("XNYS")
    selected: list[HistoricalBar] = []
    for supplied in bars:
        # Future session contents have no authority over an already completed view.
        if supplied.session > cutoff.date():
            continue
        if not calendar.is_session(supplied.session):
            raise ValueError("weekly input contains a non-session date")
        close_at = calendar.session_close(supplied.session).to_pydatetime()
        if close_at <= cutoff:
            bar = HistoricalBar.model_validate(supplied.model_dump())
            if bar.observed_at != close_at or bar.known_at < bar.observed_at:
                raise ValueError("daily observation/availability must follow exchange close")
            selected.append(bar)
    if not selected:
        return WeeklySeries(bars=[], excluded_weeks=[], warnings=["NO_COMPLETED_DAILY_OBSERVATIONS"], cutoff=cutoff)
    dates = [b.session for b in selected]
    expected = [s.date() for s in calendar.sessions_in_range(dates[0], dates[-1])]
    if dates != expected:
        raise ValueError("unique complete chronological daily sessions required for weekly aggregation")
    signatures = {(b.symbol, b.currency, b.source, b.source_url, b.adjustment_policy, b.data_quality, b.pit_status, b.license_scope, b.provenance.get("provider_version", "NOT_REPORTED")) for b in selected}
    if len(signatures) != 1 or selected[0].currency != "USD":
        raise ValueError("mixed weekly identity, currency, provider, version, adjustment or evidence")
    first = selected[0]
    if first.adjustment_policy == "NOT_APPLICABLE" or first.data_quality not in {DataQuality.REAL, DataQuality.HISTORICAL, DataQuality.DELAYED, DataQuality.FIXTURE}:
        raise ValueError("unsupported weekly price evidence")
    for supplied in actions:
        action = CorporateAction.model_validate(supplied.model_dump())
        # A later disclosure cannot make an already affected RAW interval safe.
        # This is a source-qualification rejection, not use of future action values
        # to calculate an adjusted historical signal or profitable execution path.
        if action.symbol == first.symbol and dates[0] <= action.effective_date <= dates[-1] and first.adjustment_policy == "RAW":
            raise ValueError("RAW_CORPORATE_ACTION_REQUIRES_ADJUSTED_RESEARCH_SERIES")
    grouped: dict[date, list[HistoricalBar]] = {}
    for bar in selected:
        grouped.setdefault(week_start(bar.session), []).append(bar)
    output: list[WeeklyBar] = []
    exclusions: list[ExcludedWeek] = []
    warnings = []
    for monday, rows in grouped.items():
        expected_week = sessions_of_week(monday)
        last_close = calendar.session_close(expected_week[-1]).to_pydatetime()
        reason: Literal["PARTIAL_BOUNDARY_WEEK", "WEEK_NOT_CLOSED_AT_CUTOFF", "DATA_NOT_AVAILABLE_AT_CUTOFF"] | None = None
        if last_close > cutoff:
            reason = "WEEK_NOT_CLOSED_AT_CUTOFF"
        elif tuple(b.session for b in rows) != expected_week:
            reason = "PARTIAL_BOUNDARY_WEEK"
        elif any(b.known_at > cutoff for b in rows):
            reason = "DATA_NOT_AVAILABLE_AT_CUTOFF"
        if reason:
            exclusions.append(ExcludedWeek(week_start=monday, reason=reason, observed_sessions=[b.session for b in rows], expected_sessions=list(expected_week)))
            continue
        try:
            volume = None if any(b.volume is None for b in rows) else math.fsum(float(b.volume or 0) for b in rows)
        except OverflowError as exc:
            raise ValueError("non-finite aggregated weekly volume") from exc
        if volume is None:
            warnings.append("MISSING_DAILY_VOLUME_WEEKLY_VOLUME_WITHHELD")
        elif not math.isfinite(volume):
            raise ValueError("non-finite aggregated weekly volume")
        output.append(WeeklyBar(
            symbol=str(first.symbol), week_start=monday, first_session=rows[0].session,
            last_session=rows[-1].session, session_count=len(rows), open=rows[0].open,
            high=max(b.high for b in rows), low=min(b.low for b in rows), close=rows[-1].close,
            volume=volume, observed_at=last_close,
            available_at=max(last_close, *(b.known_at for b in rows)), as_of=cutoff,
            source=first.source, source_url=first.source_url,
            source_versions=[first.provenance.get("provider_version", "NOT_REPORTED")],
            source_hash=_hash([b.model_dump(mode="json") for b in rows]),
            adjustment_policy=first.adjustment_policy, data_quality=first.data_quality,
            pit_status=first.pit_status, license_scope=first.license_scope,
        ))
    if first.pit_status != "VERIFIED":
        warnings.append("RECONSTRUCTED_WEEKLY_VALUES_NOT_CERTIFIED_HISTORICAL_SIGNAL_INPUT")
    if first.adjustment_policy == "UNKNOWN":
        warnings.append("UNKNOWN_WEEKLY_ADJUSTMENT_PRICE_ONLY_DIAGNOSTIC")
    return WeeklySeries(bars=output, excluded_weeks=exclusions, warnings=sorted(set(warnings)), cutoff=cutoff)


def aggregate_weekly(data: ReplayDataset, cutoff: datetime | None = None) -> WeeklyDataset:
    """Versioned-data weekly view, with identity and cross-asset alignment checks."""
    at = aware_utc(data.cutoff if cutoff is None else cutoff)
    if at > aware_utc(data.cutoff):
        raise ValueError("weekly cutoff cannot exceed dataset cutoff")
    if not data.bars:
        raise ValueError("nonempty weekly dataset required")
    result: dict[str, list[WeeklyBar]] = {}
    excluded: dict[str, list[ExcludedWeek]] = {}
    identities: dict[str, SecurityIdentity] = {}
    warnings: list[str] = []
    for symbol, rows in data.bars.items():
        identity = data.identities.get(symbol)
        if identity is None:
            raise ValueError("weekly instrument identity missing")
        identity = SecurityIdentity.model_validate(identity.model_dump())
        if identity.symbol != symbol or identity.currency != "USD" or identity.as_of > at:
            raise ValueError("weekly instrument identity unavailable or mismatched")
        if identity.exchange.upper().split("-")[0] not in {"NASDAQ", "NYSE", "AMEX", "NYSEARCA"}:
            raise ValueError("weekly calendar unsupported for exchange")
        if data.mode == "STRICT_PIT" and (not identity.identity_verified or not identity.active):
            raise ValueError("strict weekly identity not verified")
        view = aggregate_weekly_bars(rows, cutoff=at, actions=data.actions)
        if any(bar.symbol != symbol for bar in view.bars):
            raise ValueError("weekly bar symbol does not match dataset identity")
        result[symbol], excluded[symbol], identities[symbol] = view.bars, view.excluded_weeks, identity
        warnings.extend(view.warnings)
        if data.mode == "STRICT_PIT" and view.bars:
            first_open = xcals.get_calendar("XNYS").session_open(view.bars[0].first_session).to_pydatetime()
            if identity.as_of > first_open:
                raise ValueError("strict weekly historical identity unavailable")
            if any(b.pit_status != "VERIFIED" or b.adjustment_policy == "UNKNOWN" for b in view.bars):
                raise ValueError("strict weekly data requires explicit adjustment and verified PIT")
    alignments = {tuple((b.week_start, b.first_session, b.last_session) for b in rows) for rows in result.values()}
    if len(alignments) != 1:
        raise ValueError("unaligned available weekly asset series")
    qualities = {bar.data_quality for rows in result.values() for bar in rows}
    if DataQuality.FIXTURE in qualities and qualities != {DataQuality.FIXTURE}:
        raise ValueError("fixture and real weekly assets cannot be mixed")
    if data.mode == "STRICT_PIT" and qualities and qualities != {DataQuality.FIXTURE} and (not data.historical_universe_verified or not data.corporate_actions_complete):
        raise ValueError("strict real weekly universe/corporate-action coverage not verified")
    if len({bar.source for rows in result.values() for bar in rows}) > 1:
        warnings.append("MIXED_WEEKLY_ASSET_PROVIDERS_REVIEW_REQUIRED")
    if not data.historical_universe_verified:
        warnings.append("WEEKLY_HISTORICAL_UNIVERSE_NOT_VERIFIED")
    if not data.corporate_actions_complete:
        warnings.append("WEEKLY_CORPORATE_ACTION_COVERAGE_NOT_VERIFIED")
    return WeeklyDataset(bars=result, identities=identities, excluded_weeks=excluded,
        warnings=sorted(set(warnings)), cutoff=at, mode=data.mode,
        historical_universe_verified=data.historical_universe_verified,
        corporate_actions_complete=data.corporate_actions_complete,
        source_hash=_hash({"bars": {symbol: [b.source_hash for b in rows] for symbol, rows in result.items()},
            "identities": {symbol: identity.model_dump(mode="json") for symbol, identity in identities.items()},
            "mode": data.mode, "historical_universe_verified": data.historical_universe_verified,
            "corporate_actions_complete": data.corporate_actions_complete}))
