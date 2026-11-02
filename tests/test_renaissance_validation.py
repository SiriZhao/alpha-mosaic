"""Hand-calculable numerical and information-boundary validation."""

import json
import math
from datetime import date, timedelta

import numpy as np
import pytest

from alphamosaic.backtesting.models import EquityPoint, Fill, ReplayConfig, ReplayResult
from alphamosaic.evaluation.analytics import analyze, benchmark_metrics, returns_metrics
from alphamosaic.evaluation.scientific import (
    DEFAULT_RANKING_WEIGHTS,
    HoldoutAudit,
    Standardizer,
    block_bootstrap_mean,
    chronological_split,
    fit_standardizer,
    rank_candidates,
    walk_forward_folds,
)


def replay(navs: list[float], **updates) -> ReplayResult:
    result = ReplayResult(
        strategy="manual-accounting-sample",
        kind="HISTORICAL",
        acceptance="FIXTURE",
        config=ReplayConfig(initial_cash=100),
        equity=[
            EquityPoint(session=date(2024, 1, 2) + timedelta(days=i), nav=nav, cash=nav, positions={})
            for i, nav in enumerate(navs)
        ],
        fills=[],
        unfilled_orders=[],
        applied_actions=[],
        turnover=0,
        fees=0,
        slippage_cost=0,
        diagnostics=[],
    )
    return result.model_copy(update=updates)


def test_geometric_returns_include_initial_capital_for_drawdown() -> None:
    result = returns_metrics([-0.1, 0.1, -0.2], periods_per_year=3)
    assert result["return"] == pytest.approx(-0.208)
    assert result["cagr"] == pytest.approx(-0.208)
    assert result["max_drawdown"] == pytest.approx(-0.208)
    assert result["drawdown_duration_sessions"] == 3
    assert result["calmar"] == pytest.approx(-1)


def test_sample_volatility_and_sharpe_have_explicit_annualization() -> None:
    result = returns_metrics([0.01, -0.01], periods_per_year=2)
    assert result["volatility"] == pytest.approx(0.02)
    assert result["sharpe"] == pytest.approx(0)
    assert result["sortino"] == pytest.approx(0)
    assert result["cagr"] == pytest.approx(-0.0001)


def test_risk_free_conversion_and_downside_deviation_use_every_period() -> None:
    result = returns_metrics([0.02, 0.0], periods_per_year=1, risk_free_annual=0.01)
    assert result["sharpe"] == pytest.approx(0)
    values = returns_metrics([0.02, -0.01], periods_per_year=1)
    assert values["sortino"] == pytest.approx(0.005 / math.sqrt(0.0001 / 2))


def test_zero_and_bankrupt_returns_do_not_produce_infinite_ratios() -> None:
    zeros = returns_metrics([0, 0, 0])
    assert zeros["return"] == 0
    assert zeros["max_drawdown"] == 0
    assert zeros["volatility"] == 0
    assert zeros["sharpe"] is None
    assert zeros["sortino"] is None
    assert zeros["calmar"] is None
    bankrupt = returns_metrics([-1, 0], periods_per_year=2)
    assert bankrupt["return"] == -1
    assert bankrupt["cagr"] == -1
    assert bankrupt["max_drawdown"] == -1
    json.dumps(bankrupt, allow_nan=False)


def test_empty_and_single_return_have_explicit_missing_statistics() -> None:
    assert all(value is None for value in returns_metrics([]).values())
    assert returns_metrics([0.1])["volatility"] is None
    assert returns_metrics([0.1])["sharpe"] is None


@pytest.mark.parametrize("values", [[float("nan")], [float("inf")], [-1.0001], [[0.1]]])
def test_invalid_returns_fail_closed(values) -> None:
    with pytest.raises(ValueError):
        returns_metrics(values)


def test_wealth_overflow_is_rejected() -> None:
    with pytest.raises(ValueError, match="compounded wealth"):
        returns_metrics([1e308, 1e308])


