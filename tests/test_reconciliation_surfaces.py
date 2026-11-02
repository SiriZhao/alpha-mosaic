"""Actual CLI, MCP job and terminal actions preserve interrupted research evidence."""

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import pytest
from typer.testing import CliRunner

from alphamosaic.cli.app import app as cli
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import ExperimentStore
from alphamosaic.mcp.server import create_server


def started(home: Path):
    service = ApplicationService(home)
    dataset = service.research_demo(80)["dataset_id"]
    plan = service.plan_research({"dataset_id": dataset,
        "question": "Can saved interrupted evidence be inspected without executing the remaining trials?",
        "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic", "stress"]})
    service.research_workflow().store.append(plan["plan_id"], "RUN_STARTED", {"max_trials": 2})
    return service, plan["plan_id"]


def recorded_then_corrupt(home: Path, monkeypatch: pytest.MonkeyPatch):
    service = ApplicationService(home)
    dataset = service.research_demo(80)["dataset_id"]
    plan = service.plan_research({"dataset_id": dataset,
        "question": "Does report failure preserve an already recorded outcome and the completed reconciliation?",
        "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic", "stress"]})
    workflow = service.research_workflow()
    original_append = workflow.store.append
    def lose_parent(plan_id, kind, payload):
        original_append(plan_id, kind, payload)
        if kind == "TOOL_RESULT":
            raise RuntimeError("simulated-parent-loss-after-recorded-result")
    with monkeypatch.context() as patch:
        patch.setattr(workflow.store, "append", lose_parent)
        with pytest.raises(RuntimeError, match="simulated-parent-loss"):
            service.run_research_plan(plan["plan_id"])
    result = ExperimentStore(home / "experiments").list()
    assert len(result) == 1 and result[0]["status"] == "COMPLETED"
    (home / "experiments" / result[0]["experiment_id"] / "equity.csv").write_text("corrupt-fixture")
    return service, plan["plan_id"]


def test_cli_reconciles_without_running_trials_and_repeated_output_is_stable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, plan_id = started(tmp_path)
    original = service.research_plan(plan_id)["events"]
    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    first = CliRunner().invoke(cli, ["reconcile-research-plan", plan_id])
    assert first.exit_code == 0, first.output
    report = json.loads(first.output)
    assert report["status"] == "INTERRUPTED" and report["trials_dispatched"] == report["trials_attempted"] == 0
    assert service.research_plan(plan_id)["events"][:len(original)] == original
    assert ExperimentStore(tmp_path / "experiments").list() == []
    again = CliRunner().invoke(cli, ["reconcile-research-plan", plan_id])
    assert again.exit_code == 0 and json.loads(again.output) == report


def test_cli_report_failure_does_not_claim_committed_reconciliation_was_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, plan_id = recorded_then_corrupt(tmp_path, monkeypatch)
    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    result = CliRunner().invoke(cli, ["reconcile-research-plan", plan_id])
    assert result.exit_code == 1
    record = json.loads(result.output)
    assert record["status"] == service.research_plan(plan_id)["status"] == "INTERRUPTED"
    assert record["report_status"] == "BLOCKED" and "integrity" in record["report_error"]
    assert len(service.research_experiments()) == 1


def test_mcp_reconciliation_is_an_explicit_bounded_local_job(tmp_path: Path) -> None:
    service, plan_id = started(tmp_path)
    server = create_server(service)
    tool = next(t for t in server._tool_manager.list_tools() if t.name == "reconcile_research_plan")
    assert tool.annotations is not None and tool.annotations.read_only_hint is False
    assert tool.annotations.open_world_hint is False and tool.annotations.destructive_hint is False
    async def invoke():
        launched = await server._tool_manager.call_tool("reconcile_research_plan", {"plan_id": plan_id}, cast(Any, None))
        assert launched["status"] == "READY" and "no experiments rerun" in launched["message"].lower()
        deadline = asyncio.get_running_loop().time() + 10
        while True:
            state = await server._tool_manager.call_tool("job_status", {"job_id": launched["job_id"]}, cast(Any, None))
            if state["status"] != "RUNNING":
                return state
            assert asyncio.get_running_loop().time() < deadline
            await asyncio.sleep(.01)
    state = asyncio.run(invoke())
    assert state["status"] == "READY" and state["result"]["status"] == "INTERRUPTED"
    assert state["result"]["broker_enabled"] is False
    assert service.research_experiments() == []


def test_terminal_reconciles_in_background_and_keeps_the_saved_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    service, plan_id = started(tmp_path)
    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    st.cache_resource.clear()
    try:
        terminal = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"), default_timeout=30).run()
        terminal.sidebar.radio[0].set_value("AI Research").run()
        next(b for b in terminal.button if b.label == "Reconcile saved attempts (no rerun)").click().run()
        state = terminal.session_state["plan_job"].result(timeout=30)
        assert state["status"] == "INTERRUPTED"
        terminal.run()
        assert not terminal.exception
        assert any(b.label == "Inspect late response evidence" for b in terminal.button)
        assert any(h.value == "Interrupted-run evidence" for h in terminal.subheader)
        assert service.research_plan(plan_id)["status"] == "INTERRUPTED" and service.research_experiments() == []
    finally:
        st.cache_resource.clear()


def test_terminal_corrupt_original_report_keeps_audit_visible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    service, plan_id = recorded_then_corrupt(tmp_path, monkeypatch)
    monkeypatch.setenv("ALPHAMOSAIC_HOME", str(tmp_path))
    st.cache_resource.clear()
    try:
        terminal = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "src/alphamosaic/ui/app.py"), default_timeout=30).run()
        terminal.sidebar.radio[0].set_value("AI Research").run()
        assert not terminal.exception
        next(b for b in terminal.button if b.label == "Reconcile saved attempts (no rerun)").click().run()
        assert terminal.session_state["plan_job"].result(timeout=30)["status"] == "INTERRUPTED"
        terminal.run()
        assert not terminal.exception
        assert any("Computed plan report unavailable" in item.value for item in terminal.error)
        assert any(cast(Any, item).label == "Download saved audit" for item in terminal.get("download_button"))
        assert service.research_plan(plan_id)["status"] == "INTERRUPTED"
    finally:
        st.cache_resource.clear()
