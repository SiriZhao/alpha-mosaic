import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from starlette.testclient import TestClient

from alphamosaic.core.contracts import DataQuality, FusionSignal, SignalDirection, Status
from alphamosaic.integrations.danelfin import DanelfinAdapter
from alphamosaic.integrations.registry import IntegrationRegistry
from alphamosaic.integrations.tradingagents import TradingAgentsAdapter
from alphamosaic.mcp.remote import create_remote_app
from alphamosaic.signals_fusion import SignalFusionEngine


def signal(source: str, direction: SignalDirection, evidence: str) -> FusionSignal:
    now = datetime.now(UTC)
    return FusionSignal(
        source=source,
        symbol="AAA",
        direction=direction,
        strength=0.8,
        reliability=0.5,
        horizon="weeks",
        data_quality=DataQuality.HISTORICAL,
        evidence_ids=[evidence],
        observed_at=now - timedelta(minutes=1),
        known_at=now - timedelta(minutes=1),
        rationale=[source + " rationale"],
    )


def test_optional_integrations_fail_closed_without_credentials() -> None:
    outcome = TradingAgentsAdapter(Path("runtime"), package_available=False).research("AAPL")
    assert outcome.status == Status.NOT_CONFIGURED
    assert outcome.verdict is None
    result = asyncio.run(DanelfinAdapter(api_key=None).score("AAPL"))
    assert result["status"] == Status.NOT_CONFIGURED.value
    records = {item.name: item for item in IntegrationRegistry().records()}
    assert records["Danelfin"].status.value == "READY_UNCONFIGURED"


def test_fusion_detects_conflict_and_duplicate_evidence() -> None:
    result = SignalFusionEngine().fuse("AAA", [
        signal("technical", SignalDirection.BULLISH, "bar-1"),
        signal("fundamental", SignalDirection.BEARISH, "bar-2"),
        signal("dependent", SignalDirection.BULLISH, "bar-1"),
    ])
    assert result.direction == SignalDirection.CONFLICTED
    assert any("overlap" in item for item in result.conflicts)
    assert result.research_confidence is None


def test_remote_requires_a_long_bearer_token() -> None:
    try:
        create_remote_app(token="short")
    except ValueError as exc:
        assert "16 characters" in str(exc)
    else:
        raise AssertionError("remote app must reject short tokens")


def test_remote_streamable_http_initialize_and_tools() -> None:
    token = "t" * 32
    app = create_remote_app(token=token)
    with TestClient(app) as client:
        headers = {
            "Host": "127.0.0.1:80",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        initialize = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "acceptance", "version": "1"},
            },
        }
        response = client.post("/mcp", headers=headers, json=initialize)
        assert response.status_code == 200
        session_id = response.headers["mcp-session-id"]
        assert "AlphaMosaic" in response.text
        headers["mcp-session-id"] = session_id
        listed = client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert listed.status_code == 200
        assert "system_status" in listed.text


def test_remote_rejects_non_local_http_and_records_redacted_audit(tmp_path: Path) -> None:
    token = "t" * 32
    audit = tmp_path / "audit.jsonl"
    app = create_remote_app(token=token, audit_path=audit, allow_insecure_localhost=False)
    with TestClient(app) as client:
        blocked = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert blocked.status_code == 400
        assert token not in audit.read_text(encoding="utf-8")


def test_danelfin_timeout_and_budget_are_explicit() -> None:
    async def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated timeout", request=request)

    async def run() -> None:
        transport = httpx.MockTransport(timeout_handler)
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = DanelfinAdapter(api_key="test-key", client=client, min_interval=0, timeout=0.01)
            result = await adapter.score("AAPL")
            assert result["status"] == Status.TIMEOUT.value
            assert adapter.quota["requests"] == 1
            limited = DanelfinAdapter(api_key="test-key", monthly_budget=0, min_interval=0, client=client)
            result = await limited.score("AAPL")
            assert result["status"] == Status.RATE_LIMITED.value

    asyncio.run(run())
