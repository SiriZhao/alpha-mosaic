"""User-facing weekly execution and frozen research-plan actions, not only navigation."""

from pathlib import Path

import pytest

from alphamosaic.core.service import ApplicationService


def test_terminal_executes_weekly_case_and_a_frozen_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    st.cache_resource.clear()
    service = ApplicationService(tmp_path)
    service.research_demo(100)
    source = Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"
    app = AppTest.from_file(str(source), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Strategy Lab").run()
    next(s for s in app.selectbox if s.label == "Strategy").set_value("weekly_momentum").run()
    assert not app.exception
    assert any(n.label == "Lookback weeks" for n in app.number_input)
    assert all(n.label != "Lookback sessions" for n in app.number_input)
    next(b for b in app.button if b.label == "Run local experiment").click().run()
    result = app.session_state["job"].result(timeout=30)
    assert result["status"] == "COMPLETED", result.get("error")
    assert result["config"]["replay"]["decision_frequency"] == "WEEKLY"
    assert result["analysis"]["trade_analysis"]["status"] == "VERIFIED"
    app.run()
    app.sidebar.radio[0].set_value("Backtest Results").run()
    assert not app.exception
    assert {tab.label for tab in app.tabs} >= {"Closed FIFO matches", "Asset accounting", "Weekly view"}
    app.sidebar.radio[0].set_value("AI Research").run()
    next(s for s in app.multiselect if s.label.startswith("Predeclared strategies")).set_value(["buy_and_hold"])
    next(b for b in app.button if b.label == "Freeze research plan").click().run()
    assert not app.exception
    plans = service.research_plans()
    assert len(plans) == 1 and service.research_plan(plans[0]["plan_id"])["status"] == "FROZEN"
    next(b for b in app.button if b.label == "Execute frozen local plan").click().run()
    state = app.session_state["plan_job"].result(timeout=60)
    assert state["status"] == "COMPLETED"
    app.run()
    assert not app.exception
    report = service.research_plan_report(plans[0]["plan_id"])
    assert report["trials_attempted"] == 2 and len(report["critics"]) == 2
    st.cache_resource.clear()
