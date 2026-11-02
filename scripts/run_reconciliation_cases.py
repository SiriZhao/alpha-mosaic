"""Reproduce explicit FIXTURE parent interruptions; reconciliation never runs trials."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import canonical, digest, source_manifest


class SimulatedInterruption(RuntimeError):
    pass


def run(home: Path) -> dict:
    initial_source = source_manifest()["source_hash"]
    service = ApplicationService(home)
    dataset = service.research_demo(80)
    workflow = service.research_workflow()
    worker = workflow._worker
    cases = []

    def declare():
        return service.plan_research({"dataset_id": dataset["dataset_id"],
            "question": "Can frozen synthetic work survive explicit parent-loss injection without duplicate execution or invented process success?",
            "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic", "stress"]})

    def interrupt(plan_id: str, after_worker: bool):
        def stop(request, response, timeout):
            if after_worker:
                outcome = worker(request, response, timeout)
                if outcome["status"] != "COMPLETED":
                    raise AssertionError("fixture worker did not produce a sealed completed artifact")
            raise SimulatedInterruption("explicit-software-fixture-parent-loss")
        with patch.object(workflow, "_worker", side_effect=stop):
            try:
                service.run_research_plan(plan_id)
            except SimulatedInterruption:
                return
        raise AssertionError("expected parent-loss fixture did not interrupt")

    frozen = declare()
    before = service.research_plan(frozen["plan_id"])
    assert service.reconcile_research_plan(frozen["plan_id"]) == before
    cases.append({"case": "frozen_noop", "plan_id": frozen["plan_id"], "status": "FROZEN"})

    artifact_plan = declare()
    interrupt(artifact_plan["plan_id"], True)
    prior = service.research_experiments()
    matching = [item for item in prior if (item.get("research_context") or {}).get("plan_id") == artifact_plan["plan_id"]]
    assert len(matching) == 1
    artifact_files = {p: digest(p.read_bytes()) for p in (home / "experiments" / matching[0]["experiment_id"]).iterdir() if p.is_file()}
    recovered = service.reconcile_research_plan(artifact_plan["plan_id"])
    record = next(e["payload"] for e in recovered["events"] if e["kind"] == "RECOVERED_ATTEMPT")
    assert record["classification"] == "RECOVERED_COMPLETED_ARTIFACT" and record["exit_status"] == "NOT_OBSERVED"
    assert not any(e["kind"] == "TOOL_RESULT" for e in recovered["events"])
    assert service.reconcile_research_plan(artifact_plan["plan_id"]) == recovered
    assert service.run_research_plan(artifact_plan["plan_id"]) == recovered
    assert {p: digest(p.read_bytes()) for p in artifact_files} == artifact_files
    cases.append({"case": "sealed_artifact_parent_result_lost", "plan_id": artifact_plan["plan_id"],
        "status": recovered["status"], "classification": record["classification"],
        "exit_status": record["exit_status"], "artifact": record["artifact"]})

    delayed_plan = declare()
    interrupt(delayed_plan["plan_id"], False)
    fenced = service.reconcile_research_plan(delayed_plan["plan_id"])
    call = next(e["payload"] for e in fenced["events"] if e["kind"] == "TOOL_CALL")
    directory = workflow.store.root / delayed_plan["plan_id"]
    late = worker(directory / (call["attempt_id"] + "-request.json"),
        directory / (call["attempt_id"] + "-response.json"), 60)
    assert late["status"] == "FAILED" and service.research_experiments() == prior
    observed = service.reconcile_research_plan(delayed_plan["plan_id"])
    assert len(observed["events"]) == len(fenced["events"]) + 1
    assert observed["events"][-1]["kind"] == "RECONCILIATION_RESPONSE_OBSERVED"
    assert service.reconcile_research_plan(delayed_plan["plan_id"]) == observed
    record = next(e["payload"] for e in observed["events"] if e["kind"] == "RECOVERED_ATTEMPT")
    assert record["classification"] == "INTERRUPTED_UNRESOLVED"
    cases.append({"case": "delayed_prestart_worker_refused", "plan_id": delayed_plan["plan_id"],
        "status": observed["status"], "classification": record["classification"],
        "late_worker": late["status"], "late_observations": 1})

    # Deliberately retain an interrupted fixture for the explicit browser action.
    # It has no live worker; persisted state alone never certifies that fact.
    browser = declare()
    interrupt(browser["plan_id"], False)
    assert source_manifest()["source_hash"] == initial_source
    evidence = {"status": "PASSED", "scope": "FIXTURE_SOFTWARE_FAULT_INJECTION_ONLY",
        "market_performance_inference": "PROHIBITED", "source_hash": initial_source,
        "dataset_id": dataset["dataset_id"], "cases": cases,
        "browser_pending_plan": browser["plan_id"], "recovered_plan": artifact_plan["plan_id"],
        "setup_experiments": len(prior), "reconciliation_experiments_executed": 0,
        "process_success_inferred": False, "broker_enabled": False}
    home.mkdir(parents=True, exist_ok=True)
    with (home / ("reconciliation-suite-" + uuid4().hex + ".json")).open("xb") as stream:
        stream.write(canonical(evidence))
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path("runtime/reconciliation-cases"))
    print(json.dumps(run(parser.parse_args().home)))