def test_descriptive_regression_is_hand_calculable() -> None:
    benchmark = [-0.01, 0, 0.01]
    portfolio = [-0.019, 0.001, 0.021]
    result = benchmark_metrics(portfolio, benchmark, periods_per_year=3)
    assert result["beta"] == pytest.approx(2)
    assert result["alpha_annualized_arithmetic"] == pytest.approx(0.003)
    assert result["tracking_error"] == pytest.approx(0.01 * math.sqrt(3))
    assert result["correlation"] == pytest.approx(1)
    assert result["information_ratio"] == pytest.approx(0.1 * math.sqrt(3))


def test_constant_benchmark_cannot_identify_beta() -> None:
    result = benchmark_metrics([0.01, 0.02], [0, 0])
    assert result["beta"] is None
    assert result["alpha_annualized_arithmetic"] is None
    assert result["correlation"] is None
    with pytest.raises(ValueError, match="aligned"):
        benchmark_metrics([0.1], [0.1, 0.2])


@pytest.mark.parametrize(
    ("basis", "other_basis", "expected"),
    [(None, None, "BLOCKED_UNKNOWN_RETURN_BASIS"),
     ("PRICE", "TOTAL_RETURN", "BLOCKED_RETURN_BASIS_MISMATCH"),
     ("RAW_WITH_CASH_ACTIONS", "RAW_WITH_CASH_ACTIONS", "COMPARABLE_SIMULATED_RETURNS")],
)
def test_benchmark_comparison_requires_consistent_return_basis(basis, other_basis, expected) -> None:
    result = analyze(replay([90, 99, 100]), replay([90, 99, 100]),
                     return_basis=basis, benchmark_return_basis=other_basis)
    assert result["benchmark_status"] == expected
    if expected.startswith("BLOCKED"):
        assert result["metrics"]["beta"] is None


def test_benchmark_misalignment_and_evidence_class_block_regression() -> None:
    a, b = replay([100, 110]), replay([100, 110])
    b = b.model_copy(update={"equity": [p.model_copy(update={"session": p.session + timedelta(days=1)}) for p in b.equity]})
    assert analyze(a, b, return_basis="PRICE", benchmark_return_basis="PRICE")["benchmark_status"] == "BLOCKED_UNALIGNED_SESSIONS"
    b = replay([100, 110], acceptance="REAL_RECONSTRUCTED")
    assert analyze(a, b, return_basis="PRICE", benchmark_return_basis="PRICE")["benchmark_status"] == "BLOCKED_EVIDENCE_CLASS_MISMATCH"


def test_drawdown_episodes_and_trade_count_do_not_invent_lot_statistics() -> None:
    fill = Fill(session=date(2024, 1, 2), symbol="AAA", quantity=1, price=10, fee=1, slippage_cost=0)
    result = analyze(replay([90, 100, 80], fills=[fill], fees=1), rolling_window=2)
    assert result["metrics"]["fill_count"] == 1
    assert result["metrics"]["trade_count"] is None
    assert result["metrics"]["win_rate"] is None
    assert result["metrics"]["transaction_cost_drag_initial_capital"] == 0.01
    assert result["drawdown_episodes"] == [
        {"start": "2024-01-02", "recovery": "2024-01-03", "underwater_sessions": 1, "maximum_drawdown": pytest.approx(-0.1)},
        {"start": "2024-01-04", "recovery": None, "underwater_sessions": 1, "maximum_drawdown": pytest.approx(-0.2)},
    ]
    assert "volatility" not in result["rolling"][0]
    json.dumps(result, allow_nan=False)


def test_equity_history_requires_order_and_positive_nav() -> None:
    with pytest.raises(ValueError, match="positive"):
        analyze(replay([100, 0]))
    data = replay([100, 110])
    with pytest.raises(ValueError, match="chronological"):
        analyze(data.model_copy(update={"equity": list(reversed(data.equity))}))


def test_exposure_grid_preserves_flat_cash_and_missing_legacy_marks() -> None:
    data = replay([100] * 5)
    updates = [
        {"cash": 100, "positions": {}, "market_values": {}},
        {"cash": 40, "positions": {"AAA": 1}, "market_values": {"AAA": 60}},
        {"cash": 100, "positions": {}, "market_values": {}},
        {"cash": 50, "positions": {"AAA": 1}, "market_values": {}},
        {"cash": 50, "positions": {"AAA": 1, "BBB": 1}, "market_values": {"AAA": 50}},
    ]
    data = data.model_copy(update={"equity": [point.model_copy(update=update) for point, update in zip(data.equity, updates, strict=True)]})
    rows = analyze(data)["exposures"]
    assert [row["session"] for row in rows] == [str(point.session) for point in data.equity]
    assert [row["cash_weight"] for row in rows] == [1, .4, 1, .5, .5]
    assert [row["concentration_hhi"] for row in rows] == [0, pytest.approx(.36), 0, None, None]


