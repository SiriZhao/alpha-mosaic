"""Least-privilege MCP 2.x server. No filesystem, shell, credential or order tools."""

import asyncio
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

from alphamosaic.core.service import ApplicationService


def create_server(service: ApplicationService | None = None) -> MCPServer:
    application = service or ApplicationService()
    server = MCPServer(
        "AlphaMosaic",
        instructions="Research only. Heuristic ranking is not a return probability. No broker execution.",
    )
    annotations = ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True
    )

    @server.tool(annotations=annotations)
    def get_system_status() -> dict[str, Any]:
        """Return installation, market-calendar and research-only permission status."""
        return application.status()

    @server.tool(annotations=annotations)
    def list_providers() -> list[dict[str, Any]]:
        """List adapter capabilities; install health does not prove live data access."""
        return application.providers()

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=True, destructive_hint=False, idempotent_hint=False, open_world_hint=True
        )
    )
    async def scan_opportunities(universe_limit: int = 30, top: int = 10) -> dict[str, Any]:
        """Discover and rank a bounded current US pool. No report writes or orders."""
        report = await asyncio.to_thread(
            application.scan, universe_limit=universe_limit, top=top, persist=False
        )
        return report.model_dump(mode="json")

    @server.tool(annotations=annotations)
    async def get_stock_snapshot(symbol: str) -> dict[str, Any]:
        """Fetch a validated stock snapshot with provenance and missing-data flags."""
        return await asyncio.to_thread(application.analyze, symbol)

    @server.tool(annotations=annotations)
    def get_candidate_ranking() -> dict[str, Any]:
        """Return the saved ranking with its run ID and data cutoff."""
        return application.ranking()

    @server.tool(annotations=annotations)
    def get_research_report() -> dict[str, Any]:
        """Return the latest schema-validated research report in the configured store."""
        return application.latest_report()

    return server
