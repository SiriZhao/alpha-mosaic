"""Append-only review of interrupted fixed plans; never execute or retry a trial."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from alphamosaic.common.locking import exclusive_lease
from alphamosaic.common.paths import contained_child, unredirected
from alphamosaic.experiments.runner import (
    ExperimentConfig,
    ExperimentStore,
    canonical,
    digest,
    source_manifest,
)

if TYPE_CHECKING:
    from alphamosaic.agents.workflow import ResearchWorkflow

_RESPONSE_LIMIT = 65536
_CLASSIFICATIONS = {"RECORDED_OUTCOME_PRESERVED", "RECOVERED_COMPLETED_ARTIFACT", "INTERRUPTED_UNRESOLVED"}


def _response(path: Path) -> dict[str, Any]:
    """Snapshot bounded immutable response bytes, without inferring a writer's exit."""
    try:
        path = unredirected(path)
        if not path.exists():
            return {"state": "ABSENT_OBSERVED", "absence_is_final": False}
        with path.open("rb") as stream:
            raw = stream.read(_RESPONSE_LIMIT + 1)
        if len(raw) > _RESPONSE_LIMIT:
            return {"state": "OVERSIZED", "byte_limit": _RESPONSE_LIMIT}
        return {"state": "PRESENT", "bytes": len(raw), "sha256": digest(raw), "content_hex": raw.hex()}
    except (OSError, ValueError) as exc:
        return {"state": "UNREADABLE", "error_type": type(exc).__name__}


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("state") == "PRESENT":
        raw = bytes.fromhex(snapshot["content_hex"])
        if len(raw) > _RESPONSE_LIMIT or snapshot.get("bytes") != len(raw) or snapshot.get("sha256") != digest(raw):
            raise ValueError("response snapshot bytes or digest mismatch")
    elif snapshot.get("state") not in {"ABSENT_OBSERVED", "OVERSIZED", "UNREADABLE"}:
        raise ValueError("unknown response snapshot state")
    elif snapshot["state"] == "ABSENT_OBSERVED" and snapshot.get("absence_is_final") is not False:
        raise ValueError("response absence cannot establish process exit")


