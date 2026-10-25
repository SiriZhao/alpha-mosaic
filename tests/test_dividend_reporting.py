"""Accounting disclosure must preserve missing evidence and distinct cash/claim records."""

import json
from pathlib import Path

import pytest

from alphamosaic.reporting.research import dividend_accounting_evidence


def test_legacy_report_does_not_infer_zero_unpaid_claims_from_absent_fields() -> None:
    item = {"config": {"replay": {}}, "result": {"equity": [{"cash": 100}]}}
    evidence = dividend_accounting_evidence(item)
    assert evidence["accounting_schema_version"] == 1
    assert evidence["dividend_accounting"] == "LEGACY_EX_DATE_CASH"
    assert evidence["missing_legacy_fields"] is True
    assert "final_receivables" not in evidence and "payments" not in evidence
    assert "not modeled" in evidence["convention"]


def test_payment_disclosure_retains_claim_while_cash_and_payment_evidence_are_distinct() -> None:
    item = {"config": {"replay": {"accounting_schema_version": 2,
                "dividend_accounting": "PAY_DATE_RECEIVABLE",
                "payment_availability": "NEXT_XNYS_OPEN_AFTER_PAY_DATE"}},
            "result": {"equity": [{"cash": 0, "receivables": {"manual-fixture-claim": 10}}],
                       "dividend_entitlements": [{"entitlement_id": "manual-fixture-claim", "amount": 10}],
                       "dividend_payments": []}}
    evidence = dividend_accounting_evidence(item)
    assert evidence["final_receivables"] == {"manual-fixture-claim": 10}
    assert evidence["payments"] == []
    assert item["result"]["equity"][0]["cash"] == 0
    del item["result"]["dividend_payments"]
    assert dividend_accounting_evidence(item)["payments"] is None


def test_terminal_shows_unpaid_claims_and_separate_market_weight_from_a_real_experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    from test_independent_dividend_payment import fixture_data, payment_config

    from alphamosaic.core.service import ApplicationService

    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    st.cache_resource.clear()
    service = ApplicationService(tmp_path)
    manifest = service.experiment_runner().datasets.save(fixture_data())
    item = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold", "symbols": ["AAA"],
        "benchmark": "AAA", "end": "2024-01-05", "replay": payment_config().model_dump(mode="json")})
    assert item["status"] == "COMPLETED", item.get("error")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Backtest Results").run()
    assert not app.exception
    assert any(tab.label == "Dividend accounting" for tab in app.tabs)
    assert any(metric.label == "Unpaid dividend claims" and metric.value == "$10.00" for metric in app.metric)
    disclosure = json.loads(app.json[-1].value)
    assert sum(disclosure["final_receivables"].values()) == 10
    assert disclosure["payments"] == []
    assert disclosure["dividend_accounting"] == "PAY_DATE_RECEIVABLE"
    app.sidebar.radio[0].set_value("Risk Lab").run()
    assert not app.exception
    exposures = app.dataframe[0].value
    ex = exposures.loc[exposures["session"] == "2024-01-04"].iloc[0]
    assert (ex["cash_weight"], ex["market_weight"], ex["receivable_weight"]) == pytest.approx((0, .99, .01))
    assert any("Receivables are not spendable cash" in caption.value for caption in app.caption)
    report = (service.experiment_runner().store.path(item["experiment_id"]) / "report.md").read_text(encoding="utf-8")
    assert "Dividend Accounting" in report and '"final_receivables"' in report
    st.cache_resource.clear()
