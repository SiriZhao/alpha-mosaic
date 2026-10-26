"""Unified least-privilege MCP surface for local and remote transports."""

import asyncio
import re
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

from alphamosaic.core.service import ApplicationService


class JobManager:
    def __init__(self, max_jobs: int = 32, max_workers: int = 2) -> None:
        if not 1 <= max_workers <= max_jobs <= 128:
            raise ValueError("bounded job/worker limits required")
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="alphamosaic-job")
        self._jobs: dict[str, Future[Any]] = {}
        self._max_jobs = max_jobs
        self._lock = threading.RLock()

    def submit(self, function: Callable[[], Any]) -> str:
        with self._lock:
            if len(self._jobs) >= self._max_jobs:
                expired = next((key for key, future in self._jobs.items() if future.done()), None)
                if expired is not None:
                    del self._jobs[expired]
                else:
                    raise ValueError("local job quota exhausted; wait for an existing job")
            job_id = uuid4().hex
            self._jobs[job_id] = self._executor.submit(function)
            return job_id

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"status": "UNKNOWN_OR_EXPIRED", "job_id": job_id}
            cancelled = job.cancel()
        return {"status": "CANCELLED" if cancelled else "ALREADY_FINISHED" if job.done() else "RUNNING_USE_DECLARED_WORKER_DEADLINE", "job_id": job_id}

    def status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            return {"status": "FAILED", "job_id": job_id, "diagnostics": ["unknown or expired job; persisted experiments/plans remain inspectable"]}
        if job.cancelled():
            return {"status": "CANCELLED", "job_id": job_id}
        if not job.done():
            return {"status": "RUNNING", "job_id": job_id}
        try:
            return {"status": "READY", "job_id": job_id, "result": job.result()}
        except Exception as exc:
            return {"status": "FAILED", "job_id": job_id, "diagnostics": [type(exc).__name__]}


_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.-]{0,14}$")


def _symbols(values: list[str], *, minimum: int, maximum: int) -> list[str] | dict[str, Any]:
    normalized = list(dict.fromkeys(item.strip().upper() for item in values if isinstance(item, str)))
    if not minimum <= len(normalized) <= maximum:
        return {"status": "INVALID_INPUT", "diagnostics": [f"symbols must contain {minimum}..{maximum} unique values"]}
    invalid = [item for item in normalized if not _SYMBOL.fullmatch(item)]
    if invalid:
        return {"status": "INVALID_INPUT", "diagnostics": [f"invalid symbol: {item}" for item in invalid]}
    return normalized


