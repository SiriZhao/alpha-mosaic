"""Persisted requests alone cannot authorize late or duplicate research workers."""

import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from alphamosaic.agents.worker import main as worker_main
from alphamosaic.agents.workflow import ResearchPlanRequest, ResearchWorkflow
from alphamosaic.common.locking import exclusive_lease
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import ExperimentStore, canonical, digest


def dispatched(home: Path):
    dataset = ApplicationService(home).research_demo(80)["dataset_id"]
    workflow = ResearchWorkflow(home)
    plan = workflow.create(ResearchPlanRequest(dataset_id=dataset,
        question="Does this fixed passive trial preserve its single dispatch identity?",
        strategies=["buy_and_hold"], cost_scenarios=["realistic"]))
    attempt = uuid4().hex
    config = {**plan["trials"][0]["config"], "research_context": {
        "plan_id": plan["plan_id"], "attempt_id": attempt, "ordinal": 0}}
    workflow.store.append(plan["plan_id"], "RUN_STARTED", {"max_trials": 1})
    workflow.store.append(plan["plan_id"], "TOOL_CALL", {"tool": "RUN_LOCAL_EXPERIMENT",
        "ordinal": 0, "attempt_id": attempt,
        "config_hash": digest(canonical(plan["trials"][0]["config"])), "timeout_seconds": 60})
    directory = workflow.store.root / plan["plan_id"]
    directory.mkdir()
    path = directory / (attempt + "-request.json")
    payload = {"config": config, "expected_source_hash": plan["source_hash"],
        "dataset_hash": plan["dataset_hash"], "response": attempt + "-response.json"}
    path.write_bytes(canonical(payload))
    return workflow, plan, attempt, path, payload


@pytest.mark.parametrize("change", ["unknown_plan", "changed_config", "finished_plan", "context_removed"])
def test_worker_refuses_unauthorized_or_terminal_dispatch_before_creating_artifact(tmp_path: Path, change: str) -> None:
    workflow, plan, attempt, path, payload = dispatched(tmp_path)
    if change == "unknown_plan":
        payload["config"]["research_context"]["plan_id"] = "f" * 32
    elif change == "changed_config":
        payload["config"]["strategy"] = "trend"
    elif change == "context_removed":
        payload["config"]["research_context"] = None
    else:
        workflow.store.append(plan["plan_id"], "TOOL_RESULT", {
            "ordinal": 0, "attempt_id": attempt, "status": "TIMED_OUT"})
        workflow.store.append(plan["plan_id"], "RUN_FINISHED", {
            "status": "FAILED", "attempted": 1, "declared": 1, "completed": 0})
    path.write_bytes(canonical(payload))
    assert worker_main(tmp_path, path) == 1
    assert ExperimentStore(tmp_path / "experiments").list() == []


def test_duplicate_pending_attempt_cannot_create_second_experiment_after_parent_loss(tmp_path: Path) -> None:
    _, _, _, path, _ = dispatched(tmp_path)
    assert worker_main(tmp_path, path) == 0
    before = ExperimentStore(tmp_path / "experiments").list()
    assert len(before) == 1 and before[0]["status"] == "COMPLETED"
    # The first completed response is immutable; a late duplicate must not run
    # another experiment before discovering that its response already exists.
    with pytest.raises(FileExistsError):
        worker_main(tmp_path, path)
    assert ExperimentStore(tmp_path / "experiments").list() == before


def test_unidentified_partial_experiment_directory_cannot_be_treated_as_no_prior_attempt(tmp_path: Path) -> None:
    _, _, _, path, _ = dispatched(tmp_path)
    partial = tmp_path / "experiments" / ("a" * 32)
    partial.mkdir()
    assert worker_main(tmp_path, path) == 1
    assert list(partial.parent.iterdir()) == [partial]


@pytest.mark.parametrize("change", ["ordinal", "attempt", "response", "extra", "noncanonical", "recorded_outcome"])
def test_worker_request_is_bound_to_one_pending_canonical_call(tmp_path: Path, change: str) -> None:
    workflow, plan, attempt, path, payload = dispatched(tmp_path)
    if change == "ordinal":
        payload["config"]["research_context"]["ordinal"] = 1
    elif change == "attempt":
        payload["config"]["research_context"]["attempt_id"] = "f" * 32
    elif change == "response":
        payload["response"] = "other-response.json"
    elif change == "extra":
        payload["unreviewed"] = True
    elif change == "recorded_outcome":
        workflow.store.append(plan["plan_id"], "TOOL_RESULT", {"ordinal": 0,
            "attempt_id": attempt, "status": "TIMED_OUT"})
    path.write_bytes(json.dumps(payload, indent=2).encode() if change == "noncanonical" else canonical(payload))
    assert worker_main(tmp_path, path) == 1
    assert ExperimentStore(tmp_path / "experiments").list() == []


def test_unsealed_other_attempt_is_not_authoritative_absence_of_a_previous_run(tmp_path: Path) -> None:
    _, _, _, path, payload = dispatched(tmp_path)
    partial = tmp_path / "experiments" / ("a" * 32)
    partial.mkdir()
    other = {**payload["config"], "research_context": None}
    original = canonical({"status": "RUNNING", "experiment_id": partial.name,
        "created_at": "2026-01-01T00:00:00+00:00", "config": other})
    (partial / "experiment.json").write_bytes(original)
    assert worker_main(tmp_path, path) == 1
    assert list(partial.parent.iterdir()) == [partial]
    assert (partial / "experiment.json").read_bytes() == original


def test_active_global_lease_blocks_worker_before_artifact_creation(tmp_path: Path) -> None:
    _, _, _, path, _ = dispatched(tmp_path)
    with exclusive_lease(tmp_path / "research_execution.lease"):
        assert worker_main(tmp_path, path) == 1
    assert ExperimentStore(tmp_path / "experiments").list() == []


def test_experiment_store_redirect_is_refused_before_creating_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "outside-store"
    target.mkdir()
    link = tmp_path / "experiments"
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=True)
    else:
        link.symlink_to(target, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="redirected"):
            ApplicationService(tmp_path).experiment_runner()
        assert list(target.iterdir()) == []
    finally:
        if os.name == "nt":
            os.rmdir(link)
        else:
            link.unlink()
