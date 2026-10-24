"""Immutable local research snapshots, explicit quality policy, and bounded acquisition.

Synthetic prices are exclusively FIXTURE data. Provider capture never substitutes them.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

import exchange_calendars as xcals
import numpy as np

from alphamosaic.backtesting.models import ReplayDataset
from alphamosaic.backtesting.replay import validate_dataset
from alphamosaic.core.contracts import (
    DataBatch,
    DataQuality,
    HistoricalBar,
    SecurityIdentity,
    Status,
)
from alphamosaic.providers.protocol import DataProvider

SCHEMA_VERSION = 1
_ID = re.compile(r"^[a-f0-9]{64}$")
_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.-]{0,14}$")


class QualityPolicy(StrEnum):
    REJECT = "REJECT"
    QUARANTINE = "QUARANTINE"
    WARN = "WARN"
    ACCEPT_WITH_PROVENANCE = "ACCEPT_WITH_PROVENANCE"


class DatasetQualityError(ValueError):
    def __init__(self, report: dict[str, Any]):
        self.report = report
        super().__init__("dataset quality rejected: " + ", ".join(report["flags"]))


def canonical_json(value: Any) -> bytes:
    """Portable canonical form; reject NaN/Infinity instead of serializing them."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def quality_report(data: ReplayDataset, jump_threshold: float = 0.5) -> dict[str, Any]:
    """Report structural errors separately from reviewable anomalies; never repair data."""
    if not math.isfinite(jump_threshold) or not 0 < jump_threshold <= 10:
        raise ValueError("finite jump threshold in (0, 10] required")
    issues: list[dict[str, str]] = []

    def add(code: str, severity: str = "WARNING", symbol: str = "", session: str = "") -> None:
        item = {"code": code, "severity": severity, "symbol": symbol, "session": session}
        if item not in issues:
            issues.append(item)

    def summary() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "valid": not any(i["severity"] == "ERROR" for i in issues),
            "flags": list(dict.fromkeys(i["code"] for i in issues)),
            "issues": issues,
            "jump_threshold": jump_threshold,
            "repaired": False,
        }

    try:
        checked = ReplayDataset.model_validate(data.model_dump())
        if checked != data:
            raise ValueError("dataset contract requires coercion")
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        add("INVALID_DATASET_CONTRACT", "ERROR")
        add(type(exc).__name__, "ERROR")
        return summary()
    try:
        for flag in validate_dataset(data):
            add(flag)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        # Details are schema/calendar diagnostics, never arbitrary provider response strings.
        add("INVALID_DATASET_CONTRACT", "ERROR")
        add(type(exc).__name__, "ERROR")
    reference: list[date] | None = None
    for symbol, bars in data.bars.items():
        sessions = [b.session for b in bars]
        if not _SYMBOL.fullmatch(symbol):
            add("INVALID_SYMBOL", "ERROR", symbol)
        if len(sessions) != len(set(sessions)):
            add("DUPLICATE_SESSIONS", "ERROR", symbol)
        if sessions != sorted(sessions):
            add("UNSORTED_SESSIONS", "ERROR", symbol)
        if reference is None:
            reference = sessions
        elif sessions != reference:
            add("ASSET_SESSION_MISALIGNMENT", "ERROR", symbol)
        if any(b.volume is None for b in bars):
            add("MISSING_VOLUME", symbol=symbol)
        if any(b.known_at < b.observed_at for b in bars):
            add("AVAILABILITY_PRECEDES_OBSERVATION", "ERROR", symbol)
        if len({b.source for b in bars}) > 1:
            add("MIXED_PROVIDERS_REQUIRES_REVIEW", symbol=symbol)
        if data.mode == "STRICT_PIT" and any(b.adjustment_policy == "UNKNOWN" for b in bars):
            add("STRICT_BACKTEST_REQUIRES_KNOWN_ADJUSTMENT", "ERROR", symbol)
        split_dates = {
            a.effective_date for a in data.actions if a.symbol == symbol and a.action == "SPLIT"
        }
        for prior, current in zip(bars, bars[1:], strict=False):
            if prior.close <= 0 or not math.isfinite(prior.close + current.close):
                add("INVALID_PRICE", "ERROR", symbol, str(current.session))
            elif abs(current.close / prior.close - 1) > jump_threshold:
                add(
                    "SPLIT_REQUIRES_REVIEW" if current.session in split_dates else "EXTREME_PRICE_JUMP",
                    symbol=symbol,
                    session=str(current.session),
                )
    if data.mode == "STRICT_PIT" and any(
        b.data_quality != DataQuality.FIXTURE for bars in data.bars.values() for b in bars
    ):
        if not data.corporate_actions_complete:
            add("STRICT_REAL_ACTION_COVERAGE_NOT_VERIFIED", "ERROR")
        if not data.historical_universe_verified:
            add("STRICT_REAL_UNIVERSE_NOT_VERIFIED", "ERROR")
    return summary()


