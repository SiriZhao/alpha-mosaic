"""Explicit RAW split-only weekly price hypotheses, never market observations."""

from __future__ import annotations

import math
from datetime import datetime

import exchange_calendars as xcals

from alphamosaic.backtesting.models import ReplayDataset
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar
from alphamosaic.core.weekly_features import AppliedFeatureSplit, DerivedWeeklyClose
from alphamosaic.data.weekly import _hash, aggregate_weekly, aware_utc


def _row_fingerprint(row: HistoricalBar) -> str:
    # Snapshot hashes/as_of and arbitrary provider provenance may contain future
    # rows. Fingerprint this bounded observation, not the enclosing snapshot.
    fields = {key: value for key, value in row.model_dump(mode="json").items()
              if key not in {"provenance", "as_of"}}
    fields["provider_version"] = row.provenance.get("provider_version", "NOT_REPORTED")
    return _hash(fields)


def _split_dependency(action: CorporateAction) -> AppliedFeatureSplit:
    fields = {key: value for key, value in action.model_dump(mode="json").items()
              if key not in {"provenance", "as_of"}}
    fields["provider_version"] = action.provenance.get("provider_version", "NOT_REPORTED")
    return AppliedFeatureSplit(effective_date=action.effective_date, ratio=float(action.ratio or 0),
        source_action_id=action.source_action_id, dependency_fingerprint=_hash(fields))


def derive_raw_weekly_closes(data: ReplayDataset, *, decision_at: datetime) -> dict[str, list[DerivedWeeklyClose]]:
    """Anchor only at the last complete available week; ordinary income is excluded.

    Raw weekly observations are used only to qualify sessions and availability.
    No adjusted HistoricalBar or adjusted observed WeeklyBar is constructed.
    """
    at = aware_utc(decision_at)
    data = ReplayDataset.model_validate(data.model_dump())
    view = aggregate_weekly(data.model_copy(update={"actions": []}), cutoff=at)
    calendar = xcals.get_calendar("XNYS")
    output: dict[str, list[DerivedWeeklyClose]] = {}
    for symbol, weeks in view.bars.items():
        if not weeks:
            output[symbol] = []
            continue
        if any(week.adjustment_policy != "RAW" for week in weeks):
            raise ValueError("RAW split price feature requires RAW parent observations")
        anchor = weeks[-1].last_session
        first = weeks[0].first_session
        relevant = [action for action in data.actions
                    if action.symbol == symbol and first <= action.effective_date <= anchor]
        keys = [(action.action, action.effective_date) for action in relevant]
        ids = [action.source_action_id for action in relevant if action.source_action_id is not None]
        if len(keys) != len(set(keys)) or len(ids) != len(set(ids)):
            raise ValueError("duplicate feature corporate action")
        splits = {action.effective_date for action in relevant if action.action == "SPLIT"}
        for action in relevant:
            if action.action not in {"SPLIT", "DIVIDEND"}:
                raise ValueError("unsupported feature corporate action")
            if (not calendar.is_session(action.effective_date) or action.currency != "USD"
                or action.adjustment_policy != "RAW" or not action.source.strip() or not action.source_url.strip()
                or action.known_at > at or action.known_at > calendar.session_open(action.effective_date).to_pydatetime()
                or action.observed_at > action.known_at):
                raise ValueError("feature action unavailable or invalid at effective open")
            if action.data_quality not in {DataQuality.REAL, DataQuality.HISTORICAL, DataQuality.DELAYED, DataQuality.FIXTURE}:
                raise ValueError("feature action requires observed parent evidence")
            if (action.data_quality == DataQuality.FIXTURE) != (weeks[0].data_quality == DataQuality.FIXTURE):
                raise ValueError("feature action and price evidence cannot mix fixture and observed data")
            if data.mode == "STRICT_PIT" and action.pit_status != "VERIFIED":
                raise ValueError("feature parent action not certified PIT")
            if action.action == "SPLIT" and action.ratio is None:
                raise ValueError("feature split ratio missing")
            if action.action == "DIVIDEND":
                if (action.dividend_type, action.effective_date_role, action.cash_amount_basis) != (
                    "ORDINARY_CASH", "EX_DATE", "EX_DATE_SHARES"
                ) or action.cash_amount is None or action.payment_date is None or action.source_action_id is None:
                    raise ValueError("price-only feature requires qualified ordinary dividend terms")
                if action.payment_date < action.effective_date or action.effective_date in splits:
                    raise ValueError("special/due-bill or same-date split/dividend feature unsupported")
        dependencies = [_split_dependency(action) for action in sorted(relevant,
            key=lambda action: (action.effective_date, action.action)) if action.action == "SPLIT"]
        derived = []
        for week in weeks:
            applied = [split for split in dependencies if week.last_session < split.effective_date <= anchor]
            product = 1.0
            for split in applied:
                product *= split.ratio
                if not math.isfinite(product) or product <= 0:
                    raise ValueError("unrepresentable weekly feature split product")
            close = week.close / product
            if not math.isfinite(close) or close <= 0:
                raise ValueError("unrepresentable weekly feature close")
            fingerprints = [_row_fingerprint(row) for row in data.bars[symbol]
                            if week.first_session <= row.session <= week.last_session]
            payload = dict(symbol=symbol, week_start=week.week_start, last_session=week.last_session,
                close=close, unit_anchor=anchor, policy="RAW_SPLIT_PRICE_ONLY_V1",
                input_row_fingerprints=fingerprints,
                applied_splits=[split.model_dump(mode="json") for split in applied])
            derived.append(DerivedWeeklyClose.model_validate({**payload, "decision_at": at,
                "parent_data_quality": week.data_quality, "parent_pit_status": week.pit_status,
                "dependency_fingerprint": _hash({**payload, "week_start": str(week.week_start),
                    "last_session": str(week.last_session), "unit_anchor": str(anchor)})}))
        output[symbol] = derived
    return output
