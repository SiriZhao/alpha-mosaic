# Integration acceptance — 2026-10-12

## Scope and source audit

This release was assembled on `codex/integration-alpha-next-20261012` from
`origin/main` at `fe02feed9a94aa26cd762ba29340be6ddc3cdd9b`.
The requested `codex/integration-alpha-next` worktree already contained unrelated
uncommitted work, so it was preserved. No reset, force push, unrelated-history merge,
or branch deletion was used.

| Source | Observed revision | Integration result |
|---|---:|---|
| `codex/next-opportunity-qa` | `8e2f947` | Opportunity pipeline, SEC adapter, archetypes and QA tests manually reconciled |
| `codex/next-forward-qa` | missing | No claims made |
| `codex/next-adapters-qa` | `82f5cfe` | Danelfin MCP and TradingAgents adapter changes manually reconciled |
| `codex/next-platform-delivery` | `1912fb2` | Platform delivery commit cherry-picked as `7598638` |
| `codex/batch5-alpha-validation` | `3f4cbb8` | Fast-forwarded from `origin/main` |
| `codex/project-audit-20261010` | `60c3163` | Reference only; dirty concurrent work preserved |
| `codex/batch3-opportunities` | `fb0a284` | Reference source for opportunity work |

The reconciled code retains one `ApplicationService`; CLI, local stdio MCP and
authenticated HTTP MCP all call it. Overlapping contracts and service methods were
reviewed manually instead of merging unrelated histories.

## Verification completed

The following commands completed in the isolated worktree with Python 3.12.14 and a
locked `uv` environment:

```text
uv lock --check                         PASS
uv sync --locked --all-extras --dev     PASS
uv run ruff check .                     PASS
uv run pyright                          PASS (0 errors, 0 warnings)
uv run pytest -q                        PASS (43 passed, 7 warnings)
uv build --wheel --sdist                PASS
python scripts/secret_scan.py           PASS
clean wheel + alphamosaic doctor        PASS
MCP tool registration/contract smoke    PASS
forward-init --initial-cash 100000      PASS (empty paper store)
```

The wheel smoke uses a minimal clean environment and correctly reports optional
OpenBB/QuantStats as unavailable there. No fixture is substituted for a failed live
provider. Runtime evidence is kept under ignored `runtime/` paths and contains no
credentials.

## Bounded real research demonstration

The six-symbol sample `AAPL, MSFT, GOOGL, AVGO, AMZN, NVDA` completed through
OpenBB/Nasdaq historical bars, deterministic factors, ranking and report persistence:

- pipeline run: `85fb8bdd5ca2419e9a43a5ce932da525`
- initial scan: `e1885010bc79443288fb30941d825db0`
- universe: 6; validated data: 6; preliminary candidates: 6; exclusions: 0
- mode: FAST; deep external research: 0 (no authorized model/Danelfin credentials)
- latest observed bar: 2026-10-09 20:00 UTC; request completed 2026-10-12 UTC
- SPY and QQQM benchmark series were retrieved as separate real inputs

The report therefore records `NOT_CONFIGURED`/degraded optional research and does not
invent deep theses, probabilities, or price levels. A no-action outcome remains valid.

The reproducible AAPL momentum replay used 10 bps fees and 5 bps slippage. It produced
516 observations, 6 fills, turnover 4.98917, net return 0.27271, CAGR 0.12499,
volatility 0.17983, max drawdown -0.15605, Sharpe 0.7450 and Sortino 1.0956.
These are reconstructed historical diagnostics with incomplete PIT, delisting and
corporate-action coverage; the run is explicitly `NO_DEMONSTRATED_ALPHA` and is not a
real-account result.

## Integration boundaries and readiness

Danelfin uses the official MCP SDK client path and strict score/date/schema validation;
without `DANELFIN_API_KEY` it remains `NOT_CONFIGURED`. TradingAgents is isolated and
structured-output-only; without an authorized model it remains unavailable. SEC EDGAR
is opt-in and requires `ALPHAMOSAIC_SEC_USER_AGENT` with contact information.
LEAN is `NOT_CONFIGURED`; QuantStats is analytics-only; other framework states remain
explicitly experimental, blocked or license-limited.

No broker route, account credential, arbitrary file access or shell tool is exposed.
`RESEARCH_READY` is supported for sourced/degraded research runs. `PAPER_READY` is
limited to the local immutable paper store. `ADVISORY_ELIGIBLE` is **NO** because
point-in-time evidence and independent forward validation are incomplete.

CI workflow is present in `.github/workflows/ci.yml`. A remote run URL is pending the
authenticated push and pull request created after this acceptance commit; no claim of
GitHub CI success is made here before that run completes.
