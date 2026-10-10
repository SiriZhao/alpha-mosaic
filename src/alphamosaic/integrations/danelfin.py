"""Official Danelfin MCP client with cache, deduplication and quota telemetry."""

import asyncio
import os
import threading
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from alphamosaic.core.contracts import DataQuality, ProviderHealth, Status, utc_now


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
        client: httpx.AsyncClient | None = None,
    ):
        self.endpoint = endpoint or os.environ.get("DANELFIN_MCP_URL", "https://mcp.danelfin.com/mcp")
        self.api_key = api_key if api_key is not None else os.environ.get("DANELFIN_API_KEY")
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.min_interval = min_interval
        self.monthly_budget = monthly_budget
        self._client = client
        self._cache: dict[tuple[str, str], tuple[float, Any]] = {}
        self._inflight: dict[tuple[str, str], asyncio.Future[Any]] = {}
        self._lock = asyncio.Lock()
        self._request_times: deque[float] = deque()
        self._last_request = 0.0
        self._request_count = 0
        self._sync_lock = threading.Lock()

    def health(self) -> ProviderHealth:
        configured = bool(self.api_key)
        return ProviderHealth(
            name=self.name,
            status=Status.OK if configured else Status.NOT_CONFIGURED,
            checked_at=utc_now(),
            version=None,
            capabilities=["AI_SCORE", "RANKING", "DAILY_HISTORY", "SUBSCORES", "FILTER"],
            diagnostics=[
                "Official MCP over HTTPS; no website scraping",
                "Score is research evidence, not a return probability",
                "No credentials are persisted by this adapter",
            ] if configured else ["DANELFIN_API_KEY is absent"],
        )

    @property
    def quota(self) -> dict[str, int | None]:
        return {"requests": self._request_count, "monthly_budget": self.monthly_budget}

    async def _request(self, method: str, params: dict[str, Any]) -> Any:
        if not self.api_key:
            raise RuntimeError("NOT_CONFIGURED")
        key = (method, repr(sorted(params.items())))
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and cached[0] > now:
            return cached[1]
        async with self._lock:
            cached = self._cache.get(key)
            if cached and cached[0] > time.monotonic():
                return cached[1]
            while time.monotonic() - self._last_request < self.min_interval:
                await asyncio.sleep(self.min_interval - (time.monotonic() - self._last_request))
            if self.monthly_budget is not None and self._request_count >= self.monthly_budget:
                raise RuntimeError("RATE_LIMITED")
            self._last_request = time.monotonic()
            self._request_count += 1
            client = self._client or httpx.AsyncClient(timeout=self.timeout)
            close = self._client is None
            try:
                response = await client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
                    json={"jsonrpc": "2.0", "id": self._request_count, "method": method, "params": params},
                )
                response.raise_for_status()
                body = response.json()
                if "error" in body:
                    raise RuntimeError(str(body["error"]))
                value = body.get("result")
                self._cache[key] = (time.monotonic() + self.cache_ttl.total_seconds(), value)
                return value
            finally:
                if close:
                    await client.aclose()

    async def list_tools(self) -> tuple[Status, list[dict[str, Any]], list[str]]:
        if not self.api_key:
            return Status.NOT_CONFIGURED, [], ["DANELFIN_API_KEY is absent"]
        try:
            result = await self._request("tools/list", {})
            return Status.OK, list((result or {}).get("tools", [])), []
        except httpx.TimeoutException:
            return Status.TIMEOUT, [], ["Danelfin MCP timeout"]
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            status = Status.RATE_LIMITED if "RATE_LIMITED" in str(exc) or "429" in str(exc) else Status.UNAVAILABLE
            return status, [], [f"Danelfin MCP: {type(exc).__name__}"]

    async def call_tool(self, tool: str, arguments: dict[str, Any]) -> tuple[Status, Any, list[str]]:
        if not self.api_key:
            return Status.NOT_CONFIGURED, None, ["DANELFIN_API_KEY is absent"]
        try:
            value = await self._request("tools/call", {"name": tool, "arguments": arguments})
            return Status.OK, value, []
        except httpx.TimeoutException:
            return Status.TIMEOUT, None, ["Danelfin MCP timeout"]
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            status = Status.RATE_LIMITED if "RATE_LIMITED" in str(exc) or "429" in str(exc) else Status.UNAVAILABLE
            return status, None, [f"Danelfin MCP: {type(exc).__name__}"]

    async def score(self, symbol: str) -> dict[str, Any]:
        status, tools, diagnostics = await self.list_tools()
        if status != Status.OK:
            return {"symbol": symbol, "status": status.value, "diagnostics": diagnostics}
        names = {str(item.get("name")) for item in tools}
        candidate = next((name for name in ("get_stock_score", "get_ai_score", "stock_score") if name in names), None)
        if candidate is None:
            return {"symbol": symbol, "status": Status.UNSUPPORTED.value, "diagnostics": ["score tool not advertised by Danelfin MCP"]}
        status, result, diagnostics = await self.call_tool(candidate, {"symbol": symbol})
        return {
            "symbol": symbol,
            "status": status.value,
            "source": self.name,
            "data_quality": DataQuality.REAL.value if status == Status.OK else DataQuality.MISSING.value,
            "observed_at": datetime.now(UTC).isoformat(),
            "result": result,
            "diagnostics": diagnostics,
        }

    def score_sync(self, symbol: str) -> dict[str, Any]:
        with self._sync_lock:
            return asyncio.run(self.score(symbol))
