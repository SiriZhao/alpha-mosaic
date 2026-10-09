# Professional backtesting acceptance

Date: 2026-10-09 UTC
Repository base: `371102c`
Evidence class: fixture engineering evidence unless explicitly marked otherwise.

## What is implemented

- `PaperReplayEngine` replays next-session-open orders against causal prior-close information.
- Fee and slippage bps, cash constraints, maximum positions, prior-known volume caps, partial fills,
  unfilled orders, split/dividend actions, XNYS sessions, and long-only position invariants are explicit.
- `StrategyRegistry` contains buy-and-hold, momentum, trend, quality, value, multi-factor,
  AI-rating, and signal-consensus baselines. Strategy calculation is separate from execution.
- `QuantStatsAdapter` reports compound return, CAGR, volatility, drawdown, Sharpe and Sortino.
  Validation adds SPY/QQQM price-return diagnostics, excess return, information ratio, fees,
  slippage, turnover, block-bootstrap uncertainty, walk-forward folds, regime labels, and ablation.
- `EvaluationRegistry` controls lifecycle states with deterministic evidence gates. It cannot promote
  fixture or reconstructed data, a single run, missing PIT ratings, or an LLM recommendation.
- `ForwardPaperStore` creates an isolated empty paper record and never infers a fill or return.
- `LeanAdapter` is an independent local CLI boundary. It does not install LEAN, call QuantConnect
  cloud services, buy data, or expose process execution through MCP.

## Acceptance evidence

The deterministic fixture suite has **31 passed** with ruff and pyright clean. It covers reproducible
momentum, costs, cash, volume caps, unfilled orders, corporate actions, duplicate/missing/non-session
bars, malformed and future information, PIT signal expiry, walk-forward separation, signal ablation,
benchmark alignment, lifecycle gates, empty forward initialization, and LEAN dependency blocking.

The fixture replay produced a JSON and Markdown report with two walk-forward folds and an explicit
`INSUFFICIENT_EVIDENCE_NO_DEMONSTRATED_ALPHA` status. The intentionally optimistic fixture metrics
are engineering checks only and must not be presented as investment returns.

The live OpenBB history path remains `RECONSTRUCTED_DIAGNOSTIC`: current retrieval does not provide
reviewed point-in-time fundamentals, historical universe membership, complete delistings, known
adjustment policy, or certified corporate-action timing. It is therefore not eligible for alpha
promotion. AI-rating and consensus strategies return `BLOCKED` without a licensed, real historical
PIT series; current ratings are never backfilled into the past.

## External framework review

| Resource | Review result | Decision |
|---|---|---|
| QuantConnect LEAN / lean-cli | Apache-2.0, active, independent engine and CLI | `BLOCKED` locally until Docker/LEAN and reviewed data are operator configured |
| QuantStats | Apache-2.0, active, pinned `0.0.86` | Active analytics adapter |
| VectorBT | active upstream, license response `NOASSERTION` | License review required before integration |
| Backtrader | GPL-3.0, last reviewed push 2024-08-19 | Not linked into Apache main service |
| AI Hedge Fund | MIT, active | Experimental only; no reproducibility/OOS evidence |
| FinRL | MIT, active | Experimental only; no reproducibility/OOS evidence |
| FinRL-X | upstream lookup unverified | Unsupported until API/license review succeeds |

Source metadata is retained in `docs/framework-review-sources.json`.

## Interpretation boundary

`HISTORICAL` describes a replay of sourced bars, `OUT_OF_SAMPLE` describes a chronological holdout
diagnostic, `FORWARD_PAPER` describes a future observation ledger, and a real account is not connected.
None of these labels is a claim of demonstrated alpha. Strategy promotion remains `RESEARCH` or
`BACKTESTED` until independent PIT data, multiple predeclared folds, qualified replication, and
human review satisfy the registry rules.