def test_cash_only_exposure_is_known_and_inconsistent_marks_do_not_imply_low_concentration() -> None:
    assert analyze(replay([100, 100]))["exposures"] == [
        {"session": "2024-01-02", "cash_weight": 1.0, "concentration_hhi": 0.0},
        {"session": "2024-01-03", "cash_weight": 1.0, "concentration_hhi": 0.0},
    ]
    data = replay([100])
    data.equity[0] = data.equity[0].model_copy(update={"cash": 40, "positions": {"AAA": 1}, "market_values": {"AAA": 50}})
    assert analyze(data)["exposures"][0]["concentration_hhi"] is None


def test_purging_removes_every_label_that_reaches_evaluation_boundary() -> None:
    split = chronological_split(100, label_horizon_sessions=4, embargo_sessions=2)
    assert split.train == tuple(range(54))
    assert split.validation == tuple(range(60, 74))
    assert split.holdout == tuple(range(80, 100))
    all_indices = split.train + split.validation + split.holdout + split.purged_or_embargoed
    assert sorted(all_indices) == list(range(100))
    assert max(split.train) + 4 < min(split.validation)
    assert max(split.validation) + 4 < min(split.holdout)
    with pytest.raises(ValueError, match="insufficient"):
        chronological_split(5, label_horizon_sessions=2)


def test_walk_forward_preserves_time_and_disjoint_evaluation_folds() -> None:
    folds = walk_forward_folds(30, train_sessions=10, test_sessions=5, label_horizon_sessions=2, embargo_sessions=1)
    assert folds[0] == {"train": list(range(10)), "test": list(range(13, 18)), "gap": [10, 11, 12]}
    assert folds[1]["train"] == list(range(5, 15))
    tests = [i for fold in folds for i in fold["test"]]
    assert len(set(tests)) == len(tests)
    assert all(max(f["train"]) + 2 < min(f["test"]) for f in folds)
    expanded = walk_forward_folds(30, train_sessions=10, test_sessions=5, expanding=True)
    assert expanded[1]["train"] == list(range(15))


def test_future_changes_cannot_change_training_standardization() -> None:
    split = chronological_split(10)
    original = np.arange(20, dtype=float).reshape(10, 2)
    fitted = fit_standardizer(original, split)
    mutated = original.copy()
    mutated[list(split.validation + split.holdout)] = 1e12
    assert fitted == fit_standardizer(mutated, split)
    transformed = fitted.transform(original)
    assert transformed[list(split.train)].mean(axis=0) == pytest.approx([0, 0])
    assert transformed[list(split.train)].std(axis=0) == pytest.approx([1, 1])


def test_standardizer_constant_feature_and_invalid_partition() -> None:
    split = chronological_split(10)
    fitted = fit_standardizer(np.ones((10, 2)), split)
    assert fitted.scale == (1, 1)
    assert np.array_equal(fitted.transform(np.ones((3, 2))), np.zeros((3, 2)))
    with pytest.raises(ValueError, match="width"):
        fitted.transform([[1]])
    with pytest.raises(ValueError, match="partition"):
        fit_standardizer(np.ones((11, 2)), split)


def test_bootstrap_is_reproducible_and_reports_uncertainty_limits() -> None:
    first = block_bootstrap_mean([1, 2, 3, 4], block_sessions=2, resamples=100, seed=7)
    assert first == block_bootstrap_mean([1, 2, 3, 4], block_sessions=2, resamples=100, seed=7)
    assert first["mean"] == 2.5
    assert first["mean_95pct_interval"][0] <= 2.5 <= first["mean_95pct_interval"][1]
    constant = block_bootstrap_mean([0.01] * 10, resamples=100)
    assert constant["mean_95pct_interval"] == pytest.approx([0.01, 0.01])
    assert any("repeated trials" in limit for limit in first["limitations"])


