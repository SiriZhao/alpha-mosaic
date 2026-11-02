"""Model comments and missing provenance cannot become observed strategy inputs."""

import pytest

from alphamosaic.backtesting.models import DatedSignal, payment_replay_config
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.data.datasets import synthetic_demo


def signal(data, **changes) -> DatedSignal:
    return DatedSignal.model_validate({"symbol": "SPY", "source": "explicit-test-fixture",
        "evidence_id": "observed-quality-fixture", "known_at": data.bars["SPY"][0].known_at,
        "valid_until": data.cutoff, "value": 10, "metric": "quality", "pit_verified": True,
        "data_quality": "FIXTURE", "license_scope": "Synthetic test data only", **changes})


@pytest.mark.parametrize("quality", ["MODEL_INFERENCE", "MISSING", "UNKNOWN"])
def test_unobserved_numeric_signals_cannot_enter_a_replay(quality: str) -> None:
    data = synthetic_demo(30)
    data = data.model_copy(update={"signals": [signal(data, data_quality=quality)]})
    with pytest.raises(ValueError, match="signal evidence"):
        PaperReplayEngine().run(data, StrategyRegistry().get("quality"), "quality", payment_replay_config())


@pytest.mark.parametrize("quality", ["MODEL_INFERENCE", "MISSING", "UNKNOWN", "HISTORICAL"])
def test_strategy_kernel_cannot_promote_unobserved_or_mixed_values_by_a_pit_flag_alone(quality: str) -> None:
    data = synthetic_demo(30)
    history = {symbol: bars[:1] for symbol, bars in data.bars.items()}
    target = StrategyRegistry().get("quality").allocation(history, [signal(data, data_quality=quality)],
        data.bars["SPY"][0].known_at, payment_replay_config())
    assert target.weights == {}


def test_strict_signal_requires_verified_availability() -> None:
    data = synthetic_demo(30)
    data = data.model_copy(update={"signals": [signal(data, pit_verified=False)]})
    with pytest.raises(ValueError, match="signal.*PIT"):
        PaperReplayEngine().run(data, StrategyRegistry().get("quality"), "quality", payment_replay_config())


def test_observed_signal_cannot_be_mixed_into_a_fixture_price_dataset() -> None:
    data = synthetic_demo(30)
    data = data.model_copy(update={"signals": [signal(data, data_quality="HISTORICAL")]})
    with pytest.raises(ValueError, match="fixture and observed signal"):
        PaperReplayEngine().run(data, StrategyRegistry().get("quality"), "quality", payment_replay_config())


@pytest.mark.parametrize("changes", [{"source": ""}, {"evidence_id": "   "}])
def test_empty_source_identity_does_not_qualify_an_observation(changes) -> None:
    data = synthetic_demo(30)
    data = data.model_copy(update={"signals": [signal(data, **changes)]})
    with pytest.raises(ValueError, match="signal.*source"):
        PaperReplayEngine().run(data, StrategyRegistry().get("quality"), "quality", payment_replay_config())


def test_explicit_observed_fixture_signal_still_drives_its_predeclared_baseline() -> None:
    data = synthetic_demo(30)
    data = data.model_copy(update={"signals": [signal(data)]})
    result = PaperReplayEngine().run(data, StrategyRegistry().get("quality"), "quality", payment_replay_config())
    assert result.fills and all(fill.symbol == "SPY" for fill in result.fills)
    assert result.signals[0].evidence_ids == ["observed-quality-fixture"]
