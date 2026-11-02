"""Derived research close contracts have no observation or execution authority."""

from datetime import UTC, date, datetime
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from alphamosaic.core.contracts import Contract, DataQuality


class AppliedFeatureSplit(Contract):
    effective_date: date
    ratio: float = Field(gt=0)
    source_action_id: str | None
    dependency_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


class DerivedWeeklyClose(Contract):
    symbol: str
    week_start: date
    last_session: date
    close: float = Field(gt=0)
    unit_anchor: date
    decision_at: datetime
    evidence_kind: Literal["DERIVED_FEATURE"] = "DERIVED_FEATURE"
    policy: Literal["RAW_SPLIT_PRICE_ONLY_V1"] = "RAW_SPLIT_PRICE_ONLY_V1"
    return_basis: Literal["PRICE_ONLY_EXCLUDES_DIVIDENDS"] = "PRICE_ONLY_EXCLUDES_DIVIDENDS"
    currency: Literal["USD"] = "USD"
    unit: Literal["USD_PER_ANCHOR_SHARE"] = "USD_PER_ANCHOR_SHARE"
    pit_status: Literal["NOT_APPLICABLE"] = "NOT_APPLICABLE"
    parent_data_quality: DataQuality
    parent_pit_status: Literal["VERIFIED", "RECONSTRUCTED", "NOT_APPLICABLE"]
    input_row_fingerprints: list[str] = Field(min_length=1, max_length=5)
    applied_splits: list[AppliedFeatureSplit]
    dependency_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("decision_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("aware feature decision required")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def chronology(self) -> Self:
        if not self.week_start <= self.last_session <= self.unit_anchor <= self.decision_at.date():
            raise ValueError("derived feature chronology invalid")
        if any(not self.last_session < split.effective_date <= self.unit_anchor for split in self.applied_splits):
            raise ValueError("derived feature split outside anchored interval")
        if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
               for value in self.input_row_fingerprints):
            raise ValueError("invalid bounded row fingerprint")
        return self
