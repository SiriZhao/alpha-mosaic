# Contributing

Read AGENTS.md, BACKTEST_ASSUMPTIONS.md and RESEARCH_METHODOLOGY.md. Preserve one ApplicationService and dependency direction. Financial correctness, data provenance and causal availability precede features or speed.

Use Python3.12, a codex/ development branch and an isolated worktree. Preserve unknown local changes/data; never reset, clean, force-push or rewrite shared history. Reproduce defects with meaningful failing tests, fix the cause, run the required checks in TESTING.md and update CURRENT_STATE/NEXT_STEPS plus evidence. Stage explicit reviewed paths and scan staged blobs. No fixture success may replace a network failure.

Strategies need a hypothesis, data requirements, fixed formula/parameters, rebalance rule, failure conditions, cost assumptions and validation plan. Keep all attempted experiments and holdout contamination history. Never use a good-looking backtest to invent probabilities or claim demonstrated alpha.

Do not contribute broker execution routes, account secrets, paid provisioning, copied incompatible source, unlicensed provider data or arbitrary tool-executable code. New dependencies require actual version/license review. CI must use public-authorized or clearly synthetic inputs without personal credentials.
