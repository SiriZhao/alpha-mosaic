"""Independent finite-input regressions for portfolio and return arithmetic."""

import math
import warnings

import numpy as np
import pytest

from alphamosaic.evaluation.analytics import benchmark_metrics, returns_metrics
from alphamosaic.portfolio.construction import inverse_volatility


def test_inverse_volatility_does_not_overflow_on_subnormal_positive_inputs() -> None:
    result = inverse_volatility({"AAA": 5e-324, "BBB": 1e-323, "CASH": 0})
    assert result == pytest.approx({"AAA": 2 / 3, "BBB": 1 / 3})
    assert all(math.isfinite(value) and value > 0 for value in result.values())


def test_huge_finite_return_then_bankruptcy_preserves_representable_moments() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = returns_metrics([1e200, -1], periods_per_year=252)
    assert result["return"] == -1
    assert result["cagr"] == -1
    assert result["volatility"] == pytest.approx(math.sqrt(126) * 1e200)
    assert result["sharpe"] == pytest.approx(math.sqrt(126))
    assert result["sortino"] == pytest.approx(math.sqrt(126) * 1e200)


def test_large_risk_free_downside_does_not_generate_spurious_zero_sortino() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = returns_metrics([0, 0], periods_per_year=1, risk_free_annual=1e200)
    assert result["sortino"] == pytest.approx(-1)
    assert result["sharpe"] is None


def test_benchmark_regression_scales_moments_before_squaring() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = benchmark_metrics([1e200, 0, 1e200], [1e200, 0, 1e200])
    assert result["beta"] == pytest.approx(1)
    assert result["alpha_annualized_arithmetic"] == pytest.approx(0)
    assert result["correlation"] == pytest.approx(1)
    assert result["tracking_error"] == 0
    assert result["information_ratio"] is None


@pytest.mark.parametrize("periods", [True, 0, -1, 52.5, float("nan"), float("inf"), 1_000_001])
def test_invalid_annualization_is_rejected_before_any_empty_or_numeric_branch(periods) -> None:
    for function, args in ((returns_metrics, ([],)), (benchmark_metrics, ([], []))):
        with pytest.raises(ValueError, match="annualization"):
            function(*args, periods_per_year=periods)


def test_numpy_integral_annualization_is_supported() -> None:
    assert returns_metrics([0, 0], periods_per_year=np.int64(52))["volatility"] == 0


def test_unrepresentable_wealth_still_fails_closed_without_runtime_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises(ValueError, match="compounded wealth"):
            returns_metrics([1e200, 1e200])


def test_unrepresentable_active_volatility_does_not_erase_defined_information_ratio() -> None:
    largest = np.finfo(float).max
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = benchmark_metrics([largest, -1], [-1, largest])
    assert result["tracking_error"] is None
    assert result["information_ratio"] == 0
    assert result["beta"] == pytest.approx(-1)
    assert result["correlation"] == pytest.approx(-1)
    assert all(value is None or math.isfinite(value) for value in result.values())


@pytest.mark.parametrize("fault", ["price_underflow", "volume_overflow"])
def test_split_adjusted_strategy_history_cannot_hide_invalid_derived_values(fault: str) -> None:
    from test_backtesting import dataset

    from alphamosaic.backtesting.replay import _causal_history, validate_dataset
    from alphamosaic.core.contracts import CorporateAction

    data = dataset(5)
    rows = data.bars["AAA"]
    if fault == "price_underflow":
        rows = [bar.model_copy(update={"open": 1e-200, "close": 1e-200, "high": 1e-200, "low": 1e-200}) for bar in rows]
    else:
        rows = [bar.model_copy(update={"volume": 1e200}) for bar in rows]
    data.bars["AAA"] = rows
    evidence = rows[0].model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    action = CorporateAction(**evidence, action="SPLIT", effective_date=rows[2].session, ratio=1e200)
    data = data.model_copy(update={"actions": [action]})
    validate_dataset(data)
    with pytest.raises(ValueError, match="split-adjusted history"):
        _causal_history(data, 4)
