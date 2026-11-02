"""Data provenance, failure capture, immutability and corrupt-input regression checks."""

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from alphamosaic.core.contracts import (
    DataBatch,
    DataQuality,
    ProviderHealth,
    SecurityIdentity,
    Status,
    utc_now,
)
from alphamosaic.data.datasets import (
    DatasetQualityError,
    DatasetStore,
    QualityPolicy,
    quality_report,
    synthetic_demo,
)


def test_snapshot_roundtrip_is_deterministic_and_content_addressed(tmp_path: Path) -> None:
    data = synthetic_demo(count=70)
    assert data == synthetic_demo(count=70)
    assert data != synthetic_demo(count=70, seed=3)
    store = DatasetStore(tmp_path)
    manifest = store.save(data)
    assert store.load(manifest["dataset_id"]) == data
    assert store.save(data) == manifest
    assert store.list() == [manifest]
    assert manifest["data_quality"] == ["FIXTURE"]
    assert manifest["adjustment_method"] == ["RAW"]
    assert manifest["price_series_kind"] == ["RAW_PRICE"]
    assert manifest["dataset_version"] == manifest["dataset_hash"]
    assert manifest["source_versions"] == ["NOT_REPORTED"]
    assert manifest["frequency"] == "DAILY"
    assert manifest["universe_selection_method"] == "EXPLICIT_FIXED_SYNTHETIC"
    assert "synthetic" in manifest["provider"][0]
    with pytest.raises(ValueError, match="different metadata"):
        store.save(data, {"replace": "forbidden"})


