import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

import pytest

from alphamosaic.core.contracts import (
    DataQuality,
    HistoricalBar,
    SecurityIdentity,
)
from alphamosaic.data.validation import validate_batch
from alphamosaic.factors.engine import FactorEngine
from alphamosaic.mcp.server import create_server
from alphamosaic.portfolio.risk import assess_weights


def bars(symbol: str, count: int = 80) -> list[HistoricalBar]:
    now = datetime.now(UTC)
    result = []
    for index in range(count):
        session = date.today() - timedelta(days=count - index)
        close = 100 + index
        result.append(
            HistoricalBar(
                symbol=symbol,
                source="fixture",
                source_url="https://example.invalid/fixture",
                observed_at=now - timedelta(days=count - index),
                known_at=now,
                as_of=now,
                currency="USD",
                data_quality=DataQuality.FIXTURE,
                adjustment_policy="SPLIT",
                provenance={"test": "true"},
                license_scope="test-only",
                session=session,
                open=close - 1,
                high=close + 1,
                low=close - 2,
                close=close,
                volume=1_000_000,
            )
        )
    return result


def identity(symbol: str) -> SecurityIdentity:
    return SecurityIdentity(
        symbol=symbol,
        exchange="NASDAQ-GS",
        currency="USD",
        active=True,
        identity_source="fixture",
        identity_verified=True,
        as_of=datetime.now(UTC),
    )


def test_factor_engine_is_deterministic_and_keeps_missing_factors_null() -> None:
    result = FactorEngine().calculate(bars("AAA"), bars("SPY"))
    assert result["momentum_63d"] == pytest.approx(63 / 116)
    assert result["quality_roe"] is None
    assert result["value_earnings_yield"] is None


def test_validation_rejects_identity_mismatch_and_future_information() -> None:
    now = datetime.now(UTC)
    current = bars("AAA", 80)
    current[0] = current[0].model_copy(update={"symbol": "BBB"})
    current[1] = current[1].model_copy(update={"known_at": now + timedelta(minutes=1)})
    flags = validate_batch(identity("AAA"), current, now)
    assert "SECURITY_IDENTITY_MISMATCH" in flags
    assert "FUTURE_INFORMATION" in flags


def test_risk_weights_are_long_only_and_bounded() -> None:
    assert assess_weights({"AAA": 0.05, "BBB": 0.05}) == []
    assert "CONCENTRATION:AAA" in assess_weights({"AAA": 0.11})
    with pytest.raises(ValueError):
        assess_weights({"AAA": -0.1})


def test_mcp_server_exposes_only_read_tools() -> None:
    server = create_server()
    names = {tool.name for tool in server._tool_manager.list_tools()}
    assert {"system_status", "provider_health", "scan_market", "analyze_stock", "run_backtest"} <= names
    assert {"get_system_status", "list_providers", "scan_opportunities"} <= names
    status = asyncio.run(server._tool_manager.call_tool("get_system_status", {}, cast(Any, None)))
    assert status["broker_enabled"] is False
    assert status["mode"] == "RESEARCH_ONLY"
