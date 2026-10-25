"""Bounded experiment execution with complete local artifact fingerprints."""

import csv
import hashlib
import json
import platform
import re
import subprocess
import threading
import time
from datetime import date
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field, model_validator

from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.common.locking import exclusive_lease
from alphamosaic.core.contracts import Contract, utc_now
from alphamosaic.data.datasets import DatasetStore
from alphamosaic.evaluation.analytics import analyze
from alphamosaic.evaluation.scientific import HoldoutAudit
from alphamosaic.evaluation.trades import analyze_trades
from alphamosaic.evaluation.weekly import analyze_weekly


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class ResearchExecutionContext(Contract):
    plan_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    attempt_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    ordinal: int = Field(ge=0, le=5)


class ExperimentConfig(Contract):
    dataset_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    strategy: str = Field(default="trend", max_length=50)
    symbols: list[str] = Field(default_factory=lambda: ["SPY"], min_length=1, max_length=10)
    benchmark: str = Field(default="SPY", pattern=r"^[A-Z][A-Z0-9.-]{0,14}$")
    question: str = Field(default="Does this fixed rule survive costs?", min_length=10, max_length=1000)
    replay: ReplayConfig = Field(default_factory=ReplayConfig)
    start: date | None = None
    end: date | None = None
    validation: Literal["EXPLORATORY", "PREDECLARED_HOLDOUT"] = "EXPLORATORY"
    research_context: ResearchExecutionContext | None = None

    @model_validator(mode="after")
    def dates(self) -> "ExperimentConfig":
        if self.start and self.end and self.start >= self.end:
            raise ValueError("start must precede end")
        if self.validation == "PREDECLARED_HOLDOUT" and self.start is None:
            raise ValueError("holdout requires explicit evaluation start")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("duplicate symbols")
        if self.strategy.startswith("weekly_") and self.replay.decision_frequency != "WEEKLY":
            raise ValueError("weekly strategies require explicit WEEKLY decisions and weekly parameters")
        return self


def subset(data: ReplayDataset, symbols: list[str]) -> ReplayDataset:
    if set(symbols) - set(data.bars):
        raise ValueError("symbols absent from versioned dataset")
    return data.model_copy(update={
        "bars": {s: data.bars[s] for s in symbols},
        "identities": {s: data.identities[s] for s in symbols},
        "actions": [a for a in data.actions if a.symbol in symbols],
        "signals": [s for s in data.signals if s.symbol in symbols],
    })


def source_manifest() -> dict[str, Any]:
    source = Path(__file__).resolve().parents[1]
    hashes = {p.relative_to(source).as_posix(): digest(p.read_bytes()) for p in sorted(source.rglob("*.py"))}
    return {"source_hash": digest(canonical(hashes)), "source_files": hashes}


