from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import exchange_calendars as xcals
import pandas as pd
import pytest

from alphamosaic.backtesting.models import (
    DatedSignal,
    ReplayConfig,
    ReplayDataset,
    TargetAllocation,
)
from alphamosaic.backtesting.replay import PaperReplayEngine, validate_dataset
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar, SecurityIdentity
from alphamosaic.evaluation.quantstats_adapter import QuantStatsAdapter
from alphamosaic.evaluation.registry import EvaluationEvidence, EvaluationRegistry
from alphamosaic.evaluation.validation import experiment, summarize, walk_forward
from alphamosaic.integrations.lean import LeanAdapter
from alphamosaic.portfolio.forward import ForwardPaperStore


def dataset(count: int = 260, volume: float | None = 1_000_000) -> ReplayDataset:
    calendar = xcals.get_calendar("XNYS")
    sessions = list(calendar.sessions_in_range("2022-01-03", "2024-01-01"))[:count]
    bars: dict[str, list[HistoricalBar]] = {}
    identities = {}
    for symbol, rate in (("AAA", 0.002), ("BBB", -0.001)):
        identities[symbol] = SecurityIdentity(
            symbol=symbol,
            exchange="NYSE",
            currency="USD",
            active=True,
            identity_source="fixture",
            identity_verified=True,
            as_of=calendar.session_open(sessions[0]).to_pydatetime(),
        )
        bars[symbol] = []
        for i, session in enumerate(sessions):
            close = 100 * (1 + rate) ** i
            at = calendar.session_close(session).to_pydatetime()
            bars[symbol].append(
                HistoricalBar(
                    symbol=symbol,
                    source="fixture",
                    source_url="https://example.invalid/fixture",
                    observed_at=at,
                    known_at=at,
                    as_of=at,
                    data_quality=DataQuality.FIXTURE,
                    adjustment_policy="RAW",
                    currency="USD",
                    provenance={"generator": "deterministic"},
                    license_scope="test-only",
                    pit_status="VERIFIED",
                    session=session.date(),
                    open=close,
                    high=close * 1.01,
                    low=close * 0.99,
                    close=close,
                    volume=volume,
                )
            )
    return ReplayDataset(bars=bars, identities=identities, cutoff=datetime(2024, 1, 2, tzinfo=UTC))


def replay(data: ReplayDataset, name: str = "momentum", **kwargs: Any):
    return PaperReplayEngine().run(data, StrategyRegistry().get(name), name, ReplayConfig(**kwargs))


def test_reproducible_momentum_and_cash_constraints():
    a, b = replay(dataset(), max_positions=1), replay(dataset(), max_positions=1)
    assert a == b and a.fills and a.acceptance == "FIXTURE"
    assert {f.symbol for f in a.fills} == {"AAA"}
    assert all(p.cash >= 0 and len(p.positions) <= 1 for p in a.equity)
    assert a.fees > 0 and a.slippage_cost > 0
    assert any(o["reason"] == "CASH_CONSTRAINT" for o in a.unfilled_orders)
    assert a.validated_alpha is False and a.broker_enabled is False


def test_fee_slippage_and_liquidity_change_actual_fills():
    free = replay(dataset(), fee_bps=0, slippage_bps=0)
    costly = replay(dataset(), fee_bps=100, slippage_bps=100)
    assert costly.equity[-1].nav < free.equity[-1].nav
    partial = replay(dataset(volume=100))
    assert partial.fills and all(abs(f.quantity) <= 1 for f in partial.fills)
    assert any(o["reason"] == "VOLUME_CAP" for o in partial.unfilled_orders)
    for volume in (0, None):
        blocked = replay(dataset(volume=volume))
        assert not blocked.fills and blocked.unfilled_orders
        assert all(p.nav == 100_000 for p in blocked.equity)


def test_today_volume_does_not_size_orders():
    d = dataset(90, volume=100)
    altered = d.model_copy(deep=True)
    altered.bars["AAA"][84] = altered.bars["AAA"][84].model_copy(update={"volume": 1_000_000_000})
    a, b = replay(d), replay(altered)
    assert [f for f in a.fills if f.session == d.bars["AAA"][84].session] == [
        f for f in b.fills if f.session == d.bars["AAA"][84].session
    ]


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate",
        "missing",
        "weekend",
        "future",
        "identity",
        "exchange",
        "malformed",
        "reconstructed",
        "late",
    ],
)
def test_reject_bad_data_and_lookahead(defect: str):
    d = dataset(90)
    if defect == "duplicate":
        d.bars["AAA"][2] = d.bars["AAA"][1]
    elif defect == "missing":
        d.bars["AAA"].pop(2)
    elif defect == "weekend":
        d.bars["AAA"][0] = d.bars["AAA"][0].model_copy(
            update={"session": pd.Timestamp("2022-01-02").date()}
        )
    elif defect == "future":
        d.bars["AAA"][0] = d.bars["AAA"][0].model_copy(
            update={"known_at": d.cutoff + timedelta(days=1)}
        )
    elif defect == "identity":
        d.bars["AAA"][0] = d.bars["AAA"][0].model_copy(update={"symbol": "BBB"})
    elif defect == "exchange":
        d.identities["AAA"] = d.identities["AAA"].model_copy(update={"exchange": "UNKNOWN"})
    elif defect == "malformed":
        d.bars["AAA"][0] = d.bars["AAA"][0].model_copy(update={"high": 1})
    elif defect == "reconstructed":
        d.bars["AAA"][0] = d.bars["AAA"][0].model_copy(update={"pit_status": "RECONSTRUCTED"})
    else:
        d.bars["AAA"][0] = d.bars["AAA"][0].model_copy(
            update={"known_at": d.bars["AAA"][1].observed_at, "as_of": d.cutoff}
        )
    with pytest.raises(ValueError):
        replay(d)


