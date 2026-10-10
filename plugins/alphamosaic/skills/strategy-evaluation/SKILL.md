---
name: alphamosaic-strategy-evaluation
description: Evaluate transparent paper-only strategies with reproducible inputs and explicit limitations.
---

Call `run_backtest` or `evaluate_strategy` with the requested symbol and strategy. Report fees, benchmarks, observations, signal coverage, and limitations. Historical evaluation is not forward or real-account performance. Use `get_signal_history` and `get_forward_performance` to report when forward data is unavailable; never infer it from historical results.
