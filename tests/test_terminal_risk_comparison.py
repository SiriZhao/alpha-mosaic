"""Actual terminal risk and compatibility boundaries using persisted experiments."""

import json
import math
from pathlib import Path

import pytest

from alphamosaic.backtesting.models import preset_config
from alphamosaic.core.service import ApplicationService


def test_terminal_renders_qualified_risk_and_blocks_incompatible_curve_overlay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    st.cache_resource.clear()

    service = ApplicationService(tmp_path)
    manifest = service.research_demo(100)
    base = {"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold", "symbols": ["SPY"], "benchmark": "SPY"}
    a = service.research_experiment({**base, "replay": preset_config("realistic").model_dump(mode="json")})
    b = service.research_experiment({**base, "replay": preset_config("stress").model_dump(mode="json")})
    period = a["result"]["equity"]
    c = service.research_experiment({**base, "start": period[30]["session"]})
    assert all(item["status"] == "COMPLETED" for item in (a, b, c))
    assert a["analysis"]["conventions"]["rolling_window_sessions"] == 21
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Risk Lab").run()
    next(s for s in app.selectbox if s.label == "Experiment").set_value(a["experiment_id"]).run()
    assert not app.exception
    assert {tab.label for tab in app.tabs} >= {"Rolling risk", "Exposure and concentration", "Costs and asset accounting", "Drawdown episodes"}
    next(s for s in app.selectbox if s.label == "Rolling statistic").set_value("beta").run()
    assert len(app.get("plotly_chart")) == 5
    assert any("21 sessions" in caption.value and "252 periods/year" in caption.value for caption in app.caption)
    assert any("FIXTURE synthetic_demo v1" in caption.value for caption in app.caption)
    assert any("subtracted from NAV again" in caption.value for caption in app.caption)

    app.sidebar.radio[0].set_value("Experiment Comparison").run()
    app.multiselect[0].set_value([a["experiment_id"], b["experiment_id"]]).run()
    assert not app.exception
    chart = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert len(chart["data"]) == 2
    assert len(chart["layout"]["meta"]["research_provenance"]) == 2
    assert any("FIXTURE" in annotation["text"] for annotation in chart["layout"]["annotations"])
    assert any("fee-only counterfactual" in caption.value for caption in app.caption)
    assert chart["data"][0]["y"] == [point["nav"] / a["config"]["replay"]["initial_cash"] for point in a["result"]["equity"]]
    next(r for r in app.radio if r.label == "Comparison curve").set_value("Underwater").run()
    chart = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert chart["data"][0]["y"] == [row["drawdown"] for row in a["analysis"]["rolling"]]
    app.multiselect[0].set_value([a["experiment_id"], c["experiment_id"]]).run()
    assert not app.exception
    assert not app.get("plotly_chart")
    assert any("overlaid curves" in warning.value for warning in app.warning)

    # A corrupted selection reports failure instead of plotting stale evidence.
    path = service.experiment_runner().store.path(a["experiment_id"])
    (path / "checksums.json").write_text("{}")
    app.multiselect[0].set_value([a["experiment_id"]]).run()
    assert not app.exception and not app.get("plotly_chart")
    assert any("Comparison evidence could not be loaded" in error.value for error in app.error)
    st.cache_resource.clear()


def test_legacy_exposure_missing_dates_remain_gaps_and_missing_evidence_is_not_zero() -> None:
    from streamlit.testing.v1 import AppTest

    item = {"experiment_id": "a" * 32, "acceptance": "FIXTURE", "return_basis": "PRICE",
            "config": {"dataset_id": "b" * 64, "benchmark": "SPY", "replay": {"fee_bps": 10, "slippage_bps": 5, "spread_bps": 2}},
            "dataset_manifest": {"provider": ["manual UI contract fixture"], "cutoff": "2024-01-04T21:00:00+00:00"},
            "result": {"equity": [{"session": day} for day in ("2024-01-02", "2024-01-03", "2024-01-04")]},
            "analysis": {"metrics": {}, "exposures": [
                {"session": "2024-01-02", "cash_weight": .5, "concentration_hhi": .25},
                {"session": "2024-01-04", "cash_weight": .5, "concentration_hhi": .25}], "attribution": {"fees_usd": 1}}}
    source = "import json\nfrom alphamosaic.ui.views import risk_views\nrisk_views(json.loads(" + repr(json.dumps(item)) + "))"
    app = AppTest.from_string(source, default_timeout=30).run()
    assert not app.exception
    frame = app.dataframe[0].value
    assert list(frame["session"]) == [point["session"] for point in item["result"]["equity"]]
    assert math.isnan(float(frame.loc[1, "cash_weight"]))
    assert math.isnan(float(frame.loc[1, "concentration_hhi"]))
    assert any("Legacy exposure coverage omits 1" in warning.value for warning in app.warning)
    assert any("Cost components not recorded" in warning.value for warning in app.warning)
    assert any("Drawdown episodes were not recorded" in info.value for info in app.info)
    assert all("No drawdown episodes" not in info.value for info in app.info)
    cash_chart = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert cash_chart["data"][0]["connectgaps"] is False
