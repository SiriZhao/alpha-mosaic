"""Integration and failure evidence across service, store, report and terminal."""

import json
from pathlib import Path

import pytest

from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments import runner


@pytest.fixture
def service(tmp_path: Path) -> ApplicationService:
    return ApplicationService(tmp_path)


def configuration(service: ApplicationService) -> dict:
    manifest = service.research_demo(100)
    return {"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold", "symbols": ["SPY"], "benchmark": "SPY"}


def test_service_reproduces_accounting_and_exports_complete_reports(service: ApplicationService) -> None:
    config = configuration(service)
    first, second = service.research_experiment(config), service.research_experiment(config)
    assert first["status"] == second["status"] == "COMPLETED"
    assert first["result"] == second["result"]
    assert first["analysis"] == second["analysis"]
    assert first["dataset_hash"] == config["dataset_id"]
    assert first["experiment_id"] != second["experiment_id"]
    assert first["acceptance"] == "FIXTURE" and first["validated_alpha"] is False
    assert service.research_comparison([first["experiment_id"], second["experiment_id"]])["status"] == "COMPARABLE"
    path = service.experiment_runner().store.path(first["experiment_id"])
    report = (path / "report.html").read_text(encoding="utf-8")
    assert "FIXTURE" in report and "spread_cost" in report and "plotly" in report
    assert service.research_result(first["experiment_id"])["result"] == first["result"]


def test_failure_is_recorded_and_provenance_failure_is_a_failed_run(service: ApplicationService, monkeypatch: pytest.MonkeyPatch) -> None:
    failed = service.research_experiment({"dataset_id": "0" * 64})
    assert failed["status"] == "FAILED"
    assert service.research_result(failed["experiment_id"])["error"]["type"] == "FileNotFoundError"
    config = configuration(service)
    def broken_manifest() -> dict:
        raise OSError("source unavailable")
    monkeypatch.setattr(runner, "code_manifest", broken_manifest)
    failed = service.research_experiment(config)
    assert failed["status"] == "FAILED"
    assert service.research_result(failed["experiment_id"])["error"]["message"] == "source unavailable"


def test_store_rejects_missing_hashes_and_artifact_tampering(service: ApplicationService) -> None:
    item = service.research_experiment(configuration(service))
    store = service.experiment_runner().store
    path = store.path(item["experiment_id"])
    (path / "checksums.json").write_text("{}")
    with pytest.raises(ValueError, match="incomplete"):
        store.load(item["experiment_id"])
    assert store.list()[0]["status"] == "CORRUPT"


def test_interrupted_run_is_visible_and_never_complete(service: ApplicationService) -> None:
    store = service.experiment_runner().store
    key = "a" * 32
    path = store.path(key)
    path.mkdir()
    (path / "experiment.json").write_text(json.dumps({"experiment_id": key, "status": "RUNNING", "created_at": "2026-01-01T00:00:00Z", "config": {"strategy": "trend", "dataset_id": "b" * 64, "validation": "EXPLORATORY"}}))
    assert store.load(key)["integrity"] == "INCOMPLETE_INTERRUPTED_OR_ACTIVE"
    assert store.list()[0]["status"] == "RUNNING"
    with pytest.raises(ValueError):
        store.load("../escape")


def test_incompatible_dates_are_blocked_and_holdout_review_is_recorded(service: ApplicationService) -> None:
    config = configuration(service)
    first = service.research_experiment(config)
    data = service.experiment_runner().datasets.load(config["dataset_id"])
    start = data.bars["SPY"][75].session.isoformat()
    second = service.research_experiment({**config, "start": start, "validation": "PREDECLARED_HOLDOUT"})
    assert second["status"] == "COMPLETED"
    assert second["holdout_audit"]["uses"] == 1
    assert second["holdout_audit"]["independent_validation"] is False
    assert service.research_comparison([first["experiment_id"], second["experiment_id"]])["status"] == "INCOMPATIBLE"


def test_quota_and_config_revalidation(service: ApplicationService) -> None:
    config = runner.ExperimentConfig.model_validate(configuration(service))
    engine = service.experiment_runner()
    assert engine._slot.acquire(blocking=False)
    try:
        with pytest.raises(ValueError, match="quota"):
            engine.run(config)
    finally:
        engine._slot.release()
    with pytest.raises(ValueError):
        engine.run(config.model_copy(update={"dataset_id": "../escape"}))


def test_quantstats_zero_variance_is_missing_sharpe_without_runtime_warning() -> None:
    import warnings

    import pandas as pd

    from alphamosaic.evaluation.quantstats_adapter import QuantStatsAdapter
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        metrics = QuantStatsAdapter().metrics(pd.Series([0.0] * 30))
    assert metrics["sharpe"] is None and metrics["return"] == 0


def test_terminal_minimum_dataset_and_navigation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    ApplicationService(tmp_path).research_demo(80)
    path = Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"
    app = AppTest.from_file(str(path), default_timeout=30).run()
    assert not app.exception
    for page in ("Data Explorer", "Strategy Lab", "Backtest Results", "Experiment Comparison", "Risk Lab", "AI Research", "Reports"):
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page


def test_corrupt_dataset_remains_visible_without_blocking_healthy_listing(service: ApplicationService) -> None:
    good = service.research_demo(80)
    store = service.experiment_runner().datasets
    bad = store.root / ("0" * 64)
    bad.mkdir()
    (bad / "manifest.json").write_text("{}")
    rows = service.research_datasets()
    assert {row.get("state") for row in rows} == {"AVAILABLE", "CORRUPT"}
    assert store.load(good["dataset_id"]).bars
    with pytest.raises(ValueError):
        store.load("0" * 64)
