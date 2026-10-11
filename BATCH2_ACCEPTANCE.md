# Batch 2 acceptance — multi-source research

Date: 2026-10-11
Base: `824a9b1ce0a12a31f88127fd28498860b0447537`

## Delivered

- Danelfin uses the official MCP Python `ClientSession` and Streamable HTTP transport. It performs initialize, tool enumeration, advertised-schema validation, tool calls, structured JSON extraction, timeout/quota/cache handling and explicit unsupported/error states. A score is stored as dated `DanelfinScoreObservation` and converted to a `FusionSignal` only after symbol, date and 1–10 range validation. It is documented as conviction evidence, never a return probability.
- TradingAgents targets the official `v0.6.0` release in an isolated subprocess. FAST, BALANCED and DEEP map to upstream debate, risk-discussion, tool-round and recursion settings; results/cache/memory paths are scoped under the AlphaMosaic runtime and the worker emits JSON-only stdout. Only exact structured `verdict`/`final_rating` values are accepted; prose keyword parsing is removed. Unsupported or unstructured output remains research opinion/insufficient evidence.
- SignalFusionEngine now rejects duplicated evidence, shared dependency keys, repeated content fingerprints and signals derived from already-seen evidence. Correlated sources cannot mechanically raise confidence.
- ResearchEngine validates the serialized Danelfin observation and signal at the orchestration boundary, retains the observation and provider metadata, and leaves unconfigured providers out of fusion.

## Official upstream checks

- Danelfin documentation returned HTTP 200 on 2026-10-11. It advertises `get_stock_score`, `get_etf_score`, `get_top_ranked`, `screen_by_score`, `get_score_history`, `get_best_stocks`, `get_trade_ideas`, `get_trading_parameters`, `get_price_forecast`, `get_performance`, and alert tools. Authentication is `Authorization: Bearer <DANELFIN_API_KEY>` at `https://mcp.danelfin.com/mcp`. The docs state scores are 1–10 conviction scores and list plan quotas; no paid plan was purchased.
- TradingAgents GitHub latest release endpoint returned `v0.6.0`, published 2026-10-03. The v0.6.0 `pyproject.toml` confirms Python `>=3.11`; this project keeps it optional and does not inject its large dependency graph into the core package.

## Local verification

- `ruff check src tests scripts`: passed.
- `pyright`: 0 errors, 0 warnings.
- `pytest -q --basetemp .pytest-batch2-final2`: **14 passed**, 4 dependency deprecation warnings and one MCP transport cleanup warning.
- `alphamosaic providers` and `alphamosaic doctor`: OpenBB/Nasdaq installed and available; SEC EDGAR is `NOT_CONFIGURED` because no contact User-Agent is configured.
- `alphamosaic research AAPL,GOOGL,AVGO --profile FAST` completed against live OpenBB/Nasdaq history. Evidence is in [batch2-research-20261011.json](docs/audits/batch2-research-20261011.json): AAPL `BULLISH` from deterministic momentum, GOOGL and AVGO `BEARISH` from the same deterministic factor. All three TradingAgents outcomes are `NOT_CONFIGURED` because the optional package/model credentials are absent; all three Danelfin outcomes are `NOT_CONFIGURED` because `DANELFIN_API_KEY` is absent. No external score or model verdict was fabricated.

## Acceptance boundaries

This is protocol and deterministic-chain verification, not `LIVE_VERIFIED` for Danelfin or TradingAgents. No authorized credentials, optional TradingAgents install, or external model call was available. Danelfin ranking, screening, historical-score, and subscores are schema-ready but not live-verified. The three-stock run has no licensed valuation, analyst-estimate, news, catalyst or point-in-time fundamentals source; prices are research data with provider and adjustment limitations. No return probability, demonstrated alpha, broker action or real-account effect is claimed.

## Reproduction

```powershell
.venv/Scripts/python.exe -m ruff check src tests scripts
.venv/Scripts/python.exe -m pyright
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .pytest-batch2-final2
.venv/Scripts/alphamosaic.exe research AAPL,GOOGL,AVGO --profile FAST
```
