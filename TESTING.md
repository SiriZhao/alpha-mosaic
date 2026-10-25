# Verification commands and scope

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
