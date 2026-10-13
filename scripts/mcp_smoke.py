"""Real local MCP handshake and read-only invocation; no market API calls."""

import argparse
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(home: str | None = None, run_id: str | None = None) -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "alphamosaic.cli.app", "mcp", "serve"], env={"ALPHAMOSAIC_HOME": home} if home else None)
    async with stdio_client(params) as streams:
        async with ClientSession(*streams, read_timeout_seconds=30) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("get_system_status", {})
            if result.is_error:
                raise RuntimeError("MCP read-only invocation failed")
            payload = result.structured_content
            if payload is None:
                for item in result.content:
                    if item.type == "text":
                        payload = json.loads(item.text)
                        break
            if not isinstance(payload, dict) or payload.get("broker_enabled") is not False:
                raise RuntimeError("MCP research safety contract failed")
            if run_id:
                ranking = await session.call_tool("rank_opportunities", {"run_id": run_id})
                if ranking.is_error or ranking.structured_content is None or ranking.structured_content.get("run_id") != run_id:
                    raise RuntimeError("MCP ranking run-id mismatch")
            print(json.dumps({"status": "PASSED", "protocol_version": initialized.protocol_version, "tool_count": len(tools.tools), "invocation": "get_system_status", "ranking_run_id": run_id, "broker_enabled": False, "remote_chatgpt": "NOT_VERIFIED"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    asyncio.run(main(args.home, args.run_id))
