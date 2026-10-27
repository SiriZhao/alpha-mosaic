# Verification commands and scope

## Benchmark reference continuation — 2026-10-27

Full goal ACTIVE. Main source now includes typed BenchmarkSpecV1 cash-zero-interest and explicit equal-weight references plus legacy-preserving first-eligible-open scheduling. The exact selected-asset return-basis fix is integrated as9e3d80f. Current local source hash is b617f682003bebb246ef55e1de57a4cad2534d730d453922e0493e6979af13bc across65 Python files. Full regression passed444 tests; focused benchmark tests passed7; Ruff/Pyright/secret checks passed. A separate hand-oracle process passed flat cash, exact zero-cost shares, first-open phase, fee accounting and fail-closed configuration/grid paths with unchanged source fingerprints. A second model review was attempted but unavailable due model capacity; this is explicitly unverified. Core is not yet wired into ExperimentConfig/plans/workers/analytics/UI/reports and is not published or real-data qualified. See docs/BENCHMARK_REFERENCE_ACCEPTANCE_20261027.md and evidence/benchmark-reference-20261027.

Current RAW weekly source1824b28cee25aaa1a585553b3f6c030eaab244d579c27346b35a771da102afee:434 full tests, zero failures/errors/skips; four upstream calendar deprecations remain. Financial RuntimeWarnings are errors. Independent final12 verifies actual form/background job, manual share units/plain split text, price/income separation, raw fills, export integrity and byte-preserved schema3 reading. Earlier core28/integration30 reviews overlap and are not additive unique counts. Source-identical62-file fresh base wheel, actual32-tool MCP and eight-page14-capture browser gates passed. Negative attempts remain archived. Published8345b8e passed CI40325500811 with434 tests and all gates; see the RAW-weekly qualification-summary/hosted-ci records. See docs/RAW_WEEKLY_ACCEPTANCE_20261026.md and evidence/raw-weekly-20261026/acceptance.json; earlier counts below are historical.

Latest reconciliation source0754fabeee4494cff23fbf0ec5ec325972b07138ce7fbfae27c5a8419e05f1f9 passed397 full tests with RuntimeWarning as error and no failed/error/skipped cases. Actual Windows junctions and native-lineage-verified owned-parent termination are included. Five real CLI/MCP/UI actions, three initially failing semantic audit counterexamples, fixed-worker interruption/late-response/idempotence and corrupt-report preservation are covered. Fresh60-file-matching base wheel/CLI/32-tool MCP and final eight-page15-capture browser action/focused three-capture view passed. After a verified reset,36 independent current-source target tests passed with no failures/errors/skips; original cap and ACL failures remain separately identified. Qualified compositea4c5f2e passed hosted CI40312008132 with397 tests and all quality/dependency gates; hosted LF and local Windows byte identities are separate. See docs/RESEARCH_RECONCILIATION_ACCEPTANCE_20261026.md; older counts below are historical.

Latest dispatch checkpoint:361 full tests passed with RuntimeWarning as error, including both actual Windows junction cases; independent14-case dispatch review also passed. Six actual pre-fix worker failures are preserved alongside canonical request/identity/outcome/lease/unsealed-artifact regressions. See docs/RESEARCH_DISPATCH_ACCEPTANCE_20261025.md for scope and source-specific wheel/CI records. Earlier346/271/267 test counts apply to their named sources.

Latest ordinary-payment checkpoint:346 full tests passed with RuntimeWarning as error. Independent hand ledgers, multiple lots/partial exits/splits/multiple payments, late/unsupported terms, future-price perturbation, daily/weekly/model comparison gates, strict-real legacy refusal, immutable old artifacts and actual cash/claim terminal actions are covered. Final source/evidence: docs/DIVIDEND_PAYMENT_ACCEPTANCE_20261025.md. Earlier271/267-test records remain historical; source-specific wheel/CI checks must be observed separately.

Latest risk-terminal follow-up:271 tests passed with RuntimeWarning as error, including actual qualified/incompatible/corrupt comparison actions, immutable legacy gaps, and hand-verifiable flat-cash/mark reconciliation. Independent review used a legal15-session alternating-holdings replay to reproduce the old missing-date defect. Current source and browser/wheel evidence are in docs/TERMINAL_RISK_ACCEPTANCE_20261025.md; older267-test records remain historical.

Continuation coverage adds extreme finite-moment/OLS/denormal-volatility cases, validated split-derived history, FIFO golden matching/fees/dividends/reverse-split/complete-session accounting, real weekly decisions with Good Friday and next-open causality, source-view late action rejection and constructor/config reproducibility. Workflow tests execute actual worker processes, hard deadlines, global leases, immutable plans, corrupted audit sequences/final counters, old-schema preservation, untrusted-home module shadowing and junction containment. Permission to construct the junction fixture may be needed under a restricted Windows sandbox; it is not skipped to create a passing result.

```powershell
uv sync --locked --all-extras --dev
uv run ruff check .
uv run pyright
uv run pytest -q -W error::RuntimeWarning --basetemp runtime/pytest-final
uv run python scripts/mcp_smoke.py --home runtime/mcp-check
uv run python scripts/benchmark_replay.py --sessions 100
uv build
uv run python scripts/secret_scan.py
uv run pip-audit --local --vulnerability-service osv --timeout 10 --progress-spinner off
```

Use a unique repository-owned basetemp, TEMP and UV_CACHE_DIR on restricted Windows hosts. Borrowed interpreters require explicit PYTHONPATH to this checkout's src; otherwise installed editable packages may import another branch. No stale test result is acceptance of a changed tree.

Tests cover unit formulas/hand-worked cash cases, generated weight constraints, causal future-perturbation regression, strict input failure cases, integration/unique artifact exports, independent seeded ledger reconstruction and Streamlit AppTest navigation. `test_independent_accounting` separately reconstructs48 seeded scenarios/879 fills using raw split/dividend economics rather than replay's internal accounting helpers. `test_danelfin_lifecycle` checks real MockTransport timeout/deadline/cancellation with garbage collection and remaining-task checks.

The small performance smoke verifies exact repeat equality and records local timing; no universal runtime threshold is asserted. Full case profiling is manual. Browser navigation/screenshots use `scripts/terminal_smoke.py`; headless AppTest is not equivalent to browser rendering. Offline tests do not fetch paid/real market data. Network capture is explicit opt-in and must retain unavailable/partial states.

Clean-wheel acceptance uses a fresh environment with base dependencies, runs doctor/research-demo/local experiment and a real stdio MCP handshake from outside the source checkout, and confirms the imported path belongs to site-packages. Optional OpenBB/QuantStats/terminal absence must remain valid for the core research path. Hosted CI must be observed separately before being marked passed.