def test_sell_before_buy_and_invalid_strategy_targets():
    class Rotate:
        def allocation(self, history, signals, at, config):
            selected = "AAA" if len(history["AAA"]) < 20 else "BBB"
            return TargetAllocation(decision_at=at, weights={selected: 1})

    d = dataset(50)
    result = PaperReplayEngine().run(d, Rotate(), "rotate", ReplayConfig(rebalance_sessions=10))
    assert any(f.quantity < 0 for f in result.fills)
    assert any(f.symbol == "BBB" and f.quantity > 0 for f in result.fills)
    with pytest.raises(ValueError):
        TargetAllocation(decision_at=d.cutoff, weights={"AAA": 1.1})
    with pytest.raises(ValueError):
        TargetAllocation(decision_at=d.cutoff, weights={"AAA": -0.1})


def test_split_and_dividend_and_duplicate_action():
    d = dataset(6)
    for symbol in d.bars:
        d.bars[symbol] = [
            b.model_copy(update={"open": 100.0, "close": 100.0, "high": 101.0, "low": 99.0})
            for b in d.bars[symbol]
        ]
    for i in range(3, 6):
        d.bars["AAA"][i] = d.bars["AAA"][i].model_copy(
            update={"open": 50.0, "close": 50.0, "high": 51.0, "low": 49.0}
        )
    base = d.bars["AAA"][0].model_dump(
        exclude={"session", "open", "close", "high", "low", "volume"}
    )
    split = CorporateAction(
        **base, effective_date=d.bars["AAA"][3].session, action="SPLIT", ratio=2
    )
    dividend = CorporateAction(
        **base, effective_date=d.bars["AAA"][4].session, action="DIVIDEND", cash_amount=1
    )
    d = d.model_copy(update={"actions": [split, dividend]})
    r = replay(d, "buy_and_hold", fee_bps=0, slippage_bps=0)
    assert r.equity[3].nav == r.equity[2].nav
    assert r.equity[3].positions["AAA"] == 2 * r.equity[2].positions["AAA"]
    assert r.equity[4].nav - r.equity[3].nav == r.equity[3].positions["AAA"]
    with pytest.raises(ValueError, match="duplicate"):
        validate_dataset(d.model_copy(update={"actions": [split, split]}))
    with pytest.raises(ValueError, match="RAW"):
        validate_dataset(
            d.model_copy(
                update={
                    "bars": {
                        s: [b.model_copy(update={"adjustment_policy": "SPLIT"}) for b in bars]
                        for s, bars in d.bars.items()
                    }
                }
            )
        )


def test_quantstats_is_actual_analytics_and_benchmark_alignment():
    import quantstats as qs

    returns = pd.Series([0.01, -0.02, 0.03, 0.004] * 30)
    metrics = QuantStatsAdapter().metrics(returns)
    assert metrics["sharpe"] == pytest.approx(qs.stats.sharpe(returns, rf=0, periods=252))
    assert metrics["return"] == pytest.approx(qs.stats.comp(returns))
    d = dataset()
    result = summarize(replay(d), {"SPY": d.bars["AAA"], "QQQM": d.bars["BBB"]})
    assert set(result["benchmarks"]) == {"SPY", "QQQM"}
    assert "cagr" in result["metrics"] and result["uncertainty"]
    bad = summarize(replay(d), {"SPY": d.bars["AAA"][1:]})
    assert bad["benchmark_status"]["SPY"] == "BLOCKED_UNALIGNED_HISTORY"