def _annotations(idempotent: bool = True, *, read_only: bool = True, open_world: bool = True) -> ToolAnnotations:
    return ToolAnnotations(read_only_hint=read_only, destructive_hint=False, idempotent_hint=idempotent, open_world_hint=open_world)


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

    @server.tool(annotations=_annotations())
    def framework_matrix() -> list[dict[str, Any]]:
        return application.framework_matrix()

    @server.tool(annotations=_annotations())
    def research_datasets() -> list[dict[str, Any]]:
        """List local versioned datasets; no arbitrary filesystem access."""
        return application.research_datasets()

    @server.tool(annotations=_annotations())
    def research_experiments() -> list[dict[str, Any]]:
        return application.research_experiments()

    @server.tool(annotations=_annotations(False, read_only=False, open_world=False))
    def plan_research(config: dict[str, Any]) -> dict[str, Any]:
        return application.plan_research(config)

    @server.tool(annotations=_annotations(False, read_only=False, open_world=False))
    def run_research_plan(plan_id: str) -> dict[str, Any]:
        application.research_plan(plan_id)
        return {"status": "READY", "job_id": jobs.submit(lambda: application.run_research_plan(plan_id))}

    @server.tool(annotations=_annotations(False, read_only=False, open_world=False))
    def reconcile_research_plan(plan_id: str) -> dict[str, Any]:
        """Inspect interrupted local attempts and close their audit; never retry trials."""
        application.research_plan(plan_id)
        return {"status": "READY", "job_id": jobs.submit(lambda: application.reconcile_research_plan(plan_id)),
                "message": "Local saved-evidence reconciliation only; no experiments rerun. Poll job_status."}

    @server.tool(annotations=_annotations(open_world=False))
    def research_plan_status(plan_id: str) -> dict[str, Any]:
        return application.research_plan(plan_id)

    @server.tool(annotations=_annotations(open_world=False))
    def research_plan_report(plan_id: str) -> dict[str, Any]:
        return application.research_plan_report(plan_id)

    @server.tool(annotations=_annotations(False, read_only=False, open_world=False))
    def cancel_queued_job(job_id: str) -> dict[str, Any]:
        return jobs.cancel(job_id)

    @server.tool(annotations=_annotations(False))
    def run_research_experiment(config: dict[str, Any]) -> dict[str, Any]:
        """Run a typed bounded local simulation; no broker or external code execution."""
        from alphamosaic.experiments.runner import ExperimentConfig
        checked = ExperimentConfig.model_validate(config).model_dump(mode="json")
        job_id = jobs.submit(lambda: application.research_experiment(checked))
        return {"status": "READY", "job_id": job_id, "message": "local research only; poll job_status"}

    @server.tool(annotations=_annotations())
    def compare_research_experiments(experiment_ids: list[str]) -> dict[str, Any]:
        return application.research_comparison(experiment_ids)

    @server.tool(annotations=_annotations(False))
    async def scan_market(universe_limit: int = 30, top: int = 10) -> dict[str, Any]:
        report = await asyncio.to_thread(application.scan, universe_limit=universe_limit, top=top, persist=True)
        return {"status": "READY" if report.status.value == "OK" else "DEGRADED", "report": report.model_dump(mode="json", exclude={"source_batches"})}

    @server.tool(annotations=_annotations(False))
    def discover_opportunities(mode: str = "FAST", universe_limit: int = 30, top: int = 10,
                               deep: int = 3, pool: str = "BROAD_LIQUIDITY",
                               symbols: list[str] | None = None, resume: bool = False) -> dict[str, Any]:
        job_id = jobs.submit(lambda: application.discover_opportunities(mode, universe_limit, top, deep, pool, symbols, resume))
        return {"status": "READY", "job_id": job_id, "message": "poll job_status"}

    @server.tool(annotations=_annotations())
    def rank_opportunities(run_id: str | None = None) -> dict[str, Any]:
        return application.ranking(run_id)

    @server.tool(annotations=_annotations())
    async def analyze_stock(symbol: str) -> dict[str, Any]:
        result = await asyncio.to_thread(application.analyze, symbol)
        return {"status": "READY" if result["status"] == "OK" else "DEGRADED", **result}

    @server.tool(annotations=_annotations(False))
    async def compare_stocks(symbols: list[str]) -> dict[str, Any]:
        checked = _symbols(symbols, minimum=2, maximum=10)
        if isinstance(checked, dict):
            return checked
        return await asyncio.to_thread(application.compare, checked)

    @server.tool(annotations=_annotations(False))
    def research_portfolio(symbols: list[str], profile: str = "FAST") -> dict[str, Any]:
        checked = _symbols(symbols, minimum=1, maximum=5)
        if isinstance(checked, dict):
            return checked
        job_id = jobs.submit(lambda: application.research_portfolio(checked, profile.upper()))
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
    def evaluate_forward(signal_id: str) -> dict[str, Any]:
        return application.evaluate_forward(signal_id)

    @server.tool(annotations=_annotations(False))
    def generate_investment_report(symbols: list[str], profile: str = "FAST") -> dict[str, Any]:
        checked = _symbols(symbols, minimum=1, maximum=5)
        if isinstance(checked, dict):
            return checked
        return application.investment_report(checked, profile.upper())

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
