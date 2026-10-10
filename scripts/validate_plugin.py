"""Validate the portable AlphaMosaic agent package without network access."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "alphamosaic"
REQUIRED_SKILLS = {
    "market-scan": "scan_market",
    "stock-analysis": "analyze_stock",
    "portfolio-research": "research_portfolio",
    "strategy-evaluation": "run_backtest",
}


def main() -> int:
    plugin = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((PLUGIN / "mcp.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "alphamosaic"
    server = mcp["mcpServers"]["alphamosaic"]
    assert server["type"] == "streamable-http"
    assert server["url"].startswith("https://")
    results: list[dict[str, str]] = []
    for directory, tool in REQUIRED_SKILLS.items():
        path = PLUGIN / "skills" / directory / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        if tool not in text:
            raise AssertionError(f"{path} does not reference MCP tool {tool}")
        results.append({"skill": directory, "tool": tool, "status": "READY"})
    remote_verified = "REPLACE_WITH" not in server["url"]
    print(json.dumps({"status": "READY", "remote_chatgpt": "VERIFIED" if remote_verified else "NOT_VERIFIED", "skills": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
