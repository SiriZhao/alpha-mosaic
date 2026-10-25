# Frozen research dispatch boundary

Status: implemented and locally verified; full platform goal remains ACTIVE. This checkpoint prevents unauthorized, duplicate or late planned experiment creation. It does not implement interrupted-plan reconciliation or automatic resumption.

## Reproduced problem and repaired contract

The fixed worker previously trusted a persisted request without binding it to its frozen audit call. Four counterexamples actually created experiments for an unknown plan, modified strategy, already terminated plan, or duplicate pending attempt. Independent review found two further paths: removing the research context bypassed planned authorization, and a partial experiment directory without metadata disappeared from globbed listings. All six failures were reproduced before repair; original JUnit files are retained.

`ExperimentRunner.run()` now holds the global per-home OS lease across planned authorization and experiment creation. Authorization verifies an open audited plan, a unique pending attempt/ordinal, unchanged full configuration, frozen source/manifest fingerprints and exact canonical request/response names. An existing response or experiment for that attempt refuses dispatch. Every experiment child is inspected; unidentified, corrupt, redirected and unsealed records prevent planned dispatch instead of proving absence of a prior run. Original paths are checked before store construction can resolve away a junction. Ordinary direct experiments remain available without fabricated plan context.

The fixed worker requires its nonnull plan/attempt context and exact directory/request/response identity. Its source, request and dataset boundaries are checked before invoking the shared service. Authorization failure never creates an experiment; immutable response-file collisions remain visible errors. No worker command, filesystem path, broker or credential tool is added.

Source SHA256: `a26523a908f264868dee7eb4da6a3df92f4ab0b16a2bf65514c52d74b1b1c988`.

## Verification

Full regression:361 passed, zero failed/error/skipped, RuntimeWarning treated as error; four upstream calendar deprecations remain visible. Both Windows junction tests actually ran with the required sandbox permission. Ruff/Pyright and uv lock check passed;140 locked dependencies are unchanged. Independent reviewer ran14 dispatch cases successfully, intentionally deselecting only its junction case; parent full regression includes that case. The reviewer verified unchanged source hashes before/after and found no remaining guard-scope blocker.

Coverage includes missing/mutated context, wrong ordinal/attempt/response, extra/noncanonical request content, an outcome recorded before termination, duplicate requests, unidentified and unsealed other-attempt artifacts, active global lease, actual root junction rejection and the existing real subprocess/frozen-plan integration. Negative paths check absence of a new artifact and preserve original partial records.

Fresh wheel/build/MCP and hosted CI are separate gates recorded in `evidence/research-dispatch-20261025/`. Prior payment evidence and browser captures apply to their named source; this change does not alter UI/report code. No synthetic result establishes market performance.

Local final package acceptance passed: wheel and installed bytes match all59 tested source files, sdist excludes runtime/venv/Git, and a new base environment without OpenBB/QuantStats/Streamlit/Plotly completed the frozen workflow, four dividend cases, four isolated trials, CLI doctor and31-tool stdio MCP. Initial default-cache permission and proxy/pip download failures are recorded; a bounded uv install succeeded without changing dependencies or borrowing another environment. Hosted CI must still be read against the published implementation commit.

## Independent review and next recovery contract

The first test scaffold used30 sessions where the service requires at least80; this was corrected before reproducing the four actual dispatch failures. No production or financial assertion was weakened. Independent review additionally caught original-path resolution and trust in unsealed RUNNING records; both were repaired before full acceptance.

Future reconciliation must acquire plan then global OS leases, append a durable dispatch fence, and preserve the original hash chain and outcomes. A uniquely matched sealed completed artifact can be reported as `RECOVERED_COMPLETED_ARTIFACT` with `exit_status=NOT_OBSERVED`; it must not be forged into a historical successful TOOL_RESULT. Existing failed/timed-out outcomes must not be upgraded. Missing, corrupt, ambiguous or incomplete candidates remain unresolved, and unattempted trials are not silently scheduled. Repeated or interrupted reconciliation must be idempotent and append-only.

A delayed child checks the terminal fence under the same global lease before creating an experiment. The global lease does **not** certify that all response writers have exited: workers write responses after releasing it and BUSY workers may also write. Late immutable responses remain extra evidence, never authority to rewrite history or infer process success. Persisted file contents, PID strings and timestamps do not prove liveness.

Remaining implementation: explicit reconciliation events/API/CLI/UI, candidate matching and integrity accounting, safe reconciliation restart and delayed-response tests. A directory-wide scan is deliberately conservative and linear in retained experiments; an indexed optimization requires profiling and equivalent correctness. Local checks do not protect against a hostile filesystem writer replacing all bytes and hashes concurrently. No completion or production-readiness claim is made.
