# Interrupted research-plan reconciliation

Status: **Implemented & locally verified within the explicit contract**. Full Renaissance objective remains ACTIVE and incomplete. Published-commit/hosted-CI proof is recorded separately from these local measurements.

Source SHA256: `0754fabeee4494cff23fbf0ec5ec325972b07138ce7fbfae27c5a8419e05f1f9`.

This is the actual Windows-checkout/package byte hash. Git's normalized source-blob hash is eb95dc08e3be43f543261860fe627a50737f01162511aebc23a54bb5f22d5713; all49 differing files were verified to differ only in line endings. Hosted Linux/source identity is captured separately from local byte qualification. No cross-platform exact-result claim or silent relaxation of source-comparison gates is introduced.

## Behavior and evidence boundaries

An explicit reconciliation acquires the plan and global execution OS leases, in that order. A busy lease refuses the operation without inferring process liveness from a file, PID string or timestamp. A durable RECONCILIATION_STARTED fence prevents a delayed child from creating an experiment under the same global lease. Existing call/result events and experiment files are preserved.

Each dispatched attempt receives one append-only review:

- RECORDED_OUTCOME_PRESERVED retains the original result, including timeout/failure/BUSY. It makes no new artifact-quality claim.
- RECOVERED_COMPLETED_ARTIFACT identifies one sealed artifact whose full configuration, context, request, dataset content/manifest, source version and checksums qualify. It records exit_status=NOT_OBSERVED and never invents a historical successful TOOL_RESULT.
- INTERRUPTED_UNRESOLVED retains missing, ambiguous, corrupt, unsealed, contradictory or unsupported evidence. Absence is not proof that a process exited or did no work.

RECONCILIATION_FINISHED closes the original run as INTERRUPTED with separate recorded/recovered/unresolved/unattempted counts. No missing trial is scheduled; no old outcome is upgraded or rewritten. Reconciliation itself can resume after a fence/attempt-record interruption without duplicating prior events. Unstarted FROZEN and already finished original plans are no-ops.

Responses can arrive after the experiment lease releases. Repeated explicit inspection appends unique bounded response observations with classification_effect=NONE; it never reclassifies a prior review. Snapshots read at most64KiB. Oversized/unreadable input cannot qualify a recovered artifact. The current reconciler source is recorded separately, allowing review of older frozen artifacts when their recorded identities still qualify; no old computation is rerun.

ApplicationService exposes the shared operation to CLI, a bounded asynchronous MCP job and the nonblocking AI Research page. The terminal distinguishes matched artifacts from original outcomes and shows unknown process exit explicitly. If a previously completed experiment is now corrupt, computed reporting is blocked while the saved audit and completed reconciliation remain inspectable/downloadable. CLI reports that combination truthfully instead of pretending the already committed reconciliation was blocked.

## Actual verification

Final complete regression: **397 passed**, zero failed/error/skipped, RuntimeWarning treated as error, four visible upstream calendar deprecations. All actual Windows junction cases ran. Ruff, Pyright, lock check and secret scan passed. A real test-owned parent was terminated after its child sealed an artifact; native Windows lineage and exact Python image were verified first, leases released, original files stayed byte-identical and reconciliation created no duplicate trial.

Five CLI/MCP/AppTest surface tests exercise actual operations, repeated calls and corrupt-report behavior. Three additional semantic counterexamples initially failed: a valid hash chain could carry a failed response, wrong artifact ID or missing reviewer-source fingerprint alongside a recovery claim. Semantic validation now rejects these contradictions; financial assertions were not weakened.

A fresh base-wheel installation without OpenBB/QuantStats/Streamlit/Plotly completed four dividend cases/four frozen trials and three recovery cases, CLI doctor and actual32-tool stdio MCP. All60 packaged and installed Python files match the tested source. Sdist inspection excludes runtime, virtual environments and Git metadata. Base installation used cached dependencies; no dependency relaxation, model key or paid resource was required.

Browser QA verified all eight pages/mobile and an actual explicit reconciliation action with15 captures, asserted actual selected plan/experiment identities, and checked the before/after viewer source hash. A focused three-capture read-only check placed the recovered row and unknown exit status in the visible viewport; its image was inspected. Earlier source-specific captures are preserved. A refresh-button replacement timeout was diagnosed in the QA script and fixed with bounded rerender handling; the required terminal-state assertion remains intact.

Machine evidence, final JUnit, original semantic failures, original process-PID failure, recovered-core records and screenshots are in `evidence/research-reconciliation-20261026/`. All displayed market labels/prices/results are FIXTURE software evidence only.

## Independent work and retained failures

The implementation and read-only design/core review used separate worktrees. After sub-agents reached their usage limit, the parent preserved corecf0ebcf, integrated it as1e80320 and completed the counterexamples/interfaces/regression. The original core passed27 cases; its earlier combined run had one diagnostic-ordering failure, and an earlier setup run failed before execution because its temporary path did not exist. The initial frozen independent attempt did not complete at the cap and remains recorded as such in acceptance.json.

After the stated reset time was verified, one resumed independent review succeeded on the actual final MAIN source:36 targeted tests passed, zero failed/error/skipped, including the real junction, genuine owned-parent termination and CLI/MCP/UI checks. Before/after hashes both match0754fabeee4494cff23fbf0ec5ec325972b07138ce7fbfae27c5a8419e05f1f9; no source edits or blocking findings. The resumed first sandbox run had35 temp-directory ACL setup errors and is preserved separately from the successful elevated run. `independent-review.json` and `independent-current-qualified.xml` provide the newer current-source qualification; they do not retroactively relabel the initial cap/environment failures or qualify the full platform/real data.

The first genuine-process scaffold assumed the Windows venv launcher PID equaled the Python parent PID. That assertion failed. The repaired test queries native lineage and executable identity before terminating only the owned Python parent, rather than weakening the ownership check. Original failure records remain archived.

## Reproduce

```powershell
uv run python scripts/run_reconciliation_cases.py --home runtime/new-recovery-cases
$env:ALPHAMOSAIC_HOME = (Join-Path (Get-Location) 'runtime/new-recovery-cases')
uv run alphamosaic research-plans
uv run alphamosaic reconcile-research-plan PLAN_ID
uv run python -m streamlit run src/alphamosaic/ui/app.py --theme.base dark
uv run pytest tests/test_reconciliation_process.py -q -W error::RuntimeWarning
```

Use an actual generated plan ID. The suite explicitly injects parent loss around real fixed workers, retains a separately identified pending browser fixture and asserts no reconciliation-created experiments. The genuine-process test is additional evidence beyond exception injection. Choose a new home for a new suite; no unknown directory or finalized report is replaced.

## Limits and next work

This is single-user local integrity, not authentication against a hostile concurrent filesystem writer. Candidate inspection is a conservative linear full-store scan with no silent truncation. Unsealed/unknown artifacts remain unresolved and block new planned dispatch; no automatic quarantine, cleanup, retry or grade promotion is introduced. Late observations do not prove eventual absence of writers. Unsupported legacy schemas require explicit review rather than silent migration.

Real licensed PIT/actions/universe/delisting research, cash-in-lieu/special economics, causal RAW weekly adjustments, broader benchmarks/portfolio/factor/statistical validation, richer robustness controls, PDF/Parquet and adaptive model planning remain incomplete. No broker or real-account path exists in this feature.
