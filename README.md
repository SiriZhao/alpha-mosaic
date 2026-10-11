# AlphaMosaic

AlphaMosaic is an independent, evidence-first investment research platform. It discovers a
bounded current US equity universe, computes deterministic factors, ranks opportunities and
produces JSON/Markdown research bundles. It is research and paper evaluation only: there is no
broker connector, order route, credential tool or claim of validated alpha.

## Quick start

```powershell
uv sync --all-extras
uv run alphamosaic doctor
uv run alphamosaic providers
uv run alphamosaic analyze AAPL --fundamentals
uv run alphamosaic integrations
uv run alphamosaic research AAPL,XOM,TSLA --profile FAST
uv run alphamosaic scan --universe-limit 10 --top 10
uv run alphamosaic report
uv run alphamosaic mcp serve
```

The default provider is an isolated OpenBB V5 Nasdaq adapter. Network failures are explicit
statuses; fixture data is never substituted. Reports are written below `ALPHAMOSAIC_HOME` (or
the repository-local `runtime`) in unique run directories, and runtime data is ignored by Git.

## What is implemented

- Pydantic contracts for market observations, historical bars, fundamentals, evidence, factors,
  candidates, risk, decisions, backtests and provider health.
- Current screener discovery plus explicit symbols, imports and user watchlists.
- Momentum, relative strength, trend, volume, volatility, drawdown, liquidity, quality and value
  fields when the provider supplies them. Scores are heuristic percentile ranks, never return
  probabilities.
- Fixed SMA diagnostic with QuantStats metrics, benchmark comparison, turnover and fees.
- Evidence-gated paper replay with transparent buy-and-hold, momentum, trend, quality, value,
  multi-factor, AI-rating and signal-consensus baselines. Use `alphamosaic strategies` to inspect
  the registry, `alphamosaic backtest AAPL --strategy momentum` for a reconstructed-history diagnostic,
  and `alphamosaic forward-init` to create an empty isolated paper record. Fixture and reconstructed
  metrics never certify alpha; AI-rating history is blocked without a licensed PIT time series.
- QuantConnect LEAN is isolated behind an optional local CLI adapter and remains `BLOCKED` when Docker,
  the LEAN CLI or reviewed data are absent. QuantStats is pinned as an analytics adapter; VectorBT,
  Backtrader, FinRL and AI Hedge Fund remain under license/reproducibility review.
- Unified read-only MCP tools for system/provider health, market scan, ranking, stock analysis, comparison, bounded portfolio research jobs, strategy evaluation, backtest, signal history, forward performance and investment reports. Local stdio is available with `alphamosaic mcp serve`; authenticated Streamable HTTP is opt-in via `python -m alphamosaic.mcp.remote`.
- TradingAgents v0.6.0 and Danelfin adapters are optional and fail closed as `NOT_CONFIGURED` without authorized credentials. `IntegrationRegistry` records license and connection maturity for the listed external resources.
- A portable ChatGPT plugin package is under `plugins/alphamosaic/`. Set the authenticated deployment URL in `mcp.json` only after HTTPS and bearer authentication are in place; local MCP success is not remote ChatGPT verification.

See [ARCHITECTURE.md](ARCHITECTURE.md), [INTEGRATIONS.md](INTEGRATIONS.md),
[CURRENT_STATE.md](CURRENT_STATE.md) and [NEXT_STEPS.md](NEXT_STEPS.md) for boundaries and
measured acceptance. This project is unrelated to Meridian Alpha and never modifies it.

## Framework and forward validation

`uv run alphamosaic frameworks` prints the non-installing integration matrix for LEAN,
QuantStats, VectorBT, AI Hedge Fund, FinRL-X, FinRL and Backtrader. The matrix reports adapter,
dependency, startup, computation and validation states independently. The local PaperReplay engine
owns fills, cash, fees, slippage and corporate actions; QuantStats is analytics-only and cannot be
treated as a second execution engine. `ForwardPaperStore` freezes source-hashed paper signals and
evaluates predeclared T+5/T+20/T+60 horizons with frozen cost assumptions. See
[BATCH5_FRAMEWORK_AND_ALPHA_VALIDATION.md](BATCH5_FRAMEWORK_AND_ALPHA_VALIDATION.md) for the
dated audit, real-data evidence and blockers.

## Plugin and remote MCP

The portable package contains `plugin.json`, `mcp.json`, and four skills. Every skill calls a named MCP tool and instructs the assistant to preserve sourced-or-missing values and provider statuses. The remote server exposes `/health` and authenticated `/mcp`, enforces a bearer token of at least 16 characters, request rate limits, a 4 MiB body limit, bounded sessions and localhost defaults. It does not expose shell, arbitrary files, credentials, or broker orders.

## Environment variables

- `ALPHAMOSAIC_HOME`: repository-owned runtime/report location.
- `DANELFIN_API_KEY`: optional official Danelfin MCP Bearer key; never committed.
- `DANELFIN_MCP_URL`: optional endpoint override for an authorized deployment.
- `ALPHAMOSAIC_MCP_TOKEN`: required for remote MCP and must be supplied through deployment secrets.
- `ALPHAMOSAIC_MCP_HOST` / `ALPHAMOSAIC_MCP_PORT`: remote bind settings; defaults are `127.0.0.1:8000`.
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`: optional model authorization for TradingAgents; the adapter remains `NOT_CONFIGURED` when absent.

No real broker token, account data, or API key belongs in this repository.

## Architecture and limits

The CLI and MCP transports call one `ApplicationService`; providers and optional integrations sit
behind protocols, while reporting stores immutable run bundles. MCP exposes read-only research and
paper diagnostics only. Values remain sourced or missing, timestamps are timezone-aware, and
point-in-time, survivorship, corporate-action, licensing, and provider-availability limits remain
visible in every report. This repository is public; no visibility change is required.

## Roadmap

Next work is operator-owned HTTPS deployment verification, licensed point-in-time datasets, and
independent forward evidence. Those are prerequisites for any future evidence promotion and are
not configured or claimed by this release. See [BATCH6_PLATFORM_ACCEPTANCE.md](BATCH6_PLATFORM_ACCEPTANCE.md)
for measured checks and remaining deployment conditions.
