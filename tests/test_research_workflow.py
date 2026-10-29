"""Real bounded worker execution and durable research-plan audit behavior."""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from alphamosaic.agents.worker import main as worker_main
from alphamosaic.agents.workflow import ResearchPlanRequest, ResearchPlanStore, ResearchWorkflow
from alphamosaic.common.locking import ResearchBusyError, exclusive_lease
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import ExperimentStore


@pytest.fixture
def workflow(tmp_path: Path) -> tuple[ResearchWorkflow, str]:
    manifest = ApplicationService(tmp_path).research_demo(100)
    return ResearchWorkflow(tmp_path), manifest["dataset_id"]


def request(dataset: str, **changes) -> ResearchPlanRequest:
    return ResearchPlanRequest.model_validate({"dataset_id": dataset,
        "question": "Does the unchanged passive baseline survive both declared cost assumptions?",
        "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic", "stress"], **changes})


def test_frozen_plan_runs_both_declared_cases_and_never_silently_repeats(workflow) -> None:
    engine, dataset = workflow
    # A writable dataset directory must never become a Python module search entry.
    shadow = engine.home / "alphamosaic"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("raise RuntimeError('UNTRUSTED_DATA_HOME_IMPORTED')")
    plan = engine.create(request(dataset))
    assert engine.status(plan["plan_id"])["status"] == "FROZEN"
    result = engine.run(plan["plan_id"])
    assert result["status"] == "COMPLETED", result["events"]
    calls = [e for e in result["events"] if e["kind"] == "TOOL_CALL"]
    outcomes = [e for e in result["events"] if e["kind"] == "TOOL_RESULT"]
    assert len(calls) == len(outcomes) == 2
    assert [e["payload"]["ordinal"] for e in calls] == [0, 1]
    experiments = ExperimentStore(engine.home / "experiments")
    for event in outcomes:
        item = experiments.load(event["payload"]["experiment_id"])
        assert item["config"]["research_context"]["plan_id"] == plan["plan_id"]
        assert item["config"]["research_context"]["attempt_id"] == event["payload"]["attempt_id"]
        assert item["dataset_hash"] == plan["dataset_hash"]
        assert item["review"]["automatic_promotion"] is False
    repeated = ResearchWorkflow(engine.home).run(plan["plan_id"])
    assert repeated == result
    assert len(experiments.list()) == 2
    report = engine.report(plan["plan_id"])
    assert report["trials_attempted"] == 2 and len(report["critics"]) == 2
    assert report["comparison"]["status"] == "COMPARABLE"
    assert report["selection"] == "ALL_OUTCOMES_RETAINED"


def test_real_worker_deadline_is_recorded_and_cannot_automatically_retry(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset, cost_scenarios=["realistic"], per_experiment_seconds=.001))
    result = engine.run(plan["plan_id"])
    assert result["status"] == "FAILED"
    outcomes = [e for e in result["events"] if e["kind"] == "TOOL_RESULT"]
    assert len(outcomes) == 1 and outcomes[0]["payload"]["status"] == "TIMED_OUT"
    assert engine.run(plan["plan_id"]) == result


def test_interrupted_state_never_claims_process_liveness_or_restarts(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    engine.store.append(plan["plan_id"], "RUN_STARTED", {"max_trials": 2})
    result = engine.run(plan["plan_id"])
    assert result["status"] == "INCOMPLETE_OR_RUNNING"
    assert result["process_liveness"] == "NOT_INFERRED_FROM_PERSISTED_STATE"
    assert len(result["events"]) == 1


def test_active_os_lease_rejects_concurrent_run_and_releases_after_context(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    path = engine.store.root / (plan["plan_id"] + ".lease")
    with exclusive_lease(path), pytest.raises(ResearchBusyError):
        engine.run(plan["plan_id"])
    with exclusive_lease(path):
        pass


def test_global_lease_covers_direct_service_and_planned_workers(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset, cost_scenarios=["realistic"]))
    with exclusive_lease(engine.home / "research_execution.lease"):
        with pytest.raises(ResearchBusyError):
            ApplicationService(engine.home).research_experiment({"dataset_id": dataset})
        state = engine.run(plan["plan_id"])
    outcomes = [e for e in state["events"] if e["kind"] == "TOOL_RESULT"]
    assert outcomes[0]["payload"]["status"] == "BUSY"
    assert state["status"] == "FAILED"


def test_audit_rejects_forged_completion_and_mutated_event_payload(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    engine.store.append(plan["plan_id"], "RUN_STARTED", {"max_trials": 2})
    engine.store.append(plan["plan_id"], "RUN_FINISHED", {"status": "COMPLETED", "attempted": 0, "declared": 2, "completed": 0})
    with pytest.raises(ValueError, match="counters"):
        engine.status(plan["plan_id"])
    with engine.store.connection() as db:
        db.execute("UPDATE events SET payload='{}' WHERE plan_id=? AND sequence=1", (plan["plan_id"],))
    with pytest.raises(ValueError, match="hash"):
        engine.store.events(plan["plan_id"])


def test_legacy_audit_database_is_rejected_without_replacement(tmp_path: Path) -> None:
    path = tmp_path / "plans.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE events(event_id TEXT,payload TEXT)")
        db.execute("INSERT INTO events VALUES('original','preserve')")
    original = path.read_bytes()
    with pytest.raises(ValueError, match="legacy"):
        ResearchPlanStore(tmp_path)
    assert path.read_bytes() == original


def test_worker_exit_failure_cannot_become_success_from_response_file(workflow, monkeypatch: pytest.MonkeyPatch) -> None:
    engine, _ = workflow
    request_path, response = engine.home / "request.json", engine.home / "response.json"
    request_path.write_text("{}")
    response.write_text(json.dumps({"status": "COMPLETED", "experiment_id": "a" * 32}))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 7))
    with pytest.raises(ValueError, match="abnormally"):
        engine._worker(request_path, response, 10)


