# Batch 6 Opportunity QA

Date: 2026-10-12 UTC. Branch: `codex/next-opportunity-qa` from `origin/codex/batch3-opportunities`.

## Correctness fixes

- SEC companyfacts no longer maps total `Liabilities` to debt; only debt-specific tags qualify.
- Operating margin uses `OperatingIncomeLoss / Revenue`, never net income margin.
- Annual fact selection remains filed-date point-in-time bounded and excludes quarterly facts.
- Archetype categorisation is fail-closed: momentum requires trend, volume, volatility and market-regime evidence; no fallback category is emitted.
- Resume checkpoints are reused only within the same UTC data date, preventing stale snapshots from being replayed under a new cutoff.

## Validation

- Added regression tests for SEC annual/PIT selection and fail-closed momentum categorisation.
- `python -m pytest` was attempted but the local environment did not expose `uv`; the suite stalled in provider/calendar setup and was stopped. `python -m compileall` and diff review remain to be rerun in the configured Python 3.12/uv environment.
- Real-data acceptance: NOT_VERIFIED in this continuation; no network data was fabricated and no credentials or broker routes were used.

## Remaining risks

- CIK/ticker historical mapping, units, revised facts, stale cache policy, ranking missingness penalties, and full FAST/DEEP acceptance require the configured CI/toolchain pass.
- Existing Batch 3 survivorship and reconstructed-history limitations remain.

## Integration notes

Cherry-pick the self-contained QA commit after reviewing the SEC tag policy and checkpoint date rule. Preserve the paper-only, provider-fail-closed boundaries.
