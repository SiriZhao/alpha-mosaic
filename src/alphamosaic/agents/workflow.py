"""Frozen research plans with typed, quota-bounded local simulation tools."""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import Field, model_validator

from alphamosaic.backtesting.models import WeeklyStrategyParameters, preset_config
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.common.locking import exclusive_lease
from alphamosaic.common.paths import contained_child, unredirected
from alphamosaic.core.benchmark_contracts import BenchmarkSpecV1
from alphamosaic.core.contracts import Contract, utc_now
from alphamosaic.data.datasets import DatasetStore
from alphamosaic.experiments.runner import ExperimentConfig, canonical, digest, source_manifest

_ID = re.compile(r"^[a-f0-9]{32}$")


class ResearchPlanRequest(Contract):
    dataset_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    question: str = Field(min_length=10, max_length=1000)
    symbols: list[str] = Field(default_factory=lambda: ["SPY"], min_length=1, max_length=10)
    benchmark: str = Field(default="SPY", pattern=r"^[A-Z][A-Z0-9.-]{0,14}$")
    benchmark_spec: BenchmarkSpecV1 | None = Field(default=None, exclude_if=lambda value: value is None)
    strategies: list[str] = Field(default_factory=lambda: ["buy_and_hold", "trend"], min_length=1, max_length=3)
    cost_scenarios: list[Literal["realistic", "stress", "zero"]] = Field(default_factory=lambda: ["realistic", "stress"], min_length=1, max_length=3)
    start: date | None = None
    end: date | None = None
    max_trials: int = Field(default=6, ge=1, le=6)
    per_experiment_seconds: float = Field(default=60, gt=0, le=600)
    total_seconds: float = Field(default=300, gt=0, le=1800)
    weekly_parameters: WeeklyStrategyParameters = Field(default_factory=WeeklyStrategyParameters)

    @model_validator(mode="after")
    def bounded(self) -> ResearchPlanRequest:
        if len(set(self.strategies)) != len(self.strategies) or len(set(self.cost_scenarios)) != len(self.cost_scenarios):
            raise ValueError("duplicate trials are not permitted")
        if len(self.strategies) * len(self.cost_scenarios) > self.max_trials:
            raise ValueError("plan exceeds its declared trial budget")
        if "realistic" not in self.cost_scenarios:
            raise ValueError("a realistic-cost primary case is required")
        for name in self.strategies:
            StrategyRegistry().get(name)
        if self.benchmark_spec is not None and self.benchmark != "SPY":
            raise ValueError("benchmark_spec conflicts with an explicit legacy benchmark ticker")
        return self


class ExplanationAdapter(Protocol):
    """A trusted optional text adapter has no tool or numeric-result authority."""

    def explain(self, evidence: dict[str, Any]) -> str: ...


