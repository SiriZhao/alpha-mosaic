# AlphaMosaic requirement audit — 2026-11-06

This matrix audits the requested Renaissance scope against the current isolated delivery head. `Verified` means the named evidence covers the stated boundary. `Partial` and `Blocked` are intentional acceptance states; they do not certify a production research platform or market performance.

| Requirement area | Status | Current evidence and boundary |
|---|---|---|
| Repository audit, architecture and research-only boundary | Verified within tested scope | `CURRENT_STATE_AUDIT.md`, `ARCHITECTURE.md`, `SECURITY.md`, broker-disabled service status, hosted secret scan and MCP smoke. No broker order route is exposed. |
| Versioned data lifecycle and deterministic fixtures | Verified within fixture/diagnostic scope | Dataset manifests, content hashes, quality policies, provenance contracts and synthetic reproducibility tests. |
| Licensed real/PIT market data, historical membership and delistings | Blocked | Provider capture remained partial/unknown adjustment; strict replay refuses missing action, PIT, membership and delisting evidence. No synthetic result is promoted. |
| Future-function and availability controls | Verified within tested scope | Next-session execution, known-at checks, chronological splits, holdout contamination audit, future perturbation tests, and the parameter-window regression. |
| Event replay and long-only cash accounting | Verified within declared model | Replay events, cash/share/NAV conservation, costs, splits, ordinary dividend claims/payments, FIFO reconstruction and negative-path financial tests. Special distributions, cash-in-lieu and delisting economics remain unsupported. |
| Configurable execution costs and baseline cases | Verified within declared model | Zero, realistic and stress presets; fees, slippage, spread, delay, lot and participation limits; reproducible fixture cases and frozen cost trials. Opening-auction liquidity is not certified. |
| Strategy and portfolio construction | Partial | Fixed daily/weekly baseline registry and basic long-only constraints are implemented. Full covariance risk budgeting, reliable sector constraints and general constrained optimization remain planned. |
| Analytics, risk and attribution | Partial | Daily/weekly metrics, rolling risk, drawdowns, exposure, concentration, cost and matched-lot attribution are tested. Factor causality, full covariance attribution and advanced selection correction remain incomplete. |
| Scientific validation and overfitting controls | Verified within declared boundary | Chronological splits, walk-forward, purge/embargo, holdout contamination audit, bounded parameter sensitivity with parent windows, explicit trial accounting and no-selection semantics. DSR/PBO/Reality Check are planned. |
| Experiment registry and reproducibility | Verified within local artifact boundary | Unique experiment IDs, source/dependency/dataset fingerprints, immutable artifact manifests, JSON/CSV/HTML/Markdown exports, failed/interrupted visibility and clean-wheel CI. |
| Dashboard and reports | Partial | Eight-page local Streamlit terminal, background jobs, provenance, risk/comparison views, parameter robustness tab and downloadable reports are tested. Broad scenario controls, comprehensive interaction QA, PDF and Parquet export are incomplete. |
| AI research agent | Partial | Frozen deterministic planner, bounded workers, critic and optional model adapter are implemented. No paid LLM is required. Adaptive model planning, quarantine/indexing and selection-adjusted statistics remain planned. |
| CI, security and independent review | Verified for delivered head | Hosted CI run 42229495936 passed tests, Ruff, Pyright, build, clean-wheel, dependency audit, secret scan and MCP smoke. Independent review closed the four PR correctness findings; PR #5 remains draft and unmerged. |

## Acceptance decision

The current state is a **research-grade prototype with explicit partial and blocked boundaries**, not production-grade research acceptance. The highest-value external prerequisite is a legally usable point-in-time dataset with raw prices, complete corporate actions, historical constituents and delisting outcomes. The highest-value internal follow-up is special-distribution/cash-in-lieu/delisting accounting plus broader independent golden cases. No alpha, return probability or investment recommendation is certified.
