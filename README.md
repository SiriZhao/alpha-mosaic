# AlphaMosaic

AlphaMosaic is an independent, evidence-first investment intelligence platform. It discovers a
bounded current US equity universe, computes deterministic factors, compares optional external
research engines, runs transparent paper backtests and exposes the same application through CLI,
stdio MCP and authenticated Streamable HTTP MCP. It is research and paper evaluation only: there
is no broker connector, order route, credential tool or claim of validated alpha.

## Quick start

```powershell
uv sync --all-extras
uv run alphamosaic doctor
uv run alphamosaic providers
uv run alphamosaic analyze AAPL --fundamentals
uv run alphamosaic scan --universe-limit 10 --top 10
uv run alphamosaic research AAPL,XOM,TSLA --profile FAST
uv run alphamosaic integrations
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
- Transparent paper backtests with fees, slippage, cash/position constraints, benchmark metrics,
  walk-forward and signal-ablation diagnostics. QuantStats is optional.
- TradingAgents v0.6.0 and Danelfin adapters are isolated and fail closed as `NOT_CONFIGURED`
  until their authorized dependencies and credentials are supplied.
- A multi-source signal fusion engine detects stale, duplicate, dependent and conflicting evidence
  and reports research confidence rather than a return probability.
- Unified read-only MCP tools for status, providers, scans, stock analysis, comparison, research,
  backtests, signal history and reports. Long research is returned as a bounded `job_id`.
- Portable `plugins/alphamosaic` package with four skills; each skill calls an MCP tool and keeps
  missing or failed data explicit.

## Architecture

```text
CLI / stdio MCP / Streamable HTTP MCP
                 |
        ApplicationService (one authority)
          /       |        \
   providers  research     backtesting
      |       /     \          |
 OpenBB   TradingAgents  Danelfin   deterministic engine
                 |
       contracts -> validation -> reports
```

Adapters isolate upstream APIs. Domain contracts never import provider, MCP or CLI internals.
The remote server binds to localhost by default, requires a bearer token, enforces request and
rate limits, and must sit behind operator-managed HTTPS before any public deployment.

## MCP and ChatGPT package

Run local stdio MCP with `uv run alphamosaic mcp serve`. For an authenticated local Streamable HTTP
endpoint, set `ALPHAMOSAIC_MCP_TOKEN` to a token of at least 16 characters and run
`uv run python -m alphamosaic.mcp.remote`. Set `ALPHAMOSAIC_AUDIT_LOG` to enable redacted JSONL
request audit records. `plugins/alphamosaic/mcp.json` intentionally contains a deployment
placeholder; replace it only after deploying HTTPS and completing a real ChatGPT tool call.

The available MCP tools include `system_status`, `provider_health`, `scan_market`,
`rank_opportunities`, `analyze_stock`, `compare_stocks`, `research_portfolio`, `job_status`,
`evaluate_strategy`, `run_backtest`, `get_signal_history`, `get_forward_performance` and
`generate_investment_report`, plus backward-compatible read-only aliases.

## Security, cost and data limits

No credentials are committed or returned by tools. Commercial websites are not scraped; their
registry entries remain `LICENSE_BLOCKED` or `EXPERIMENTAL` until an approved interface and data
license exist. Provider software licenses do not grant redistribution rights to retrieved data.
Optional model calls use FAST/BALANCED/DEEP bounded budgets and never place orders. Current scans
are survivorship-biased and reconstructed historical data may lack point-in-time corporate action
coverage; these limitations remain attached to reports.

## Validation standard and roadmap

Fixture tests and live data acceptance are separate. Historical metrics, forward simulation and
real-account returns are distinct evidence classes. A strategy cannot become advisory-eligible
from a single backtest, and AI scores cannot be backfilled from today's value. See
[FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md), [ARCHITECTURE.md](ARCHITECTURE.md),
[INTEGRATIONS.md](INTEGRATIONS.md), [CURRENT_STATE.md](CURRENT_STATE.md) and
[NEXT_STEPS.md](NEXT_STEPS.md) for measured results and blockers. This project is unrelated to
Meridian Alpha and never modifies it.
