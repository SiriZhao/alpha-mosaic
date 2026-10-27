"""ApplicationService integration for typed benchmark references."""

from pathlib import Path

from alphamosaic.backtesting.benchmarks import cash_zero_interest, equal_weight
from alphamosaic.backtesting.models import ReplayConfig
from alphamosaic.core.service import ApplicationService
from alphamosaic.data.datasets import synthetic_demo


def _service_and_manifest(tmp_path: Path) -> tuple[ApplicationService, dict, tuple]:
    service = ApplicationService(tmp_path)
    data = synthetic_demo(80)
    manifest = service.experiment_runner().datasets.save(data)
    sessions = tuple(row.session for row in data.bars["SPY"])
    return service, manifest, sessions


def test_cash_reference_runs_without_forged_benchmark_result_and_reports_model_basis(tmp_path: Path) -> None:
    service, manifest, sessions = _service_and_manifest(tmp_path)
    spec = cash_zero_interest(sessions, initial_cash=100_000)
    item = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold",
        "symbols": ["SPY"], "benchmark_spec": spec.model_dump(mode="json")})
    assert item["status"] == "COMPLETED", item.get("error")
    assert item["benchmark_result"] is None
    assert item["benchmark_reference"]["spec"]["kind"] == "CASH_ZERO_INTEREST"
    assert item["analysis"]["benchmark_status"] == "COMPARABLE_MODEL_ASSUMPTION_REFERENCE"
    assert item["analysis"]["weekly"]["benchmark_status"] == "COMPARABLE_MODEL_ASSUMPTION_REFERENCE"
    report = (service.experiment_runner().store.path(item["experiment_id"]) / "report.md").read_text(encoding="utf-8")
    assert "MODEL_ASSUMPTION_CASH_ZERO_INTEREST" in report
    assert service.research_result(item["experiment_id"])["benchmark_reference"] == item["benchmark_reference"]


def test_equal_weight_reference_uses_typed_points_and_preserves_legacy_ticker_serialization(tmp_path: Path) -> None:
    service, manifest, sessions = _service_and_manifest(tmp_path)
    config = ReplayConfig(initial_cash=100_000, fee_bps=0, slippage_bps=0, spread_bps=0,
        max_volume_fraction=1)
    spec = equal_weight(("SPY", "QQQM"), sessions, initial_cash=100_000, replay_config=config)
    item = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold",
        "symbols": ["SPY"], "benchmark_spec": spec.model_dump(mode="json")})
    assert item["status"] == "COMPLETED", item.get("error")
    assert item["benchmark_reference"]["spec"]["kind"] == "EQUAL_WEIGHT"
    assert item["analysis"]["benchmark_status"] == "COMPARABLE_TYPED_REFERENCE"
    assert "benchmark_spec" in item["config"]
    legacy = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold",
        "symbols": ["SPY"], "benchmark": "QQQM"})
    assert legacy["status"] == "COMPLETED", legacy.get("error")
    assert "benchmark_spec" not in legacy["config"]


def test_frozen_plan_retains_typed_cash_reference_through_worker_dispatch(tmp_path: Path) -> None:
    service, manifest, sessions = _service_and_manifest(tmp_path)
    spec = cash_zero_interest(sessions, initial_cash=100_000)
    plan = service.plan_research({"dataset_id": manifest["dataset_id"],
        "question": "Does the passive baseline remain comparable to a frozen cash model reference?",
        "symbols": ["SPY"], "benchmark_spec": spec.model_dump(mode="json"),
        "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic"]})
    assert plan["trials"][0]["config"]["benchmark_spec"]["kind"] == "CASH_ZERO_INTEREST"
    state = service.run_research_plan(plan["plan_id"])
    assert state["status"] == "COMPLETED", state
    report = service.research_plan_report(plan["plan_id"])
    assert report["trials_attempted"] == 1 and len(report["critics"]) == 1
    assert report["critics"][0]["kind"] == "DETERMINISTIC_CRITIC"