def test_walk_forward_and_ablation_and_ai_blocker():
    d = dataset()
    result = experiment(d, {"SPY": d.bars["AAA"], "QQQM": d.bars["BBB"]}, ReplayConfig())
    folds = result["walk_forward"]["folds"]
    assert len(folds) == 2 and result["walk_forward"]["observations"] == 126
    assert all(f["train_end"] < f["test_start"] <= f["test_end"] for f in folds)
    assert folds[0]["test_end"] < folds[1]["test_start"]
    assert result["ablation"]["removed_signal"] == "trend"
    assert result["strategies"]["ai_rating"]["status"] == "BLOCKED"
    assert len(result["slippage_sensitivity"]) == 3
    assert result["alpha_status"] == "INSUFFICIENT_EVIDENCE_NO_DEMONSTRATED_ALPHA"
    assert walk_forward(dataset(90), ReplayConfig())["status"] == "BLOCKED"


def test_pit_signal_cutoff_and_expiry():
    d = dataset(90)
    at = d.bars["AAA"][63].observed_at
    s = DatedSignal(
        symbol="AAA",
        source="fixture",
        evidence_id="one",
        metric="ai_rating",
        value=9,
        known_at=at,
        valid_until=at + timedelta(days=1),
        pit_verified=True,
        data_quality="FIXTURE",
        license_scope="test-only",
    )
    strategy = StrategyRegistry().get("ai_rating")
    assert strategy.allocation(d.bars, [s], at, ReplayConfig()).weights == {"AAA": 1}
    assert not strategy.allocation(d.bars, [s], at - timedelta(seconds=1), ReplayConfig()).weights
    assert not strategy.allocation(d.bars, [s], at + timedelta(days=2), ReplayConfig()).weights


@pytest.mark.parametrize("acceptance", ["FIXTURE", "REAL_RECONSTRUCTED"])
def test_fixture_and_reconstructed_cannot_promote(acceptance: str):
    e = EvaluationEvidence(
        strategy="momentum",
        run_id="test",
        acceptance=acceptance,
        replay_completed=True,
        qualified_data=True,
        oos_folds=10,
        oos_observations=1000,
        excess_lower_bound=0.01,
        maximum_drawdown=-0.1,
        independent_replication=True,
        forward_initialized=True,
        qualified_forward_observations=500,
        forward_excess_lower_bound=0.01,
    )
    assert EvaluationRegistry().evaluate(e)["state"] == "BACKTESTED"
    assert (
        EvaluationRegistry().evaluate(e.model_copy(update={"rejected": True}))["state"]
        == "REJECTED"
    )


def test_promotion_requires_independent_oos_and_forward():
    e = EvaluationEvidence(
        strategy="momentum",
        run_id="test",
        acceptance="REAL_PIT",
        replay_completed=True,
        qualified_data=True,
        oos_folds=3,
        oos_observations=252,
        excess_lower_bound=0.01,
        maximum_drawdown=-0.1,
        independent_replication=True,
    )
    registry = EvaluationRegistry()
    assert registry.evaluate(e)["state"] == "OUT_OF_SAMPLE_PASSED"
    assert (
        registry.evaluate(e.model_copy(update={"independent_replication": False}))["state"]
        == "BACKTESTED"
    )
    assert (
        registry.evaluate(e.model_copy(update={"forward_initialized": True}))["state"]
        == "FORWARD_TESTING"
    )
    assert (
        registry.evaluate(
            e.model_copy(
                update={
                    "forward_initialized": True,
                    "qualified_forward_observations": 126,
                    "forward_excess_lower_bound": 0.01,
                }
            )
        )["state"]
        == "ELIGIBLE_FOR_ADVISORY"
    )


def test_forward_initialization_idempotent_and_no_fake_returns(tmp_path: Path):
    store = ForwardPaperStore(tmp_path)
    assert store.status()["status"] == "NOT_CONFIGURED"
    first = store.initialize(10_000)
    assert store.initialize(50_000) == first
    assert first["return"] is None and first["qualified_observations"] == 0
    assert first["initial_cash_usd"] == 10_000 and first["broker_enabled"] is False


def test_lean_missing_dependencies_and_no_cloud_calls(monkeypatch):
    monkeypatch.setattr("alphamosaic.integrations.lean.shutil.which", lambda name: None)
    adapter = LeanAdapter()
    assert adapter.health()["status"] == "BLOCKED"
    assert (
        adapter.run(Path("project"), Path("workspace"), Path("out"))["verified_computation"]
        is False
    )


def test_report_and_service_blocked_rating(tmp_path: Path):
    from alphamosaic.core.service import ApplicationService

    service = ApplicationService(tmp_path)
    assert service.run_backtest("AAA", "ai_rating")["status"] == "BLOCKED"
    d = dataset()
    result = service.backtest_experiment(d, {"SPY": d.bars["AAA"], "QQQM": d.bars["BBB"]})
    root = Path(result["report_directory"])
    assert (root / "report.json").is_file() and "FIXTURE" in (root / "report.md").read_text()
    assert {r["state"] for r in result["evaluation_states"]} <= {"BACKTESTED", "RESEARCH"}
