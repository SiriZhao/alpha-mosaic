"""Signal-price exports retain economic meaning and independent artifact integrity."""

import csv
import json
from datetime import date
from pathlib import Path

import pytest
from test_raw_weekly_features import POLICY, action, prices
from test_weekly_research import data_between

from alphamosaic.backtesting.models import WeeklyStrategyParameters, payment_replay_config
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import canonical
from alphamosaic.reporting.research import weekly_feature_evidence


def completed(service: ApplicationService, strategy: str = "weekly_momentum") -> dict:
    data = data_between("2024-01-02", "2024-02-02")
    split, rise = date(2024, 1, 10), date(2024, 1, 17)
    data = prices(data, [(date.min, 100), (split, 50), (rise, 55)])
    data = data.model_copy(update={"actions": [action(data, split)]})
    manifest = service.experiment_runner().datasets.save(data)
    config = payment_replay_config(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0,
        max_volume_fraction=1, min_cash_buffer=0, decision_frequency="WEEKLY", weekly_feature_policy=POLICY,
        weekly_parameters=WeeklyStrategyParameters(lookback_weeks=2))
    item = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": strategy,
        "symbols": ["AAA"], "benchmark": "AAA", "replay": config.model_dump(mode="json")})
    assert item["status"] == "COMPLETED", item.get("error")
    return item


def test_complete_price_dependencies_are_exported_and_integrity_is_enforced(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path)
    item = completed(service)
    directory = service.experiment_runner().store.path(item["experiment_id"])
    with (directory / "weekly_price_features.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    signals = {signal["signal_id"]: signal for signal in item["result"]["signals"]}
    assert rows and len(rows) == sum(len(signal["feature_evidence"]) for signal in signals.values())
    for row in rows:
        signal = signals[row["signal_id"]]
        original = next(feature for feature in signal["feature_evidence"] if feature["dependency_fingerprint"] == row["dependency_fingerprint"])
        assert float(row["close"]) == original["close"]
        assert json.loads(row["applied_splits"]) == original["applied_splits"]
        assert row["decision_at"] == row["signal_generated_at"] == signal["generated_at"]
        assert row["return_basis"] == "PRICE_ONLY_EXCLUDES_DIVIDENDS"
        assert row["evidence_kind"] == "DERIVED_FEATURE" and row["pit_status"] == "NOT_APPLICABLE"
    assert item["result"]["fills"][0]["price"] == 55
    report = (directory / "report.md").read_text(encoding="utf-8")
    assert "Weekly Signal Price Features" in report and "PRICE_ONLY_EXCLUDES_DIVIDENDS" in report
    assert "RAW_WITH_CASH_ACTIONS" in report and "weekly_price_features.csv" in report
    assert service.research_result(item["experiment_id"])["result"] == item["result"]
    # An incomplete seal must not make the declared export silently optional.
    manifest = json.loads((directory / "checksums.json").read_bytes())
    manifest.pop("weekly_price_features.csv")
    (directory / "checksums.json").write_bytes(canonical(manifest))
    with pytest.raises(ValueError, match="incomplete experiment artifact manifest"):
        service.research_result(item["experiment_id"])


def test_disclosure_does_not_infer_passive_or_legacy_feature_consumption(tmp_path: Path) -> None:
    passive = weekly_feature_evidence(completed(ApplicationService(tmp_path), "buy_and_hold"))
    assert passive["requested_policy"] == POLICY and passive["recorded_feature_rows"] == 0
    assert passive["consumption_status"] == "NO_DERIVED_FEATURES_RECORDED"
    assert passive["feature_return_basis"] == passive["feature_pit_status"] == "NOT_RECORDED"
    legacy = weekly_feature_evidence({"config": {"replay": {}}, "result": {}})
    assert legacy["requested_policy"] == "LEGACY_REJECT_RAW_ACTIONS"
    assert legacy["recorded_feature_rows"] == 0 and "no separate legacy" in legacy["artifact"]


def test_terminal_preserves_explicit_policy_and_displays_recorded_feature_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    st.cache_resource.clear()
    try:
        item = completed(ApplicationService(tmp_path))
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"), default_timeout=30).run()
        app.sidebar.radio[0].set_value("Strategy Lab").run()
        next(select for select in app.selectbox if select.label == "Strategy").set_value("weekly_momentum").run()
        policy = next(select for select in app.selectbox if select.label == "Weekly signal price policy")
        assert policy.value == "LEGACY_REJECT_RAW_ACTIONS"
        policy.set_value(POLICY).run()
        assert not app.exception
        app.sidebar.radio[0].set_value("Backtest Results").run()
        assert not app.exception
        assert any(tab.label == "Signal price features" for tab in app.tabs)
        evidence = json.loads(next(tab for tab in app.tabs if tab.label == "Signal price features").json[0].value)
        assert evidence["recorded_feature_rows"] == weekly_feature_evidence(item)["recorded_feature_rows"] > 0
        assert evidence["feature_return_basis"] == "PRICE_ONLY_EXCLUDES_DIVIDENDS"
        assert any("signal policy " + POLICY in caption.value for caption in app.caption)
    finally:
        st.cache_resource.clear()
