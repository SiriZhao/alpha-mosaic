# Current state (2026-10-11)

## Batch 5 delivered

- Added `FrameworkIntegrationMatrix` and `alphamosaic frameworks` for the seven requested upstream resources. Adapter, install, startup, computation and validation states are independent fields.
- Added `BacktestEngineAdapter`, `PaperReplayAdapter`, and an explicit QuantStats analytics adapter. QuantStats is not represented as a second execution engine.
- Added deterministic same-input comparison with dataset fingerprint, session/fill/cash/NAV checks, fees, slippage and difference explanations.
- Replaced the empty forward-paper extension with immutable source-hashed signal freezing and idempotent T+5/T+20/T+60 paper outcomes using frozen cost assumptions.
- Added `StrategyEvaluationRegistry` evidence recording for strategy version, engine, source fingerprint, metrics and failure evidence; it cannot promote a strategy.
- Added 3 framework/engine/forward contract tests. Full suite now passes 34 tests.

## Measured evidence

- Python 3.12.14 environment: Ruff passed; Pyright passed with the parent repository virtualenv; Pytest 34 passed.
- Live OpenBB/Nasdaq AAPL request: 277 rows, about 9.91 seconds.
- Live explicit scan: AAPL/MSFT/NVDA, run `683d84524a5b400d895aa67c2c7d7804`, 3 eligible and 3 candidates, `REAL_DATA`; MCP ranking returned the same run ID.
- QuantStats 0.0.86 installed and used; LEAN/Docker absent. VectorBT, FinRL-X, FinRL, AI Hedge Fund and Backtrader intentionally not installed.

## Acceptance boundary

All replay/forward tests use fixtures or reconstructed data and are engineering evidence only. OpenBB current-history diagnostics are not PIT-certified because adjustment, delisting, historical-universe and corporate-action coverage is incomplete. No demonstrated alpha, advisory eligibility, broker execution or real-account return is claimed.

`uv`, `pip-audit` and GitHub push are unavailable in this continuation: `uv`/audit tooling is absent and the GitHub CLI token returns HTTP 401. The exact checks remain in [BATCH5_FRAMEWORK_AND_ALPHA_VALIDATION.md](BATCH5_FRAMEWORK_AND_ALPHA_VALIDATION.md).

## Integration continuation (2026-10-12)

The release branch `codex/integration-alpha-next-20261012` was created from
`origin/main` and reconciles Batch 5, platform delivery, opportunity QA, and adapter
work without modifying the occupied legacy integration worktree. Current measured
baseline is 43 passing tests, Ruff pass, Pyright pass with zero diagnostics, locked uv
sync pass, wheel/sdist build pass, clean-wheel doctor pass, secret scan pass, MCP smoke
pass, and forward-store initialization pass. The bounded six-symbol live sample found
6/6 validated bars and produced a persisted FAST report; optional deep providers were
not configured. See [INTEGRATION_ACCEPTANCE_20261011.md](INTEGRATION_ACCEPTANCE_20261011.md).

## Continuation acceptance (2026-10-12)

- Baseline: PR #1 head `de2fe0c`; dirty concurrent worktree preserved in a separate branch.
- Forward P0 fixed with append-only `observations`, immutable `mature_outcomes`, legacy migration compatibility, persisted bar idempotency, late-data handling, cutoff checks, exchange-session validation and frozen-result conflict protection.
- Factor aliases now define `volume_ratio`, `volatility_20d` and date-aligned `market_regime`; archetype prerequisites abstain when evidence is missing.
- Deep opportunity ranking only changes when a validated Danelfin observation or same-period SEC result is present. Model-only or unavailable services leave baseline ordering and emit NO_ACTION.
- SEC facts are constrained to annual forms, fiscal end, fiscal year, duration and filing cutoff; revisions after cutoff and mixed periods are excluded.
- Full local regression: 50 passed; Ruff passed; Pyright passed with zero diagnostics. Warnings are dependency deprecations and an existing MCP transport cleanup warning.
- Real providers were not re-called in this continuation because the bounded evidence run already exists and optional research credentials are not configured. No alpha or advisory eligibility is claimed.

## Data chain repair (2026-10-13)

See docs/audits/DATA_QUALITY_ACCEPTANCE_20261013.md for the latest continuation evidence.
Null-volume SPY prices now participate in price-only validation; QQQM is independent.
Reports expose separate benchmark, factor, research, action and software states.
The real bounded run 2955da45109a443e9ac16ba8a2d5c6eb produced 30/29/10 with all
relative SPY/QQQM factors present. The frozen-source six-symbol run
1a7d0349fbd646a7ba5b3b5dae3c1201 produced both-benchmark historical diagnostics.
72 tests, Ruff, Pyright, build, clean-wheel doctor and real stdio MCP passed.
Overall research remains PARTIAL / PRELIMINARY_RESEARCH_ONLY / NO_ACTION because
basic financial evidence, exchange mapping and investment-grade PIT coverage are incomplete.

CI evidence for this data-quality branch: PR #3 checks passed in Actions runs
38417014880 and 38416829439. Dependency-audit export now includes optional extras
and omits the unpublished project itself. Software checks do not turn reconstructed
market data into PIT certification or establish alpha.
