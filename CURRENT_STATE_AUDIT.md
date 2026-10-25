# Renaissance checkpoint audit — 2026-10-24

Current continuation addendum (2026-10-25): the recovered-baseline findings below are historical. Weekly strategies/annualization, reconciled FIFO statistics and the bounded frozen-plan workflow are now implemented and verified in a583a1e. Current local and hosted suites both passed267 tests; hosted CI40157996079 and exact clean-commit reproduction are recorded in `docs/evidence/continuation-20261025/`. Full platform acceptance still requires the real-data, risk/portfolio/statistical/report/recovery/model work listed in `docs/CONTINUATION_ACCEPTANCE_20261025.md`. Do not treat the old missing-weekly or pending-CI entries below as current findings.

Scope: source inspection and execution in `runtime/renaissance-20261024`, starting at `ccd369e`. The root checkout remains on `codex/project-audit-20261010` with unrelated dirty work. Existing worktrees and local research data were preserved. Earlier acceptance notes are history, not acceptance of this tree.

## Implemented and verified at the recovered baseline

- Python 3.12 src-layout application; one ApplicationService behind CLI and MCP. Explicit source path produced **72 passing baseline tests**. A borrowed interpreter without PYTHONPATH initially imported the old root package; those collection errors were environment failures, not passing acceptance.
- Replay engine, source contracts, fixed strategies, reconstructed research provider, forward/evaluation stores, authenticated optional HTTP MCP, unique report directories. Source code and executable tests, rather than filenames, establish these capabilities.
- No broker order connector or agent-accessible arbitrary shell/file tool was found. Subprocess boundaries are fixed provider workers, Git provenance queries, optional research workers and an operator-only LEAN backtest boundary. LEAN is not installed/certified and is not exposed as an arbitrary-path MCP tool.

## Partially implemented

- Existing replay had next-open execution and raw corporate actions, but lacked complete event/cash audit trails, configurable spread/delay/lot and robust execution constraints. This milestone extends it rather than replacing it.
- Older summaries call QuantStats an independent analytics path; it receives the same replay returns and is **not independent execution validation**.
- Existing AI integrations require optional authorization. Renaissance adds a deterministic critic and ModelAdapter protocol, not a complete autonomous planner/LLM agent.

## Broken issues reproduced and repaired

- High: nested model_copy could bypass validation; replay now revalidates the complete contract.
- High: opening gaps could violate buy-side weight constraints; opening-value/cost/cash constraints now gate buys. Subsequent market drift is diagnosed, not disguised as continuous compliance.
- High: overlapping delayed sells could exceed holdings; reserved sells now prevent overselling.
- High: pending order quantities after a split lacked an immutable revision trail; append-only order adjustments now link the original order, split and fill.
- Medium: experiment integrity could accept an empty checksum map and hide interrupted runs as corruption. Required artifacts, identity checks and explicit incomplete RUNNING records now fail closed.
- Medium: unknown or incompatible benchmark bases could be drawn as comparable. Reports, comparison and UI now enforce explicit compatibility.
- Medium: zero-variance QuantStats Sharpe emitted invalid division; explicit undefined-ratio handling is tested.
- Medium: Danelfin timeout cancellation leaked MCP transport resources. Independent tracemalloc located the allocation; same-task lifecycle cleanup and cancellation regression tests repair it.
- Low: terminal dark background initially retained light-theme text, and screenshots could capture loading placeholders. Theme configuration and browser completion checks correct this.

## Unverified / missing / unsafe conditions

- **High — Blocked:** strict real historical performance. One network capture returned SPY/QQQM 706 rows each with UNKNOWN adjustment; TLT EMPTY. No three-asset dataset was published. PIT, complete corporate actions, historical universe and delisting coverage are unverified.
- **High — Forbidden:** interpreting FIXTURE case returns as market evidence, causal factor attribution, future-return probability or demonstrated alpha.
- **Medium — Missing:** weekly aggregation, closed-lot win/profit/holding statistics, sector constraints, full covariance risk budgeting, constrained optimization, genuine factor-return attribution, delisting economics and dividend payment-date accounting.
- **Medium — Planned:** full LLM planning orchestration, durable global agent quotas, advanced multiple-testing statistics, paper candidate promotion and production deployment. No automatic strategy promotion is implemented.
- **Medium — Unverified:** remote ChatGPT calls and this milestone's hosted CI until an actual run is observed. Local MCP success is a separate gate.
- **Low — Technical debt:** exchange-calendars emits NumPy timedelta deprecation warnings. No warning suppression or dependency source patch is used.

## Security and publishing

GitHub connector identity and ADMIN/push ownership were verified for SiriZhao/alpha-mosaic. The existing repository is **public**; visibility was not changed and no repository was created. GitHub CLI token is invalid. Publishing status and actual final checks are recorded in ALPHA_MOSAIC_DELIVERY_REPORT.md. Runtime provider payloads and private/local artifacts remain ignored; only synthetic screenshots and software evidence are eligible for review.
