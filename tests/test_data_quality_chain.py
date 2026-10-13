"""Deterministic fault injection for the 2026-10-13 benchmark incident."""

import asyncio
import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from test_opportunity_pipeline import FixtureProvider

from alphamosaic.backtesting.diagnostic import trend_diagnostic
from alphamosaic.core.contracts import DataBatch, Status
from alphamosaic.core.service import ApplicationService
from alphamosaic.data.validation import validate_batch
from alphamosaic.factors.engine import FactorEngine
from alphamosaic.mcp.server import create_server
from alphamosaic.providers.openbb import OpenBBDataProvider
from alphamosaic.providers.sec_edgar import SecEdgarAdapter
from alphamosaic.reporting.store import ReportStore
from alphamosaic.screening.universe import UniverseManager


class FaultProvider(FixtureProvider):
    def __init__(self, fault: str = "volume") -> None:
        super().__init__()
        self.fault = fault

    def history(self, symbol, start, end) -> DataBatch:
        batch = super().history(symbol, start, end)
        if symbol == "SPY":
            if self.fault in {"unavailable", "timeout", "quota", "empty"}:
                status = {"unavailable": Status.UNAVAILABLE, "timeout": Status.TIMEOUT, "quota": Status.QUOTA, "empty": Status.EMPTY}[self.fault]
                return DataBatch(status=status, evidence=[batch.evidence[0].model_copy(update={"status": status, "diagnostics": [self.fault]})])
            if self.fault == "gap":
                return batch.model_copy(update={"bars": batch.bars[:40] + batch.bars[41:]})
            if self.fault == "ohlc":
                return batch.model_copy(update={"bars": [batch.bars[0].model_copy(update={"high": 1}), *batch.bars[1:]]})
            if self.fault == "stale":
                return batch.model_copy(update={"bars": batch.bars[:-1]})
            if self.fault == "split":
                return batch.model_copy(update={"bars": [*batch.bars[:-1], batch.bars[-1].model_copy(update={"close": 30, "open": 30, "high": 31, "low": 29})]})
            if self.fault == "volume":
                return batch.model_copy(update={"bars": [bar.model_copy(update={"volume": None}) for bar in batch.bars]})
        return batch


def test_null_etf_volume_retains_valid_prices_and_both_relative_factors(tmp_path: Path) -> None:
    provider = FaultProvider()
    spy = provider.history("SPY", None, None)
    assert not validate_batch(spy.identity, spy.bars, provider.now, purpose="PRICE_BENCHMARK")
    report = ApplicationService(tmp_path, provider).scan(symbols=["AAA", "BBB", "CCC"], evaluate=False)
    assert report.eligible_count == 3
    assert report.benchmark_validity["SPY"]["missing_volume"] == 90
    assert all(item.factors["relative_strength_spy_63d"] is not None for item in report.candidates)
    assert all(item.factors["relative_strength_qqqm_63d"] is not None for item in report.candidates)
    assert report.evaluation_status == "DISABLED_BY_REQUEST"
    assert report.evaluation is None
    assert report.assessment["INVESTMENT_ACTION"] == "NO_ACTION"
    assert report.assessment["SOFTWARE_ACCEPTANCE"] == "NOT_VERIFIED"


@pytest.mark.parametrize("fault,flag", [("gap", "MISSING_SESSIONS"), ("ohlc", "INVALID_OHLC"), ("stale", "STALE_HISTORY"), ("split", "PRICE_DISCONTINUITY_REQUIRES_REVIEW"), ("unavailable", None), ("timeout", None), ("quota", None), ("empty", "EMPTY_HISTORY")])
def test_invalid_spy_propagates_degradation_without_disabling_qqqm(tmp_path: Path, fault: str, flag: str | None) -> None:
    service = ApplicationService(tmp_path, FaultProvider(fault))
    report = service.scan(symbols=["AAA"], evaluate=False)
    assert report.status == Status.PARTIAL
    assert report.benchmark_validity["SPY"]["status"] == "BLOCKED"
    assert report.benchmark_validity["QQQM"]["status"] == "VALID_PRICE_SERIES"
    candidate = report.candidates[0]
    assert candidate.factors["relative_strength_spy_63d"] is None
    assert candidate.factors["relative_strength_qqqm_63d"] is not None
    assert candidate.ranking_status == "DEGRADED_BENCHMARK"
    assert candidate.research_score is not None and candidate.factor_coverage is not None
    assert candidate.research_score <= candidate.factor_coverage
    assert candidate.factor_evidence["quality_roe"].source == "MISSING"
    if flag:
        assert flag in cast(list[str], report.benchmark_validity["SPY"]["flags"])
    ranking = service.ranking(report.run_id)
    assert ranking["run_id"] == report.run_id and ranking["status"] == "PARTIAL"
    assert ranking["assessment"]["BENCHMARK_VALIDITY"] == "DEGRADED"


