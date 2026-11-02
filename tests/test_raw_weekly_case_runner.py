"""Exercise the reproducible FIXTURE suite through sealed service artifacts."""

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

from alphamosaic.experiments.runner import ExperimentStore


def _files(home: Path) -> dict[str, str]:
    return {
        str(path.relative_to(home)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in home.rglob("*")
        if path.is_file()
    }


def test_service_case_suite_is_financially_reproducible_and_preserves_prior_homes(
    tmp_path: Path,
) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_raw_weekly_cases.py"
    entry = runpy.run_path(str(script))
    sentinel = tmp_path / "existing-evidence.txt"
    sentinel.write_bytes(b"preserve existing user evidence")
    first: dict[str, Any] = entry["run"](tmp_path)
    assert first["status"] == "PASSED" and all(first["checks"].values())
    assert first["market_performance_inference"] == "PROHIBITED"
    assert first["broker_enabled"] is first["validated_alpha"] is False
    first_home = Path(first["research_home"])
    assert first_home.parent == tmp_path and first_home != tmp_path
    assert json.loads(Path(first["summary_path"]).read_bytes()) == first
    saved = _files(first_home)
    store = ExperimentStore(first_home / "experiments")
    artifacts = {row["case"]: store.load(row["experiment_id"]) for row in first["cases"]}
    assert len(artifacts) == 8
    guard = artifacts["default_guard"]
    assert guard["status"] == "FAILED" and "result" not in guard
    assert guard["config"]["replay"]["weekly_feature_policy"] == "LEGACY_REJECT_RAW_ACTIONS"
    assert "weekly RAW corporate-action" in guard["error"]["message"]
    for label, item in artifacts.items():
        if label == "default_guard":
            continue
        assert item["status"] == "COMPLETED" and item["acceptance"] == "FIXTURE"
        assert item["return_basis"] == "RAW_WITH_CASH_ACTIONS"
        assert item["analysis"]["trade_analysis"]["reconciliation"]["status"] == "PASSED"
        assert item["result"]["fills"]
        assert all(not signal["feature_evidence"] for signal in item["benchmark_result"]["signals"])
        features = [
            feature
            for signal in item["result"]["signals"]
            for feature in signal["feature_evidence"]
        ]
        assert features and all(
            feature["evidence_kind"] == "DERIVED_FEATURE"
            and feature["pit_status"] == "NOT_APPLICABLE"
            and feature["parent_data_quality"] == "FIXTURE"
            for feature in features
        )

    # This is a controlled cost comparison, with all non-cost inputs fixed.
    costs = [
        artifacts[label] for label in ("momentum_zero", "momentum_realistic", "momentum_stress")
    ]
    comparable_configs = []
    for item in costs:
        config = json.loads(json.dumps(item["config"]))
        for field in ("fee_bps", "slippage_bps", "spread_bps"):
            config["replay"].pop(field)
        comparable_configs.append(config)
    assert comparable_configs[0] == comparable_configs[1] == comparable_configs[2]
    assert first["cost_comparison"]["status"] == "COMPARABLE"
    assert costs[0]["result"]["fees"] == 0 < costs[1]["result"]["fees"] < costs[2]["result"]["fees"]
    original, repeat = artifacts["momentum_zero"], artifacts["momentum_repeat"]
    keys = ("result", "benchmark_result", "analysis")
    financial = {key: original[key] for key in keys}
    assert financial == {key: repeat[key] for key in keys}
    expected_hash = hashlib.sha256(
        json.dumps(financial, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    assert (
        first["repeat"]["original_financial_hash"]
        == first["repeat"]["repeat_financial_hash"]
        == expected_hash
    )
    assert (
        first["price_and_income"]["before_ex_point"]["nav"]
        == first["price_and_income"]["ex_point"]["nav"]
        == 1100
    )
    assert first["price_and_income"]["unpaid_cutoff_receivables"]

    second = entry["run"](tmp_path)
    assert second["status"] == "PASSED" and second["research_home"] != first["research_home"]
    assert second["dataset_id"] == first["dataset_id"]
    assert second["repeat"]["original_financial_hash"] == expected_hash
    assert _files(first_home) == saved
    assert sentinel.read_bytes() == b"preserve existing user evidence"
