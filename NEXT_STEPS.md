# Next steps

## Typed benchmark integration — 2026-10-27

Full goal ACTIVE. BenchmarkSpecV1 is optional in ExperimentConfig and frozen research plans; legacy ticker configs serialize unchanged. ApplicationService persists cash/equal-weight references separately from benchmark_result, daily/weekly analytics distinguish model-assumption cash comparisons, and reports/terminal traces label typed references. Frozen cash plans/workers passed. Current source hash24a28b1f8cca6a09a0855409081fd1b719a52c5518fb28b8e5f18b68097a09c6 (65 Python files) passed447 full tests, 2 direct benchmark integration tests, 3 plan/worker integration tests, Ruff, Pyright and secret scan. Typed cash browser QA passed 12 captures with no browser errors. Second-model review was unavailable due capacity; real/PIT qualification remains blocked.

## Typed benchmark integration — 2026-10-27

Full goal ACTIVE. BenchmarkSpecV1 is now accepted as an optional ExperimentConfig reference while legacy benchmark ticker configs serialize unchanged. ApplicationService persists cash/equal-weight references separately from benchmark_result; daily and weekly analytics distinguish model-assumption cash comparisons from ordinary simulated market comparisons; reports and terminal chart labels handle typed references. Current source hash04b13c174888670389f507417b6dc7a2908bd725af5a4ed8f96ddf956d4a957c (65 Python files) passed446 full tests, 2 service integration tests, Ruff, Pyright and secret scan. Existing 7 benchmark-core tests and hand oracle remain evidence; second-model review was unavailable due capacity. Browser benchmark interaction and frozen-plan/worker benchmark wiring remain pending; real data/PIT qualification remains blocked.

## Benchmark reference continuation — 2026-10-27

Full goal ACTIVE. Main source now includes typed BenchmarkSpecV1 cash-zero-interest and explicit equal-weight references plus legacy-preserving first-eligible-open scheduling. The exact selected-asset return-basis fix is integrated as9e3d80f. Current local source hash is b617f682003bebb246ef55e1de57a4cad2534d730d453922e0493e6979af13bc across65 Python files. Full regression passed444 tests; focused benchmark tests passed7; Ruff/Pyright/secret checks passed. A separate hand-oracle process passed flat cash, exact zero-cost shares, first-open phase, fee accounting and fail-closed configuration/grid paths with unchanged source fingerprints. A second model review was attempted but unavailable due model capacity; this is explicitly unverified. Core is not yet wired into ExperimentConfig/plans/workers/analytics/UI/reports and is not published or real-data qualified. See docs/BENCHMARK_REFERENCE_ACCEPTANCE_20261027.md and evidence/benchmark-reference-20261027.

Isolated benchmark-basis component source5f86be17f76e876e460af4775b1c6d69327fbc698480f5bbf670fb4630184608 passed42 targets and independent4. Three pre-fix failures proved whole-dataset convention propagation; strategy/benchmark bases now resolve per selected basket and legacy missing metadata stays NOT_RECORDED. See docs/BENCHMARK_BASIS_ACCEPTANCE_20261026.md. This is not published/main acceptance: full regression/package/UI/current CI remain pending. Explicit BenchmarkSpec/scheduler work remains separately in progress; full objective ACTIVE.