def test_extreme_feature_and_bootstrap_statistics_fail_before_emitting_infinity() -> None:
    with pytest.raises(ValueError, match="fitted statistics"):
        fit_standardizer(np.full((10, 2), 1e308), chronological_split(10))
    with pytest.raises(ValueError, match="bootstrap statistics"):
        block_bootstrap_mean([1e308] * 10, resamples=100)
    with pytest.raises(ValueError, match="standardized"):
        Standardizer((0,), (1e-100,), (0,)).transform([[1e308]])


def test_ranking_missing_dimensions_remain_unscored_and_custom_weights_are_explicit() -> None:
    dimensions = dict.fromkeys(DEFAULT_RANKING_WEIGHTS, 0.5)
    rows = rank_candidates([{"id": "complete", "dimensions": dimensions}, {"id": "missing", "dimensions": {}}])
    assert rows[0]["research_priority_score"] == pytest.approx(0.5)
    assert rows[1]["research_priority_score"] is None
    assert rows[1]["status"] == "INSUFFICIENT_EVIDENCE"
    custom = rank_candidates([{"id": "a", "dimensions": {"data": 0.25}}], {"data": 5})
    assert custom[0]["weights"] == {"data": 1}
    assert custom[0]["research_priority_score"] == 0.25
    with pytest.raises(ValueError, match="finite"):
        rank_candidates([], {"a": 1e308, "b": 1e308})
    with pytest.raises(ValueError, match="dimension"):
        rank_candidates([{"dimensions": {"a": True}}], {"a": 1})


def test_holdout_tuning_contamination_is_persistent_and_events_are_immutable(tmp_path) -> None:
    audit = HoldoutAudit(tmp_path)
    args = {"dataset_hash": "a" * 64, "holdout_sessions": ["2024-01-02", "2024-01-03"], "purpose": "review"}
    first = audit.record(**args, experiment_id="one")
    first_files = {p.name: p.read_bytes() for p in tmp_path.glob("*.json")}
    assert first["status"] == "HOLDOUT_REVIEW_RECORDED"
    second = audit.record(**args, experiment_id="two", informs_tuning=True)
    third = audit.record(**args, experiment_id="three", informs_tuning=False)
    assert second["contaminated"] is True
    assert third["status"] == "CONTAMINATED_BY_TUNING"
    assert third["uses"] == 3
    assert third["independent_validation"] is False
    assert all((tmp_path / name).read_bytes() == content for name, content in first_files.items())


def test_holdout_repeated_review_never_becomes_independent_validation(tmp_path) -> None:
    audit = HoldoutAudit(tmp_path)
    audit.record("a" * 64, ["2024-01-02"], experiment_id="one", purpose="inspect")
    result = audit.record("a" * 64, ["2024-01-02"], experiment_id="two", purpose="inspect")
    assert result["status"] == "REPEATED_HOLDOUT_REVIEW"
    assert result["independent_validation"] is False
    with pytest.raises(ValueError, match="calendar dates"):
        audit.record("a" * 64, ["tomorrow"], experiment_id="three", purpose="inspect")


def test_redeclaring_overlapping_holdout_cannot_remove_tuning_contamination(tmp_path) -> None:
    audit = HoldoutAudit(tmp_path)
    audit.record("a" * 64, ["2024-01-02", "2024-01-03"], experiment_id="one", purpose="parameter change", informs_tuning=True)
    overlap = audit.record("a" * 64, ["2024-01-03", "2024-01-04"], experiment_id="two", purpose="inspect")
    assert overlap["contaminated"] is True
    assert len(overlap["overlapping_tuning_event_ids"]) == 1
    disjoint = audit.record("a" * 64, ["2024-02-01"], experiment_id="three", purpose="inspect")
    assert disjoint["contaminated"] is False


def test_holdout_malformed_event_is_not_silently_ignored(tmp_path) -> None:
    audit = HoldoutAudit(tmp_path)
    first = audit.record("a" * 64, ["2024-01-02"], experiment_id="one", purpose="inspect")
    (tmp_path / "invalid.json").write_text('{"informs_tuning": "false"}', encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        audit.status(first["holdout_id"])
