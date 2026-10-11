"""Unified least-privilege MCP surface for local and remote transports."""

import asyncio
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

from alphamosaic.core.service import ApplicationService


class JobManager:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="alphamosaic-job")
        self._jobs: dict[str, Future[Any]] = {}

    def submit(self, function: Callable[[], Any]) -> str:
        job_id = uuid4().hex
        self._jobs[job_id] = self._executor.submit(function)
        return job_id

    def status(self, job_id: str) -> dict[str, Any]:
        job = self._jobs.get(job_id)
        if job is None:
            return {"status": "FAILED", "job_id": job_id, "diagnostics": ["unknown job"]}
        if not job.done():
            return {"status": "RUNNING", "job_id": job_id}
        try:
            return {"status": "READY", "job_id": job_id, "result": job.result()}
        except Exception as exc:
            return {"status": "FAILED", "job_id": job_id, "diagnostics": [type(exc).__name__]}


def _annotations(idempotent: bool = True) -> ToolAnnotations:
    return ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=idempotent, open_world_hint=True)


def create_server(service: ApplicationService | None = None) -> MCPServer:
    application = service or ApplicationService()
    jobs = JobManager()
    server = MCPServer(
        "AlphaMosaic",
        instructions="Research-only financial intelligence. Sourced or missing values only; broker execution disabled.",
    )

    @server.tool(annotations=_annotations())
    def system_status() -> dict[str, Any]:
        return {"status": "READY", "checked_at": datetime.now(UTC).isoformat(), **application.status()}

    @server.tool(annotations=_annotations())
    def provider_health() -> dict[str, Any]:
        return application.provider_health()

    @server.tool(annotations=_annotations(False))
    async def scan_market(universe_limit: int = 30, top: int = 10) -> dict[str, Any]:
        report = await asyncio.to_thread(application.scan, universe_limit=universe_limit, top=top, persist=True, evaluate=False)
        return {"status": "READY" if report.candidates else "DEGRADED", "report": report.model_dump(mode="json")}

    @server.tool(annotations=_annotations(False))
    async def discover_opportunities(mode: str = "FAST", universe_limit: int = 30, top: int = 10,
                                     deep: int = 3, pool: str = "BROAD_LIQUIDITY",
                                     symbols: list[str] | None = None, resume: bool = False) -> dict[str, Any]:
        """Run the bounded Batch 3 opportunity pipeline and persist its run snapshot."""
        return await asyncio.to_thread(application.discover_opportunities, mode.upper(), universe_limit, top, deep, pool.upper(), symbols, resume)

    @server.tool(annotations=_annotations())
    def rank_opportunities() -> dict[str, Any]:
        return {"status": "READY", **application.ranking()}

    @server.tool(annotations=_annotations())
    async def analyze_stock(symbol: str) -> dict[str, Any]:
        result = await asyncio.to_thread(application.analyze, symbol)
        return {"status": "READY" if result["status"] == "OK" else "DEGRADED", **result}

    @server.tool(annotations=_annotations(False))
    async def compare_stocks(symbols: list[str]) -> dict[str, Any]:
        return await asyncio.to_thread(application.compare, symbols)

    @server.tool(annotations=_annotations(False))
    def research_portfolio(symbols: list[str], profile: str = "FAST") -> dict[str, Any]:
        job_id = jobs.submit(lambda: application.research_portfolio(symbols, profile.upper()))
        return {"status": "READY", "job_id": job_id, "message": "research job accepted; poll job_status"}

    @server.tool(annotations=_annotations())
    def job_status(job_id: str) -> dict[str, Any]:
        return jobs.status(job_id)

    @server.tool(annotations=_annotations(False))
    async def evaluate_strategy(symbol: str, strategy: str = "momentum") -> dict[str, Any]:
        return await asyncio.to_thread(application.evaluate_strategy, symbol, strategy)

    @server.tool(annotations=_annotations(False))
    async def run_backtest(symbol: str, strategy: str = "momentum", out_of_sample: bool = False, fee_bps: float = 10) -> dict[str, Any]:
        return await asyncio.to_thread(application.run_backtest, symbol, strategy, out_of_sample, fee_bps)

    @server.tool(annotations=_annotations())
    def get_signal_history(symbol: str | None = None) -> dict[str, Any]:
        return application.signal_history(symbol)

    @server.tool(annotations=_annotations())
    def get_forward_performance(symbol: str | None = None) -> dict[str, Any]:
        return application.forward_performance(symbol)

    @server.tool(annotations=_annotations(False))
    def generate_investment_report(symbols: list[str], profile: str = "FAST") -> dict[str, Any]:
        return application.investment_report(symbols, profile.upper())

    @server.tool(annotations=_annotations())
    def get_system_status() -> dict[str, Any]:
        return system_status()

    @server.tool(annotations=_annotations())
    def list_providers() -> list[dict[str, Any]]:
        return application.providers()

    @server.tool(annotations=_annotations(False))
    async def scan_opportunities(universe_limit: int = 30, top: int = 10) -> dict[str, Any]:
        return await scan_market(universe_limit, top)

    @server.tool(annotations=_annotations())
    async def get_stock_snapshot(symbol: str) -> dict[str, Any]:
        return await analyze_stock(symbol)

    @server.tool(annotations=_annotations())
    def get_candidate_ranking() -> dict[str, Any]:
        return rank_opportunities()

    @server.tool(annotations=_annotations())
    def get_research_report() -> dict[str, Any]:
        return application.latest_report()

    return server
