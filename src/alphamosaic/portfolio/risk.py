"""Risk filters and review-only sizing; no order generation."""

from alphamosaic.core.contracts import RiskAssessment


def assess_risk(symbol: str, factors: dict[str, float | None]) -> RiskAssessment:
    flags: list[str] = []
    volatility = factors.get("volatility_63d")
    liquidity = factors.get("liquidity_20d_usd")
    drawdown = factors.get("max_drawdown")
    if volatility is None or liquidity is None or drawdown is None:
        flags.append("MISSING_RISK_INPUT")
    if liquidity is not None and liquidity < 2_000_000:
        flags.append("ILLIQUID")
    if volatility is not None and volatility > 1:
        flags.append("EXTREME_VOLATILITY")
    if drawdown is not None and drawdown < -0.5:
        flags.append("DEEP_DRAWDOWN")
    return RiskAssessment(
        symbol=symbol,
        review_allowed=not flags,
        flags=flags,
        maximum_review_weight=min(0.05, 0.01 / volatility)
        if not flags and volatility and volatility > 0
        else 0,
    )


def assess_weights(weights: dict[str, float], maximum: float = 0.10) -> list[str]:
    import math

    if not 0 < maximum <= 1:
        raise ValueError("invalid maximum weight")
    if any(not math.isfinite(value) or value < 0 for value in weights.values()):
        raise ValueError("finite long-only weights required")
    flags = [f"CONCENTRATION:{symbol}" for symbol, weight in weights.items() if weight > maximum]
    if sum(weights.values()) > 1 + 1e-9:
        flags.append("LEVERAGE_NOT_ALLOWED")
    return flags
