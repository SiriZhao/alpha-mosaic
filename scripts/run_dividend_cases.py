"""Reproduce ordinary-dividend payment cases using explicitly synthetic raw prices."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

import exchange_calendars as xcals

from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset, preset_config
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar
from alphamosaic.core.service import ApplicationService
from alphamosaic.data.datasets import (
    DatasetQualityError,
    QualityPolicy,
    quality_report,
    synthetic_demo,
)


def dividend_fixture() -> ReplayDataset:
    data = synthetic_demo(126)
    rows = data.bars["SPY"]
    dates = [bar.session for bar in rows]
    calendar = xcals.get_calendar("XNYS")
    known = calendar.session_open(dates[10]).to_pydatetime()
    evidence = dict(symbol="SPY", source="FIXTURE ordinary-dividend-cases v1",
        source_url="https://example.invalid/alphamosaic/ordinary-dividend-fixture-v1",
        observed_at=known, known_at=known, as_of=known, currency="USD",
        data_quality=DataQuality.FIXTURE, adjustment_policy="RAW", pit_status="VERIFIED",
        license_scope="Project-generated synthetic data; Apache-2.0",
        provenance={"meaning": "software-fixture-not-market-prices", "version": "1"})
    actions = [CorporateAction.model_validate({**evidence, "action": "DIVIDEND",
        "effective_date": dates[20], "cash_amount": 1,
        "effective_date_role": "EX_DATE", "dividend_type": "ORDINARY_CASH",
        "payment_date": dates[30], "cash_amount_basis": "EX_DATE_SHARES",
        "source_action_id": "fixture-SPY-ordinary-dividend-v1"}),
        CorporateAction.model_validate({**evidence, "action": "SPLIT", "effective_date": dates[25], "ratio": 2})]
    changed = []
    for index, bar in enumerate(rows):
        adjustment = 1 if index >= 20 else 0
        split = 2 if index >= 25 else 1
        changed.append(HistoricalBar.model_validate({**bar.model_dump(),
            **{key: (getattr(bar, key) - adjustment) / split for key in ("open", "high", "low", "close")},
            "volume": bar.volume * split if bar.volume is not None else None,
            "source": evidence["source"], "source_url": evidence["source_url"],
            "provenance": {**bar.provenance, "fixture_transform": "one-dollar-ex-drop-then-two-for-one-split"}}))
    return ReplayDataset.model_validate({**data.model_dump(), "bars": {**data.bars, "SPY": changed}, "actions": actions})


def run(home: Path) -> dict:
    service = ApplicationService(home)
    data = dividend_fixture()
    quality = quality_report(data)
    if not quality["valid"] or set(quality["flags"]) - {"SPLIT_REQUIRES_REVIEW"}:
        raise DatasetQualityError(quality)
    # This local generator explicitly divides all later prices and multiplies
    # share/volume units by two. Preserve the split warning and its fixture-only
    # review; never extend this acceptance to acquired market data.
    metadata = {"purpose": "FIXTURE_ONLY_DIVIDEND_ACCOUNTING", "reviewed_flags": quality["flags"],
                "quality_review": "Known generated two-for-one split; raw price and volume units explicitly transformed; no anomaly repaired or real provider data accepted"}
    manifest = service.experiment_runner().datasets.save(data, metadata,
        policy=QualityPolicy.ACCEPT_WITH_PROVENANCE if quality["flags"] else QualityPolicy.REJECT)
    dates = [bar.session for bar in data.bars["SPY"]]
    rows = []
    ids = {}
    for name, scenario, end, legacy in (
        ("realistic_full", "realistic", dates[-1], False),
        ("stress_full", "stress", dates[-1], False),
        ("realistic_unpaid_cutoff", "realistic", dates[26], False),
        ("legacy_diagnostic", "realistic", dates[-1], True),
    ):
        replay = preset_config(scenario).model_dump(mode="json")
        if legacy:
            replay = ReplayConfig.model_validate({**replay, "accounting_schema_version": 1,
                "dividend_accounting": "LEGACY_EX_DATE_CASH"}).model_dump(mode="json")
        item = service.research_experiment({"dataset_id": manifest["dataset_id"],
            "strategy": "buy_and_hold", "symbols": ["SPY"], "benchmark": "SPY", "end": str(end),
            "question": "Do frozen synthetic dividend rights reconcile across splits, cash availability and an unpaid evaluation boundary?",
            "replay": replay})
        ids[name] = item["experiment_id"]
        rows.append({"case": name, "experiment_id": item["experiment_id"], "status": item["status"],
            "error": item.get("error"), "acceptance": item.get("acceptance"),
            "accounting": item.get("analysis", {}).get("trade_analysis", {}).get("reconciliation", {})})
    comparison = service.research_comparison([ids["realistic_full"], ids["stress_full"]])
    legacy_comparison = service.research_comparison([ids["realistic_full"], ids["legacy_diagnostic"]])
    # Unsupported action-aware weekly signals must remain an auditable failure.
    weekly = preset_config("realistic").model_dump(mode="json")
    weekly["decision_frequency"] = "WEEKLY"
    blocked = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "weekly_trend",
        "symbols": ["SPY"], "benchmark": "SPY", "replay": weekly})
    plan = service.plan_research({"dataset_id": manifest["dataset_id"], "symbols": ["SPY"], "benchmark": "SPY",
        "strategies": ["buy_and_hold", "trend"], "cost_scenarios": ["realistic", "stress"],
        "question": "Do predeclared daily baselines preserve ordinary-dividend accounting through isolated fixed research workers?"})
    state = service.run_research_plan(plan["plan_id"])
    report = service.research_plan_report(plan["plan_id"])
    passed = all(row["status"] == "COMPLETED" for row in rows) and comparison["status"] == "COMPARABLE" and legacy_comparison["status"] == "INCOMPATIBLE" and blocked["status"] == "FAILED" and state["status"] == "COMPLETED" and report["trials_attempted"] == len(report["critics"]) == 4
    return {"status": "PASSED" if passed else "FAILED", "scope": "FIXTURE_ACCOUNTING_ONLY",
        "market_performance_inference": "PROHIBITED", "dataset_id": manifest["dataset_id"],
        "cases": rows, "cost_comparison": comparison["status"], "legacy_comparison": legacy_comparison["status"],
        "frozen_plan": {"plan_id": plan["plan_id"], "status": state["status"], "trials": report["trials_attempted"], "critics": len(report["critics"])},
        "weekly_action_boundary": {"experiment_id": blocked["experiment_id"], "status": blocked["status"], "error": blocked.get("error")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path("runtime/dividend-cases"))
    args = parser.parse_args()
    args.home.mkdir(parents=True, exist_ok=True)
    evidence = run(args.home)
    with (args.home / ("suite-" + uuid4().hex + ".json")).open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, indent=2)
    print(json.dumps(evidence))
    if evidence["status"] != "PASSED":
        raise SystemExit(1)