def test_dataset_and_manifest_tampering_are_rejected(tmp_path: Path) -> None:
    store = DatasetStore(tmp_path)
    manifest = store.save(synthetic_demo(count=12))
    directory = tmp_path / manifest["dataset_id"]
    payload = json.loads((directory / "dataset.json").read_bytes())
    payload["dataset"]["bars"]["SPY"][0]["close"] += 1
    (directory / "dataset.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="content hash"):
        store.load(manifest["dataset_id"])
    raw_manifest = json.loads((directory / "manifest.json").read_bytes())
    raw_manifest["data_quality"] = ["REAL"]
    (directory / "manifest.json").write_text(json.dumps(raw_manifest))
    with pytest.raises(ValueError, match="manifest hash"):
        store.manifest(manifest["dataset_id"])


@pytest.mark.parametrize("identifier", ["../outside", "A" * 64, "a" * 63, "x/y", ""])
def test_dataset_id_cannot_escape_store(tmp_path: Path, identifier: str) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        DatasetStore(tmp_path).load(identifier)


def test_anomalies_have_explicit_policy_and_quarantine_cannot_replay(tmp_path: Path) -> None:
    data = synthetic_demo(count=12).model_copy(deep=True)
    original = data.bars["SPY"][-1]
    data.bars["SPY"][-1] = original.model_copy(update={
        "open": original.open * 3, "high": original.high * 3,
        "low": original.low * 3, "close": original.close * 3,
    })
    store = DatasetStore(tmp_path / "rejected")
    with pytest.raises(DatasetQualityError) as rejected:
        store.save(data)
    assert "EXTREME_PRICE_JUMP" in rejected.value.report["flags"]
    assert store.list() == []
    quarantined = DatasetStore(tmp_path / "quarantine")
    manifest = quarantined.save(data, policy=QualityPolicy.QUARANTINE)
    assert manifest["state"] == "QUARANTINED"
    with pytest.raises(ValueError, match="quarantined"):
        quarantined.load(manifest["dataset_id"])
    allowed = DatasetStore(tmp_path / "warn")
    manifest = allowed.save(data, policy=QualityPolicy.WARN)
    assert allowed.load(manifest["dataset_id"]) == data
    assert manifest["quality_report"]["repaired"] is False
    explicit = DatasetStore(tmp_path / "provenance")
    manifest = explicit.save(data, {"review": "test anomaly retained"}, policy=QualityPolicy.ACCEPT_WITH_PROVENANCE)
    assert explicit.load(manifest["dataset_id"]) == data


@pytest.mark.parametrize("damage", ["duplicate", "unsorted", "alignment", "ohlc", "negative_volume", "future", "unknown_adjustment"])
def test_structural_or_pit_errors_cannot_be_waived(tmp_path: Path, damage: str) -> None:
    data = synthetic_demo(count=12).model_copy(deep=True)
    if damage == "duplicate":
        data.bars["SPY"][1] = data.bars["SPY"][0]
    elif damage == "unsorted":
        data.bars["SPY"][0], data.bars["SPY"][1] = data.bars["SPY"][1], data.bars["SPY"][0]
    elif damage == "alignment":
        data.bars["TLT"].pop(2)
    elif damage == "ohlc":
        data.bars["SPY"][1] = data.bars["SPY"][1].model_copy(update={"high": 1})
    elif damage == "negative_volume":
        data.bars["SPY"][1] = data.bars["SPY"][1].model_copy(update={"volume": -1})
    elif damage == "future":
        data.bars["SPY"][1] = data.bars["SPY"][1].model_copy(update={"known_at": data.cutoff + timedelta(days=1)})
    else:
        data.bars["SPY"] = [b.model_copy(update={"adjustment_policy": "UNKNOWN"}) for b in data.bars["SPY"]]
    assert quality_report(data)["valid"] is False
    with pytest.raises(DatasetQualityError):
        DatasetStore(tmp_path).save(data, policy=QualityPolicy.WARN)


class OfflineFailureProvider:
    """A protocol test double; only this test supplies it explicitly."""

    def __init__(self, raises: bool = False):
        self.calls = 0
        self.raises = raises

    def health(self) -> ProviderHealth:
        return ProviderHealth(name="test", status=Status.NETWORK_ERROR, checked_at=utc_now(), capabilities=[], diagnostics=[])

    def universe(self, limit: int) -> tuple[list[SecurityIdentity], str]:
        return [], "test"

    def history(self, symbol: str, start: date, end: date) -> DataBatch:
        self.calls += 1
        if self.raises:
            raise ConnectionError("sensitive text must not be logged")
        return DataBatch(status=Status.NETWORK_ERROR, evidence=[])


@pytest.mark.parametrize("raises", [True, False])
def test_network_capture_opt_in_and_failure_evidence_no_fixture_fallback(tmp_path: Path, raises: bool) -> None:
    store = DatasetStore(tmp_path)
    provider = OfflineFailureProvider(raises)
    with pytest.raises(ValueError, match="allow_network"):
        store.capture_provider(provider, ["SPY"], date(2022, 1, 1), date(2022, 3, 1))
    assert provider.calls == 0
    response = store.capture_provider(provider, ["SPY"], date(2022, 1, 1), date(2022, 3, 1), allow_network=True)
    assert response["status"] == "PROVIDER_UNAVAILABLE_OR_PARTIAL"
    assert response["dataset_id"] is None and not store.list()
    captured = tmp_path / "acquisitions" / response["attempt_id"] / "response.json"
    assert json.loads(captured.read_bytes()) == response
    assert "sensitive" not in captured.read_text()


def test_pending_incomplete_publish_is_not_listed(tmp_path: Path) -> None:
    (tmp_path / ".pending-incomplete").mkdir()
    assert DatasetStore(tmp_path).list() == []


@pytest.mark.parametrize("damage", ["naive_time", "unavailable_observation", "missing_session", "infinite_price"])
def test_malformed_or_unavailable_inputs_return_audit_flags(damage: str) -> None:
    data = synthetic_demo(count=12).model_copy(deep=True)
    bar = data.bars["SPY"][1]
    if damage == "naive_time":
        data.bars["SPY"][1] = bar.model_copy(update={"known_at": bar.known_at.replace(tzinfo=None)})
    elif damage == "unavailable_observation":
        data.bars["SPY"][1] = bar.model_copy(update={"known_at": bar.observed_at - timedelta(minutes=1)})
    elif damage == "infinite_price":
        data.bars["SPY"][1] = bar.model_copy(update={"close": float("inf")})
    else:
        for bars in data.bars.values():
            bars.pop(2)
    report = quality_report(data)
    assert report["valid"] is False
    assert report["repaired"] is False


@pytest.mark.parametrize("coverage", ["corporate_actions_complete", "historical_universe_verified"])
def test_real_strict_pit_requires_reviewed_coverage(tmp_path: Path, coverage: str) -> None:
    data = synthetic_demo(count=12).model_copy(deep=True)
    data = data.model_copy(update={coverage: False})
    for symbol in data.bars:
        data.bars[symbol] = [b.model_copy(update={"data_quality": DataQuality.HISTORICAL}) for b in data.bars[symbol]]
    with pytest.raises(DatasetQualityError):
        DatasetStore(tmp_path).save(data, policy=QualityPolicy.ACCEPT_WITH_PROVENANCE)


def test_provider_conflict_is_reviewable_but_never_silently_repaired(tmp_path: Path) -> None:
    data = synthetic_demo(count=12).model_copy(deep=True)
    data.bars["SPY"][1] = data.bars["SPY"][1].model_copy(update={"source": "second explicit fixture provider"})
    with pytest.raises(DatasetQualityError):
        DatasetStore(tmp_path).save(data)
    manifest = DatasetStore(tmp_path).save(data, policy=QualityPolicy.WARN)
    assert "MIXED_PROVIDERS_REQUIRES_REVIEW" in manifest["quality_report"]["flags"]


class SnapshotProvider(OfflineFailureProvider):
    """Explicit successful protocol double, never used by production acquisition."""

    def __init__(self, quality: DataQuality = DataQuality.HISTORICAL):
        super().__init__()
        self.data = synthetic_demo(count=12)
        self.quality = quality

    def history(self, symbol: str, start: date, end: date) -> DataBatch:
        self.calls += 1
        return DataBatch(
            status=Status.OK,
            identity=self.data.identities[symbol],
            bars=[b.model_copy(update={"data_quality": self.quality, "pit_status": "RECONSTRUCTED"}) for b in self.data.bars[symbol]],
            evidence=[],
        )


@pytest.mark.parametrize("damage", ["fixture", "outside_range", "bad_contract"])
def test_invalid_provider_success_is_persisted_as_failed_acquisition(tmp_path: Path, damage: str) -> None:
    provider = SnapshotProvider(DataQuality.FIXTURE if damage == "fixture" else DataQuality.HISTORICAL)
    if damage == "bad_contract":
        # A provider can bypass Pydantic with model_copy; capture must still record failure.
        provider.data.identities["SPY"] = provider.data.identities["SPY"].model_copy(update={"currency": "BAD-CURRENCY"})
    start = date(2020, 1, 1) if damage == "outside_range" else date(2016, 1, 1)
    end = date(2020, 2, 1) if damage == "outside_range" else date(2016, 3, 1)
    response = DatasetStore(tmp_path).capture_provider(provider, ["SPY"], start, end, allow_network=True)
    assert response["status"] == "DATASET_REJECTED"
    assert response["dataset_id"] is None
    persisted = tmp_path / "acquisitions" / response["attempt_id"] / "response.json"
    assert json.loads(persisted.read_bytes()) == response


def test_successful_capture_stays_reconstructed_and_preserves_provider_payload(tmp_path: Path) -> None:
    provider = SnapshotProvider()
    store = DatasetStore(tmp_path)
    response = store.capture_provider(provider, ["SPY"], date(2016, 1, 1), date(2016, 3, 1), allow_network=True)
    assert response["status"] == "ACQUIRED_DIAGNOSTIC"
    data = store.load(response["dataset_id"])
    assert data.mode == "RECONSTRUCTED_DIAGNOSTIC"
    assert data.historical_universe_verified is False
    assert data.corporate_actions_complete is False
    assert response["responses"]["SPY"]["bars"] == [b.model_dump(mode="json") for b in data.bars["SPY"]]
    assert "SURVIVORSHIP_DELISTING_COVERAGE_NOT_VERIFIED" in store.manifest(response["dataset_id"])["quality_report"]["flags"]
