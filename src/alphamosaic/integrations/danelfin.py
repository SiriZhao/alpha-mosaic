"""Danelfin MCP adapter using the official MCP ClientSession transport.

The adapter discovers the server's advertised tools and schemas before calling them. It never
assumes a score field is a return probability and fails closed when a response cannot be validated
as a dated, symbol-matched score.
"""

import asyncio
import hashlib
import json
import os
import threading
import time
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from typing import Any

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from alphamosaic.core.contracts import (
    DanelfinScoreObservation,
    DataQuality,
    FusionSignal,
    ProviderHealth,
    SignalDirection,
    Status,
    utc_now,
)

SOURCE_URL = "https://mcp.danelfin.com/docs/en"
MCP_VERSION = "mcp-sdk-client-session"
OFFICIAL_TOOLS = {
    "stock_score": "get_stock_score",
    "etf_score": "get_etf_score",
    "ranking": "get_top_ranked",
    "screening": "screen_by_score",
    "history": "get_score_history",
}


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    return value


def _payload(result: Any) -> dict[str, Any] | None:
    """Extract structured JSON from a CallToolResult without interpreting prose as facts."""

    dumped = _jsonable(result)
    if isinstance(dumped, dict) and dumped.get("isError"):
        return None
    if isinstance(dumped, dict):
        structured = dumped.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        content = dumped.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        parsed = json.loads(str(item.get("text", "")))
                    except json.JSONDecodeError:
                        continue
                    if isinstance(parsed, dict):
                        return parsed
    return dumped if isinstance(dumped, dict) else None


def _find(payload: dict[str, Any], names: set[str]) -> Any:
    for key, value in payload.items():
        if key.lower() in names:
            return value
        if isinstance(value, dict):
            found = _find(value, names)
            if found is not None:
                return found
    return None


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, (str, date, datetime)):
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    else:
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            try:
                parsed = datetime.combine(date.fromisoformat(text[:10]), datetime.min.time())
            except ValueError:
                return None
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)


def _number(value: Any, lower: float, upper: float) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if lower <= number <= upper else None


def _schema_arguments(
    schema: dict[str, Any], symbol: str, start: str | None = None, end: str | None = None
) -> dict[str, Any] | None:
    """Build only arguments advertised by the live tool schema; unknown fields fail closed."""

    properties = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    result: dict[str, Any] = {}
    for name in properties:
        lowered = name.lower()
        if lowered in {"symbol", "ticker", "stock", "asset", "security"}:
            result[name] = symbol
        elif lowered in {"start", "start_date", "from", "from_date", "date_from"} and start:
            result[name] = start
        elif lowered in {"end", "end_date", "to", "to_date", "date_to"} and end:
            result[name] = end
    return result if required.issubset(result) else None