def _candidates(home: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Inspect every directory, including metadata-free interrupted children."""
    candidates: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    try:
        root = unredirected(home / "experiments")
        if not root.exists():
            return candidates, issues
        store = ExperimentStore(root)
        for entry in sorted(root.iterdir()):
            try:
                entry = unredirected(entry)
                if not entry.is_dir():
                    raise ValueError("unidentified experiment entry")
                item = store.load(entry.name)
                if item.get("integrity") == "INCOMPLETE_INTERRUPTED_OR_ACTIVE":
                    raise ValueError("unsealed experiment identity is not authoritative")
                if item.get("status") not in {"COMPLETED", "FAILED"}:
                    raise ValueError("unknown sealed experiment status")
                ExperimentConfig.model_validate(item["config"])
                config_path = contained_child(entry, "config.json")
                if config_path.read_bytes() != canonical(item["config"]):
                    raise ValueError("experiment configuration file differs from sealed record")
                candidates.append({"item": item, "fingerprints": {
                    "experiment_id": entry.name,
                    "experiment_sha256": digest(contained_child(entry, "experiment.json").read_bytes()),
                    "checksums_sha256": digest(contained_child(entry, "checksums.json").read_bytes()),
                    "config_sha256": digest(config_path.read_bytes())}})
            except (OSError, ValueError, KeyError, TypeError) as exc:
                fingerprints = {}
                for name in ("experiment.json", "config.json", "checksums.json"):
                    try:
                        path = contained_child(entry, name)
                        if path.is_file():
                            fingerprints[name] = digest(path.read_bytes())
                    except (OSError, ValueError):
                        pass
                issues.append({"entry": entry.name, "error_type": type(exc).__name__,
                    "reason": str(exc)[:300], "unverified_metadata_fingerprints": fingerprints})
    except (OSError, ValueError) as exc:
        issues.append({"entry": "EXPERIMENT_STORE", "error_type": type(exc).__name__, "reason": str(exc)[:300]})
    return candidates, issues


def _inspect(workflow: ResearchWorkflow, plan: dict[str, Any], call: dict[str, Any],
             recorded: dict[str, Any] | None, candidates: list[dict[str, Any]],
             issues: list[dict[str, Any]]) -> dict[str, Any]:
    attempt, ordinal = call["attempt_id"], call["ordinal"]
    directory = contained_child(workflow.store.root, plan["plan_id"])
    response = _response(directory / (attempt + "-response.json"))
    evidence: dict[str, Any] = {"attempt_id": attempt, "ordinal": ordinal,
        "classification": "RECORDED_OUTCOME_PRESERVED" if recorded else "INTERRUPTED_UNRESOLVED",
        "recorded_outcome": recorded, "exit_status": "NOT_REEVALUATED" if recorded else "NOT_OBSERVED", "response_snapshot": response,
        "response_snapshot_hash": digest(canonical(response)), "artifact_qualification": "NOT_ESTABLISHED",
        "candidate_issues": issues}
    if recorded:
        evidence["artifact_qualification"] = "HISTORICAL_OUTCOME_ONLY_NOT_FRESH_ARTIFACT_VERIFICATION"
        return evidence
    try:
        context = {"plan_id": plan["plan_id"], "attempt_id": attempt, "ordinal": ordinal}
        config = {**plan["trials"][ordinal]["config"], "research_context": context}
        ExperimentConfig.model_validate(config)
        expected = {"config": config, "expected_source_hash": plan["source_hash"],
            "dataset_hash": plan["dataset_hash"], "response": attempt + "-response.json"}
        request = contained_child(directory, attempt + "-request.json").read_bytes()
        evidence["request_sha256"] = digest(request)
        if request != canonical(expected):
            raise ValueError("request differs from the exact frozen authorization")
        workflow.datasets.load(config["dataset_id"])
        manifest = workflow.datasets.manifest(config["dataset_id"])
        if manifest["manifest_hash"] != plan["manifest_hash"] or manifest["dataset_hash"] != plan["dataset_hash"]:
            raise ValueError("dataset content or provenance differs from frozen plan")
        if issues:
            raise ValueError("unidentified, corrupt or unsealed candidates prevent unique artifact qualification")
        matches = [entry for entry in candidates if
            (entry["item"]["config"].get("research_context") or {}).get("attempt_id") == attempt
            or ((entry["item"]["config"].get("research_context") or {}).get("plan_id") == plan["plan_id"]
                and (entry["item"]["config"].get("research_context") or {}).get("ordinal") == ordinal)]
        evidence["candidate_ids"] = [entry["fingerprints"]["experiment_id"] for entry in matches]
        if len(matches) != 1:
            raise ValueError("no unique matching sealed experiment; absence is not process evidence")
        item = matches[0]["item"]
        if item["status"] != "COMPLETED" or item["config"] != config or item.get("dataset_hash") != plan["dataset_hash"]:
            raise ValueError("candidate status, context, full configuration or data hash mismatch")
        if item.get("dataset_manifest", {}).get("manifest_hash") != plan["manifest_hash"] or item.get("reproducibility", {}).get("source_hash") != plan["source_hash"]:
            raise ValueError("candidate source or provenance differs from frozen plan")
        if response["state"] == "PRESENT":
            actual = json.loads(bytes.fromhex(response["content_hex"]))
            expected_response = {"status": "COMPLETED", "experiment_id": item["experiment_id"],
                "source_hash": plan["source_hash"], "error": None}
            if actual != expected_response:
                raise ValueError("response contradicts the uniquely sealed artifact")
        elif response["state"] != "ABSENT_OBSERVED":
            raise ValueError("response evidence is unreadable or outside its bounded schema")
        evidence.update(classification="RECOVERED_COMPLETED_ARTIFACT",
            artifact_qualification="CHECKSUMS_AND_FROZEN_IDENTITY_VERIFIED_NOT_PROCESS_EXIT_PROOF",
            artifact=matches[0]["fingerprints"], dataset_hash=plan["dataset_hash"],
            manifest_hash=plan["manifest_hash"], source_hash=plan["source_hash"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        evidence["unresolved_reason"] = {"error_type": type(exc).__name__, "reason": str(exc)[:500]}
    return evidence


def _summary(plan: dict[str, Any], calls: list[dict[str, Any]], results: dict[str, Any],
             records: list[dict[str, Any]], reconciliation_id: str) -> dict[str, Any]:
    return {"reconciliation_id": reconciliation_id, "status": "INTERRUPTED",
        "declared": len(plan["trials"]), "dispatched": len(calls), "recorded_outcomes": len(results),
        "recovered_completed_artifacts": sum(r["classification"] == "RECOVERED_COMPLETED_ARTIFACT" for r in records),
        "unresolved_attempts": sum(r["classification"] == "INTERRUPTED_UNRESOLVED" for r in records),
        "unattempted_ordinals": [t["ordinal"] for t in plan["trials"][len(calls):]],
        "new_trials_executed": 0, "original_outcomes_rewritten": False,
        "process_liveness": "NOT_INFERRED_FROM_PERSISTED_STATE", "automatic_promotion": False}


def _observe(workflow: ResearchWorkflow, plan: dict[str, Any], records: list[dict[str, Any]],
             events: list[dict[str, Any]], reconciliation_id: str) -> None:
    seen = {(r["attempt_id"], r["response_snapshot_hash"]) for r in records}
    seen.update((e["payload"]["attempt_id"], e["payload"]["response_snapshot_hash"])
                for e in events if e["kind"] == "RECONCILIATION_RESPONSE_OBSERVED")
    directory = contained_child(workflow.store.root, plan["plan_id"])
    for record in records:
        snapshot = _response(directory / (record["attempt_id"] + "-response.json"))
        hashed = digest(canonical(snapshot))
        if (record["attempt_id"], hashed) not in seen:
            workflow.store.append(plan["plan_id"], "RECONCILIATION_RESPONSE_OBSERVED", {
                "reconciliation_id": reconciliation_id, "attempt_id": record["attempt_id"],
                "ordinal": record["ordinal"], "response_snapshot": snapshot,
                "response_snapshot_hash": hashed, "classification_effect": "NONE"})


def reconcile(workflow: ResearchWorkflow, plan_id: str) -> dict[str, Any]:
    """Fence and review an interrupted run; original artifacts and results stay intact."""
    workflow.store.validate_id(plan_id)
    with exclusive_lease(workflow.store.root / (plan_id + ".lease")), exclusive_lease(workflow.home / "research_execution.lease"):
        state = workflow.status(plan_id)
        if state["status"] in {"FROZEN", "COMPLETED", "PARTIAL", "FAILED"}:
            return state
        plan, events = state["plan"], state["events"]
        starts = [e for e in events if e["kind"] == "RECONCILIATION_STARTED"]
        if not starts:
            workflow.store.append(plan_id, "RECONCILIATION_STARTED", {
                "reconciliation_id": uuid4().hex, "original_event_count": len(events),
                "original_head_hash": events[-1]["content_hash"], "dispatch_disabled": True,
                "reviewer_source_hash": source_manifest()["source_hash"]})
            events = workflow.store.events(plan_id)
            starts = [e for e in events if e["kind"] == "RECONCILIATION_STARTED"]
        reconciliation_id = starts[0]["payload"]["reconciliation_id"]
        calls = [e["payload"] for e in events if e["kind"] == "TOOL_CALL"]
        results = {e["payload"]["attempt_id"]: e["payload"] for e in events if e["kind"] == "TOOL_RESULT"}
        records = [e["payload"] for e in events if e["kind"] == "RECOVERED_ATTEMPT"]
        if state["status"] != "INTERRUPTED":
            candidates, issues = _candidates(workflow.home)
            for call in calls[len(records):]:
                record = {"reconciliation_id": reconciliation_id,
                    **_inspect(workflow, plan, call, results.get(call["attempt_id"]), candidates, issues)}
                workflow.store.append(plan_id, "RECOVERED_ATTEMPT", record)
                records.append(record)
            workflow.store.append(plan_id, "RECONCILIATION_FINISHED", _summary(plan, calls, results, records, reconciliation_id))
        _observe(workflow, plan, records, events, reconciliation_id)
        return workflow.status(plan_id)


def validate_reconciliation(plan: dict[str, Any], original: list[dict[str, Any]],
                            events: list[dict[str, Any]]) -> None:
    """Validate recovery semantics in addition to the store's hash-chain checks."""
    calls = [e["payload"] for e in original if e["kind"] == "TOOL_CALL"]
    results = {e["payload"]["attempt_id"]: e["payload"] for e in original if e["kind"] == "TOOL_RESULT"}
    start = events[0]["payload"]
    reconciliation_id = start["reconciliation_id"]
    if len(reconciliation_id) != 32 or any(c not in "0123456789abcdef" for c in reconciliation_id):
        raise ValueError("invalid reconciliation identity")
    if not original or any(e["kind"] == "RUN_FINISHED" for e in original) or start.get("original_event_count") != len(original) or start.get("original_head_hash") != original[-1]["content_hash"] or start.get("dispatch_disabled") is not True:
        raise ValueError("reconciliation fence differs from original audit")
    records: list[dict[str, Any]] = []
    observations: set[tuple[str, str]] = set()
    finished = False
    for event in events[1:]:
        kind, payload = event["kind"], event["payload"]
        if kind not in {"RECOVERED_ATTEMPT", "RECONCILIATION_FINISHED", "RECONCILIATION_RESPONSE_OBSERVED"}:
            raise ValueError("research dispatch or reclassification after reconciliation fence")
        if payload.get("reconciliation_id") != reconciliation_id:
            raise ValueError("reconciliation event identity mismatch")
        if kind == "RECOVERED_ATTEMPT" and not finished:
            if len(records) >= len(calls):
                raise ValueError("reconciliation reviewed an undispatched trial")
            call = calls[len(records)]
            exit_status = "NOT_REEVALUATED" if call["attempt_id"] in results else "NOT_OBSERVED"
            if payload.get("attempt_id") != call["attempt_id"] or payload.get("ordinal") != call["ordinal"] or payload.get("classification") not in _CLASSIFICATIONS or payload.get("exit_status") != exit_status or payload.get("recorded_outcome") != results.get(call["attempt_id"]):
                raise ValueError("reconciliation attempt or historical outcome mismatch")
            if (payload["classification"] == "RECORDED_OUTCOME_PRESERVED") != (call["attempt_id"] in results):
                raise ValueError("reconciliation must preserve every recorded outcome")
            if payload["classification"] == "RECOVERED_COMPLETED_ARTIFACT":
                artifact = payload.get("artifact", {})
                fingerprints = [artifact.get(name, "") for name in ("experiment_sha256", "checksums_sha256", "config_sha256")]
                experiment_id = artifact.get("experiment_id", "")
                fingerprints.append(payload.get("request_sha256", ""))
                if payload.get("source_hash") != plan["source_hash"] or payload.get("dataset_hash") != plan["dataset_hash"] or payload.get("manifest_hash") != plan["manifest_hash"] or len(experiment_id) != 32 or any(c not in "0123456789abcdef" for c in experiment_id) or any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value) for value in fingerprints):
                    raise ValueError("recovered artifact lacks frozen identity evidence")
                if payload.get("artifact_qualification") != "CHECKSUMS_AND_FROZEN_IDENTITY_VERIFIED_NOT_PROCESS_EXIT_PROOF" or payload.get("candidate_issues") != [] or payload.get("candidate_ids") != [experiment_id]:
                    raise ValueError("recovered artifact qualification contradicts its candidate evidence")
            _validate_snapshot(payload["response_snapshot"])
            if payload.get("response_snapshot_hash") != digest(canonical(payload["response_snapshot"])):
                raise ValueError("reconciliation response snapshot hash mismatch")
            observations.add((call["attempt_id"], payload["response_snapshot_hash"]))
            records.append(payload)
        elif kind == "RECONCILIATION_FINISHED" and not finished:
            if len(records) != len(calls) or payload != _summary(plan, calls, results, records, reconciliation_id):
                raise ValueError("reconciliation completion counters or classifications mismatch")
            finished = True
        elif kind == "RECONCILIATION_RESPONSE_OBSERVED" and finished:
            _validate_snapshot(payload["response_snapshot"])
            pair = (payload.get("attempt_id"), payload.get("response_snapshot_hash"))
            if not any(r["attempt_id"] == pair[0] and r["ordinal"] == payload.get("ordinal") for r in records) or pair in observations or payload.get("classification_effect") != "NONE" or payload.get("response_snapshot_hash") != digest(canonical(payload["response_snapshot"])):
                raise ValueError("late response observation duplicates or changes recovery classification")
            observations.add(pair)
        else:
            raise ValueError("research dispatch or reclassification after reconciliation fence")
