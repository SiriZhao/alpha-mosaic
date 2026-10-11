# Integrations

## Framework maturity (Batch 5)

`alphamosaic frameworks` runs a local, non-installing audit of QuantConnect LEAN, QuantStats, VectorBT, AI Hedge Fund, FinRL-X, FinRL and Backtrader. The result separates `adapter_present`, `dependency_installed`, `engine_started`, `computation_succeeded` and `validation_passed`; an importable package cannot promote a strategy.

The local execution path is the deterministic AlphaMosaic PaperReplay engine. QuantStats 0.0.86 is an analytics-only boundary over the resulting return series. LEAN has a local CLI adapter but remains `NOT_CONFIGURED` until an operator supplies Docker/CLI, a pinned project and licensed data. VectorBT, FinRL, FinRL-X and AI Hedge Fund remain isolated/experimental; Backtrader remains license-blocked by GPL-3.0.

## Forward evidence

`ForwardPaperStore` freezes source-hashed signals and evaluates only predeclared T+5/T+20/T+60 horizons with the frozen reference price, transaction-cost assumptions and benchmark. Repeated signal IDs must be byte-identical. Outcomes are paper research states (`NOT_TRIGGERED`, `HOLDING`, `AT_HORIZON`, `INSUFFICIENT_DATA`) and cannot be represented as real-account returns.

See [BATCH5_FRAMEWORK_AND_ALPHA_VALIDATION.md](BATCH5_FRAMEWORK_AND_ALPHA_VALIDATION.md) for the dated upstream audit, live OpenBB evidence, comparison result and exact blockers.
