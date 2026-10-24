"""Deterministic cash-only allocation constraints, without fitted optimizers."""

import math

from alphamosaic.backtesting.models import ReplayConfig


def constrain_weights(
    weights: dict[str, float], config: ReplayConfig
) -> tuple[dict[str, float], list[str]]:
    """Cap targets and retain unallocated capital as cash; never renormalize above caps."""
    if any(not math.isfinite(v) or v < 0 for v in weights.values()):
        raise ValueError("finite long-only weights required")
    if sum(weights.values()) > 1 + 1e-10:
        raise ValueError("no leverage permitted")
    if len([v for v in weights.values() if v > 0]) > config.max_positions:
        raise ValueError("position limit exceeded")
    result = {s: min(v, config.max_single_weight) for s, v in weights.items() if v > 0}
    flags = (
        ["SINGLE_ASSET_TARGET_CAPPED"] if any(weights[s] != v for s, v in result.items()) else []
    )
    total = sum(result.values())
    ceiling = min(config.max_gross_exposure, 1 - config.min_cash_buffer)
    if total > ceiling:
        result = {s: v * ceiling / total for s, v in result.items()}
        flags.append("GROSS_TARGET_CAPPED_FOR_CASH")
    return result, flags


def inverse_volatility(volatilities: dict[str, float]) -> dict[str, float]:
    """Inverse volatility is a diagonal risk-budget approximation, not risk parity."""
    if any(not math.isfinite(v) or v < 0 for v in volatilities.values()):
        raise ValueError("finite nonnegative volatilities required")
    scores = {s: 1 / v for s, v in volatilities.items() if v > 0}
    total = sum(scores.values())
    return {s: v / total for s, v in scores.items()} if total else {}
