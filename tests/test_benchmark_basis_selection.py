"""Benchmark conventions follow the actual selected assets, not unrelated rows."""

from pathlib import Path

from alphamosaic.core.service import ApplicationService
from alphamosaic.data.datasets import synthetic_demo


def _registered(service: ApplicationService) -> str:
    data = synthetic_demo(80)
    data = data.model_copy(update={"bars": {symbol: [row.model_copy(update={
        "adjustment_policy": "SPLIT" if symbol == "TLT" else "RAW"}) for row in rows]
        for symbol, rows in data.bars.items()}})
    return service.experiment_runner().datasets.save(data)["dataset_id"]


def test_unselected_asset_does_not_poison_matching_raw_research_basis(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path)
    item = service.research_experiment({"dataset_id": _registered(service), "strategy": "buy_and_hold",
        "symbols": ["SPY"], "benchmark": "QQQM"})
    assert item["status"] == "COMPLETED", item.get("error")
    assert item["return_basis"] == "RAW_WITH_CASH_ACTIONS"
    assert item["benchmark_return_basis"] == "RAW_WITH_CASH_ACTIONS"
    assert item["analysis"]["benchmark_status"] == "COMPARABLE_SIMULATED_RETURNS"
    assert item["analysis"]["weekly"]["benchmark_status"] == "COMPARABLE_SIMULATED_WEEKLY_RETURNS"


def test_disjoint_asset_basis_mismatch_stays_explicit_and_uncompared(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path)
    item = service.research_experiment({"dataset_id": _registered(service), "strategy": "buy_and_hold",
        "symbols": ["SPY"], "benchmark": "TLT"})
    assert item["status"] == "COMPLETED", item.get("error")
    assert item["return_basis"] == "RAW_WITH_CASH_ACTIONS" and item["benchmark_return_basis"] == "PRICE"
    for analysis in (item["analysis"], item["analysis"]["weekly"]):
        assert analysis["benchmark_status"] == "BLOCKED_RETURN_BASIS_MISMATCH"
        assert analysis["metrics"]["beta"] is None and analysis["metrics"]["correlation"] is None


def test_mixed_selected_basis_is_not_assigned_the_benchmark_basis(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path)
    item = service.research_experiment({"dataset_id": _registered(service), "strategy": "buy_and_hold",
        "symbols": ["SPY", "TLT"], "benchmark": "QQQM"})
    assert item["status"] == "COMPLETED", item.get("error")
    assert item["return_basis"] is None and item["benchmark_return_basis"] == "RAW_WITH_CASH_ACTIONS"
    assert item["analysis"]["benchmark_status"] == "BLOCKED_UNKNOWN_RETURN_BASIS"
