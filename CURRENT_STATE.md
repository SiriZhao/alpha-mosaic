# Current state (2026-10-09)

Implemented and locally verified:

- Pydantic evidence contracts with UTC chronology and point-in-time guards.
- Isolated OpenBB V5 Nasdaq adapter with current-universe discovery, historical OHLCV, profile
  and optional fundamentals; no synthetic fallback.
- Deterministic momentum, relative strength, trend, volume, volatility, drawdown and liquidity
  factors; heuristic percentile ranking and risk filtering.
- Unique JSON/Markdown reports, historical diagnostic metrics, CLI commands and six read-only MCP
  tools through one `ApplicationService`.
- Python 3.12 environment contains OpenBB core 2.0.1, Nasdaq 2.0.0, SEC 2.0.0, MCP 2.3.0,
  QuantStats 0.0.86, ruff 0.16.10, pyright 1.1.414 and pytest 9.1.1.

Measured acceptance:

- `ruff check .`: passed.
- `pyright`: passed.
- Foundation tests: 4 passed.
- `alphamosaic doctor`, `providers` and `analyze AAPL --fundamentals`: passed against live
  Nasdaq data; AAPL returned 132 rows and recorded evidence.
- `python -m build --no-isolation --wheel --sdist`: passed after using a repository-owned temp
  directory; produced `alphamosaic-0.1.0-py3-none-any.whl` and `.tar.gz`.
- Clean Python 3.12 wheel environment: installed the wheel plus base dependencies with `uv`, and
  `alphamosaic doctor` completed with OpenBB/QuantStats correctly reported as optional absent.
- Live explicit scan of 10 symbols: 8 candidates, 2 exclusions, `REAL_DATA` report with unique
  JSON and Markdown run bundle under the ignored runtime report store.
- GitHub CLI authentication for SiriZhao is invalid, so private remote creation/push is blocked.

## Upstream integration acceptance (2026-10-09)

- `TradingAgentsAdapter` targets the official v0.6.0 release through a bounded JSON subprocess. FAST/BALANCED/DEEP budgets, timeout, cache metadata and model-key gates are implemented. This run reports `NOT_CONFIGURED` because the optional package and authorized model credentials are absent; no natural-language probability is parsed.
- `DanelfinAdapter` uses the official MCP HTTP endpoint with Bearer-key, cache, deduplication, interval, quota, timeout and stale-result guards. This run reports `NOT_CONFIGURED` because `DANELFIN_API_KEY` is absent; no web scraping or mock success is used.
- `IntegrationRegistry` records OpenBB, TradingAgents, Danelfin, AI Hedge Fund, FINVIZ, TradingView, TIKR and Seeking Alpha with connection/license/test states.
- `SignalFusionEngine` validates PIT chronology, symbol identity, duplicate evidence and shared dependencies; conflicting-source results are `CONFLICTED` with confidence withheld.
- Live public research completed for AAPL, XOM and TSLA: OpenBB/Nasdaq history -> factors -> fused decisions -> JSON report `runtime/research/20261009-upstream-research.json`. Directions were AAPL `BULLISH`, XOM `BULLISH`, TSLA `BEARISH`; TradingAgents and Danelfin outcomes are explicitly `NOT_CONFIGURED` for all three.
- Local MCP exposes the unified tools plus backward-compatible aliases. Remote Streamable HTTP is opt-in, bearer-authenticated, rate-limited and bound to localhost by default.
- Portable plugin assets are under `plugins/alphamosaic/`; the remote URL is intentionally a deployment placeholder, so ChatGPT remote verification remains `NOT_VERIFIED`.
- Integration validation: `ruff` passed, `pyright` passed, `pytest` 8 passed. Local stdio MCP handshake listed 19 tools and invoked `system_status`; authenticated remote smoke returned `/health` 200 and unauthenticated `/mcp` 401. ChatGPT remote connection remains `NOT_VERIFIED`.
Known limitations: current screener is survivorship-biased, historical data is reconstructed and
adjustment policy is unknown, fundamentals are partial, news/catalyst feeds are not connected, optional multi-agent providers are unconfigured, forward signal storage is not initialized, and there is no demonstrated alpha or broker execution.

## Professional backtesting and alpha QA (2026-10-09)

- Added a deterministic causal `PaperReplayEngine` with next-session-open execution, fees, slippage,
  prior-known liquidity caps, partial/unfilled orders, cash/position constraints, XNYS sessions,
  split/dividend handling, and fail-closed data/PIT/identity checks.
- Added transparent buy-and-hold, momentum, trend, quality, value, multi-factor, AI-rating and
  signal-consensus baselines. `QuantStats 0.0.86` now reports CAGR, volatility, max drawdown, Sharpe,
  Sortino, benchmark excess return, information ratio, turnover, fees, slippage, uncertainty, regime
  diagnostics, walk-forward folds and a trend ablation.
- Added deterministic strategy lifecycle gates, an empty forward-paper initializer, and a separate
  local LEAN CLI boundary. The MCP server does not expose arbitrary process execution.
- Acceptance evidence: **31 backtesting/foundation/integration tests passed**, ruff and pyright passed,
  and `uv build` produced wheel/sdist. The fixture experiment is explicitly `FIXTURE` and
  `INSUFFICIENT_EVIDENCE_NO_DEMONSTRATED_ALPHA`; its metrics are engineering evidence only.
- Live OpenBB history remains `REAL_RECONSTRUCTED` and is not eligible for alpha promotion because PIT,
  survivorship, delisting, adjustment-policy and corporate-action evidence is incomplete. LEAN is
  `BLOCKED` locally because Docker and the LEAN CLI are absent. No paid service, commercial data,
  broker, or real account was used.
