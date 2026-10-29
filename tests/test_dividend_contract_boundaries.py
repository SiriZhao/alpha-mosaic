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
from alphamosaic.core.contracts import DataQuality
from alphamosaic.evaluation.analytics import analyze
from alphamosaic.evaluation.trades import analyze_trades
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


def test_legacy_cash_credit_cannot_qualify_as_a_strict_real_dividend_replay() -> None:
    # Schema-boundary counterexample only: these are synthetic test values, not
    # acquired historical observations or an accepted real-data experiment.
    fixture = fixture_data()
    data = fixture.model_copy(update={
        "bars": {symbol: [bar.model_copy(update={"data_quality": DataQuality.HISTORICAL}) for bar in bars]
                 for symbol, bars in fixture.bars.items()},
        "actions": [action.model_copy(update={"data_quality": DataQuality.HISTORICAL}) for action in fixture.actions],
    })
    with pytest.raises(ValueError, match="legacy.*strict real"):
        PaperReplayEngine().run(data, FixedTargets({data.bars["AAA"][0].session: {"AAA": 1}}), "independent-frozen-targets",
            ReplayConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, rebalance_sessions=1, max_volume_fraction=1))


@pytest.mark.parametrize("quality", [DataQuality.MODEL_INFERENCE, DataQuality.MISSING])
def test_inference_or_missing_action_evidence_cannot_create_dividend_income(quality: DataQuality) -> None:
    with pytest.raises(ValueError, match="corporate action evidence"):
        replay(fixture_data(dividend_changes={"data_quality": quality}))


def test_observed_action_evidence_cannot_be_mixed_into_synthetic_prices() -> None:
    with pytest.raises(ValueError, match="fixture and observed corporate"):
        replay(fixture_data(dividend_changes={"data_quality": DataQuality.HISTORICAL}))


@pytest.mark.parametrize("quality", [DataQuality.MODEL_INFERENCE, DataQuality.MISSING, DataQuality.HISTORICAL])
def test_independent_reconstruction_refuses_unqualified_action_evidence(quality: DataQuality) -> None:
    data = fixture_data()
    valid = replay(data)
    altered = data.model_copy(update={"actions": [action.model_copy(update={"data_quality": quality}) for action in data.actions]})
    assert analyze_trades(valid, altered)["status"] == "BLOCKED"
