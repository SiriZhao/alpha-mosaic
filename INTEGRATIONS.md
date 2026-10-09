# Integrations

## OpenBB V5

The pinned optional integration uses `openbb-core==2.0.1`, `openbb-nasdaq==2.0.0` and
`openbb-sec==2.0.0`, corresponding to the OpenBB V5 foundation. OpenBB core is Apache-2.0;
provider website terms still govern retrieved data. The Nasdaq adapter currently supports a
current screener, historical OHLCV, profile and optional financial fields. It does not claim
free real-time data, unlimited quotas, complete historical index membership, or redistribution
rights.

The first live acceptance request was an AAPL historical/profile/fundamental request on 2026-10-09
UTC. It returned 132 historical rows and recorded request/completion timestamps, source URL,
fields, `HISTORICAL` quality, unknown adjustment policy and reconstructed PIT status in the
snapshot evidence. Provider health and signal validity remain separate.

## Analytics

`quantstats==0.0.86` is an optional adapter for finite return, volatility, drawdown, Sharpe and
Sortino metrics. The diagnostic is historical or fixed chronological holdout only; it is not a
claim of live performance or demonstrated alpha.

## Current upstream registry

The registry is executable (`alphamosaic integrations`) and separates software maturity from data entitlement and connection health.

| Resource | Interface | State | Notes |
|---|---|---|---|
| OpenBB | Python adapter | ACTIVE when installed | Historical/profile/fundamental requests use configured OpenBB providers; provider terms apply. |
| TradingAgents | Optional Python subprocess | READY_UNCONFIGURED | Targets the v0.6.0 release API and normalizes bounded research text; package and authorized model key required. |
| Danelfin | Official remote MCP | READY_UNCONFIGURED | Uses the documented Bearer-key MCP endpoint only; no web scraping. |
| AI Hedge Fund | Manual review | EXPERIMENTAL | No stable entitlement-safe production adapter enabled. |
| FINVIZ | Manual/file import | LICENSE_BLOCKED | No scraping adapter. |
| TradingView | Manual/file import | LICENSE_BLOCKED | No scraping adapter. |
| TIKR | Manual/file import | LICENSE_BLOCKED | No scraping adapter. |
| Seeking Alpha | Manual/file import | LICENSE_BLOCKED | No scraping adapter. |

`READY_UNCONFIGURED` means the boundary is implemented but credentials or optional packages are absent; it is never treated as a successful data source.

## Research and fusion boundary

`ResearchEngine` runs deterministic factors first, then bounded TradingAgents and Danelfin adapters for at most five candidates. `SignalFusionEngine` checks symbol identity, timestamps, duplicate evidence IDs, source dependency overlap and conflicts before producing `BULLISH`, `BEARISH`, `NEUTRAL`, `CONFLICTED`, or `INSUFFICIENT_EVIDENCE`. Confidence is research confidence only, not a return probability.

All provider outcomes remain attached to each decision. Missing credentials produce `NOT_CONFIGURED`; network or quota failures produce explicit degraded outcomes.

## Official references

- [TradingAgents v0.6.0 release](https://github.com/TauricResearch/TradingAgents/releases)
- [Danelfin MCP documentation](https://mcp.danelfin.com/docs/en)
