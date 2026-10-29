"""Generated allocation constraints supplement independent ledger scenarios."""

import math

from hypothesis import given, settings
from hypothesis import strategies as hs

from alphamosaic.backtesting.models import ReplayConfig
from alphamosaic.portfolio.construction import constrain_weights


@settings(max_examples=60, deadline=None, derandomize=True)
@given(
    hs.lists(hs.floats(min_value=0, max_value=1, allow_nan=False), min_size=1, max_size=10),
    hs.floats(min_value=.01, max_value=1, allow_nan=False),
    hs.floats(min_value=0, max_value=.9, allow_nan=False),
)
def test_cash_and_single_asset_caps_hold_for_generated_allocations(values: list[float], cap: float, cash: float) -> None:
    total = max(1.0, sum(values))
    weights = {f"A{i}": value / total for i, value in enumerate(values)}
    config = ReplayConfig(max_single_weight=cap, min_cash_buffer=cash)
    constrained, _ = constrain_weights(weights, config)
    assert sum(constrained.values()) <= 1 - cash + 1e-10
    assert all(math.isfinite(value) and 0 < value <= cap + 1e-10 for value in constrained.values())
    assert all(constrained[symbol] <= weights[symbol] + 1e-10 for symbol in constrained)
