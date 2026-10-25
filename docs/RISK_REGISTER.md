# Risk register

Risk-terminal follow-up: independently reproduced omitted cash-only exposure dates are repaired for new analytics; unqualified marks remain null, and legacy UI dates are aligned without backfill. Qualified overlays show complete execution configurations; chart exports carry provenance. The new dividend entitlement/payment design identifies receivable and spendability requirements but does not implement or certify them. See TERMINAL_RISK_ACCEPTANCE_20261025.md for271-test scope and DIVIDEND_PAYMENT_ACCOUNTING_DESIGN.md for the remaining P0 migration.

## Continuation risk changes — 2026-10-25

R2/R3: scaled finite moments, denormal inverse-vol weights and split-derived OHLCV now have reproduced numeric regressions; FIFO/asset reconstruction requires complete sessions and action/cash/mark coverage. No payment-date dividend/cash-in-lieu/delisting model is inferred from these fixes.

R5/R8: fixed-plan execution, per-home cross-process leases, native worker deadlines, bounded job queues, immutable plan rows and hashed/counter-validated audit events are implemented. Untrusted data-home module loading and existing junction redirection are refused. Safe interrupted-plan reconciliation and adaptive model orchestration remain unfinished; persisted state never proves liveness. Local hash/path checks do not provide multi-tenant authentication or hostile filesystem race-proofing.

R9: installed packages no longer borrow an outer checkout's Git SHA. Current frozen source/267-test/base-wheel/browser evidence is separate from the old milestone. Publication CI for new code must be observed separately. Fresh OSV audit found no known vulnerabilities and no skipped package records; the raw report is retained in the continuation evidence directory.

- R1 High / Blocked: real input adjustment, PIT availability, complete actions and delistings. Owner: data. Gate: no strict real replay without explicit reviewed provenance. Next: licensed snapshots and independent checks.
- R2 High / Mitigated in tested scope: future leakage and same-close execution. Owner: accounting. Gate: next eligible session, availability checks, future perturbation tests. Residual: provider timestamps are assertions, not independent certification.
- R3 High / Mitigated in tested scope: cash/quantity corruption, opening-gap constraints, overlapping sells and split order changes. Owner: accounting plus independent QA. Evidence: independent reconstruction of 48 scenarios/879 fills. Residual: no cash-in-lieu, payment delay or delisting economic model.
- R4 Medium / Explicit approximation: same-day daily volume caps are ex-post capacity assumptions; opening liquidity is unknown. No fill guarantee or capacity certification.
- R5 Medium / Mitigated: missing/corrupt/incomplete artifacts. Content hashes and required files detect ordinary corruption; local checksums are not cryptographic authenticity against an attacker rewriting both data and hashes. Corrupt datasets cannot replay.
- R6 Medium / Explicit limitation: price drift can exceed weight targets after fills; engine records diagnostics. Sector mapping and continuous intraday hard risk enforcement are not implemented.
- R7 High / Blocked: overfit/repeated holdout claims. Local append-only audit propagates tuning contamination across overlapping same-hash sessions. Out-of-band inspections and revised-dataset contamination require human review. Bootstrap is a stationary-mean diagnostic, not selection-adjusted proof.
- R8 Medium / Partial: AI planner/tool governance. Only typed bounded simulation tools, ModelAdapter protocol and deterministic critic are present. No arbitrary command/file/broker tool. Full autonomous planner/global quota system remains Planned.
- R9 Medium / Verification gate: source files and installed environment must be frozen and the UI restarted. Before/after disk hashes cannot prove that old Python objects were not cached in memory. Reproducibility is verified on fresh processes.
- R10 Low / Open: exchange-calendars NumPy deprecation. Keep visible; upgrade only with correctness regression. The separate MCP coroutine leak was reproduced and repaired rather than suppressed.
- R11 Medium / External: GitHub CLI authentication invalid, existing repo public, hosted CI/remote ChatGPT separate gates. No runtime market payload or credentials may enter the commit. Publication outcome is in the delivery report.
