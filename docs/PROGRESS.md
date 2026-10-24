# Recoverable progress

Resume date: 2026-10-24. Working branch: codex/renaissance-20261024. Base: ccd369e. Root dirty branch untouched.

- Recovered four Renaissance worktrees and preserved all in-progress code.
- Baseline: 72 passed using Python 3.12 with explicit source path.
- Integrated data commit 99f62f8 as b57986e; data tests 29 passed.
- Integrated validation 588fc16 / 29c38b1 as 5eb771e / afc3d45; scientific tests 29 passed.
- Integrated accounting ea59b9f as 31ebdde; accounting/backtest tests 41 passed.
- Integrated independent ledger test 51c695d as b3abff4; 48 seeded scenarios, 879 fills.
- Integrated Danelfin lifecycle repair 6e93698 as 4ca05a6; related 24 tests passed with RuntimeWarning treated as an error.
- Added authoritative service/CLI/MCP experiment paths, local Streamlit terminal, complete experiment exports, deterministic critic, compatibility gates and recoverable failures.
- Eight fixed FIXTURE cases plus one failed control completed. Initial profiled suite 81.306s; metadata optimization follow-up 39.881s. These are individual instrumented local measurements, not universal speed claims; exact output equality is checked separately.
- Browser navigation tested all eight pages and mobile report layout. Initial visual review found theme/loading issues; fixes and subsequent screenshots are retained in software acceptance evidence.
- Real capture: SPY/QQQM 706 HISTORICAL rows each, UNKNOWN adjustment; TLT EMPTY. No dataset or historical performance published from this attempt.

Final commands, counts, artifact locations, CI/publication status and blockers are maintained in ../ALPHA_MOSAIC_DELIVERY_REPORT.md. Resume from that report rather than rerunning old branches or assuming this roadmap is complete.

Publication checkpoint2026-10-25: integration commit a6dd38e pushed and remote verified; draft PR #4 stacked on #3; implementation CI40135345657 passed. A clean committed eight-case rerun matched exact accounting/analytics. Its anomalous elapsed interval is explicitly unusable for performance comparison. Full production acceptance remains incomplete because strict real data and documented research capabilities remain blocked/planned.
