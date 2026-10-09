"""Deterministic research factors; scores have no probability interpretation."""

import numpy as np

from alphamosaic.core.contracts import CompanyFundamentals, HistoricalBar


class FactorEngine:
    def calculate(
        self,
        bars: list[HistoricalBar],
        benchmark: list[HistoricalBar],
        fundamentals: CompanyFundamentals | None = None,
    ) -> dict[str, float | None]:
        if len(bars) < 65:
            raise ValueError("at least 65 sessions required")
        close = np.array([bar.close for bar in bars], dtype=float)
        volume = np.array([bar.volume for bar in bars], dtype=float)
        returns = close[1:] / close[:-1] - 1
        relative = None
        reference = {bar.session: bar.close for bar in benchmark}
        first, last = bars[-64].session, bars[-1].session
        if first in reference and last in reference:
            relative = float(close[-1] / close[-64] - reference[last] / reference[first])
        quality = fundamentals.return_on_equity if fundamentals else None
        pe = fundamentals.pe_ratio if fundamentals else None
        return {
            "momentum_21d": float(close[-1] / close[-22] - 1),
            "momentum_63d": float(close[-1] / close[-64] - 1),
            "relative_strength_spy_63d": relative,
            "trend_20_60": float(np.mean(close[-20:]) / np.mean(close[-60:]) - 1),
            "volume_change_5_20": float(np.mean(volume[-5:]) / np.mean(volume[-20:]) - 1)
            if np.mean(volume[-20:]) > 0
            else None,
            "volatility_63d": float(np.std(returns[-63:], ddof=1) * np.sqrt(252)),
            "max_drawdown": float(np.min(close / np.maximum.accumulate(close) - 1)),
            "liquidity_20d_usd": float(np.mean(close[-20:] * volume[-20:])),
            "quality_roe": quality,
            "value_earnings_yield": 1 / pe if pe is not None and pe > 0 else None,
        }
