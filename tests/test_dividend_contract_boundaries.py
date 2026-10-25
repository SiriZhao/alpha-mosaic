"""Payment-model migration and benchmark semantics independent of equal NAV paths."""

from datetime import timedelta, timezone

import pytest
from test_independent_dividend_payment import FixedTargets, fixture_data, replay

from alphamosaic.backtesting.models import (
    DividendEntitlement,
    DividendPayment,
    ReplayConfig,
    payment_replay_config,
)
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.evaluation.analytics import analyze
from alphamosaic.evaluation.weekly import analyze_weekly
from alphamosaic.experiments.runner import ExperimentConfig


@pytest.mark.parametrize("frequency", ["daily", "weekly"])
def test_both_daily_and_weekly_benchmark_gates_reject_different_dividend_models_even_with_equal_nav(frequency: str) -> None:
    data = fixture_data(through="2024-01-19")
    modern = replay(data)
    legacy = PaperReplayEngine().run(data, FixedTargets({data.bars["AAA"][0].session: {"AAA": 1}}), "independent-frozen-targets",
        ReplayConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, rebalance_sessions=1, max_volume_fraction=1))
    assert [point.nav for point in modern.equity] == [point.nav for point in legacy.equity]
    function = analyze if frequency == "daily" else analyze_weekly
    blocked = function(modern, benchmark_result=legacy, return_basis="RAW_WITH_CASH_ACTIONS", benchmark_return_basis="RAW_WITH_CASH_ACTIONS")
    assert blocked["benchmark_status"] == "BLOCKED_ACCOUNTING_MODEL_MISMATCH"
    assert blocked["metrics"]["beta"] is None
    assert blocked["metrics"]["alpha_annualized_arithmetic"] is None
    assert blocked["metrics"]["tracking_error"] is None
    assert blocked["metrics"]["information_ratio"] is None


def test_old_missing_config_fields_remain_legacy_while_new_experiment_defaults_are_explicit() -> None:
    legacy = ReplayConfig.model_validate({"initial_cash": 1000})
    assert legacy.accounting_schema_version == 1 and legacy.dividend_accounting == "LEGACY_EX_DATE_CASH"
    modern = ExperimentConfig(dataset_id="a" * 64).replay
    assert modern.accounting_schema_version == 2 and modern.dividend_accounting == "PAY_DATE_RECEIVABLE"
    with pytest.raises(ValueError):
        ReplayConfig.model_validate({"accounting_schema_version": 2, "dividend_accounting": "LEGACY_EX_DATE_CASH"})
    with pytest.raises(ValueError):
        payment_replay_config(accounting_schema_version=1)


def test_entitlement_and_payment_timestamps_reject_naive_and_normalize_aware_offsets() -> None:
    result = replay(fixture_data())
    entitlement, payment = result.dividend_entitlements[0], result.dividend_payments[0]
    for field in ("accrued_at", "available_at"):
        value = getattr(entitlement, field)
        assert value is not None
        with pytest.raises(ValueError, match="aware"):
            DividendEntitlement.model_validate({**entitlement.model_dump(), field: value.replace(tzinfo=None)})
    with pytest.raises(ValueError, match="aware"):
        DividendPayment.model_validate({**payment.model_dump(), "at": payment.at.replace(tzinfo=None)})
    shifted = payment.at.astimezone(timezone(timedelta(hours=8)))
    assert DividendPayment.model_validate({**payment.model_dump(), "at": shifted}).at == payment.at
