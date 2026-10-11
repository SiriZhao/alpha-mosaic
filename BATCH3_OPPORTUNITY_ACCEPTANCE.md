# Batch 3 Opportunity Discovery Acceptance

Date: 2026-10-11 (UTC)
Branch: `codex/batch3-opportunities`
Starting SHA: `824a9b1ce0a12a31f88127fd28498860b0447537`

## Delivered

- Added a single `OpportunityDiscoveryPipeline` with universe discovery, validation, preliminary factor ranking, archetype categorisation, bounded deep research and report persistence.
- Added six explicit archetypes: `QUALITY_GROWTH`, `EARNINGS_REVISION`, `VALUATION_DISLOCATION`, `MOMENTUM_BREAKOUT`, `EVENT_CATALYST`, and `MEAN_REVERSION`. Each declares evidence, assumptions, failure risks, regime and holding horizon.
- Added an opt-in SEC EDGAR adapter boundary and financial contract fields. No SEC call was marked live because `ALPHAMOSAIC_SEC_USER_AGENT` was not configured.
- Added CLI `alphamosaic opportunities`, MCP `discover_opportunities`, immutable report snapshots and deterministic checkpoint resume.
- Reports preserve initial run ID/cutoff, provider states, factors, missing evidence, archetype gaps, deep decision when valid and explicit `NO_ACTION` reasons. Broker execution remains impossible.

## Real public-data evidence

The bounded FAST run used OpenBB V5/Nasdaq public endpoints:

- pipeline run `2be1ff56d5e8496d865442d1d1fa980a`
- initial scan `b741867374b146889a1e1b1113774ac3`
- universe/data-success/preliminary/exclusions: `10 / 10 / 10 / 0`
- elapsed time: 61.94 seconds
- observed latest bars: 2026-10-09 20:00 UTC

The public provider returned a malformed/null-volume SPY benchmark row. It remains an invalid provider evidence record and was not repaired with a fixture.

A separate real-data DEEP run for AAPL, GOOGL and AVGO completed:

- pipeline run `c4f6363b36c743ceb7a383c05b265652`
- initial scan `aa2bc69943a14a59b8a5e05864b32c4d`
- universe/data-success/preliminary/deep: `3 / 3 / 3 / 3`
- elapsed time: 68.98 seconds
- TradingAgents and Danelfin were unavailable/not configured. All three summaries therefore retain `NO_ACTION`; no external score manufactured a rerank.

## Verification

- `pytest`: **11 passed**
- `ruff check src tests`: **passed**
- `pyright`: **0 errors, 0 warnings** with the repository Python 3.12 environment
- Real OpenBB chain completed: OpenBB -> factors -> rank -> JSON/Markdown report -> CLI, preserving provider failures
- MCP discovery uses the same `ApplicationService`; no arbitrary filesystem or shell tool was added

## Boundaries

- The broad pool is a bounded current Nasdaq/NYSE/AMEX screener sample and is survivorship-biased, not a complete market census or historical index membership set.
- Nasdaq history is reconstructed at retrieval with unknown adjustment/corporate-action policy, not certified point-in-time data.
- SEC, analyst estimates, earnings revisions, primary-source catalysts, news and commercial scores were not configured. Archetype scores remain null when prerequisites are missing.
- FAST invokes no LLM. DEEP is bounded per candidate; unavailable providers do not block scanning.
- No output is a return probability, demonstrated alpha, recommendation or broker instruction.
