# Batch 5 framework and alpha validation

Date: 2026-10-11 (Asia/Shanghai)
Branch: `codex/batch5-alpha-validation`
Base: `fe02fee` (`origin/main` at start)

## Scope and evidence boundary

This batch adds an auditable framework matrix, a common backtest adapter contract, execution/statistics comparison, and immutable forward-paper signal evidence. It does not install large machine-learning environments, call a paid service, connect a broker, or claim demonstrated alpha.

`PaperReplayEngine` remains the only local order/position/cash execution engine. `QuantStats 0.0.86` is an independently maintained return-statistics implementation; it is deliberately reported as **analytics-only**, not as a second fill engine. Therefore the same-input comparison confirms deterministic replay/statistics agreement but does not claim two independent execution implementations.

## Framework Integration Matrix

The matrix is executable through `alphamosaic frameworks` and `ApplicationService.framework_matrix()`.

| Framework | Latest audited version | License/SPDX | Adapter | Dependency | Engine started | Computation | Validation | State |
|---|---:|---|---|---|---|---|---|---|
| QuantConnect LEAN | v2.4.0.1 (upstream audit) | Apache-2.0 | Present (local CLI boundary) | Not installed | No | No | No | NOT_CONFIGURED |
| QuantStats | 0.0.86 | Apache-2.0 | Present | Installed | Run-scoped | Run-scoped | Evidence-gated | READY |
| VectorBT | v1.1.2 | Apache-2.0 + Commons Clause | None | Not installed | No | No | No | EXPERIMENTAL |
| AI Hedge Fund | v2.5.0 (upstream audit) | MIT | None | Not installed | No | No | No | EXPERIMENTAL |
| FinRL-X | upstream endpoint unavailable during audit | UNVERIFIED | None | Not installed | No | No | No | BLOCKED |
| FinRL | v0.3.8 upstream / PyPI 0.3.7 | MIT | None | Not installed | No | No | No | EXPERIMENTAL |
| Backtrader | PyPI 1.9.78.123 | GPL-3.0-only | None | Not installed | No | No | No | LICENSE_BLOCKED |

The upstream audit recorded official URLs, release/commit metadata where reachable, license text, Python metadata, and package data on 2026-10-10. Some GitHub API calls returned 403 in the restricted environment; those rows remain explicitly unverified. VectorBT's Commons Clause prohibits selling a service derived from the software and requires a separate legal review before any adapter. Backtrader's GPL boundary is incompatible with importing it into the Apache-2.0 core without a reviewed isolation/distribution decision.

## Adapter and comparison results

- `BacktestEngineAdapter` separates adapter presence, installed dependency, startup, computation, and validation.
- `PaperReplayAdapter` executes next-session-open fills with the existing fee, slippage, liquidity, cash, split/dividend and XNYS checks.
- `QuantStatsAdapterEngine` consumes the exact resulting equity return series. It never creates fills or changes cash.
- `compare_engine_paths()` records a canonical dataset SHA-256, same sessions, cost configuration, fills, cash, NAV difference, fees, slippage, metrics and the reason any apparent difference exists.
- Fixture verification: same strategy (`momentum`), same bars and `fee_bps=20/slippage_bps=10` produced `COMPUTED`, `same_sessions=true`, `same_fills=true`, `nav_max_absolute_difference=0`, and a positive fee total. This is reproducibility evidence only.
- LEAN was not run: Docker and the `lean` executable are absent. No QuantConnect cloud service or commercial data was used.

## ForwardPaperStore

`ForwardPaperStore.freeze_signal()` stores an immutable, source-hashed record containing symbol, signal ID, issued/as-of timestamps, reference price, horizon, model version, direction, entry/invalidation conditions, benchmark, fee/slippage assumptions and the broker-disabled flag. Reusing a signal ID with different evidence raises an error.

`evaluate()` uses only bars strictly after the frozen `as_of` date, rejects duplicate/out-of-order bars, applies the frozen entry reference and fee/slippage assumptions, and writes idempotent T+5/T+20/T+60 outcomes. Outcomes are `NOT_TRIGGERED`, `HOLDING`, `AT_HORIZON`, or `INSUFFICIENT_DATA`; every output retains the original source hash. These are forward paper observations, never real-account returns.

`StrategyEvaluationRegistry` records strategy version, engine, source fingerprint, acceptance,
metrics and failure evidence as append-only experiment metadata. It does not promote a strategy;
the existing deterministic lifecycle rules and human review remain the only promotion boundary.

## Real public-data chain

OpenBB/Nasdaq was available in the inherited Python 3.12.14 environment. A live AAPL request on 2026-10-11 returned 277 historical rows in approximately 9.91 seconds and was saved in the ignored runtime evidence bundle. An explicit live scan of AAPL, MSFT and NVDA returned:

- run ID: `683d84524a5b400d895aa67c2c7d7804`
- acceptance: `REAL_DATA`
- universe: 3; eligible: 3; candidates: 3
- elapsed: approximately 19.25 seconds
- MCP `rank_opportunities` returned the same run ID and three candidates from the persisted report

The source is current/retrieved historical data with reconstructed PIT and incomplete survivorship/corporate-action evidence. It is not a certified point-in-time backtest and yields `NO_DEMONSTRATED_ALPHA`.

## Validation run

- Ruff: passed after the new adapter/forward tests.
- Pytest: **34 passed**, 6 existing dependency warnings.
- Pyright: passed using the repository Python 3.12 environment (`--venvpath ..\\..`).
- Build/clean-wheel and `uv lock --check`: not rerun in this restricted continuation because `uv` is unavailable and the worktree has no local `.venv`; previous Batch 1/2 baseline remains separate evidence.
- Vulnerability audit: `pip-audit` is not installed in this environment; no claim is made for that check.
- GitHub push: blocked by invalid `gh` token (HTTP 401); no remote mutation was attempted.

## Decision

The framework layer is ready for reviewed local paper research. It is **not** eligible for advisory promotion: there is no independently qualified PIT dataset, no LEAN run, no complete historical universe/delisting set, and no forward observation sample. The correct alpha status remains `NO_DEMONSTRATED_ALPHA`.
