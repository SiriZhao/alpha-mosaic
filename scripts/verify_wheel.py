"""Run from a clean base-wheel interpreter outside the source checkout."""

import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import alphamosaic
from alphamosaic.core.service import ApplicationService


def verify() -> dict:
    package = Path(alphamosaic.__file__).resolve()
    if not package.is_relative_to(Path(sys.prefix).resolve()):
        raise AssertionError("wheel smoke imported source outside the clean environment")
    optional = {}
    for name in ("openbb-core", "quantstats", "streamlit", "plotly"):
        try:
            optional[name] = version(name)
        except PackageNotFoundError:
            optional[name] = "NOT_INSTALLED"
    if set(optional.values()) != {"NOT_INSTALLED"}:
        raise AssertionError("base wheel smoke requires optional dependencies absent")
    service = ApplicationService(Path("wheel-research"))
    manifest = service.research_demo(100)
    result = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold"})
    if result["status"] != "COMPLETED" or result["acceptance"] != "FIXTURE":
        raise AssertionError("base wheel offline experiment failed: " + str(result.get("error")))
    if service.status()["broker_enabled"] is not False:
        raise AssertionError("research boundary failed")
    if result["reproducibility"]["git_sha"] != "NOT_AVAILABLE" or result["reproducibility"]["source_kind"] != "INSTALLED_PACKAGE":
        raise AssertionError("installed wheel borrowed an unrelated parent-checkout Git identity")
    if result["config"]["replay"].get("dividend_accounting") != "PAY_DATE_RECEIVABLE":
        raise AssertionError("new base-wheel experiment did not record payment accounting")
    from alphamosaic.backtesting.benchmarks import cash_zero_interest
    benchmark_data = service.experiment_runner().datasets.load(manifest["dataset_id"])
    benchmark_sessions = tuple(row.session for row in benchmark_data.bars["SPY"])
    cash_spec = cash_zero_interest(benchmark_sessions, initial_cash=result["config"]["replay"]["initial_cash"])
    typed = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold",
        "symbols": ["SPY"], "benchmark_spec": cash_spec.model_dump(mode="json")})
    if (typed["status"] != "COMPLETED" or typed.get("benchmark_result") is not None
            or typed.get("benchmark_reference", {}).get("spec", {}).get("kind") != "CASH_ZERO_INTEREST"
            or typed["analysis"]["benchmark_status"] != "COMPARABLE_MODEL_ASSUMPTION_REFERENCE"):
        raise AssertionError("base-wheel typed cash benchmark workflow failed")
    plan = service.plan_research({"dataset_id": manifest["dataset_id"], "question": "Does the frozen passive baseline reconcile in the base-wheel offline workflow?", "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic"]})
    state = service.run_research_plan(plan["plan_id"])
    if state["status"] != "COMPLETED" or service.research_plan_report(plan["plan_id"])["trials_attempted"] != 1:
        raise AssertionError("base-wheel bounded plan workflow failed")
    from run_dividend_cases import run
    dividends = run(Path("wheel-dividend-research"))
    if dividends["status"] != "PASSED":
        raise AssertionError("base-wheel payment accounting cases failed")
    from run_reconciliation_cases import run as reconcile_cases
    recovery = reconcile_cases(Path("wheel-reconciliation-research"))
    from run_raw_weekly_cases import run as raw_weekly_cases
    weekly = raw_weekly_cases(Path("wheel-raw-weekly-research"))
    if weekly["status"] != "PASSED":
        raise AssertionError("base-wheel RAW weekly feature cases failed")
    return {"status": "PASSED", "source_hash": result["reproducibility"]["source_hash"], "source_kind": result["reproducibility"]["source_kind"], "package_path": str(package), "python": sys.version.split()[0], "optional": optional, "experiment_id": result["experiment_id"], "typed_cash_experiment_id": typed["experiment_id"], "plan_id": plan["plan_id"], "plan_status": state["status"], "fifo_reconciliation": result["analysis"]["trade_analysis"]["reconciliation"]["status"], "weekly_analysis": result["analysis"]["weekly"]["status"], "dividend_cases": len(dividends["cases"]), "dividend_plan": dividends["frozen_plan"], "unsupported_weekly_action_status": dividends["weekly_action_boundary"]["status"], "raw_weekly_cases": len(weekly["cases"]), "raw_weekly_checks": weekly["checks"], "reconciliation_cases": len(recovery["cases"]), "reconciliation_new_experiments": recovery["reconciliation_experiments_executed"], "acceptance": result["acceptance"], "broker_enabled": False}


if __name__ == "__main__":
    print(json.dumps(verify()))
