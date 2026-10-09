# AlphaMosaic final acceptance record

Date: 2026-10-09 (Asia/Shanghai)

## Verified locally

- OpenBB V5 Nasdaq adapter: live AAPL historical/profile request, 132 rows, provenance and
  reconstructed PIT labels recorded.
- TradingAgents v0.6.0 adapter: official Python API isolated behind a bounded worker with FAST,
  BALANCED and DEEP profiles. Current result: `NOT_CONFIGURED` because the optional package and
  authorized model credentials are absent.
- Danelfin adapter: official remote MCP endpoint, Bearer credential from `DANELFIN_API_KEY`,
  cache, deduplication, rate interval, dynamic budget, timeout and explicit failure statuses.
  Current result: `NOT_CONFIGURED`; no scraping or mock success.
- Signal fusion: chronology, identity, evidence overlap, source dependency and conflict checks.
- Three-stock live research: AAPL, XOM and TSLA. Deterministic factors produced decisions;
  missing external agents remain explicitly unconfigured.
- Local MCP: stdio initialize/list-tools/tool-call handshake succeeded with 19 tools.
- Remote MCP security smoke: `/health` returned 200; unauthenticated `/mcp` returned 401.
- Plugin package: portable `plugin.json`, `mcp.json` and four MCP-calling skills validate as JSON
  and remain marked remote-unverified until a real HTTPS ChatGPT connection is completed.

## Checks

- Ruff: passed.
- Pyright: 0 errors.
- Pytest: 8 passed.
- `uv lock --check`: passed.
- Runtime contains no broker, shell, arbitrary-file, credential or order tool.

## Deliberately unverified

- TradingAgents real model execution: no authorized model key or optional package in the current
  environment.
- Danelfin real score/ranking/history call: no authorized API key.
- Public ChatGPT plugin connection: no public HTTPS endpoint, tunnel, or manual ChatGPT setup was
  authorized; local MCP success is not remote verification.
- Forward signal performance: no initialized forward observation store.
- Demonstrated alpha: none claimed. Current signals are research evidence and heuristic ranking.

The project remains research-only and broker-disabled. No paid service, cloud deployment, domain,
credential, or real-account action was performed.