class DanelfinAdapter:
    name = "Danelfin"

    def __init__(
        self,
        timeout: float = 20,
        cache_ttl: timedelta = timedelta(hours=6),
        min_interval: float = 0.2,
        monthly_budget: int | None = None,
        endpoint: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
    ):
        self.endpoint = endpoint or os.environ.get("DANELFIN_MCP_URL", "https://mcp.danelfin.com/mcp")
        self.api_key = api_key if api_key is not None else os.environ.get("DANELFIN_API_KEY")
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.min_interval = min_interval
        self.monthly_budget = monthly_budget
        self._client = client
        self._cache: dict[tuple[str, str], tuple[float, Any]] = {}
        self._lock = asyncio.Lock()
        self._request_count = 0
        self._sync_lock = threading.Lock()
        self._last_test: dict[str, str] = {}
        self._last_request = 0.0

    def health(self) -> ProviderHealth:
        configured = bool(self.api_key)
        return ProviderHealth(
            name=self.name,
            status=Status.PARTIAL if configured else Status.NOT_CONFIGURED,
            checked_at=utc_now(),
            version=MCP_VERSION,
            capabilities=list(OFFICIAL_TOOLS),
            diagnostics=[
                "Official MCP ClientSession over Streamable HTTP; no website scraping",
                "AI score is a 1-10 conviction score, not a return probability",
                "No credentials are persisted by this adapter",
            ] if configured else ["DANELFIN_API_KEY is absent"],
            lifecycle={
                "installed": "INSTALLED",
                "configured": "CONFIGURED" if configured else "NOT_CONFIGURED",
                "connected": "CONNECTED" if self._last_test else "NOT_TESTED",
                "data_validated": "VALIDATED" if self._last_test.get("data_validated") == "true" else "NOT_TESTED",
                "research_ready": "READY" if self._last_test.get("data_validated") == "true" else "NO",
            },
            last_test=dict(self._last_test),
        )

    @property
    def quota(self) -> dict[str, int | None]:
        return {"requests": self._request_count, "monthly_budget": self.monthly_budget}

    @asynccontextmanager
    async def _session_tools(self) -> AsyncIterator[tuple[ClientSession, list[Any]]]:
        if not self.api_key:
            raise RuntimeError("NOT_CONFIGURED")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Keep AnyIO transport scopes and their cleanup in the same task. An
        # outer native deadline bounds negotiation, tool calls and cleanup.
        client = self._client or create_mcp_http_client(headers=headers)
        try:
            with anyio.fail_after(self.timeout):
                async with AsyncExitStack() as stack:
                    if self._client is None:
                        await stack.enter_async_context(client)
                    streams = streamable_http_client(self.endpoint, http_client=client)
                    read_stream, write_stream = await stack.enter_async_context(streams)
                    session = await stack.enter_async_context(
                        ClientSession(read_stream, write_stream, read_timeout_seconds=self.timeout)
                    )
                    init = await session.initialize()
                    tools = (await session.list_tools()).tools
                    self._last_test = {
                        "checked_at": utc_now().isoformat(),
                        "protocol_version": str(init.protocol_version),
                        "tool_count": str(len(tools)),
                        "data_validated": "false",
                    }
                    yield session, tools
        except ExceptionGroup as exc:
            # Task groups wrap transport errors. Preserve mixed failures rather
            # than misclassifying a non-timeout fault as a deadline expiration.
            timed_out, other = exc.split((TimeoutError, httpx.TimeoutException))
            if timed_out is not None and other is None:
                raise TimeoutError("Danelfin MCP transport timeout") from exc
            raise

    async def _call(
        self, capability: str, symbol: str, arguments: dict[str, Any] | None = None
    ) -> tuple[Status, Any, list[str]]:
        if not self.api_key:
            return Status.NOT_CONFIGURED, None, ["DANELFIN_API_KEY is absent"]
        key = (capability, json.dumps(arguments or {"symbol": symbol}, sort_keys=True))
        cached = self._cache.get(key)
        if cached and cached[0] > time.monotonic():
            return Status.OK, cached[1], []
        if self.monthly_budget is not None and self._request_count >= self.monthly_budget:
            return Status.RATE_LIMITED, None, ["configured monthly request budget exhausted"]
        async with self._lock:
            delay = self.min_interval - (time.monotonic() - self._last_request)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_request = time.monotonic()
            self._request_count += 1
            try:
                async with self._session_tools() as (session, tools):
                    tool_name = OFFICIAL_TOOLS[capability]
                    advertised = next((tool for tool in tools if tool.name == tool_name), None)
                    if advertised is None:
                        return Status.UNSUPPORTED, None, [f"official tool {tool_name} was not advertised"]
                    call_args = arguments or _schema_arguments(advertised.input_schema, symbol)
                    if call_args is None:
                        return Status.UNSUPPORTED, None, [f"required schema fields for {tool_name} are unknown"]
                    result = await session.call_tool(tool_name, call_args)
                    payload = _payload(result)
                    if payload is None:
                        return Status.INVALID_DATA, None, [f"{tool_name} returned an MCP error or no structured JSON"]
                # A failed cleanup must not leave an apparently successful cache hit.
                self._cache[key] = (time.monotonic() + self.cache_ttl.total_seconds(), payload)
                return Status.OK, payload, []
            except TimeoutError:
                return Status.TIMEOUT, None, ["Danelfin MCP ClientSession timeout"]
            except httpx.TimeoutException:
                return Status.TIMEOUT, None, ["Danelfin MCP transport timeout"]
            except (httpx.HTTPError, OSError, RuntimeError, ValueError, ExceptionGroup) as exc:
                text = str(exc).lower()
                status = Status.RATE_LIMITED if "429" in text or "quota" in text else Status.UNAVAILABLE
                return status, None, [f"Danelfin MCP {type(exc).__name__}"]

    async def list_tools(self) -> tuple[Status, list[dict[str, Any]], list[str]]:
        if not self.api_key:
            return Status.NOT_CONFIGURED, [], ["DANELFIN_API_KEY is absent"]
        try:
            async with self._session_tools() as (_, tools):
                return Status.OK, [_jsonable(tool) for tool in tools], []
        except TimeoutError:
            return Status.TIMEOUT, [], ["Danelfin MCP session timeout"]
        except Exception as exc:
            return Status.UNAVAILABLE, [], [f"Danelfin MCP session: {type(exc).__name__}"]

    async def capability(
        self,
        name: str,
        symbol: str = "",
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call an advertised official capability without guessing its response semantics."""

        if name not in OFFICIAL_TOOLS:
            return {"status": Status.UNSUPPORTED.value, "diagnostics": [f"unsupported capability: {name}"]}
        status, payload, diagnostics = await self._call(name, symbol.upper(), arguments)
        return {
            "status": status.value,
            "capability": name,
            "source": self.name,
            "result": payload,
            "diagnostics": diagnostics,
        }

    async def ranking(self, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.capability("ranking", arguments=arguments)

    async def screening(self, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.capability("screening", arguments=arguments)

    async def score_history(
        self, symbol: str, start: str | None = None, end: str | None = None
    ) -> dict[str, Any]:
        arguments = {key: value for key, value in {"symbol": symbol, "start": start, "end": end}.items() if value}
        return await self.capability("history", symbol, arguments)

    async def score(self, symbol: str) -> dict[str, Any]:
        normalized = symbol.upper()
        status, result, diagnostics = await self._call("stock_score", normalized)
        response: dict[str, Any] = {
            "symbol": normalized,
            "status": status.value,
            "source": self.name,
            "diagnostics": diagnostics,
        }
        if status != Status.OK:
            return response
        try:
            observation, signal, parse_diagnostics = self._parse_score(normalized, result)
        except (TypeError, ValueError) as exc:
            observation, signal, parse_diagnostics = None, None, [f"validated score contract rejected response: {type(exc).__name__}"]
        if observation is None or signal is None:
            response["status"] = Status.INVALID_DATA.value
            response["diagnostics"] = parse_diagnostics
            return response
        self._last_test["data_validated"] = "true"
        response["observation"] = observation.model_dump(mode="json")
        response["signal"] = signal.model_dump(mode="json")
        return response

    def _parse_score(
        self, symbol: str, payload: dict[str, Any]
    ) -> tuple[DanelfinScoreObservation | None, FusionSignal | None, list[str]]:
        returned = _find(payload, {"symbol", "ticker", "stock", "security"})
        if str(returned or "").upper() != symbol:
            return None, None, ["response symbol does not match requested security"]
        score = _number(_find(payload, {"ai_score", "aiscore", "score"}), 1, 10)
        when = _parse_date(_find(payload, {"score_date", "scoredate", "date", "as_of", "timestamp"}))
        now = utc_now()
        if score is None or when is None or when > now:
            return None, None, ["score, 1-10 range, and non-future score date are required"]
        subs: dict[str, float | None] = {}
        raw_subs = _find(payload, {"subscores", "sub_scores"})
        if isinstance(raw_subs, dict):
            for key, value in raw_subs.items():
                number = _number(value, 1, 10)
                if number is not None:
                    subs[str(key)] = number
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        score_date = when.date()
        observation = DanelfinScoreObservation(
            symbol=symbol,
            source="Danelfin MCP get_stock_score",
            source_url=SOURCE_URL,
            observed_at=when,
            known_at=when,
            as_of=when,
            currency="USD",
            data_quality=DataQuality.REAL,
            adjustment_policy="NOT_APPLICABLE",
            provenance={"transport": "official MCP ClientSession", "retrieved_at": now.isoformat()},
            license_scope="Danelfin service terms; no redistribution assumed",
            factor="danelfin_ai_score",
            value=score,
            methodology="Official Danelfin 1-10 AI conviction score; not a return probability",
            validated_predictive_probability=False,
            ai_score=score,
            identity_match=True,
            sub_scores=subs,
            score_date=score_date,
            valid_until=when + timedelta(days=1),
            capability="STOCK_SCORE",
            response_id=str(_find(payload, {"id", "score_id"}) or "") or None,
            content_fingerprint=fingerprint,
        )
        direction = (
            SignalDirection.BULLISH
            if score >= 7
            else SignalDirection.BEARISH
            if score <= 4
            else SignalDirection.NEUTRAL
        )
        signal = FusionSignal(
            source="Danelfin MCP get_stock_score",
            symbol=symbol,
            direction=direction,
            strength=round(abs(score - 5.5) / 4.5, 4),
            reliability=None,
            horizon="daily-to-weeks",
            data_quality=DataQuality.REAL,
            evidence_ids=[observation.response_id] if observation.response_id else [],
            observed_at=when,
            known_at=when,
            rationale=[f"Danelfin AI score {score:.1f}/10; conviction scale only"],
            dependency_keys=[f"danelfin:{symbol}:{score_date.isoformat()}"],
            content_fingerprint=fingerprint,
        )
        return observation, signal, []

    def score_sync(self, symbol: str) -> dict[str, Any]:
        with self._sync_lock:
            return asyncio.run(self.score(symbol))
