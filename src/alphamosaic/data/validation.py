"""Fail-closed normalization and exchange-calendar freshness."""

from datetime import date, datetime

import exchange_calendars as xcals

from alphamosaic.core.contracts import HistoricalBar, SecurityIdentity


def completed_session(cutoff: datetime) -> date:
    calendar = xcals.get_calendar("XNYS")
    session = calendar.date_to_session(cutoff.date(), direction="previous")
    if calendar.session_close(session).to_pydatetime() > cutoff:
        session = calendar.previous_session(session)
    return session.date()


def market_state(cutoff: datetime) -> str:
    calendar = xcals.get_calendar("XNYS")
    return "OPEN" if calendar.is_open_on_minute(cutoff.replace(second=0, microsecond=0)) else "CLOSED"


def validate_batch(
    identity: SecurityIdentity | None, bars: list[HistoricalBar], cutoff: datetime
) -> list[str]:
    flags: list[str] = []
    if identity is None or not identity.identity_verified:
        flags.append("IDENTITY_NOT_VERIFIED")
    elif not identity.active or identity.exchange.upper().split("-")[0] not in {
        "NASDAQ", "NYSE", "AMEX", "NYSEARCA"
    }:
        flags.append("INACTIVE_OR_UNSUPPORTED_EXCHANGE")
    elif identity.currency != "USD":
        flags.append("UNSUPPORTED_CURRENCY")
    if identity is not None and identity.as_of > cutoff:
        flags.append("FUTURE_IDENTITY")
    if not bars:
        return flags + ["EMPTY_HISTORY"]
    if any(bar.volume is None for bar in bars):
        flags.append("MISSING_VOLUME")
    sessions = [bar.session for bar in bars]
    if len(sessions) != len(set(sessions)):
        flags.append("DUPLICATE_SESSIONS")
    if sessions != sorted(sessions):
        flags.append("UNSORTED_SESSIONS")
    if any(bar.known_at > cutoff or bar.observed_at > cutoff for bar in bars):
        flags.append("FUTURE_INFORMATION")
    if identity is not None and any(
        bar.symbol != identity.symbol or bar.currency != identity.currency for bar in bars
    ):
        flags.append("SECURITY_IDENTITY_MISMATCH")
    if len({bar.adjustment_policy for bar in bars}) != 1:
        flags.append("MIXED_ADJUSTMENT_POLICY")
    if len({bar.data_quality for bar in bars}) != 1:
        flags.append("MIXED_DATA_QUALITY")
    calendar = xcals.get_calendar("XNYS")
    if any(not calendar.is_session(day) for day in sessions):
        flags.append("NON_SESSION_BAR")
    if sessions[-1] < completed_session(cutoff):
        flags.append("STALE_HISTORY")
    if len(bars) < 65:
        flags.append("INSUFFICIENT_HISTORY")
    return flags