@pytest.mark.parametrize("changes", [
    {"strategies": ["unknown"]}, {"strategies": ["trend", "trend"]},
    {"cost_scenarios": ["zero"]}, {"cost_scenarios": ["realistic", "realistic"]},
    {"max_trials": 1}, {"total_seconds": float("inf")}, {"per_experiment_seconds": 0},
    {"dataset_id": "../escape"}, {"shell_command": "anything"},
])
def test_unknown_tools_unbounded_inputs_and_unreviewed_grids_are_rejected(workflow, changes) -> None:
    _, dataset = workflow
    with pytest.raises(ValueError):
        request(dataset, **changes)


def test_invalid_assets_and_dates_cannot_be_frozen(workflow) -> None:
    engine, dataset = workflow
    with pytest.raises(ValueError, match="assets"):
        engine.create(request(dataset, symbols=["ABSENT"]))
    with pytest.raises(ValueError):
        engine.create(request(dataset, start="2020-02-01", end="2020-01-01"))


def test_plan_integrity_identity_and_source_mismatch_fail_closed(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    with engine.store.connection() as db:
        db.execute("UPDATE plans SET payload=? WHERE plan_id=?", (json.dumps({**plan, "hypothesis": "changed"}), plan["plan_id"]))
    with pytest.raises(ValueError, match="integrity"):
        engine.store.load(plan["plan_id"])
    with pytest.raises(ValueError):
        engine.status("../escape")
    with pytest.raises(ValueError):
        worker_main(engine.home, engine.home / "untrusted.json")


def test_optional_model_text_is_isolated_from_numeric_evidence(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    class TextAdapter:
        def explain(self, evidence: dict) -> str:
            evidence["outcomes"].append({"invented": 999999})
            return "This text is a hypothesis, not a computed observation."
    result = engine.report(plan["plan_id"], TextAdapter())
    assert result["outcomes"] == []
    assert result["optional_model_commentary"]["evidence_class"] == "MODEL_INFERENCE"
    assert result["optional_model_commentary"]["numeric_authority"] is False
    assert engine.store.events(plan["plan_id"]) == []


@pytest.mark.parametrize("text", ["The future return is 99%", "Guaranteed alpha is available"])
def test_optional_model_cannot_introduce_uncomputed_figures_or_promotion(workflow, text: str) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    class UnsupportedAdapter:
        def explain(self, evidence: dict) -> str:
            return text
    with pytest.raises(ValueError):
        engine.report(plan["plan_id"], UnsupportedAdapter())


def test_plan_directory_junction_cannot_redirect_artifact_writes(workflow) -> None:
    engine, dataset = workflow
    plan = engine.create(request(dataset))
    target = engine.home / "outside-plan-store"
    target.mkdir()
    link = engine.store.root / plan["plan_id"]
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=True)
    else:
        link.symlink_to(target, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="redirected"):
            engine.run(plan["plan_id"])
        assert list(target.iterdir()) == []
        assert engine.store.events(plan["plan_id"]) == []
        with pytest.raises(ValueError, match="redirected"):
            with exclusive_lease(link / "unsafe.lease"):
                pytest.fail("lease followed the redirected parent")
        assert list(target.iterdir()) == []
    finally:
        if os.name == "nt":
            os.rmdir(link)
        else:
            link.unlink()
