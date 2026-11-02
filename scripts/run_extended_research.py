"""Fixed daily/weekly/FIFO cases and a bounded frozen-plan demonstration."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from alphamosaic.backtesting.models import preset_config
from alphamosaic.core.service import ApplicationService


def run(home: Path, sessions: int = 260) -> dict:
    service = ApplicationService(home)
    manifest = service.research_demo(sessions)
    cases = []
    for name in ("mean_reversion", "weekly_equal_weight", "weekly_momentum", "weekly_trend"):
        replay = preset_config("realistic").model_dump(mode="json")
        replay["decision_frequency"] = "WEEKLY" if name.startswith("weekly_") else "DAILY"
        config = {"dataset_id": manifest["dataset_id"], "strategy": name, "symbols": ["SPY", "QQQM", "TLT"],
                  "benchmark": "SPY", "question": "Does a fixed daily or calendar-week baseline reconcile after costs, splits and closed-lot accounting?", "replay": replay}
        item = service.research_experiment(config)
        if item["status"] != "COMPLETED":
            raise AssertionError(f"{name} failed: {item.get('error')}")
        trades = item["analysis"]["trade_analysis"]
        if trades["status"] != "VERIFIED" or trades["reconciliation"]["status"] != "PASSED":
            raise AssertionError("accounting analysis did not qualify")
        cases.append({"strategy": name, "experiment_id": item["experiment_id"], "acceptance": item["acceptance"],
                      "decision_frequency": replay["decision_frequency"], "closed_fifo_matches": len(trades["closed_lots"]),
                      "weekly_observations": item["analysis"]["weekly"]["conventions"]["observations"], "accounting": trades["reconciliation"]["status"]})
    plan = service.plan_research({"dataset_id": manifest["dataset_id"], "symbols": ["SPY"],
        "question": "Do unchanged daily and weekly baselines remain reproducible across predeclared realistic and stress costs?",
        "strategies": ["buy_and_hold", "trend", "weekly_trend"], "cost_scenarios": ["realistic", "stress"]})
    state = service.run_research_plan(plan["plan_id"])
    if state["status"] != "COMPLETED":
        raise AssertionError("frozen research plan did not complete; inspect retained audit")
    report = service.research_plan_report(plan["plan_id"])
    if report["trials_attempted"] != 6 or len(report["critics"]) != 6:
        raise AssertionError("predeclared cases were not all retained")
    return {"status": "PASSED", "evidence_class": "FIXTURE", "market_performance_inference": "PROHIBITED", "dataset_id": manifest["dataset_id"],
            "cases": cases, "plan_id": plan["plan_id"], "plan_status": state["status"], "plan_attempts": report["trials_attempted"],
            "critics": len(report["critics"]), "automatic_promotion": report["automatic_promotion"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path("runtime/extended-research"))
    parser.add_argument("--sessions", type=int, default=260)
    args = parser.parse_args()
    args.home.mkdir(parents=True, exist_ok=True)
    result = run(args.home, args.sessions)
    with (args.home / ("suite-" + uuid4().hex + ".json")).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))
