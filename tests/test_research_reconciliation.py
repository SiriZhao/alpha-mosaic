"""Interrupted-plan review preserves artifacts and never replays uncertain work."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from alphamosaic.agents.worker import main as worker_main
from alphamosaic.agents.workflow import ResearchPlanRequest
from alphamosaic.common.locking import ResearchBusyError, exclusive_lease
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import ExperimentStore, canonical, digest


def interrupted(home: Path):
    service = ApplicationService(home)
    dataset = service.research_demo(80)["dataset_id"]
    workflow = service.research_workflow()
    plan = workflow.create(ResearchPlanRequest(dataset_id=dataset,
        question="Can an interrupted fixed plan be reviewed without replaying uncertain trials?",
        strategies=["buy_and_hold"], cost_scenarios=["realistic", "stress"]))
    attempt = uuid4().hex
    config = {**plan["trials"][0]["config"], "research_context": {
        "plan_id": plan["plan_id"], "attempt_id": attempt, "ordinal": 0}}
    workflow.store.append(plan["plan_id"], "RUN_STARTED", {"max_trials": 2})
    workflow.store.append(plan["plan_id"], "TOOL_CALL", {"tool": "RUN_LOCAL_EXPERIMENT",
        "attempt_id": attempt, "ordinal": 0, "timeout_seconds": 60,
        "config_hash": digest(canonical(plan["trials"][0]["config"]))})
    directory = workflow.store.root / plan["plan_id"]
    directory.mkdir()
    path = directory / (attempt + "-request.json")
    payload = {"config": config, "expected_source_hash": plan["source_hash"],
        "dataset_hash": plan["dataset_hash"], "response": attempt + "-response.json"}
    path.write_bytes(canonical(payload))
    return service, workflow, plan, attempt, path, payload


def reviews(state):
    return [e["payload"] for e in state["events"] if e["kind"] == "RECOVERED_ATTEMPT"]


def finish(state):
    return next(e["payload"] for e in state["events"] if e["kind"] == "RECONCILIATION_FINISHED")


def sealed(home: Path):
    state = interrupted(home)
    assert worker_main(home, state[4]) == 0
    item = ExperimentStore(home / "experiments").list()[0]
    return (*state, item["experiment_id"])


def reseal(path: Path, update):
    item = json.loads((path / "experiment.json").read_bytes())
    update(item)
    (path / "experiment.json").write_bytes(canonical(item))
    (path / "config.json").write_bytes(canonical(item["config"]))
    hashes = {p.name: digest(p.read_bytes()) for p in path.iterdir() if p.is_file() and p.name != "checksums.json"}
    (path / "checksums.json").write_bytes(canonical(hashes))


def test_missing_artifact_is_unresolved_not_failed_or_successful_and_never_reruns(tmp_path: Path) -> None:
    service, workflow, plan, _, _, _ = interrupted(tmp_path)
    original = workflow.store.events(plan["plan_id"])
    result = service.reconcile_research_plan(plan["plan_id"])
    assert result["status"] == "INTERRUPTED"
    assert result["events"][:len(original)] == original
    assert reviews(result)[0]["classification"] == "INTERRUPTED_UNRESOLVED"
    assert reviews(result)[0]["exit_status"] == "NOT_OBSERVED"
    assert finish(result)["unattempted_ordinals"] == [1]
    assert finish(result)["new_trials_executed"] == 0
    assert service.run_research_plan(plan["plan_id"]) == result
    assert service.reconcile_research_plan(plan["plan_id"]) == result
    assert ExperimentStore(tmp_path / "experiments").list() == []


def test_completed_artifact_is_recovered_without_inventing_original_worker_exit(tmp_path: Path) -> None:
    service, workflow, plan, _, _, _, experiment_id = sealed(tmp_path)
    directory = tmp_path / "experiments" / experiment_id
    original = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    result = service.reconcile_research_plan(plan["plan_id"])
    record = reviews(result)[0]
    assert record["classification"] == "RECOVERED_COMPLETED_ARTIFACT"
    assert record["exit_status"] == "NOT_OBSERVED" and record["artifact"]["experiment_id"] == experiment_id
    assert finish(result)["recorded_outcomes"] == 0 and finish(result)["recovered_completed_artifacts"] == 1
    assert not any(e["kind"] == "TOOL_RESULT" for e in result["events"])
    assert {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()} == original
    report = workflow.report(plan["plan_id"])
    assert report["outcomes"] == [] and report["critics"] == [] and report["comparison"] is None
    assert report["trials_dispatched"] == 1
    assert service.reconcile_research_plan(plan["plan_id"]) == result


def test_new_reconciler_source_can_review_frozen_old_artifacts_without_reexecution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, plan, _, _, _, experiment_id = sealed(tmp_path)
    from alphamosaic.agents import reconciliation
    monkeypatch.setattr(reconciliation, "source_manifest", lambda: {"source_hash": "0" * 64})
    result = service.reconcile_research_plan(plan["plan_id"])
    assert reviews(result)[0]["classification"] == "RECOVERED_COMPLETED_ARTIFACT"
    assert reviews(result)[0]["source_hash"] == plan["source_hash"] != "0" * 64
    fence = next(e["payload"] for e in result["events"] if e["kind"] == "RECONCILIATION_STARTED")
    assert fence["reviewer_source_hash"] == "0" * 64
    assert ExperimentStore(tmp_path / "experiments").list()[0]["experiment_id"] == experiment_id


def test_missing_response_does_not_invalidate_sealed_artifact_or_prove_exit(tmp_path: Path) -> None:
    service, _, plan, _, path, payload, _ = sealed(tmp_path)
    response = path.with_name(payload["response"])
    response.rename(response.with_suffix(".original-response-preserved"))
    result = service.reconcile_research_plan(plan["plan_id"])
    record = reviews(result)[0]
    assert record["classification"] == "RECOVERED_COMPLETED_ARTIFACT"
    assert record["response_snapshot"] == {"state": "ABSENT_OBSERVED", "absence_is_final": False}
    assert record["exit_status"] == "NOT_OBSERVED"


def test_delayed_prestart_child_cannot_cross_completed_reconciliation_fence(tmp_path: Path) -> None:
    service, _, plan, _, path, _ = interrupted(tmp_path)
    initial = service.reconcile_research_plan(plan["plan_id"])
    assert worker_main(tmp_path, path) == 1
    assert ExperimentStore(tmp_path / "experiments").list() == []
    observed = service.reconcile_research_plan(plan["plan_id"])
    assert reviews(observed) == reviews(initial) and finish(observed) == finish(initial)
    late = [e["payload"] for e in observed["events"] if e["kind"] == "RECONCILIATION_RESPONSE_OBSERVED"]
    assert len(late) == 1 and late[0]["classification_effect"] == "NONE"
    assert service.reconcile_research_plan(plan["plan_id"]) == observed


@pytest.mark.parametrize("lease", ["plan", "global"])
def test_reconciliation_refuses_real_os_lease_without_fencing_or_guessing_liveness(tmp_path: Path, lease: str) -> None:
    service, workflow, plan, _, _, _ = interrupted(tmp_path)
    original = workflow.store.events(plan["plan_id"])
    path = workflow.store.root / (plan["plan_id"] + ".lease") if lease == "plan" else tmp_path / "research_execution.lease"
    with exclusive_lease(path), pytest.raises(ResearchBusyError):
        service.reconcile_research_plan(plan["plan_id"])
    assert workflow.store.events(plan["plan_id"]) == original


@pytest.mark.parametrize("outcome", ["TIMED_OUT", "FAILED", "BUSY"])
def test_recorded_unsuccessful_outcome_is_never_upgraded_by_a_complete_late_artifact(tmp_path: Path, outcome: str) -> None:
    service, workflow, plan, attempt, _, _, experiment_id = sealed(tmp_path)
    recorded = {"attempt_id": attempt, "ordinal": 0, "status": outcome, "experiment_id": experiment_id}
    workflow.store.append(plan["plan_id"], "TOOL_RESULT", recorded)
    result = service.reconcile_research_plan(plan["plan_id"])
    assert reviews(result)[0]["classification"] == "RECORDED_OUTCOME_PRESERVED"
    assert reviews(result)[0]["recorded_outcome"] == recorded
    assert finish(result)["recorded_outcomes"] == 1 and finish(result)["recovered_completed_artifacts"] == 0
    assert [e["payload"] for e in result["events"] if e["kind"] == "TOOL_RESULT"] == [recorded]


@pytest.mark.parametrize("defect", ["source", "manifest", "config", "context", "duplicate", "checksum", "missing_checksum", "unknown_directory", "running", "forged_response", "request"])
def test_candidate_qualification_fails_closed_without_changing_original_artifacts(tmp_path: Path, defect: str) -> None:
    service, _, plan, _, path, payload, experiment_id = sealed(tmp_path)
    directory = tmp_path / "experiments" / experiment_id
    if defect == "source":
        reseal(directory, lambda item: item["reproducibility"].update(source_hash="f" * 64))
    elif defect == "manifest":
        reseal(directory, lambda item: item["dataset_manifest"].update(manifest_hash="f" * 64))
    elif defect == "config":
        reseal(directory, lambda item: item["config"].update(strategy="trend"))
    elif defect == "context":
        reseal(directory, lambda item: item["config"]["research_context"].update(ordinal=1))
    elif defect == "duplicate":
        duplicate = directory.parent / ("b" * 32)
        shutil.copytree(directory, duplicate)
        reseal(duplicate, lambda item: item.update(experiment_id=duplicate.name))
    elif defect == "checksum":
        (directory / "equity.csv").write_text("corrupt")
    elif defect == "missing_checksum":
        (directory / "checksums.json").rename(directory / "original-checksums-preserved.json")
    elif defect == "unknown_directory":
        (directory.parent / ("a" * 32)).mkdir()
    elif defect == "running":
        (directory / "checksums.json").rename(directory / "original-checksums-preserved.json")
        item = json.loads((directory / "experiment.json").read_bytes())
        item["status"] = "RUNNING"
        (directory / "experiment.json").write_bytes(canonical(item))
    elif defect == "forged_response":
        path.with_name(payload["response"]).write_bytes(canonical({"status": "COMPLETED", "experiment_id": "f" * 32}))
    elif defect == "request":
        path.write_bytes(canonical({**payload, "expected_source_hash": "f" * 64}))
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and "experiments" in p.parts}
    result = service.reconcile_research_plan(plan["plan_id"])
    assert reviews(result)[0]["classification"] == "INTERRUPTED_UNRESOLVED", defect
    assert finish(result)["recovered_completed_artifacts"] == 0
    assert {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and "experiments" in p.parts} == before


@pytest.mark.parametrize("phase", ["RECONCILIATION_STARTED", "RECOVERED_ATTEMPT"])
def test_reconciliation_crash_after_fence_or_record_resumes_append_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str) -> None:
    service, workflow, plan, _, _, _ = interrupted(tmp_path)
    append = workflow.store.append
    def interrupted_append(plan_id, kind, payload):
        append(plan_id, kind, payload)
        if kind == phase:
            raise RuntimeError("simulated-parent-interruption")
    monkeypatch.setattr(workflow.store, "append", interrupted_append)
    with pytest.raises(RuntimeError, match="simulated-parent"):
        service.reconcile_research_plan(plan["plan_id"])
    partial = workflow.status(plan["plan_id"])
    assert partial["status"] == "RECONCILIATION_IN_PROGRESS"
    monkeypatch.setattr(workflow.store, "append", append)
    complete = service.reconcile_research_plan(plan["plan_id"])
    assert complete["status"] == "INTERRUPTED" and len(reviews(complete)) == 1
    assert complete["events"][:len(partial["events"])] == partial["events"]


def test_audit_cannot_dispatch_or_reclassify_after_reconciliation(tmp_path: Path) -> None:
    service, workflow, plan, attempt, _, _ = interrupted(tmp_path)
    result = service.reconcile_research_plan(plan["plan_id"])
    workflow.store.append(plan["plan_id"], "TOOL_RESULT", {"attempt_id": attempt, "ordinal": 0, "status": "COMPLETED"})
    with pytest.raises(ValueError, match="after reconciliation fence"):
        workflow.status(plan["plan_id"])
    assert reviews(result)[0]["classification"] == "INTERRUPTED_UNRESOLVED"


def test_missing_recovered_proof_is_rejected_even_with_a_valid_event_hash_chain(tmp_path: Path) -> None:
    _, workflow, plan, attempt, _, _ = interrupted(tmp_path)
    events = workflow.store.events(plan["plan_id"])
    identity = uuid4().hex
    workflow.store.append(plan["plan_id"], "RECONCILIATION_STARTED", {
        "reconciliation_id": identity, "original_event_count": len(events),
        "original_head_hash": events[-1]["content_hash"], "dispatch_disabled": True,
        "reviewer_source_hash": "a" * 64})
    response = {"state": "ABSENT_OBSERVED", "absence_is_final": False}
    workflow.store.append(plan["plan_id"], "RECOVERED_ATTEMPT", {
        "reconciliation_id": identity, "attempt_id": attempt, "ordinal": 0,
        "classification": "RECOVERED_COMPLETED_ARTIFACT", "exit_status": "NOT_OBSERVED",
        "recorded_outcome": None, "response_snapshot": response,
        "response_snapshot_hash": digest(canonical(response)),
        "source_hash": plan["source_hash"], "dataset_hash": plan["dataset_hash"],
        "manifest_hash": plan["manifest_hash"], "artifact": {"experiment_id": "a" * 32}})
    with pytest.raises(ValueError, match="frozen identity evidence"):
        workflow.status(plan["plan_id"])


def test_frozen_and_finished_plans_are_noops(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path)
    dataset = service.research_demo(80)["dataset_id"]
    plan = service.plan_research({"dataset_id": dataset, "question": "Does this frozen passive plan remain unchanged during reconciliation?", "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic"]})
    before = service.research_plan(plan["plan_id"])
    assert service.reconcile_research_plan(plan["plan_id"]) == before
    result = service.run_research_plan(plan["plan_id"])
    assert result["status"] == "COMPLETED"
    assert service.reconcile_research_plan(plan["plan_id"]) == result


def test_redirected_plan_directory_is_not_followed_or_modified(tmp_path: Path) -> None:
    service, workflow, plan, _, path, _ = interrupted(tmp_path)
    original = path.parent
    preserved = original.with_name(original.name + "-preserved")
    original.rename(preserved)
    outside = tmp_path / "outside-plan"
    outside.mkdir()
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(original), str(outside)], capture_output=True, check=True)
    else:
        original.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="redirected"):
            service.reconcile_research_plan(plan["plan_id"])
        assert list(outside.iterdir()) == []
        assert workflow.status(plan["plan_id"])["status"] == "RECONCILIATION_IN_PROGRESS"
    finally:
        if os.name == "nt":
            os.rmdir(original)
        else:
            original.unlink()