class ResearchPlanStore:
    """Immutable plan rows and append-only execution events in a local SQLite store."""

    def __init__(self, root: Path):
        self.root = unredirected(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = contained_child(self.root, "plans.sqlite")
        with self.connection() as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(events)")}
            if columns and not {"previous_hash", "content_hash"} <= columns:
                raise ValueError("legacy research audit schema is unverified; original database preserved for explicit review")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS plans(
                    plan_id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                    payload TEXT NOT NULL, content_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    event_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL,
                    plan_id TEXT NOT NULL REFERENCES plans(plan_id), at TEXT NOT NULL,
                    kind TEXT NOT NULL, payload TEXT NOT NULL,
                    previous_hash TEXT NOT NULL, content_hash TEXT NOT NULL,
                    UNIQUE(plan_id, sequence));
            """)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        contained_child(self.root, "plans.sqlite")
        db = sqlite3.connect(self.database, timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def validate_id(plan_id: str) -> None:
        if not _ID.fullmatch(plan_id):
            raise ValueError("invalid research plan ID")

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_id(payload["plan_id"])
        encoded = canonical(payload)
        with self.connection() as db:
            db.execute("INSERT INTO plans VALUES(?,?,?,?)", (payload["plan_id"], payload["created_at"], encoded.decode(), digest(encoded)))
        return self.load(payload["plan_id"])

    def load(self, plan_id: str) -> dict[str, Any]:
        self.validate_id(plan_id)
        with self.connection() as db:
            row = db.execute("SELECT payload,content_hash FROM plans WHERE plan_id=?", (plan_id,)).fetchone()
        if row is None:
            raise ValueError("unknown research plan")
        if digest(row[0].encode()) != row[1]:
            raise ValueError("research plan integrity mismatch")
        plan = json.loads(row[0])
        if plan.get("plan_id") != plan_id:
            raise ValueError("research plan identity mismatch")
        return plan

    def append(self, plan_id: str, kind: str, payload: dict[str, Any]) -> None:
        self.load(plan_id)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT sequence,content_hash FROM events WHERE plan_id=? ORDER BY sequence DESC LIMIT 1", (plan_id,)).fetchone()
            sequence, previous_hash = (previous[0] + 1, previous[1]) if previous else (1, "0" * 64)
            event = {"event_id": uuid4().hex, "sequence": sequence, "plan_id": plan_id, "at": utc_now().isoformat(), "kind": kind, "payload": payload}
            db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?)", (event["event_id"], sequence, plan_id, event["at"], kind, canonical(payload).decode(), previous_hash, digest(canonical({**event, "previous_hash": previous_hash}))))

    def events(self, plan_id: str) -> list[dict[str, Any]]:
        self.load(plan_id)
        with self.connection() as db:
            rows = db.execute("SELECT event_id,sequence,at,kind,payload,previous_hash,content_hash FROM events WHERE plan_id=? ORDER BY sequence", (plan_id,)).fetchall()
        events = []
        previous_hash = "0" * 64
        for sequence, row in enumerate(rows, 1):
            event = {"event_id": row[0], "sequence": row[1], "plan_id": plan_id, "at": row[2], "kind": row[3], "payload": json.loads(row[4]), "previous_hash": row[5]}
            if row[1] != sequence or row[5] != previous_hash or digest(canonical(event)) != row[6]:
                raise ValueError("research audit event sequence or hash mismatch")
            previous_hash = row[6]
            events.append({**event, "content_hash": row[6]})
        return events

    def list(self) -> list[dict[str, Any]]:
        with self.connection() as db:
            rows = db.execute("SELECT plan_id,created_at FROM plans ORDER BY created_at DESC LIMIT 100").fetchall()
        return [{"plan_id": r[0], "created_at": r[1]} for r in rows]


class ResearchWorkflow:
    """Planner, data reviewer, runner, critic and report orchestration without live trading."""

    def __init__(self, home: Path):
        self.home = home.resolve()
        self.store = ResearchPlanStore(self.home / "research_plans")
        self.datasets = DatasetStore(self.home / "datasets")

    def create(self, request: ResearchPlanRequest) -> dict[str, Any]:
        request = ResearchPlanRequest.model_validate(request.model_dump())
        manifest = self.datasets.manifest(request.dataset_id)
        data = self.datasets.load(request.dataset_id)
        benchmark_symbols = list(request.benchmark_spec.symbols) if request.benchmark_spec is not None and request.benchmark_spec.kind == "EQUAL_WEIGHT" else [request.benchmark]
        if set([*request.symbols, *benchmark_symbols]) - data.bars.keys():
            raise ValueError("plan assets/benchmark must belong to the frozen dataset")
        if max(map(len, data.bars.values())) > 2500 or len(data.bars) > 20:
            raise ValueError("research data exceeds the bounded local simulation budget")
        trials = []
        for strategy in request.strategies:
            for scenario in request.cost_scenarios:
                config = ExperimentConfig(dataset_id=request.dataset_id, strategy=strategy,
                    symbols=request.symbols, benchmark=request.benchmark, question=request.question,
                    benchmark_spec=request.benchmark_spec,
                    replay=preset_config(scenario).model_copy(update={"decision_frequency": "WEEKLY" if strategy.startswith("weekly_") else "DAILY", "weekly_parameters": request.weekly_parameters}), start=request.start, end=request.end)
                trials.append({"ordinal": len(trials), "cost_scenario": scenario, "config": config.model_dump(mode="json")})
        plan = {"plan_id": uuid4().hex, "created_at": utc_now().isoformat(),
            "request": request.model_dump(mode="json"), "dataset_hash": manifest["dataset_hash"],
            "manifest_hash": manifest["manifest_hash"], "source_hash": source_manifest()["source_hash"],
            "hypothesis": request.question, "trials": trials,
            "data_review": {"state": manifest["state"], "quality": manifest["data_quality"], "flags": manifest["quality_report"]["flags"], "basis": manifest["adjustment_method"]},
            "counterarguments": ["Synthetic data establishes software behavior only", "Historical repeated trials do not establish alpha", "Daily liquidity and corporate-action assumptions limit execution realism"],
            "planner": "DETERMINISTIC_PREDECLARED_GRID", "frozen": True,
            "evidence_grade": "Exploratory", "automatic_promotion": False, "broker_enabled": False}
        return self.store.save(plan)

    def status(self, plan_id: str) -> dict[str, Any]:
        plan = self.store.load(plan_id)
        events = self.store.events(plan_id)
        self._validate_audit(plan, events)
        finished = [e for e in events if e["kind"] == "RUN_FINISHED"]
        reconciled = any(e["kind"] == "RECONCILIATION_FINISHED" for e in events)
        reconciling = any(e["kind"] == "RECONCILIATION_STARTED" for e in events)
        state = "INTERRUPTED" if reconciled else "RECONCILIATION_IN_PROGRESS" if reconciling else finished[-1]["payload"]["status"] if finished else "INCOMPLETE_OR_RUNNING" if events else "FROZEN"
        return {"plan": plan, "status": state, "events": events,
                "process_liveness": "NOT_INFERRED_FROM_PERSISTED_STATE", "broker_enabled": False}

    def run(self, plan_id: str) -> dict[str, Any]:
        self.store.validate_id(plan_id)
        with exclusive_lease(self.store.root / (plan_id + ".lease")):
            current = self.status(plan_id)
            if current["events"]:
                # No silent rerun after failure/interruption and no holdout-guided plan mutation.
                return current
            plan = current["plan"]
            request = ResearchPlanRequest.model_validate(plan["request"])
            if source_manifest()["source_hash"] != plan["source_hash"]:
                raise ValueError("frozen plan source changed; create and review a new plan")
            if self.datasets.manifest(request.dataset_id)["manifest_hash"] != plan["manifest_hash"]:
                raise ValueError("frozen plan dataset provenance changed")
            directory = contained_child(self.store.root, plan_id)
            directory.mkdir(exist_ok=True)
            contained_child(self.store.root, plan_id)
            deadline = time.monotonic() + request.total_seconds
            self.store.append(plan_id, "RUN_STARTED", {"max_trials": request.max_trials, "total_seconds": request.total_seconds})
            outcomes = []
            for trial in plan["trials"]:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.store.append(plan_id, "BUDGET_EXHAUSTED", {"unattempted_ordinals": [t["ordinal"] for t in plan["trials"][len(outcomes):]]})
                    break
                if source_manifest()["source_hash"] != plan["source_hash"]:
                    self.store.append(plan_id, "SOURCE_CHANGED", {})
                    break
                timeout = min(request.per_experiment_seconds, remaining)
                attempt_id = uuid4().hex
                request_path = contained_child(directory, attempt_id + "-request.json")
                response_path = contained_child(directory, attempt_id + "-response.json")
                config = {**trial["config"], "research_context": {"plan_id": plan_id, "attempt_id": attempt_id, "ordinal": trial["ordinal"]}}
                with request_path.open("xb") as stream:
                    stream.write(canonical({"config": config, "expected_source_hash": plan["source_hash"], "dataset_hash": plan["dataset_hash"], "response": response_path.name}))
                self.store.append(plan_id, "TOOL_CALL", {"tool": "RUN_LOCAL_EXPERIMENT", "ordinal": trial["ordinal"], "attempt_id": attempt_id, "config_hash": digest(canonical(trial["config"])), "timeout_seconds": timeout})
                try:
                    effective_timeout = min(timeout, deadline - time.monotonic())
                    outcome = self._worker(request_path, response_path, effective_timeout) if effective_timeout > 0 else {"status": "TIMED_OUT", "phase": "BUDGET_EXHAUSTED_BEFORE_WORKER"}
                except (ValueError, OSError, KeyError) as exc:
                    outcome = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)[:1000]}
                outcomes.append(outcome)
                self.store.append(plan_id, "TOOL_RESULT", {"ordinal": trial["ordinal"], "attempt_id": attempt_id, **outcome})
            passed = sum(o["status"] == "COMPLETED" for o in outcomes)
            state = "COMPLETED" if passed == len(plan["trials"]) else "PARTIAL" if passed else "FAILED"
            self.store.append(plan_id, "RUN_FINISHED", {"status": state, "attempted": len(outcomes), "declared": len(plan["trials"]), "completed": passed, "selection": "ALL_OUTCOMES_RETAINED", "automatic_promotion": False})
            return self.status(plan_id)

    def authorize_dispatch(self, config: ExperimentConfig) -> None:
        """Validate one pending frozen call while the caller holds the global lease."""
        from alphamosaic.experiments.runner import ExperimentStore
        context = config.research_context
        if context is None:
            raise ValueError("planned dispatch requires a research context")
        state = self.status(context.plan_id)
        plan, events = state["plan"], state["events"]
        if state["status"] != "INCOMPLETE_OR_RUNNING":
            raise ValueError("research plan is not open for dispatch")
        calls = [e["payload"] for e in events if e["kind"] == "TOOL_CALL" and e["payload"]["attempt_id"] == context.attempt_id]
        if len(calls) != 1 or calls[0]["ordinal"] != context.ordinal:
            raise ValueError("research attempt has no unique frozen authorization")
        if any(e["kind"] == "TOOL_RESULT" and e["payload"]["attempt_id"] == context.attempt_id for e in events):
            raise ValueError("research attempt already has a recorded outcome")
        expected = {**plan["trials"][context.ordinal]["config"], "research_context": context.model_dump(mode="json")}
        if config.model_dump(mode="json") != expected:
            raise ValueError("research dispatch differs from the frozen configuration")
        if source_manifest()["source_hash"] != plan["source_hash"]:
            raise ValueError("frozen dispatch source changed")
        if self.datasets.manifest(config.dataset_id)["manifest_hash"] != plan["manifest_hash"]:
            raise ValueError("frozen dispatch dataset provenance changed")
        directory = contained_child(self.store.root, context.plan_id)
        path = contained_child(directory, context.attempt_id + "-request.json")
        response = contained_child(directory, context.attempt_id + "-response.json")
        request = {"config": expected, "expected_source_hash": plan["source_hash"],
            "dataset_hash": plan["dataset_hash"], "response": response.name}
        if path.read_bytes() != canonical(request):
            raise ValueError("research dispatch request differs from its canonical authorization")
        if response.exists():
            raise ValueError("research attempt already has an immutable response")
        experiments = ExperimentStore(unredirected(self.home / "experiments"))
        # Globbed metadata listings omit empty/interrupted directories. An
        # unidentified artifact is uncertainty, never proof of no earlier run.
        for child in unredirected(experiments.root).iterdir():
            child = unredirected(child)
            if not child.is_dir():
                raise ValueError("unidentified experiment artifact prevents safe planned dispatch")
            item = experiments.load(child.name)
            if item.get("integrity") == "INCOMPLETE_INTERRUPTED_OR_ACTIVE":
                raise ValueError("unsealed experiment prevents safe planned dispatch")
            if (item["config"].get("research_context") or {}).get("attempt_id") == context.attempt_id:
                raise ValueError("research attempt already has an experiment; explicit reconciliation required")

    def reconcile(self, plan_id: str) -> dict[str, Any]:
        from alphamosaic.agents.reconciliation import reconcile
        return reconcile(self, plan_id)

    @staticmethod
    def _validate_audit(plan: dict[str, Any], events: list[dict[str, Any]]) -> None:
        fences = [i for i, event in enumerate(events) if event["kind"] == "RECONCILIATION_STARTED"]
        if fences:
            from alphamosaic.agents.reconciliation import validate_reconciliation
            first = fences[0]
            ResearchWorkflow._validate_audit(plan, events[:first])
            validate_reconciliation(plan, events[:first], events[first:])
            return
        calls: dict[str, int] = {}
        results: dict[str, str] = {}
        started = finished = False
        for event in events:
            kind, payload = event["kind"], event["payload"]
            if finished:
                raise ValueError("research audit contains events after completion")
            if kind == "RUN_STARTED":
                if started:
                    raise ValueError("duplicate research run start")
                started = True
            elif not started:
                raise ValueError("research audit must begin with a run start")
            elif kind == "TOOL_CALL":
                attempt, ordinal = payload["attempt_id"], payload["ordinal"]
                if not _ID.fullmatch(attempt) or attempt in calls or ordinal != len(calls) or ordinal >= len(plan["trials"]):
                    raise ValueError("research audit tool identity or trial quota mismatch")
                if payload.get("tool") != "RUN_LOCAL_EXPERIMENT" or payload["config_hash"] != digest(canonical(plan["trials"][ordinal]["config"])):
                    raise ValueError("research audit tool or frozen configuration mismatch")
                calls[attempt] = ordinal
            elif kind == "TOOL_RESULT":
                attempt = payload["attempt_id"]
                if attempt not in calls or attempt in results or payload["ordinal"] != calls[attempt]:
                    raise ValueError("research audit result has no unique matching call")
                if payload.get("status") not in {"COMPLETED", "FAILED", "BUSY", "TIMED_OUT"}:
                    raise ValueError("unknown research tool outcome")
                results[attempt] = payload["status"]
            elif kind == "RUN_FINISHED":
                if len(results) != len(calls):
                    raise ValueError("research audit finalized with unmatched calls")
                completed = sum(value == "COMPLETED" for value in results.values())
                declared = len(plan["trials"])
                status = "COMPLETED" if completed == declared else "PARTIAL" if completed else "FAILED"
                if payload.get("attempted") != len(calls) or payload.get("declared") != declared or payload.get("completed") != completed or payload.get("status") != status:
                    raise ValueError("research audit completion counters or status mismatch")
                finished = True
            elif kind not in {"BUDGET_EXHAUSTED", "SOURCE_CHANGED"}:
                raise ValueError("unknown research audit event")

    def _worker(self, request: Path, response: Path, timeout: float) -> dict[str, Any]:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("finite positive worker timeout required")
        # The command and code entrypoint are fixed. No agent-supplied command or path is accepted.
        command = [sys.executable, "-m", "alphamosaic.agents.worker", "--home", str(self.home), "--request", str(request)]
        environment = {k: v for k, v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT", "TEMP", "TMP", "LANG", "LC_ALL", "PYTHONUTF8"}}
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
        try:
            process = subprocess.run(command, cwd=Path(__file__).resolve().parents[2], env=environment, timeout=timeout,
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0, check=False)
        except subprocess.TimeoutExpired:
            config = json.loads(request.read_bytes())["config"]
            from alphamosaic.experiments.runner import ExperimentStore
            matches = [row for row in ExperimentStore(self.home / "experiments").list()
                       if (row.get("research_context") or {}).get("attempt_id") == config["research_context"]["attempt_id"]]
            return {"status": "TIMED_OUT", "experiment_id": matches[0]["experiment_id"] if len(matches) == 1 else None,
                    "experiment_status": matches[0]["status"] if len(matches) == 1 else "NO_UNIQUE_EXPERIMENT_RECORD", "deadline_seconds": timeout}
        except OSError as exc:
            return {"status": "FAILED", "error_type": type(exc).__name__}
        if not response.is_file() or response.is_symlink():
            return {"status": "FAILED", "error_type": "WORKER_RESPONSE_MISSING", "exit_code": process.returncode}
        payload = json.loads(response.read_bytes())
        if payload.get("status") not in {"COMPLETED", "FAILED", "BUSY"}:
            raise ValueError("invalid worker response")
        if payload["status"] == "COMPLETED":
            if process.returncode != 0:
                raise ValueError("worker exited abnormally after writing a completed response")
            from alphamosaic.experiments.runner import ExperimentStore
            item = ExperimentStore(self.home / "experiments").load(payload["experiment_id"])
            expected = json.loads(request.read_bytes())
            if item["status"] != "COMPLETED" or item["config"] != expected["config"] or item["dataset_hash"] != expected["dataset_hash"] or item["reproducibility"]["source_hash"] != expected["expected_source_hash"]:
                raise ValueError("worker result differs from the frozen research request")
        return payload

    def report(self, plan_id: str, adapter: ExplanationAdapter | None = None) -> dict[str, Any]:
        from alphamosaic.experiments.runner import ExperimentStore, compare_experiments
        state = self.status(plan_id)
        results = [e["payload"] for e in state["events"] if e["kind"] == "TOOL_RESULT"]
        store = ExperimentStore(self.home / "experiments")
        completed = [store.load(r["experiment_id"]) for r in results if r["status"] == "COMPLETED"]
        evidence = {"plan_id": plan_id, "status": state["status"], "hypothesis": state["plan"]["hypothesis"], "dataset_hash": state["plan"]["dataset_hash"],
                    "outcomes": results, "comparison": compare_experiments(completed) if completed else None,
                    "critics": [r["review"] for r in completed], "trials_attempted": len(results),
                    "selection": "ALL_OUTCOMES_RETAINED", "evidence_grade": "Exploratory", "automatic_promotion": False, "broker_enabled": False}
        evidence["reconciliation"] = [e for e in state["events"] if e["kind"].startswith("RECONCILIATION_") or e["kind"] == "RECOVERED_ATTEMPT"]
        evidence["trials_dispatched"] = sum(e["kind"] == "TOOL_CALL" for e in state["events"])
        if adapter is not None:
            text = adapter.explain(json.loads(canonical(evidence)))
            if not isinstance(text, str) or len(text) > 20000:
                raise ValueError("model explanation must be bounded text")
            if re.search(r"\d|[%$]", text):
                raise ValueError("model commentary cannot supply numerical claims; cite the computed evidence instead")
            if any(phrase in text.casefold() for phrase in ("guaranteed alpha", "stable excess returns", "low-risk high-return", "proven market-beating")):
                raise ValueError("unsupported investment promotion is not research commentary")
            evidence["optional_model_commentary"] = {"evidence_class": "MODEL_INFERENCE", "text": text, "numeric_authority": False}
        return evidence
