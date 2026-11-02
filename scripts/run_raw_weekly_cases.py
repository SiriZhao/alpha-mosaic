"""Reproduce FIXTURE weekly price features through the actual ApplicationService.

Every invocation creates a new research home. Scheduled prices are hand-declared
software inputs, never market observations, forecasts, or performance evidence.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import exchange_calendars as xcals

from alphamosaic.backtesting.models import (
    ReplayConfig,
    ReplayDataset,
    WeeklyStrategyParameters,
    payment_replay_config,
)
from alphamosaic.common.paths import unredirected
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar, SecurityIdentity
from alphamosaic.core.service import ApplicationService
from alphamosaic.data.datasets import DatasetQualityError, QualityPolicy, quality_report
from alphamosaic.experiments.runner import canonical, digest, source_manifest

POLICY = "RAW_SPLIT_PRICE_ONLY_V1"
EX_DATE = date(2024, 1, 25)
PAY_DATE = date(2024, 1, 30)
PAY_AVAILABLE = date(2024, 1, 31)


def raw_weekly_fixture() -> ReplayDataset:
    """100 → split50 → growth55 → ordinary ex54 → reverse108 → growth112."""
    calendar = xcals.get_calendar("XNYS")
    sessions = calendar.sessions_in_range("2024-01-02", "2024-02-23")
    first_open = calendar.session_open(cast(date, sessions[0])).to_pydatetime()
    declared = first_open - timedelta(days=1)
    evidence = dict(
        symbol="AAA",
        source="AlphaMosaic hand-declared RAW weekly FIXTURE v1",
        source_url="https://example.invalid/alphamosaic/raw-weekly-fixture-v1",
        currency="USD",
        data_quality=DataQuality.FIXTURE,
        adjustment_policy="RAW",
        provenance={
            "provider_version": "fixture-1",
            "meaning": "synthetic-software-input-not-market-data",
        },
        pit_status="VERIFIED",
        license_scope="Project-generated synthetic test data; Apache-2.0",
    )
    actions = [
        CorporateAction.model_validate(
            {
                **evidence,
                "observed_at": declared,
                "known_at": declared,
                "as_of": declared,
                "action": "SPLIT",
                "effective_date": "2024-01-10",
                "ratio": 2,
                "source_action_id": "fixture-AAA-split-two-for-one",
            }
        ),
        CorporateAction.model_validate(
            {
                **evidence,
                "observed_at": declared,
                "known_at": declared,
                "as_of": declared,
                "action": "DIVIDEND",
                "effective_date": EX_DATE,
                "cash_amount": 1,
                "effective_date_role": "EX_DATE",
                "dividend_type": "ORDINARY_CASH",
                "payment_date": PAY_DATE,
                "cash_amount_basis": "EX_DATE_SHARES",
                "source_action_id": "fixture-AAA-ordinary-dollar-dividend",
            }
        ),
        CorporateAction.model_validate(
            {
                **evidence,
                "observed_at": declared,
                "known_at": declared,
                "as_of": declared,
                "action": "SPLIT",
                "effective_date": "2024-02-07",
                "ratio": 0.5,
                "source_action_id": "fixture-AAA-reverse-one-for-two",
            }
        ),
    ]
    schedule = [
        (date.min, 100.0),
        (date(2024, 1, 10), 50.0),
        (date(2024, 1, 17), 55.0),
        (EX_DATE, 54.0),
        (date(2024, 2, 7), 108.0),
        (date(2024, 2, 14), 112.0),
    ]
    bars = []
    for session in sessions:
        day = session.date()
        value = next(price for start, price in reversed(schedule) if day >= start)
        units = 2 if date(2024, 1, 10) <= day < date(2024, 2, 7) else 1
        at = calendar.session_close(session).to_pydatetime()
        bars.append(
            HistoricalBar.model_validate(
                {
                    **evidence,
                    "session": day,
                    "open": value,
                    "high": value,
                    "low": value,
                    "close": value,
                    "volume": 1_000_000 * units,
                    "observed_at": at,
                    "known_at": at,
                    "as_of": at,
                }
            )
        )
    identity = SecurityIdentity(
        symbol="AAA",
        exchange="NYSE",
        currency="USD",
        active=True,
        identity_source="explicit-fixed-FIXTURE",
        identity_verified=True,
        as_of=first_open,
    )
    return ReplayDataset(
        bars={"AAA": bars},
        identities={"AAA": identity},
        actions=actions,
        cutoff=bars[-1].as_of,
        historical_universe_verified=True,
        corporate_actions_complete=True,
    )


def case_replay(cost: str = "zero", *, opt_in: bool = True) -> ReplayConfig:
    # Hold all risk/liquidity/accounting assumptions fixed while changing costs.
    fee, slippage, spread = {"zero": (0, 0, 0), "realistic": (10, 5, 2), "stress": (25, 25, 10)}[
        cost
    ]
    return payment_replay_config(
        initial_cash=1000,
        fee_bps=fee,
        slippage_bps=slippage,
        spread_bps=spread,
        min_cash_buffer=0,
        max_volume_fraction=1,
        decision_frequency="WEEKLY",
        weekly_parameters=WeeklyStrategyParameters(
            lookback_weeks=2, trend_short_weeks=2, trend_long_weeks=3
        ),
        weekly_feature_policy=POLICY if opt_in else "LEGACY_REJECT_RAW_ACTIONS",
    )


def _financial_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {key: item.get(key) for key in ("result", "benchmark_result", "analysis")}


def _execution_evidence(item: dict[str, Any], data: ReplayDataset) -> dict[str, Any]:
    """Independently compare persisted fills with sourced raw opens and calendar."""
    if item["status"] != "COMPLETED":
        return {"status": "NOT_EVALUATED", "fills": []}
    result = item["result"]
    signals = {signal["signal_id"]: signal for signal in result["signals"]}
    orders = {order["order_id"]: order for order in result["orders"]}
    bars = {str(bar.session): bar for bar in data.bars["AAA"]}
    config = item["config"]["replay"]
    calendar = xcals.get_calendar("XNYS")
    rows = []
    for fill in result["fills"]:
        order = orders[fill["order_id"]]
        signal = signals[order["signal_id"]]
        signal_day = date.fromisoformat(signal["observation_at"][:10])
        next_day = calendar.next_session(signal_day).date()
        raw = bars[fill["session"]]
        direction = 1 if fill["quantity"] > 0 else -1
        expected_price = raw.open * (
            1 + direction * (config["slippage_bps"] + config["spread_bps"] / 2) / 10_000
        )
        rows.append(
            {
                "fill_id": fill["fill_id"],
                "signal_id": signal["signal_id"],
                "session": fill["session"],
                "next_xnys_session": str(next_day),
                "raw_open": raw.open,
                "actual_fill_price": fill["price"],
                "expected_cost_adjusted_raw_open": expected_price,
                "next_open": (
                    fill["session"] == str(next_day)
                    and fill["filled_at"] == order["eligible_at"]
                    and order["eligible_at"][:10] == str(next_day)
                ),
                "price_matches_raw_execution_model": math.isclose(
                    fill["price"], expected_price, rel_tol=1e-12
                ),
            }
        )
    return {
        "status": "VERIFIED"
        if rows
        and all(row["next_open"] and row["price_matches_raw_execution_model"] for row in rows)
        else "FAILED",
        "fills": rows,
    }


def run(home_root: Path) -> dict[str, Any]:
    """Retain every case, including failures; exclusively create the suite summary."""
    root = unredirected(home_root)
    root.mkdir(parents=True, exist_ok=True)
    home = unredirected(root / ("raw-weekly-" + uuid4().hex))
    home.mkdir()
    initial_source = source_manifest()["source_hash"]
    service = ApplicationService(home)
    data = raw_weekly_fixture()
    quality = quality_report(data)
    if not quality["valid"] or set(quality["flags"]) - {"SPLIT_REQUIRES_REVIEW"}:
        raise DatasetQualityError(quality)
    manifest = service.experiment_runner().datasets.save(
        data,
        {
            "purpose": "FIXTURE_ONLY_RAW_WEEKLY_PRICE_FEATURE_AND_ACCOUNTING_BOUNDARY",
            "reviewed_flags": quality["flags"],
            "quality_review": "Hand-declared split and reverse split; raw price/volume share units are explicit. No acquired market data or repairs.",
        },
        policy=QualityPolicy.ACCEPT_WITH_PROVENANCE if quality["flags"] else QualityPolicy.REJECT,
    )
    declarations: list[tuple[str, str, str, bool, str | None]] = [
        ("default_guard", "weekly_momentum", "zero", False, None),
        ("momentum_zero", "weekly_momentum", "zero", True, None),
        ("trend_zero", "weekly_trend", "zero", True, None),
        ("equal_weight_zero", "weekly_equal_weight", "zero", True, None),
        ("momentum_realistic", "weekly_momentum", "realistic", True, None),
        ("momentum_stress", "weekly_momentum", "stress", True, None),
        ("momentum_repeat", "weekly_momentum", "zero", True, None),
        ("equal_weight_unpaid_cutoff", "weekly_equal_weight", "zero", True, "2024-01-26"),
    ]
    items: dict[str, dict[str, Any]] = {}
    for label, strategy, cost, opt_in, end in declarations:
        replay = case_replay(cost, opt_in=opt_in).model_dump(mode="json")
        if not opt_in:
            replay.pop("weekly_feature_policy")  # Exercise missing-old-field default.
        item = service.research_experiment(
            {
                "dataset_id": manifest["dataset_id"],
                "strategy": strategy,
                "symbols": ["AAA"],
                "benchmark": "AAA",
                "end": end,
                "question": "Do hand-declared raw splits and ordinary-dividend rights retain distinct weekly price and daily accounting semantics?",
                "replay": replay,
            }
        )
        items[label] = service.research_result(item["experiment_id"])  # Verify sealed artifacts.

    guard = items["default_guard"]
    completed = [
        item
        for label, item in items.items()
        if label != "default_guard" and item["status"] == "COMPLETED"
    ]
    cost_labels = ["momentum_zero", "momentum_realistic", "momentum_stress"]
    comparison = service.research_comparison(
        [items[label]["experiment_id"] for label in cost_labels]
    )
    left, right = items["momentum_zero"], items["momentum_repeat"]
    repeat = {
        "experiment_ids": [left["experiment_id"], right["experiment_id"]],
        "scope": "Exact result, passive benchmark result, and analysis; excludes outer UUID/time/elapsed metadata",
        "original_financial_hash": digest(canonical(_financial_payload(left))),
        "repeat_financial_hash": digest(canonical(_financial_payload(right))),
        "exact_financial_equality": left["status"] == right["status"] == "COMPLETED"
        and _financial_payload(left) == _financial_payload(right),
    }
    accounting: dict[str, Any] = {"status": "NOT_EVALUATED"}
    equal = items["equal_weight_zero"]
    if equal["status"] == "COMPLETED":
        result = equal["result"]
        points = {point["session"]: point for point in result["equity"]}
        before, ex_point = points["2024-01-24"], points[str(EX_DATE)]
        # Earlier signals preserve their own causal anchors. Use the ex-week signal.
        signal = next(
            signal
            for signal in result["signals"]
            if signal["observation_at"].startswith("2024-01-26")
        )
        closes = {row["last_session"]: row["close"] for row in signal["feature_evidence"]}
        price_return = closes["2024-01-26"] / closes["2024-01-19"] - 1
        entitlements, payments = result["dividend_entitlements"], result["dividend_payments"]
        unpaid = items["equal_weight_unpaid_cutoff"].get("result", {})
        accounting = {
            "status": "VERIFIED"
            if (
                before["nav"] == ex_point["nav"] == 1100
                and ex_point["market_values"]["AAA"] == 1080
                and sum(ex_point["receivables"].values()) == 20
                and len(entitlements) == len(payments) == 1
                and entitlements[0]["amount"] == payments[0]["amount"] == 20
                and payments[0]["at"].startswith(str(PAY_AVAILABLE))
                and not unpaid.get("dividend_payments")
                and unpaid.get("equity", [{}])[-1].get("receivables")
                and math.isclose(price_return, -1 / 55, abs_tol=1e-12)
            )
            else "FAILED",
            "ex_date": str(EX_DATE),
            "payment_date": str(PAY_DATE),
            "cash_available_session": str(PAY_AVAILABLE),
            "feature_policy": POLICY,
            "feature_return_basis": "PRICE_ONLY_EXCLUDES_DIVIDENDS",
            "actual_feature_closes": closes,
            "actual_ex_week_price_return": price_return,
            "hand_price_return": "54/55 - 1 = -1/55; dividend income excluded",
            "before_ex_point": before,
            "ex_point": ex_point,
            "entitlements": entitlements,
            "payments": payments,
            "unpaid_cutoff_receivables": unpaid.get("equity", [{}])[-1].get("receivables"),
        }
    cases = []
    for label, item in items.items():
        result = item.get("result", {})
        cases.append(
            {
                "case": label,
                "experiment_id": item["experiment_id"],
                "status": item["status"],
                "error": item.get("error"),
                "config": item["config"],
                "acceptance": item.get("acceptance"),
                "return_basis": item.get("return_basis"),
                "feature_signals": result.get("signals", []),
                "execution_evidence": _execution_evidence(item, data),
                "accounting_reconciliation": item.get("analysis", {})
                .get("trade_analysis", {})
                .get("reconciliation"),
                "actual_fees_usd": result.get("fees"),
                "actual_slippage_usd": result.get("slippage_cost"),
                "actual_spread_usd": result.get("spread_cost"),
                "passive_benchmark_feature_rows": sum(
                    len(signal.get("feature_evidence", []))
                    for signal in item.get("benchmark_result", {}).get("signals", [])
                ),
            }
        )
    checks = {
        "completed_opt_in_cases": len(completed) == 7,
        "default_guard_failed": guard["status"] == "FAILED"
        and "weekly RAW corporate-action" in guard.get("error", {}).get("message", ""),
        "all_completed_cases_fixture": all(
            item.get("acceptance") == "FIXTURE" for item in completed
        ),
        "all_completed_cases_derived_evidence": all(
            any(signal.get("feature_evidence") for signal in item["result"]["signals"])
            for item in completed
        ),
        "raw_next_open_execution": all(
            row["execution_evidence"]["status"] == "VERIFIED"
            for row in cases
            if row["status"] == "COMPLETED"
        ),
        "passive_benchmark_consumed_no_features": all(
            row["passive_benchmark_feature_rows"] == 0 for row in cases
        ),
        "price_vs_income_accounting": accounting["status"] == "VERIFIED",
        "cost_cases_comparable": comparison["status"] == "COMPARABLE",
        "repeat_financial_equality": repeat["exact_financial_equality"],
        "no_broker": all(
            item["broker_enabled"] is False
            and item.get("result", {}).get("broker_enabled", False) is False
            for item in items.values()
        ),
        "source_frozen": source_manifest()["source_hash"] == initial_source,
    }
    summary_path = home / "raw-weekly-suite.json"
    summary = {
        "status": "PASSED" if all(checks.values()) else "FAILED",
        "checks": checks,
        "scope": "FIXTURE_SOFTWARE_AND_FINANCIAL_BOUNDARIES_ONLY",
        "acceptance": "FIXTURE",
        "market_performance_inference": "PROHIBITED",
        "validated_alpha": False,
        "broker_enabled": False,
        "research_home": str(home),
        "summary_path": str(summary_path),
        "dataset_id": manifest["dataset_id"],
        "source_hash": initial_source,
        "script_sha256": digest(Path(__file__).read_bytes()),
        "dataset_quality": quality,
        "cases": cases,
        "repeat": repeat,
        "price_and_income": accounting,
        "cost_comparison": comparison,
        "assumptions": [
            "All prices/actions are explicitly hand-declared FIXTURE inputs, not observed market data.",
            "Derived closes use only effective splits through each complete-week anchor; ordinary dividend income is excluded.",
            "Raw daily observations alone determine next-open fills, liquidity, quantity and marks.",
            "Ordinary dividends accrue fixed ex-date rights; cash arrives at the next XNYS open after sourced pay date.",
            "Zero/realistic/stress change fee/slippage/spread only; dataset, dates, strategy, risk, frequency and accounting basis are identical.",
            "Passive benchmark uses raw daily accounting and consumes no derived weekly features.",
            "Taxes, defaults and broker-specific posting are unmodeled; deterministic cost/share-unit assumptions are recorded per case. No real PIT qualification.",
        ],
    }
    with summary_path.open("xb") as stream:
        stream.write(canonical(summary))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        type=Path,
        default=Path("runtime/raw-weekly-cases"),
        help="Parent directory; every invocation creates a unique child research home",
    )
    evidence = run(parser.parse_args().home)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "research_home": evidence["research_home"],
                "summary_path": evidence["summary_path"],
                "checks": evidence["checks"],
                "cases": [
                    {key: row[key] for key in ("case", "experiment_id", "status", "error")}
                    for row in evidence["cases"]
                ],
            },
            indent=2,
        )
    )
    raise SystemExit(0 if evidence["status"] == "PASSED" else 1)
