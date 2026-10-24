# Dependency and acceptance plan

Each stage depends on the preceding correctness gates. Exact measured final evidence is in the delivery report; earlier checkpoint numbers are not silently promoted.

## P0 — trustworthy inputs and causal accounting

Goal: preserve existing work, isolate research from trading, version validated data, prevent future information, conserve cash/positions/NAV. Dependencies: audited ccd369e contracts and exchange calendar. Acceptance: dataset tampering/quarantine/PIT failures; constant-price/round-trip/cash/split/dividend/missing-bar/next-session/future-perturbation tests; independent ledger reconstruction. Status: Implemented & locally verified on FIXTURE. Blocker: real historical evidence lacks licensed complete actions, PIT and historical membership. Next: acquire reviewed data without weakening gates.

## P1 — costs, baselines, analytics and experiments

Goal: reproducible fixed experiments with all successes and failures retained. Dependencies: P0. Acceptance: explicit fee/slippage/spread/delay/volume/lot/cash caps; human-checkable annual metrics; same-config result equality; artifact integrity and incomplete/failed status. Status: Implemented & locally verified. Next: closed-lot statistics, payment-date dividends, asset contribution accounting and broader golden datasets. Full covariance optimization remains Planned.

## P2 — validation, reports and terminal

Goal: bounded research cases, chronological splits, training-only fit, holdout contamination audit, compatible benchmark comparisons, navigable terminal and source-linked reports. Dependencies: P0/P1. Acceptance: A/B/C plus cost/parameter/holdout cases; browser navigation/screenshots; report exports and compatibility failures. Status: Implemented & locally verified within documented scope. Blocker: no trustworthy real three-asset dataset; weekly research and PDF export are not implemented. Next: broaden UI action tests and valid data snapshots.

## P3 — optional AI and advanced research

Goal: controlled hypothesis/planning/execution/critic workflow without paid-LLM dependency. Dependencies: P0–P2 and auditable tool quotas. Current status: Partially Implemented: deterministic critic, ModelAdapter protocol and typed local MCP experiment tools. Full planner, autonomous model orchestration, durable global quotas, advanced multiple-testing corrections and automatic research recommendations: Planned. No attractive backtest automatically promotes a strategy. Next: implement a small audited planner only after real-data qualification.

## Release gate

Ruff → Pyright → complete tests with financial RuntimeWarnings treated as errors → lock validation → wheel/sdist → clean base-wheel CLI/MCP smoke → secret/runtime scan → independently reviewed commit → authenticated branch push → actual hosted CI. Failed or unavailable stages are reported individually; no overall percentage substitutes for financial correctness.
