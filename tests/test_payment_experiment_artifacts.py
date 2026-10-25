"""Real service exports and immutable old-artifact reading for dividend accounting."""

import csv
import json
from pathlib import Path
from typing import Any

import pytest
from test_independent_dividend_payment import fixture_data, payment_config

from alphamosaic.backtesting.models import ReplayConfig, ReplayResult
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import ExperimentStore, canonical, digest


@pytest.mark.parametrize("end,paid,outstanding", [("2024-01-05", 0, 10), ("2024-01-12", 10, 0)])
def test_service_retains_entitlement_cash_payment_and_daily_claim_exports(tmp_path: Path, end: str, paid: float, outstanding: float) -> None:
    service = ApplicationService(tmp_path)
    manifest = service.experiment_runner().datasets.save(fixture_data())
    item = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold",
        "symbols": ["AAA"], "benchmark": "AAA", "end": end, "replay": payment_config().model_dump(mode="json")})
    assert item["status"] == "COMPLETED", item.get("error")
    assert item["artifact_schema_version"] == 3 and item["broker_enabled"] is False
    assert item["result"]["equity"][-1]["nav"] == 1000
    reconciliation = item["analysis"]["trade_analysis"]["reconciliation"]
    assert reconciliation["status"] == "PASSED"
    assert reconciliation["paid_dividends_usd"] == paid
    assert reconciliation["outstanding_dividend_receivables_usd"] == outstanding
    directory = service.experiment_runner().store.path(item["experiment_id"])
    def rows(name: str) -> list[dict[str, str]]:
        with (directory / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))
    entitlements = rows("dividend_entitlements.csv")
    payments = rows("dividend_payments.csv")
    claims = rows("receivables.csv")
    assert len(entitlements) == 1 and float(entitlements[0]["amount"]) == 10
    assert sum(float(row["amount"]) for row in payments) == paid
    assert claims and all(float(row["amount"]) == 10 for row in claims)
    if paid:
        assert payments[0]["at"] == "2024-01-09T14:30:00Z"
    checksums = json.loads((directory / "checksums.json").read_bytes())
    assert {"dividend_entitlements.csv", "dividend_payments.csv", "receivables.csv"} <= checksums.keys()
    assert service.research_result(item["experiment_id"])["result"] == item["result"]


def test_version_two_fixture_artifact_is_loaded_without_inserting_new_payment_semantics(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path / "original")
    manifest = service.experiment_runner().datasets.save(fixture_data(legacy_terms=True))
    original = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold",
        "symbols": ["AAA"], "benchmark": "AAA", "replay": ReplayConfig(initial_cash=1000, fee_bps=0, slippage_bps=0).model_dump(mode="json")})
    assert original["status"] == "COMPLETED", original.get("error")
    source = service.experiment_runner().store.path(original["experiment_id"])
    before = {p.name: p.read_bytes() for p in source.iterdir() if p.is_file()}
    legacy: dict[str, Any] = json.loads(canonical(original))
    legacy["artifact_schema_version"] = 2
    for config in (legacy["config"]["replay"], legacy["result"]["config"], legacy["benchmark_result"]["config"]):
        for key in ("accounting_schema_version", "dividend_accounting", "payment_availability"):
            config.pop(key)
    for result in (legacy["result"], legacy["benchmark_result"]):
        result.pop("dividend_entitlements")
        result.pop("dividend_payments")
        for point in [*result["equity"], *result["events"]]:
            point.pop("receivables")
    store = ExperimentStore(tmp_path / "legacy-fixture")
    target = store.path(original["experiment_id"])
    target.mkdir()
    excluded = {"checksums.json", "experiment.json", "config.json", "dividend_entitlements.csv", "dividend_payments.csv", "receivables.csv"}
    for name, data in before.items():
        if name not in excluded:
            (target / name).write_bytes(data)
    (target / "experiment.json").write_bytes(canonical(legacy))
    (target / "config.json").write_bytes(canonical(legacy["config"]))
    (target / "checksums.json").write_bytes(canonical({p.name: digest(p.read_bytes()) for p in target.iterdir()}))
    copied_before = {p.name: p.read_bytes() for p in target.iterdir()}
    loaded = store.load(original["experiment_id"])
    assert loaded == legacy
    assert "dividend_accounting" not in loaded["config"]["replay"]
    assert ReplayResult.model_validate(loaded["result"]).config.dividend_accounting == "LEGACY_EX_DATE_CASH"
    assert {p.name: p.read_bytes() for p in target.iterdir()} == copied_before
    assert {p.name: p.read_bytes() for p in source.iterdir() if p.is_file()} == before
