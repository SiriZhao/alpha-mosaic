# Dependency and acceptance plan

Each stage depends on the preceding correctness gates. Exact measured final evidence is in the delivery report; earlier checkpoint numbers are not silently promoted.

## P0 — trustworthy inputs and causal accounting

Goal: preserve existing work, isolate research from trading, version validated data, prevent future information, conserve cash/positions/NAV. Dependencies: audited ccd369e contracts and exchange calendar. Acceptance: dataset tampering/quarantine/PIT failures; constant-price/round-trip/cash/split/dividend/missing-bar/next-session/future-perturbation tests; independent ledger reconstruction. Status: Implemented & locally verified on FIXTURE. Blocker: real historical evidence lacks licensed complete actions, PIT and historical membership. Next: acquire reviewed data without weakening gates.

## P1 — costs, baselines, analytics and experiments

Goal: reproducible fixed experiments with all successes and failures retained. Dependencies: P0. Acceptance: explicit fee/slippage/spread/delay/volume/lot/cash caps; human-checkable annual metrics; same-config result equality; artifact integrity and incomplete/failed status. FIFO/asset accounting and ordinary dividend entitlement/receivable/payment are implemented with independent reconstruction, immutable legacy semantics and cross-model comparison gates. Next: cash-in-lieu/special/delisting economics, causal RAW weekly action adjustment and broader independently sourced golden data. Full covariance optimization remains Planned.

## P2 — validation, reports and terminal

Goal: bounded research cases, chronological splits, training-only fit, holdout contamination audit, compatible benchmark comparisons, navigable terminal and source-linked reports. Dependencies: P0/P1. Calendar-week aggregation, signals, next-daily-open execution and52-period analytics are implemented with explicit partial intervals. Risk/comparison viewing now exposes recorded rolling risks, complete-date concentration/cash, accounting/costs, full configurations and exportable provenance. Blocker: no qualified real three-asset dataset. Next: interactive robustness/scenario jobs, broader benchmarks, source qualification and independently verified PDF export.

## P3 — optional AI and advanced research

Goal: controlled hypothesis/planning/execution/critic workflow without paid-LLM dependency. Dependencies: P0–P2 and auditable tool quotas. Implemented: frozen hypothesis/grid, data/source review, fixed workers, per-home OS lease, subprocess deadlines, hashed audit/counter validation, retained outcomes and deterministic critics. Planned dispatch requires a unique pending canonical call. Explicit reconciliation now fences dispatch, preserves original outcomes/artifacts, separates recovered/unresolved evidence with unknown exit status, and exposes shared CLI/MCP/UI actions without retry. Current local397-test/package/browser/real-process evidence is in RESEARCH_RECONCILIATION_ACCEPTANCE_20261026.md; publication is separate. Optional comments cannot introduce numeric claims. Partial/Planned: controlled quarantine/indexing, adaptive model planning and independently validated selection corrections. No attractive backtest automatically promotes a strategy.

## Release gate

RAW weekly continuation: the separately reviewed split-only core is integrated; explicit policy selection, per-signal sealed schema4 CSV and price-versus-portfolio disclosures are implemented. Final434 regression, independent final12, all11 criteria across eight retained cases, actual14-capture browser and source-identical62-file clean base-wheel/32MCP passed. Initial errors remain archived. Current hosted publication/CI is a separate pending gate. This closes neither real-data qualification nor remaining corporate-action economics. The old default rejection remains an acceptance requirement.

Ruff → Pyright → complete tests with financial RuntimeWarnings treated as errors → lock validation → wheel/sdist → clean base-wheel CLI/MCP smoke → secret/runtime scan → independently reviewed commit → authenticated branch push → actual hosted CI. Failed or unavailable stages are reported individually; no overall percentage substitutes for financial correctness.
