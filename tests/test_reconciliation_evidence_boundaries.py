"""Independent semantic counterexamples supplement hash-chain integrity checks."""

from pathlib import Path
from uuid import uuid4

import pytest
from test_research_reconciliation import interrupted, sealed

from alphamosaic.experiments.runner import canonical, digest


@pytest.mark.parametrize("contradiction", ["failed_response", "wrong_experiment"])
def test_recovered_artifact_cannot_have_a_contradictory_response_in_a_valid_hash_chain(tmp_path: Path, contradiction: str) -> None:
    _, workflow, plan, attempt, path, _, experiment_id = sealed(tmp_path)
    events = workflow.store.events(plan["plan_id"])
    identity = uuid4().hex
    workflow.store.append(plan["plan_id"], "RECONCILIATION_STARTED", {
        "reconciliation_id": identity, "original_event_count": len(events),
        "original_head_hash": events[-1]["content_hash"], "dispatch_disabled": True,
        "reviewer_source_hash": plan["source_hash"]})
    raw = canonical({"status": "FAILED" if contradiction == "failed_response" else "COMPLETED",
        "experiment_id": "f" * 32 if contradiction == "wrong_experiment" else experiment_id,
        "source_hash": plan["source_hash"], "error": None})
    snapshot = {"state": "PRESENT", "bytes": len(raw), "sha256": digest(raw), "content_hex": raw.hex()}
    directory = tmp_path / "experiments" / experiment_id
    record = {"reconciliation_id": identity, "attempt_id": attempt, "ordinal": 0,
        "classification": "RECOVERED_COMPLETED_ARTIFACT", "recorded_outcome": None,
        "exit_status": "NOT_OBSERVED", "response_snapshot": snapshot,
        "response_snapshot_hash": digest(canonical(snapshot)),
        "artifact_qualification": "CHECKSUMS_AND_FROZEN_IDENTITY_VERIFIED_NOT_PROCESS_EXIT_PROOF",
        "candidate_issues": [], "candidate_ids": [experiment_id],
        "request_sha256": digest(path.read_bytes()), "source_hash": plan["source_hash"],
        "dataset_hash": plan["dataset_hash"], "manifest_hash": plan["manifest_hash"],
        "artifact": {"experiment_id": experiment_id,
            "experiment_sha256": digest((directory / "experiment.json").read_bytes()),
            "config_sha256": digest((directory / "config.json").read_bytes()),
            "checksums_sha256": digest((directory / "checksums.json").read_bytes())}}
    workflow.store.append(plan["plan_id"], "RECOVERED_ATTEMPT", record)
    with pytest.raises(ValueError, match="response.*contradicts|contradictory.*response"):
        workflow.status(plan["plan_id"])


def test_reconciliation_fence_requires_a_named_source_fingerprint(tmp_path: Path) -> None:
    _, workflow, plan, _, _, _ = interrupted(tmp_path)
    events = workflow.store.events(plan["plan_id"])
    workflow.store.append(plan["plan_id"], "RECONCILIATION_STARTED", {
        "reconciliation_id": uuid4().hex, "original_event_count": len(events),
        "original_head_hash": events[-1]["content_hash"], "dispatch_disabled": True,
        "reviewer_source_hash": "MISSING"})
    with pytest.raises(ValueError, match="reviewer.*source|source.*fingerprint"):
        workflow.status(plan["plan_id"])
