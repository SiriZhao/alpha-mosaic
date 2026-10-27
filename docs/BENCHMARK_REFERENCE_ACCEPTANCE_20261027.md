# Cash and equal-weight benchmark core

This checkpoint adds a typed `BenchmarkSpecV1` and two research-only references:

- `CASH_ZERO_INTEREST` is a constant zero-interest **model assumption** on an explicit XNYS session grid. It consumes no market bars, has no `CASH` security symbol, and leaves beta, regression alpha and correlation null.
- `EQUAL_WEIGHT` freezes an explicit security universe, equal target weights, daily replay configuration and the `FIRST_ELIGIBLE_OPEN_THEN_INTERVAL` schedule. It delegates fills, costs, splits, dividends, cash and positions to the canonical paper replay engine.

The old scheduler remains available when `schedule_policy=None`: with the default 21-session rebalance it can delay the first allocation until the legacy phase. The explicit benchmark phase starts at the first eligible daily open and then applies the interval. Tests prove both paths separately. Equal-weight specifications reject universe truncation, cash buffers that make the weights impossible, unsupported weekly cadence, invalid symbols, and session-grid mismatch.

The main worktree now passes **444 full tests** with zero failures/errors/skips and **7 focused benchmark tests**. A separate hand-oracle process passed cash flatness, first-open timing, exact zero-cost shares, fee accounting, non-session and market-bar cash rejection, and truncation rejection with unchanged source fingerprints. The first hand oracle incorrectly expected 12+12 shares under 10bp fees; this was preserved as negative evidence and corrected by separating zero-cost allocation from the fee case. Four exchange-calendar deprecation warnings remain.

This is local generated-FIXTURE software evidence only. A second model independent review of this new core was attempted but unavailable due to model capacity; it is recorded as `NOT_COMPLETED_MODEL_CAPACITY`. The core is not yet wired into `ExperimentConfig`, frozen research plans/workers, analytics comparison, report generation, or the dashboard. It does not qualify real data, PIT history, delistings or a sourced risk-free rate. The full Renaissance goal remains active.

Evidence: [machine acceptance](evidence/benchmark-reference-20261027/acceptance.json), [full regression](evidence/benchmark-reference-20261027/pytest-full.xml), [focused benchmark tests](evidence/benchmark-reference-20261027/pytest-focused.xml), [hand oracle](evidence/benchmark-reference-20261027/independent-hand-oracle.json), and [source provenance](evidence/benchmark-reference-20261027/source-provenance.json).
