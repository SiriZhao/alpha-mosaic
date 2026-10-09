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
- Six read-only MCP tools: status, providers, scan, snapshot, ranking and research report.

See [ARCHITECTURE.md](ARCHITECTURE.md), [INTEGRATIONS.md](INTEGRATIONS.md),
[CURRENT_STATE.md](CURRENT_STATE.md) and [NEXT_STEPS.md](NEXT_STEPS.md) for boundaries and
measured acceptance. This project is unrelated to Meridian Alpha and never modifies it.
