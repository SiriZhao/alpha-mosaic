# Continuation acceptance — 2026-10-12

## Baseline and isolation

The source baseline is PR #1 head `de2fe0cdf8e78cc03b93c68bbd956f8034eb2a62` on
`codex/integration-alpha-next-20261012`. The original `codex/project-audit-20261010`
worktree had unrelated uncommitted edits, so this work was performed in
`codex/continuation-alpha-next` under `runtime/continuation-alpha-next`.
No reset, clean, force push, main modification or broker operation was used.

## P0 forward-state repair

The previous store wrote `NOT_TRIGGERED` and `HOLDING` rows into the same immutable
outcomes table as mature results. The repair adds append-only observation events,
`mature_outcomes`, and persisted input bars. Existing databases are migrated by copying
legacy pending rows into observations while preserving the original outcomes rows.
Mature results remain immutable; revised bars fail closed; repeated evaluation is
idempotent; disjoint late batches can advance a signal; exchange sessions, cutoff and
benchmark identity are checked.

Regression coverage includes pending-to-triggered-to-mature transitions, restart and
repeat calls, partial and late batches, legacy migration, future observations, wrong
benchmarks and revised data. The failure was reproduced before implementation and the
new tests pass afterward.

## Factor and deep-ranking repair

`FactorEngine` now emits canonical `volume_ratio`, `volatility_20d` and a numeric
benchmark `market_regime` only when at least 60 date-aligned benchmark sessions exist.
The archetype registry requires positive regime evidence and independent stabilisation,
quality, valuation and growth prerequisites; missing data abstains.

DEEP mode computes a bounded research-priority score only when the decision contains
validated Danelfin observation or SEC evidence. TradingAgents model-only output cannot
change rank. When optional providers are unavailable, baseline rank is retained, deep
rank stays null and reports include NO_ACTION reasons.

## SEC/PIT repair

Annual companyfacts are anchored to one fiscal end and annual duration. Filed dates must
be available by the research cutoff; quarterly rows and later amendments are excluded.
Debt is not summed from overlapping aggregate and component facts. Missing or incomplete
coverage remains null.

## Verification

```text
uv lock --check                         NOT_RUN (tool cache/network blocked during continuation setup)
uv sync --locked --all-extras --dev     PASS (offline cache after setup)
ruff check .                            PASS
pyright                                PASS (0 errors)
pytest -q                              PASS (51 passed, 7 warnings)
uv build --wheel --sdist                PASS
secret scan                             PASS
clean-wheel smoke                       NOT_RUN (offline dependency cache missing pydantic)
MCP contract smoke                      PASS (22 tools; no broker routes)
```

The initial continuation sync attempt was blocked by an uncached scipy wheel; the locked environment was then completed from the repository cache. The independent wheel install succeeded, but its minimal offline environment could not obtain pydantic from cache, so doctor smoke is recorded as NOT_RUN.

## Readiness

The system remains research-only with `broker_enabled=false`. Forward paper tracking is
usable with sourced provider observations. `RESEARCH_READY` remains bounded by data
freshness and provider health. `ADVISORY_ELIGIBLE` remains NO because PIT, delisting,
corporate-action and independent forward evidence are incomplete. Remote ChatGPT MCP
remains NOT_VERIFIED.
