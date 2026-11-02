"""Offline cancellation, ownership and task-cleanup regressions for the MCP adapter."""

import asyncio
import gc
import warnings
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest

from alphamosaic.core.contracts import Status
from alphamosaic.integrations import danelfin
from alphamosaic.integrations.danelfin import DanelfinAdapter


@pytest.mark.parametrize("behavior", ["read_timeout", "deadline"])
def test_real_mcp_timeout_cleanup_leaves_no_tasks_or_unawaited_coroutines(behavior: str) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if behavior == "deadline":
            await asyncio.sleep(10)
        raise httpx.ReadTimeout("deliberate offline transport timeout", request=request)

    async def exercise() -> None:
        baseline = asyncio.all_tasks()
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            for _ in range(4):
                adapter = DanelfinAdapter(api_key="test-only", client=client, timeout=0.02, min_interval=0)
                outcome = await adapter.score("AAPL")
                assert outcome["status"] == Status.TIMEOUT.value
                assert not client.is_closed
                await asyncio.sleep(0)
                gc.collect()
                assert asyncio.all_tasks() <= baseline

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        asyncio.run(exercise())
        gc.collect()
    assert not [warning for warning in captured if issubclass(warning.category, RuntimeWarning)]


def install_lifecycle_doubles(monkeypatch: pytest.MonkeyPatch, stage: str):
    events = []
    started = asyncio.Event()

    def event(name: str) -> None:
        events.append((name, asyncio.current_task()))

    async def operation(name: str) -> None:
        event(name)
        if name == stage:
            started.set()
            await asyncio.sleep(10)

    class Client:
        async def __aenter__(self):
            event("client-enter")
            return self

        async def __aexit__(self, *args):
            event("client-exit")

    client = Client()

    @asynccontextmanager
    async def streams(*args, **kwargs):
        event("streams-enter")
        try:
            yield None, None
        finally:
            event("streams-exit")

    class Session:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            event("session-enter")
            if stage == "session-enter":
                raise ValueError("deliberate session construction failure")
            return self

        async def __aexit__(self, *args):
            await operation("session-exit")

        async def initialize(self):
            await operation("initialize")
            return SimpleNamespace(protocol_version="2025-11-25")

        async def list_tools(self):
            await operation("list-tools")
            return SimpleNamespace(tools=[SimpleNamespace(name="get_top_ranked", input_schema={"properties": {}})])

        async def call_tool(self, *args):
            await operation("call-tool")
            return {"structuredContent": {"items": []}}

    monkeypatch.setattr(danelfin, "create_mcp_http_client", lambda **kwargs: client)
    monkeypatch.setattr(danelfin, "streamable_http_client", streams)
    monkeypatch.setattr(danelfin, "ClientSession", Session)
    return events, started


@pytest.mark.parametrize("stage", ["initialize", "list-tools", "call-tool"])
def test_every_deadline_stage_exits_owned_resources_in_the_entering_task(monkeypatch, stage) -> None:
    async def exercise():
        events, _ = install_lifecycle_doubles(monkeypatch, stage)
        adapter = DanelfinAdapter(api_key="test-only", timeout=0.01, min_interval=0)
        outcome = await adapter.capability("ranking")
        assert outcome["status"] == Status.TIMEOUT.value
        assert [name for name, _ in events][-3:] == ["session-exit", "streams-exit", "client-exit"]
        assert all(task is asyncio.current_task() for _, task in events)

    asyncio.run(exercise())


def test_failed_session_entry_still_closes_transport_and_owned_client(monkeypatch) -> None:
    async def exercise():
        events, _ = install_lifecycle_doubles(monkeypatch, "session-enter")
        outcome = await DanelfinAdapter(api_key="test-only").capability("ranking")
        assert outcome["status"] == Status.UNAVAILABLE.value
        assert [name for name, _ in events][-2:] == ["streams-exit", "client-exit"]

    asyncio.run(exercise())


def test_success_closes_owned_resources_and_reuses_only_validated_cache(monkeypatch) -> None:
    async def exercise():
        events, _ = install_lifecycle_doubles(monkeypatch, "none")
        adapter = DanelfinAdapter(api_key="test-only", min_interval=0)
        first = await adapter.capability("ranking")
        assert first["status"] == Status.OK.value
        assert [name for name, _ in events][-3:] == ["session-exit", "streams-exit", "client-exit"]
        before = list(events)
        assert await adapter.capability("ranking") == first
        assert events == before
        assert adapter.quota["requests"] == 1

    asyncio.run(exercise())


def test_external_cancellation_propagates_and_cleans_up_instead_of_becoming_timeout(monkeypatch) -> None:
    async def exercise():
        events, started = install_lifecycle_doubles(monkeypatch, "initialize")
        adapter = DanelfinAdapter(api_key="test-only", timeout=5)
        task = asyncio.create_task(adapter.capability("ranking"))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert [name for name, _ in events][-3:] == ["session-exit", "streams-exit", "client-exit"]
        assert all(owner is task for _, owner in events)

    asyncio.run(exercise())


def test_cleanup_deadline_does_not_publish_success_to_cache(monkeypatch) -> None:
    async def exercise():
        events, _ = install_lifecycle_doubles(monkeypatch, "session-exit")
        adapter = DanelfinAdapter(api_key="test-only", timeout=0.01, min_interval=0)
        assert (await adapter.capability("ranking"))["status"] == Status.TIMEOUT.value
        assert not adapter._cache
        assert [name for name, _ in events][-2:] == ["streams-exit", "client-exit"]

    asyncio.run(exercise())