Published8345b8e94918cdbb0410c9ea840f81c61a14fbf6 has matching remote SHA; [CI40325500811](https://github.com/SiriZhao/alpha-mosaic/actions/runs/40325500811) passed434 tests and every quality/build/base-wheel/MCP/dependency/secret gate. Seven completed financial outputs and the expected default refusal reproduced exactly from the clean commit in the same environment. Hosted installed source0f213a895bb56ece42d60e6ed165aa8e6ea531d54b07c0c3e593aeee58724dcd matches raw Git blobs;51 Windows differences are line endings only. See qualification-summary.json, hosted-ci.json and committed-reproduction.json in the RAW-weekly bundle. Later evidence-only HEAD CI is observed separately.

## Current RAW weekly handoff

Current source1824b28cee25aaa1a585553b3f6c030eaab244d579c27346b35a771da102afee passed434 tests, clean62-file wheel/base workflows,32MCP,14browser captures and independent final12. Core2b9e215 and runner6243966 are integrated asf7d61c2/2ecd699. Below isolated-handoff notes are historical; do not replay integration. Read docs/RAW_WEEKLY_ACCEPTANCE_20261026.md, current Git and hosted CI before continuing; publication remains source-specific. Highest-value next work: explicitly modeled cash/equal-weight benchmarks and compatible scenario workflows, then source-qualified exceptional action economics. Strict real licensed/PIT/universe/delisting qualification remains blocked. Full objective ACTIVE; no merge or full completion is implied.

## Active full-objective continuation

Next isolated handoff is ready: runtime/renaissance-raw-weekly-20261026, branch codex/renaissance-raw-weekly-20261026, local commit2b9e21595f467e38121ec05971dd19828c5381df froma4c5f2e, clean/unpushed. Sourceef6079ec1f8527a97689c73a8ea60861f7d7e352272eaa55673a7702e103e402 (62files);189 compatibility cases and independent28 (including six runtime-only oracles) passed. Review actual six-path diff/contracts and runtime/raw-weekly-freeze-02.sha256 before integration; parent full regression/UI/report/package/CI remain pending. MAIN stays accepted0754; do not count this opt-in RAW feature as delivered yet. Independent oracles are retained at that worktree's runtime/independent_raw_weekly_review_001.py and JUnit independent-raw-weekly-001.xml.

1. Read docs/RESEARCH_RECONCILIATION_ACCEPTANCE_20261026.md and current Git/CI state. Source0754fabeee4494cff23fbf0ec5ec325972b07138ce7fbfae27c5a8419e05f1f9 has397 local tests, final package/browser/genuine-process evidence; qualified compositea4c5f2e passed hosted CI40312008132 with397 tests/all gates, independent36 and nine exact same-environment financial reruns; see qualification-summary.json. No checkpoint completes the full goal. Do not resume from the old dirty root branch or discard other worktrees.
2. Highest-value data gate remains qualified licensed raw-plus-actions/PIT/membership/delisting evidence. Keep real research blocked instead of substituting FIXTURE returns.
3. Ordinary payment accounting is implemented within its declared conservative boundary. Next P0/P1 work: source-qualified cash-in-lieu/special/delisting economics and causal action-aware RAW weekly adjustment (currently explicitly blocked), plus broader independently sourced golden evidence. Robustness/scenario job controls, benchmark choices, factor/sector data, robust portfolio construction and independently checked advanced statistics remain.
4. Explicit append-only reconciliation and shared CLI/MCP/UI are implemented within the documented contract: retain unknown exit status, original timeout/failure outcomes, late observations and all artifacts without retry. Unsealed/unknown candidates still block planned dispatch; controlled quarantine/indexing/legacy recovery requires separate reviewed work, not silent cleanup or inferred liveness. Initial capped/ACL attempts remain separate; final independent current-source review passed36 target tests after verified reset, with unchanged hashes and no blockers.
5. Adaptive model-driven hypothesis planning remains separate from the working deterministic frozen-grid workflow; no paid model authorization is assumed. Qualitative comments cannot introduce computed financial observations.
   Reproducibility follow-up: design a versioned portable source identity and freeze/compare environment fingerprints before broadening cross-platform comparisons. Current byte hashes intentionally distinguish CRLF/LF; the observed discrepancy is documented, not bypassed.
6. Prior dispatch f9dcfe3/CI40202837163 remains accepted historical evidence. Reconciliation corecf0ebcf is preserved in its own worktree and integrated locally as1e80320, with parent final source qualification. Publish only explicit reviewed paths and observe that composite's actual CI; old green runs do not qualify new code. Preserve all implementation/QA worktrees, failures, root dirty work and finalized artifacts. Usage caps are not permission to buy credits or mislabel incomplete independent testing.

## Renaissance next checkpoint

Release note: draft PR #4 exists and implementation CI run40135345657 passed. Review the stacked PR chain without auto-merging. Observe later evidence-only commit CI separately; no additional model/data credential is required for offline research.

1. Read ALPHA_MOSAIC_DELIVERY_REPORT.md, docs/PROGRESS.md and docs/RISK_REGISTER.md before resuming. Preserve all worktrees and runtime evidence. Do not restart from the older root audit branch.
2. Highest-value P0: legally licensed raw-plus-actions snapshots with reviewed PIT timestamps, historical constituents and delistings. Current network capture is PARTIAL/UNKNOWN adjustment; do not bypass qualification or substitute FIXTURE returns.
3. Extend independent golden-data/accounting tests, dividend payment-date/cash-in-lieu handling and closed-lot/asset contribution analytics. Weekly research needs explicit resampling and annualization tests.
4. Broaden terminal action/long-job/cancellation tests and durable global quotas. Full model-driven planner is not yet implemented; deterministic critic and typed simulation tools do not certify that stage.
5. Observe hosted CI and authenticated branch/PR delivery separately from local checks. GitHub CLI token is invalid; connector ADMIN identity is verified; actual Git push result is in the release addendum. Remote ChatGPT remains NOT_VERIFIED.

The older roadmap below is retained as history; its provider/credential/CI assertions are not current verification.

1. Operator-configure Docker/LEAN, a pinned project and licensed point-in-time data; run a same-input fill comparison before considering an independent execution engine.
2. Add a reviewed point-in-time dataset with historical constituents, delistings, corporate actions and transaction-cost evidence; rerun walk-forward and regime diagnostics.
3. Record forward signals daily in the immutable store and wait for predeclared T+5/T+20/T+60 observations; require independent replication and human review.
4. Review VectorBT Commons Clause, Backtrader GPL-3.0 and ML/RL dependency/security boundaries before any isolated adapter.
5. Restore `uv` and `pip-audit` in CI, rerun clean wheel/sdist and MCP smoke checks, then resolve the invalid GitHub token before push.

## Integration follow-up

1. Push `codex/integration-alpha-next-20261012`, create the pull request to `main`, and inspect the GitHub Actions run before considering merge.
2. If the operator authorizes providers, run small authenticated Danelfin and TradingAgents calls and retain their raw schema, cost, cutoff and evidence IDs.
3. Add licensed point-in-time constituents, delistings and corporate-action data before promoting any strategy beyond research diagnostics.
4. Supply missing `next-forward-qa` work or keep that line explicitly unintegrated; continue immutable forward observations at T+5/T+20/T+60.
5. Keep `ADVISORY_ELIGIBLE` disabled until independent out-of-sample and forward evidence passes the deterministic registry rules.

## Continuation next steps

1. Run the new `forward-evaluate` command on a legitimately frozen signal after a new market session; retain the raw provider cutoff and mature observation evidence.
2. Configure SEC/Danelfin/TradingAgents only with authorized credentials, then verify evidence-gated deep reranking on a small candidate set.
3. Add a licensed point-in-time universe and corporate-action/delisting history before any strategy status promotion.
4. Investigate the existing MCP transport cleanup warning and add job expiry/cancellation metrics before remote deployment.
5. Push this continuation branch and open a separate PR; do not merge PR #1 automatically.

## Active data-quality follow-up (2026-10-13)

1. Use the tested integration/continuation branches and import-path manifest for daily runs; the dirty audit worktree still has an older non-nullable volume contract.
2. Operator-configure a truthful SEC contact User-Agent; verify annual filings and per-field evidence before enabling live fundamental research.
3. Obtain an authorized exchange/security master, sectors and adjustment/corporate-action data. Keep UNKNOWN and NOT_CONFIGURED visible until then.
4. Add licensed PIT constituents/delistings and independent forward observations before strategy certification; no alpha or advisory promotion is permitted.
5. Investigate inherited Danelfin MCP transport cleanup warnings, forward data provenance and job lifecycle limits in a separately tested change.
6. Review the new branch's CI and stacked PR before merge; no automatic main merge or public deployment.

For daily operation, wait for a source history covering the latest completed
exchange session. An HTTP/SDK OK result cannot override STALE_HISTORY; do not pad
or substitute old daily prices. GitHub CLI needs operator reauthentication if its
HTTP 401 persists; public read-only CI verification is available in the meantime.
