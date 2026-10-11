from datetime import UTC, datetime, timedelta
from pathlib import Path

import exchange_calendars as xcals

from alphamosaic.core.contracts import (
    DataBatch,
    DataQuality,
    HistoricalBar,
    ProviderEvidence,
    ProviderHealth,
    SecurityIdentity,
    Status,
)
from alphamosaic.core.service import ApplicationService


class FixtureProvider:
    def __init__(self) -> None:
        self.now = datetime.now(UTC)
        calendar = xcals.get_calendar("XNYS")
        sessions = calendar.sessions_in_range((self.now - timedelta(days=140)).date(), self.now.date())[-90:]
        self.sessions = [item.date() for item in sessions]

    def health(self) -> ProviderHealth:
        return ProviderHealth(name="fixture", status=Status.OK, checked_at=self.now, capabilities=["HISTORY"], diagnostics=[])

    def universe(self, limit: int):
        return ([self.identity(symbol) for symbol in ["AAA", "BBB", "CCC"][:limit]], "fixture universe")

    def identity(self, symbol: str) -> SecurityIdentity:
        return SecurityIdentity(symbol=symbol, exchange="NASDAQ-GS", currency="USD", active=True,
            identity_source="fixture", identity_verified=True, as_of=self.now)

    def history(self, symbol: str, start, end) -> DataBatch:
        evidence = ProviderEvidence(symbol=symbol, source="fixture", source_url="https://example.invalid",
            observed_at=self.now, known_at=self.now, as_of=self.now, currency="USD", data_quality=DataQuality.FIXTURE,
            adjustment_policy="SPLIT", provenance={"fixture": "true"}, license_scope="test", endpoint="history",
            requested_at=self.now - timedelta(seconds=1), completed_at=self.now, status=Status.OK, row_count=90, fields=["close"])
        bars = []
        for index, session in enumerate(self.sessions):
            close = 100 + index * (1 if symbol != "BBB" else -0.1)
            bars.append(HistoricalBar(symbol=symbol, source="fixture", source_url="https://example.invalid",
                observed_at=self.now, known_at=self.now, as_of=self.now, currency="USD", data_quality=DataQuality.FIXTURE,
                adjustment_policy="SPLIT", provenance={"fixture": "true"}, license_scope="test", session=session,
                open=close, high=close + 1, low=close - 1, close=close, volume=1_000_000))
        return DataBatch(identity=self.identity(symbol), bars=bars, evidence=[evidence], status=Status.OK)


def test_opportunity_pipeline_persists_top_ten_and_resume(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path, FixtureProvider())
    first = service.discover_opportunities("FAST", 3, 3, 1, "BROAD_LIQUIDITY")
    assert first["universe_count"] == 3
    assert first["preliminary_count"] == 3
    assert first["acceptance"] == "FIXTURE"
    assert (tmp_path / "opportunities" / first["run_id"] / "opportunity_report.json").exists()
    resumed = service.discover_opportunities("FAST", 3, 3, 1, "BROAD_LIQUIDITY", resume=True)
    assert resumed["initial_run_id"] == first["initial_run_id"]
    assert resumed["resume_count"] == 1