def code_manifest() -> dict[str, Any]:
    source = Path(__file__).resolve().parents[1]
    project = source.parents[1]
    lock = project / "uv.lock"
    checkout = source.parent.name == "src" and (project / "pyproject.toml").is_file()
    sha, dirty = "NOT_AVAILABLE", None
    if checkout:
        try:
            root = subprocess.check_output(["git", "-C", str(project), "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
            if Path(root).resolve() != project.resolve():
                raise ValueError("source checkout is nested inside a different Git repository")
            sha = subprocess.check_output(["git", "-C", str(project), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
            dirty = bool(subprocess.check_output(["git", "-C", str(project), "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL, timeout=5).strip())
        except (OSError, subprocess.SubprocessError, ValueError):
            sha, dirty = "NOT_AVAILABLE", None
    installed = {}
    for distribution in distributions():
        metadata = distribution.metadata
        if metadata["Name"]:
            installed[metadata["Name"]] = metadata["Version"]
    return {"git_sha": sha, "git_dirty": dirty, "python": platform.python_version(),
            "source_kind": "SRC_CHECKOUT" if checkout else "INSTALLED_PACKAGE",
            "lock_hash": digest(lock.read_bytes()) if checkout and lock.exists() else None,
            **source_manifest(), "installed_dependencies": installed}


class ExperimentStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, experiment_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", experiment_id):
            raise ValueError("invalid experiment ID")
        path = self.root / experiment_id
        if path.is_symlink() or path.resolve().parent != self.root:
            raise ValueError("experiment path escapes store")
        return path

    def load(self, experiment_id: str) -> dict[str, Any]:
        path = self.path(experiment_id)
        payload = json.loads((path / "experiment.json").read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("experiment_id") != experiment_id:
            raise ValueError("experiment identity mismatch")
        if payload.get("status") == "RUNNING" and not (path / "checksums.json").exists():
            return {**payload, "integrity": "INCOMPLETE_INTERRUPTED_OR_ACTIVE"}
        manifest = json.loads((path / "checksums.json").read_text(encoding="utf-8"))
        required = {"experiment.json", "config.json"}
        if payload.get("status") == "COMPLETED":
            required |= {"report.md", "report.html", "equity.csv", "fills.csv", "orders.csv", "cash_ledger.csv", "events.csv", "signals.csv", "unfilled_orders.csv", "order_adjustments.csv"}
            if payload.get("artifact_schema_version", 1) >= 2:
                required |= {"closed_lots.csv", "open_lots.csv", "asset_attribution.csv", "weekly_equity.csv"}
        if not isinstance(manifest, dict) or not required <= manifest.keys():
            raise ValueError("incomplete experiment artifact manifest")
        for name, expected in manifest.items():
            artifact = path / name
            if Path(name).name != name or artifact.is_symlink() or artifact.resolve().parent != path or digest(artifact.read_bytes()) != expected:
                raise ValueError("experiment artifact integrity failure")
        return payload

    def list(self) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self.root.glob("*/experiment.json"), reverse=True):
            try:
                item = self.load(path.parent.name)
                rows.append({"experiment_id": item["experiment_id"], "created_at": item["created_at"],
                             "status": item["status"], "strategy": item["config"]["strategy"],
                             "dataset_id": item["config"]["dataset_id"], "acceptance": item.get("acceptance"),
                             "validation": item["config"]["validation"], "error": item.get("error")})
                rows[-1]["research_context"] = item["config"].get("research_context")
            except (ValueError, OSError, KeyError):
                rows.append({"experiment_id": path.parent.name, "status": "CORRUPT"})
        return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows([{k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()} for row in rows])


class ExperimentRunner:
    def __init__(self, home: Path):
        self.datasets = DatasetStore(home / "datasets")
        self.store = ExperimentStore(home / "experiments")
        self._slot = threading.BoundedSemaphore(1)

    def run(self, config: ExperimentConfig) -> dict[str, Any]:
        config = ExperimentConfig.model_validate(config.model_dump())
        if not self._slot.acquire(blocking=False):
            raise ValueError("research quota: one active experiment per service")
        try:
            with exclusive_lease(self.store.root.parent / "research_execution.lease"):
                return self._run(config)
        finally:
            self._slot.release()

    def _run(self, config: ExperimentConfig) -> dict[str, Any]:
        experiment_id = uuid4().hex
        path = self.store.path(experiment_id)
        path.mkdir()
        started = time.perf_counter()
        payload: dict[str, Any] = {"experiment_id": experiment_id, "created_at": utc_now().isoformat(),
            "artifact_schema_version": 2,
            "config": config.model_dump(mode="json"),
            "status": "RUNNING", "broker_enabled": False, "evidence_grade": "Exploratory", "validated_alpha": False}
        # An interrupted process leaves a visible RUNNING record; it never appears successful.
        (path / "experiment.json").write_bytes(canonical(payload))
        try:
            (path / "config.json").write_bytes(canonical(payload["config"]))
            payload["reproducibility"] = code_manifest()
            data = self.datasets.load(config.dataset_id)
            dataset_manifest = self.datasets.manifest(config.dataset_id)
            if max(map(len, data.bars.values())) > 2500 or len(data.bars) > 20:
                raise ValueError("bounded research: <=2500 sessions and <=20 dataset assets")
            selected = subset(data, config.symbols)
            registry = StrategyRegistry()
            result = PaperReplayEngine().run(selected, registry.get(config.strategy), config.strategy,
                                            config.replay, config.start, config.end)
            benchmark_data = subset(data, [config.benchmark])
            benchmark = PaperReplayEngine().run(benchmark_data, registry.get("buy_and_hold"), "buy_and_hold",
                                               config.replay, config.start, config.end)
            policies = {b.adjustment_policy for bars in data.bars.values() for b in bars}
            basis = "RAW_WITH_CASH_ACTIONS" if policies == {"RAW"} else "TOTAL_RETURN" if policies == {"TOTAL_RETURN"} else "PRICE" if policies == {"SPLIT"} else None
            analysis = analyze(result, benchmark, return_basis=basis, benchmark_return_basis=basis)
            trades = analyze_trades(result, selected)
            if trades["status"] != "VERIFIED":
                payload["rejected_result"] = result.model_dump(mode="json")
                payload["trade_analysis"] = trades
                raise ValueError("execution evidence failed independent lot/accounting reconciliation: " + trades["reason"])
            analysis["trade_analysis"] = trades
            analysis["metrics"].update(trades["metrics"])
            analysis["attribution"]["asset_pnl"] = trades["asset_attribution"]
            analysis["warnings"] = [w for w in analysis["warnings"] if not w.startswith("Trade statistics requiring matched closed lots are unavailable")]
            analysis["warnings"].extend(trades["warnings"])
            analysis["weekly"] = analyze_weekly(result, benchmark_result=benchmark, return_basis=basis, benchmark_return_basis=basis)
            if source_manifest()["source_hash"] != payload["reproducibility"]["source_hash"]:
                raise ValueError("SOURCE_CHANGED_DURING_RUN: freeze code and restart service")
            payload.update(status="COMPLETED", acceptance=result.acceptance,
                dataset_hash=dataset_manifest["dataset_hash"], dataset_manifest=dataset_manifest,
                return_basis=basis, result=result.model_dump(mode="json"),
                benchmark_result=benchmark.model_dump(mode="json"), analysis=analysis,
                warnings=list(dict.fromkeys([*result.diagnostics, *analysis.get("warnings", []),
                    "No demonstrated alpha; fixed historical rules are research diagnostics",
                    "Daily bars cannot establish executable opening-auction liquidity",
                    "Holdout labels describe declared dates, not independent prospective validation"])))
            payload["warnings"].append("Source files must be frozen and the service restarted before acceptance; a disk hash cannot certify stale in-memory modules")
            if config.validation == "PREDECLARED_HOLDOUT":
                payload["holdout_audit"] = HoldoutAudit(self.store.root.parent / "holdouts").record(
                    dataset_manifest["dataset_hash"], [p.session.isoformat() for p in result.equity],
                    experiment_id=experiment_id, purpose="DECLARED_FIXED_RULE_EVALUATION", informs_tuning=False)
            from alphamosaic.agents.research import critique
            payload["review"] = critique(payload)
            for name in ("equity", "fills", "orders", "cash_ledger", "events", "signals", "unfilled_orders", "order_adjustments"):
                _csv(path / f"{name}.csv", payload["result"].get(name, []))
            for name, rows in (("closed_lots", trades["closed_lots"]), ("open_lots", trades["open_lots"]), ("asset_attribution", trades["asset_attribution"]), ("weekly_equity", analysis["weekly"]["weekly_equity"]["points"])):
                _csv(path / f"{name}.csv", rows)
            from alphamosaic.reporting.research import write_report
            write_report(path, payload)
        except Exception as exc:
            payload.update(status="FAILED", error={"type": type(exc).__name__, "message": str(exc)[:2000]})
        payload["elapsed_seconds"] = time.perf_counter() - started
        (path / "experiment.json").write_bytes(canonical(payload))
        hashes = {p.name: digest(p.read_bytes()) for p in path.iterdir() if p.is_file()}
        (path / "checksums.json").write_bytes(canonical(hashes))
        return payload


def compare_experiments(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        raise ValueError("at least one experiment required")
    def signature(item: dict[str, Any]) -> tuple[Any, ...]:
        c = item["config"]
        dates = [p["session"] for p in item.get("result", {}).get("equity", [])]
        return item.get("dataset_hash"), item.get("return_basis"), item.get("acceptance"), item.get("reproducibility", {}).get("source_hash"), c["validation"], c["benchmark"], tuple(dates)
    comparable = all(i["status"] == "COMPLETED" and i.get("return_basis") is not None and i.get("dataset_hash") and i.get("reproducibility", {}).get("source_hash") for i in items) and len({signature(i) for i in items}) == 1
    return {"status": "COMPARABLE" if comparable else "INCOMPATIBLE",
            "warnings": [] if comparable else ["Dataset, code, evidence, dates, basis, validation or benchmark missing/differ; no pooled ranking"],
            "experiments": [{"experiment_id": i["experiment_id"], "strategy": i["config"]["strategy"],
                             "cost_model": i["config"]["replay"], "metrics": i.get("analysis", {}).get("metrics", {})} for i in items]}