def _write_new(path: Path, value: Any) -> None:
    """Exclusive file creation; existing evidence is never overwritten."""
    with path.open("xb") as handle:
        handle.write(canonical_json(value))
        handle.flush()


class DatasetStore:
    """Content-addressed versioned snapshots under a caller-selected local research root."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, dataset_id: str) -> Path:
        if not _ID.fullmatch(dataset_id):
            raise ValueError("dataset ID must be a full lowercase SHA-256 digest")
        path = (self.root / dataset_id).resolve()
        if path.parent != self.root:
            raise ValueError("dataset path escapes store")
        return path

    def save(
        self,
        data: ReplayDataset,
        metadata: dict[str, Any] | None = None,
        *,
        policy: QualityPolicy = QualityPolicy.REJECT,
    ) -> dict[str, Any]:
        """Persist only complete directories; repeated identical content is idempotent.

        REJECT rejects any anomaly. QUARANTINE retains evidence but load refuses it.
        WARN and ACCEPT_WITH_PROVENANCE allow reviewable anomalies, never structural errors.
        """
        policy = QualityPolicy(policy)
        report = quality_report(data)
        if (report["flags"] and policy == QualityPolicy.REJECT) or (
            not report["valid"] and policy != QualityPolicy.QUARANTINE
        ):
            raise DatasetQualityError(report)
        payload = {"schema_version": SCHEMA_VERSION, "dataset": data.model_dump(mode="json")}
        digest = content_hash(payload)
        destination = self._path(digest)
        qualities = sorted({b.data_quality.value for bars in data.bars.values() for b in bars})
        providers = sorted({b.source for bars in data.bars.values() for b in bars})
        manifest: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "dataset_id": digest,
            "dataset_hash": digest,
            "dataset_version": digest,
            "provider": providers,
            "source_versions": sorted({
                b.provenance.get("provider_version", "NOT_REPORTED")
                for bars in data.bars.values() for b in bars
            }),
            "fetch_timestamp": max(
                (b.as_of for bars in data.bars.values() for b in bars), default=data.cutoff
            ).isoformat(),
            "cutoff": data.cutoff.isoformat(),
            "instruments": sorted(data.bars),
            "adjustment_method": sorted({b.adjustment_policy for bars in data.bars.values() for b in bars}),
            "price_series_kind": sorted({
                {"RAW": "RAW_PRICE", "SPLIT": "SPLIT_ADJUSTED_PRICE", "TOTAL_RETURN": "TOTAL_RETURN_SERIES"}.get(b.adjustment_policy, "UNKNOWN")
                for bars in data.bars.values() for b in bars
            }),
            "calendar": "XNYS",
            "timezone": "UTC",
            "frequency": "DAILY",
            "data_quality": qualities,
            "license_scope": sorted({b.license_scope for bars in data.bars.values() for b in bars}),
            "universe_selection_method": "EXPLICIT_FIXED_SYNTHETIC" if qualities == ["FIXTURE"] else "EXPLICIT_CURRENT_SYMBOLS_SURVIVORSHIP_RISK",
            "historical_universe_verified": data.historical_universe_verified,
            "corporate_actions_complete": data.corporate_actions_complete,
            "quality_policy": policy.value,
            "quality_report": report,
            "state": "QUARANTINED" if policy == QualityPolicy.QUARANTINE else "AVAILABLE",
            "metadata": metadata or {},
        }
        manifest["manifest_hash"] = content_hash(manifest)
        if destination.exists():
            existing = self.manifest(digest)
            if existing != manifest:
                raise ValueError("dataset already exists with different metadata or quality policy")
            self._payload(digest)
            if existing["state"] == "AVAILABLE":
                self.load(digest)
            return existing
        staging = self.root / (".pending-" + uuid4().hex)
        staging.mkdir()
        _write_new(staging / "dataset.json", payload)
        _write_new(staging / "manifest.json", manifest)
        try:
            staging.rename(destination)
        except OSError:
            # A concurrent publisher may have completed the same snapshot. Never replace it.
            if not destination.exists() or self.manifest(digest) != manifest:
                raise
            self._payload(digest)
            if manifest["state"] == "AVAILABLE":
                self.load(digest)
        return manifest

    def manifest(self, dataset_id: str) -> dict[str, Any]:
        manifest = json.loads((self._path(dataset_id) / "manifest.json").read_bytes())
        expected = manifest.pop("manifest_hash", None)
        if expected != content_hash(manifest):
            raise ValueError("manifest hash mismatch")
        manifest["manifest_hash"] = expected
        if manifest.get("dataset_id") != dataset_id or manifest.get("dataset_hash") != dataset_id:
            raise ValueError("manifest identity mismatch")
        return manifest

    def load(self, dataset_id: str) -> ReplayDataset:
        manifest = self.manifest(dataset_id)
        if manifest["state"] != "AVAILABLE":
            raise ValueError("quarantined dataset cannot enter a research replay")
        payload = self._payload(dataset_id)
        data = ReplayDataset.model_validate(payload["dataset"])
        report = quality_report(data)
        if not report["valid"] or report != manifest["quality_report"]:
            raise DatasetQualityError(report)
        return data

    def _payload(self, dataset_id: str) -> dict[str, Any]:
        payload = json.loads((self._path(dataset_id) / "dataset.json").read_bytes())
        if content_hash(payload) != dataset_id or payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("dataset content hash or schema mismatch")
        return payload

    def list(self) -> list[dict[str, Any]]:
        return [self.manifest(p.name) for p in sorted(self.root.iterdir()) if p.is_dir() and _ID.fullmatch(p.name)]

    def capture_provider(
        self,
        provider: DataProvider,
        symbols: list[str],
        start: date,
        end: date,
        *,
        allow_network: bool = False,
    ) -> dict[str, Any]:
        """Opt-in bounded existing-provider acquisition; retain normalized response evidence.

        This is personal local capture, not a data redistribution license. Unknown adjustment
        and reconstructed availability stay diagnostic and cannot enter strict replay.
        """
        if not allow_network:
            raise ValueError("network acquisition requires explicit allow_network=True")
        if not 1 <= len(symbols) <= 10 or len(set(symbols)) != len(symbols):
            raise ValueError("1..10 distinct symbols required")
        if any(not _SYMBOL.fullmatch(s) for s in symbols) or not start < end or (end - start).days > 3660:
            raise ValueError("valid symbols and 1..3660 day historical range required")
        attempt_id = uuid4().hex
        directory = self.root / "acquisitions" / attempt_id
        directory.mkdir(parents=True)
        response: dict[str, Any] = {
            "attempt_id": attempt_id,
            "requested_at": datetime.now(UTC).isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "symbols": symbols,
            "status": "RUNNING",
            "responses": {},
            "dataset_id": None,
            "broker_enabled": False,
        }
        _write_new(directory / "request.json", response)
        batches: dict[str, DataBatch] = {}
        for symbol in symbols:
            try:
                batch = provider.history(symbol, start, end)
                response["responses"][symbol] = batch.model_dump(mode="json")
                if batch.status == Status.OK and batch.identity is not None and batch.bars:
                    batches[symbol] = batch
            except Exception as exc:
                response["responses"][symbol] = {"status": "FAILED", "error_type": type(exc).__name__}
        response["completed_at"] = datetime.now(UTC).isoformat()
        response["status"] = "ACQUIRED_DIAGNOSTIC" if len(batches) == len(symbols) else "PROVIDER_UNAVAILABLE_OR_PARTIAL"
        if len(batches) == len(symbols):
            try:
                if any(
                    bar.data_quality not in {DataQuality.REAL, DataQuality.HISTORICAL, DataQuality.DELAYED}
                    for batch in batches.values() for bar in batch.bars
                ):
                    raise ValueError("provider acquisition requires real historical observations")
                if any(
                    not start <= bar.session <= end
                    for batch in batches.values() for bar in batch.bars
                ):
                    raise ValueError("provider returned observations outside requested dates")
                data = ReplayDataset(
                    bars={s: b.bars for s, b in batches.items()},
                    identities={s: b.identity for s, b in batches.items() if b.identity is not None},
                    cutoff=datetime.now(UTC),
                    mode="RECONSTRUCTED_DIAGNOSTIC",
                    historical_universe_verified=False,
                    corporate_actions_complete=False,
                )
                manifest = self.save(data, {"acquisition_id": attempt_id}, policy=QualityPolicy.WARN)
                response["dataset_id"] = manifest["dataset_id"]
            except (ValueError, TypeError) as exc:
                response["status"] = "DATASET_REJECTED"
                response["quality_report"] = exc.report if isinstance(exc, DatasetQualityError) else {"error_type": type(exc).__name__}
        _write_new(directory / "response.json", response)
        return response


def synthetic_demo(count: int = 504, seed: int = 42) -> ReplayDataset:
    """A deterministic, correlated three-asset fixture, never historical market returns.

    Symbol labels are familiar research cases; prices have no relationship to those funds.
    """
    if not 2 <= count <= 2000 or not 0 <= seed < 2**32:
        raise ValueError("count in 2..2000 and unsigned 32-bit seed required")
    calendar = xcals.get_calendar("XNYS")
    sessions = list(calendar.sessions_in_range("2016-01-04", "2024-12-31"))[:count]
    rng = np.random.default_rng(seed)
    market = rng.normal(0.0002, 0.009, count)
    bars: dict[str, list[HistoricalBar]] = {}
    identities: dict[str, SecurityIdentity] = {}
    for symbol, beta, drift, initial in (("SPY", 1.0, 0.0001, 100.0), ("QQQM", 1.2, 0.00015, 80.0), ("TLT", -0.2, 0.00005, 120.0)):
        identities[symbol] = SecurityIdentity(
            symbol=symbol, exchange="NYSEARCA", currency="USD", security_type="ETF",
            active=True, identity_source="FIXTURE deterministic generator v1", identity_verified=True,
            as_of=calendar.session_open(sessions[0]).to_pydatetime(),
        )
        innovations = beta * market + rng.normal(drift, 0.003, count)
        previous = initial
        bars[symbol] = []
        for index, session in enumerate(sessions):
            opening = previous * float(np.exp(rng.normal(0, 0.002)))
            closing = opening * float(np.exp(innovations[index]))
            at = calendar.session_close(session).to_pydatetime()
            bars[symbol].append(HistoricalBar(
                symbol=symbol, source="FIXTURE synthetic_demo v1",
                source_url="https://example.invalid/alphamosaic/synthetic-demo-v1",
                observed_at=at, known_at=at, as_of=at, currency="USD",
                data_quality=DataQuality.FIXTURE, adjustment_policy="RAW",
                provenance={"generator": "numpy.PCG64", "seed": str(seed), "schema": "1", "meaning": "synthetic-not-market-prices"},
                license_scope="Project-generated synthetic data; Apache-2.0",
                pit_status="VERIFIED", session=session.date(), open=opening,
                high=max(opening, closing) * 1.003, low=min(opening, closing) * 0.997,
                close=closing, volume=float(rng.integers(500_000, 2_000_000)),
            ))
            previous = closing
    return ReplayDataset(
        bars=bars, identities=identities, cutoff=calendar.session_close(sessions[-1]).to_pydatetime(),
        mode="STRICT_PIT", historical_universe_verified=True, corporate_actions_complete=True,
    )
