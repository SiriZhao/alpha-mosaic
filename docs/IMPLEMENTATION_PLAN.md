# Dependency and acceptance plan

Each stage depends on the preceding correctness gates. Exact measured final evidence is in the delivery report; earlier checkpoint numbers are not silently promoted.

## P0 — trustworthy inputs and causal accounting

Goal: preserve existing work, isolate research from trading, version validated data, prevent future information, conserve cash/positions/NAV. Dependencies: audited ccd369e contracts and exchange calendar. Acceptance: dataset tampering/quarantine/PIT failures; constant-price/round-trip/cash/split/dividend/missing-bar/next-session/future-perturbation tests; independent ledger reconstruction. Status: Implemented & locally verified on FIXTURE. Blocker: real historical evidence lacks licensed complete actions, PIT and historical membership. Next: acquire reviewed data without weakening gates.

## P1 — costs, baselines, analytics and experiments

Goal: reproducible fixed experiments with all successes and failures retained. Dependencies: P0. Acceptance: explicit fee/slippage/spread/delay/volume/lot/cash caps; human-checkable annual metrics; same-config result equality; artifact integrity and incomplete/failed status. FIFO matched-lot statistics and additive asset accounting are implemented and independently reconciled. Next: payment-date dividends, cash-in-lieu and broader independently sourced golden datasets. Full covariance optimization remains Planned.

## P2 — validation, reports and terminal

Goal: bounded research cases, chronological splits, training-only fit, holdout contamination audit, compatible benchmark comparisons, navigable terminal and source-linked reports. Dependencies: P0/P1. Calendar-week aggregation, signals, next-daily-open execution and52-period analytics are implemented with explicit partial intervals. Risk/comparison viewing now exposes recorded rolling risks, complete-date concentration/cash, accounting/costs, full configurations and exportable provenance. Blocker: no qualified real three-asset dataset. Next: interactive robustness/scenario jobs, broader benchmarks, source qualification and independently verified PDF export.

## P3 — optional AI and advanced research

Goal: controlled hypothesis/planning/execution/critic workflow without paid-LLM dependency. Dependencies: P0–P2 and auditable tool quotas. Implemented: frozen explicit hypothesis/grid, data/source version review, fixed worker tools, per-home global experiment lease, hard worker deadlines, durable hashed audit/counter validation, complete outcome retention and deterministic critics. Optional commentary cannot introduce numeric claims or investment-promotion phrases. Partial/Planned: adaptive model planning, independently validated selection corrections and safe interrupted-plan recovery. No attractive backtest automatically promotes a strategy.

## Release gate

Ruff → Pyright → complete tests with financial RuntimeWarnings treated as errors → lock validation → wheel/sdist → clean base-wheel CLI/MCP smoke → secret/runtime scan → independently reviewed commit → authenticated branch push → actual hosted CI. Failed or unavailable stages are reported individually; no overall percentage substitutes for financial correctness.
