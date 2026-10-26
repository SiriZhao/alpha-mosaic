"""Return conventions describe the actual portfolio inputs, never unrelated assets."""

from collections.abc import Mapping, Sequence

from alphamosaic.core.contracts import HistoricalBar


def market_return_basis(bars: Mapping[str, Sequence[HistoricalBar]]) -> str | None:
    """Keep mixed/absent conventions unknown; evidence qualification is separate."""
    if not bars or any(not rows for rows in bars.values()):
        return None
    policies = {row.adjustment_policy for rows in bars.values() for row in rows}
    if len(policies) != 1:
        return None
    return {"RAW": "RAW_WITH_CASH_ACTIONS", "SPLIT": "PRICE", "TOTAL_RETURN": "TOTAL_RETURN"}.get(next(iter(policies)))