def test_volume_dependent_factors_abstain_without_nan() -> None:
    provider = FixtureProvider()
    batch = provider.history("AAA", None, None)
    bars = [bar.model_copy(update={"volume": None}) for bar in batch.bars]
    factors = FactorEngine().calculate(bars, [])
    assert factors["momentum_63d"] is not None
    assert factors["liquidity_20d_usd"] is None and factors["volume_ratio"] is None
    json.dumps(factors, allow_nan=False)
    assert "MISSING_VOLUME" in validate_batch(batch.identity, bars, provider.now)


def test_misalignment_and_future_benchmark_cannot_produce_relative_strength() -> None:
    provider = FixtureProvider()
    bars = provider.history("AAA", None, None).bars
    benchmark = provider.history("SPY", None, None).bars
    assert FactorEngine().calculate(bars, benchmark[:40] + benchmark[41:])["relative_strength_spy_63d"] is None
    future = [bar.model_copy(update={"known_at": provider.now + timedelta(days=1)}) for bar in benchmark]
    assert FactorEngine().calculate(bars, future, research_cutoff=provider.now)["relative_strength_spy_63d"] is None


def test_openbb_normalization_keeps_none_and_rejects_bad_price(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FixtureProvider()
    source = provider.history("SPY", None, None).bars
    rows = [{"date": str(bar.session), "open": bar.open, "close": bar.close, "high": bar.high, "low": bar.low, "volume": None} for bar in source]
    adapter = OpenBBDataProvider(tmp_path)
    response = {"rows": rows, "profile": [{"symbol": "SPY", "name": "Fixture ETF", "exchange": "NYSEARCA"}]}
    monkeypatch.setattr(adapter, "_request", lambda *args, **kwargs: (response, provider.now, provider.now, Status.OK))
    batch = adapter.history("SPY", source[0].session, source[-1].session)
    assert batch.status == Status.OK and all(bar.volume is None for bar in batch.bars)
    assert "MISSING_VOLUME" in batch.evidence[0].diagnostics[0]
    rows[0]["close"] = None
    bad = adapter.history("SPY", source[0].session, source[-1].session)
    assert bad.status == Status.INVALID_DATA and not bad.bars
    assert "Normalization rejected" in bad.evidence[0].diagnostics[-1]


def test_report_reproduction_explicit_run_and_immutable_conflict(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path, FaultProvider())
    first = service.scan(symbols=["AAA"], evaluate=False)
    second = service.scan(symbols=["BBB"], evaluate=False)
    directory = service.store.save(first)
    before = (directory / "report.json").read_bytes()
    generated = service.store.finalize(first.run_id)
    assert generated == service.store.finalize(first.run_id)
    hashes = json.loads((generated / "sha256.json").read_text())
    assert hashlib.sha256((generated / "daily.md").read_bytes()).hexdigest() == hashes["daily.md"]
    bundle = json.loads((generated / "daily.json").read_text())
    assert bundle["run_id"] == first.run_id and bundle["run_id"] != second.run_id
    assert bundle["external_web_check"] == "NOT_RUN"
    assert bundle["source_version"]["source_sha256"]
    assert (directory / "report.json").read_bytes() == before
    with pytest.raises(FileExistsError, match="immutable"):
        service.store.save(first.model_copy(update={"warnings": ["different"]}))
    with pytest.raises(ValueError, match="run id"):
        service.store.get("../secrets")


def test_legacy_report_has_no_invented_runtime_acceptance(tmp_path: Path) -> None:
    report = ApplicationService(tmp_path / "source", FaultProvider()).scan(symbols=["AAA"], persist=False, evaluate=False)
    raw = report.model_dump(mode="json")
    for key in ("runtime_manifest", "assessment", "benchmark_validity", "source_batches"):
        raw.pop(key)
    directory = tmp_path / report.run_id
    directory.mkdir()
    (directory / "report.json").write_text(json.dumps(raw))
    restored = ReportStore(tmp_path).get(report.run_id)
    assert restored is not None and restored.runtime_manifest == {} and restored.assessment == {}


def test_mcp_does_not_label_invalid_benchmark_ready(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path, FaultProvider("unavailable"))
    server = create_server(service)
    result = asyncio.run(server._tool_manager.call_tool("scan_market", {"universe_limit": 3, "top": 3}, cast(Any, None)))
    assert result["status"] == "DEGRADED"
    assert result["report"]["assessment"]["INVESTMENT_ACTION"] == "NO_ACTION"


def test_stratified_pool_is_deterministic_and_budgeted() -> None:
    manager = UniverseManager(FixtureProvider())
    universe = manager.stratified({"quality": ["AAA", "BBB"], "growth": ["CCC", "AAA"]}, limit=3)
    assert universe.symbols == ["CCC", "AAA", "BBB"]
    assert "styles unverified" in universe.source


def test_evaluation_requested_success_and_failure_are_distinct(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service = ApplicationService(tmp_path, FaultProvider("unavailable"))
    report = service.scan(symbols=["AAA"], evaluate=True)
    assert report.evaluation is not None
    assert "SPY" not in report.evaluation.benchmarks
    assert "QQQM" in report.evaluation.benchmarks
    assert report.evaluation_status == "DEGRADED_BENCHMARK_DIAGNOSTIC"
    assert report.evaluation.validation_level == "RECONSTRUCTED_DIAGNOSTIC"
    assert report.evaluation.dataset_fingerprint
    def fail(*args, **kwargs):
        raise ImportError("analytics unavailable")
    monkeypatch.setattr("alphamosaic.core.service.trend_diagnostic", fail)
    failed = service.scan(symbols=["AAA"], evaluate=True)
    assert failed.evaluation is None and failed.evaluation_status == "BLOCKED_DIAGNOSTIC"
    assert "ImportError" in failed.evaluation_diagnostics[0]


def test_fee_and_slippage_have_separate_accounting_and_no_alpha_claim() -> None:
    provider = FixtureProvider()
    bars = provider.history("AAA", None, None).bars
    free = trend_diagnostic(bars, {}, fee_bps=0, slippage_bps=0)
    fee_only = trend_diagnostic(bars, {}, fee_bps=20, slippage_bps=0)
    costly = trend_diagnostic(bars, {}, fee_bps=20, slippage_bps=20)
    assert fee_only.fees == costly.fees > 0
    slip = costly.metrics["slippage_return_deduction"]
    net, fees_net, free_net = costly.metrics["return"], fee_only.metrics["return"], free.metrics["return"]
    assert slip is not None and slip > 0
    assert net is not None and fees_net is not None and free_net is not None
    assert net < fees_net < free_net
    assert not costly.validated_alpha


def test_all_excluded_and_empty_pool_never_appear_ready(tmp_path: Path) -> None:
    class EmptyStock(FaultProvider):
        def history(self, symbol, start, end):
            batch = super().history(symbol, start, end)
            if symbol == "AAA":
                return batch.model_copy(update={"bars": [], "status": Status.EMPTY})
            return batch
    service = ApplicationService(tmp_path, EmptyStock())
    report = service.scan(symbols=["AAA"], evaluate=True)
    assert not report.candidates and report.status == Status.EMPTY
    assert "EMPTY_HISTORY" in report.exclusions["AAA"]
    assert report.evaluation_status == "BLOCKED_NO_CANDIDATES"
    empty = service.scan(symbols=[], evaluate=False)
    assert empty.universe_count == 0 and empty.assessment["RESEARCH_READINESS"] == "INSUFFICIENT_EVIDENCE"


def test_stock_illiquidity_and_provider_exception_are_isolated(tmp_path: Path) -> None:
    class Adverse(FaultProvider):
        def history(self, symbol, start, end):
            if symbol == "BBB":
                raise TimeoutError("private details must not be exposed")
            batch = super().history(symbol, start, end)
            if symbol == "AAA":
                return batch.model_copy(update={"bars": [bar.model_copy(update={"volume": 1}) for bar in batch.bars]})
            return batch
    report = ApplicationService(tmp_path, Adverse()).scan(symbols=["AAA", "BBB", "CCC"], evaluate=False)
    assert "ILLIQUID" in report.exclusions["AAA"]
    assert "TIMEOUT" in report.exclusions["BBB"]
    assert [item.ticker for item in report.candidates] == ["CCC"]
    assert "private details" not in report.model_dump_json()


def test_sec_financial_metrics_retain_period_units_and_publication_cutoff(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from datetime import UTC, datetime
    adapter = SecEdgarAdapter(tmp_path)
    anchor = {"start": "2024-01-01", "end": "2024-12-31", "filed": "2025-02-10", "fy": 2024, "fp": "FY", "form": "10-K", "accn": "fixture-annual"}
    def concept(value):
        return {"units": {"USD": [{**anchor, "val": value}]}}
    facts = {"facts": {"us-gaap": {"Revenues": concept(200), "NetIncomeLoss": concept(20), "Assets": concept(500), "StockholdersEquity": concept(250), "LongTermDebt": concept(100), "ShortTermBorrowings": concept(10), "CashAndCashEquivalentsAtCarryingValue": concept(30), "NetCashProvidedByUsedInOperatingActivities": concept(40), "PaymentsToAcquirePropertyPlantAndEquipment": concept(10)}}}
    facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"].append({**anchor, "end": "2023-12-31", "start": "2023-01-01", "fy": 2023, "val": 100})
    monkeypatch.setattr(adapter, "_get", lambda url: {"0": {"ticker": "AAA", "cik_str": 1}} if "company_tickers" in url else facts)
    result = adapter.fundamentals("AAA", datetime(2025, 3, 1, tzinfo=UTC))
    assert result is not None
    assert result.revenue_growth == 1 and result.net_margin == 0.1
    assert result.free_cash_flow == 30 and result.net_debt == 80
    assert result.return_on_equity is None  # no average equity denominator
    assert result.field_evidence["free_cash_flow"].period_end.isoformat() == "2024-12-31"
    assert result.field_evidence["revenue_growth"].unit == "ratio"
    assert result.known_at.isoformat().startswith("2025-02-11")
    assert adapter.fundamentals("AAA", datetime(2025, 2, 10, tzinfo=UTC)) is None
