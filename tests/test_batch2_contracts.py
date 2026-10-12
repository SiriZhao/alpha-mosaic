from datetime import UTC, datetime, timedelta
from pathlib import Path

from alphamosaic.core.contracts import DataQuality, FusionSignal, SignalDirection, Status
from alphamosaic.integrations.danelfin import DanelfinAdapter
from alphamosaic.integrations.tradingagents import _structured_verdict
from alphamosaic.signals_fusion import SignalFusionEngine


def _signal(**kwargs) -> FusionSignal:
    now = datetime.now(UTC) - timedelta(minutes=1)
    return FusionSignal(
        source=kwargs.get("source", "test"),
        symbol="AAPL",
        direction=kwargs.get("direction", SignalDirection.BULLISH),
        strength=0.8,
        reliability=0.5,
        data_quality=DataQuality.REAL,
        evidence_ids=kwargs.get("evidence_ids", []),
        dependency_keys=kwargs.get("dependency_keys", []),
        content_fingerprint=kwargs.get("content_fingerprint"),
        derived_from=kwargs.get("derived_from", []),
        observed_at=now,
        known_at=now,
        rationale=["fixture evidence"],
    )


def test_danelfin_parser_requires_identity_date_and_score_range() -> None:
    adapter = DanelfinAdapter(api_key="fixture")
    valid, signal, diagnostics = adapter._parse_score(
        "AAPL",
        {"symbol": "AAPL", "ai_score": 8.2, "score_date": "2026-10-10", "sub_scores": {"technical": 7}},
    )
    assert valid is not None and signal is not None and not diagnostics
    assert valid.ai_score == 8.2
    for payload in (
        {"symbol": "MSFT", "ai_score": 8, "score_date": "2026-10-10"},
        {"symbol": "AAPL", "ai_score": 11, "score_date": "2026-10-10"},
        {"symbol": "AAPL", "ai_score": 8},
    ):
        observation, parsed_signal, errors = adapter._parse_score("AAPL", payload)
        assert observation is None and parsed_signal is None and errors


def test_structured_tradingagents_rating_does_not_read_prose() -> None:
    assert _structured_verdict({"final_rating": "Buy", "investment_thesis": ["x"]}) == (
        "BULLISH",
        ["x"],
    )
    assert _structured_verdict({"final_trade_decision": "BUY"}) is None
    assert _structured_verdict({"final_rating": "BUY, but bear risks remain"}) is None
    assert _structured_verdict({"final_rating": "买入"}) is None


def test_fusion_deduplicates_shared_dependencies_fingerprints_and_derivations() -> None:
    result = SignalFusionEngine().fuse(
        "AAPL",
        [
            _signal(source="technical", dependency_keys=["ohlcv:AAPL:2026-10-10"]),
            _signal(source="agent", dependency_keys=["ohlcv:AAPL:2026-10-10"]),
            _signal(source="copy", content_fingerprint="same"),
            _signal(source="copy-2", content_fingerprint="same"),
            _signal(source="derived", derived_from=["ohlcv:AAPL:2026-10-10"]),
        ],
    )
    assert result.sources == ["technical", "copy"]
    assert any("shared underlying dependency" in item for item in result.conflicts)
    assert any("duplicate analysis content" in item for item in result.conflicts)
    assert any("repackaged upstream evidence" in item for item in result.conflicts)


def test_optional_integrations_remain_not_configured_without_keys(tmp_path: Path) -> None:
    from alphamosaic.integrations.tradingagents import TradingAgentsAdapter

    outcome = TradingAgentsAdapter(tmp_path, package_available=False).research("AAPL")
    assert outcome.status == Status.NOT_CONFIGURED
    assert DanelfinAdapter(api_key=None).health().status == Status.NOT_CONFIGURED
