"""Deterministic research factors; scores have no probability interpretation."""

from datetime import datetime

import numpy as np

from alphamosaic.core.contracts import CompanyFundamentals, HistoricalBar


class FactorEngine:
    def calculate(
        self,
        bars: list[HistoricalBar],
        benchmark: list[HistoricalBar],
        fundamentals: CompanyFundamentals | None = None,
        qqqm: list[HistoricalBar] | None = None,
        research_cutoff: datetime | None = None,
    ) -> dict[str, float | None]:
        if len(bars) < 65:
            raise ValueError("at least 65 sessions required")
        close = np.array([bar.close for bar in bars], dtype=float)
        volume = (
            np.array([bar.volume for bar in bars[-20:]], dtype=float)
            if all(bar.volume is not None for bar in bars[-20:]) else None
        )
        returns = close[1:] / close[:-1] - 1
        relative = None
        # Point-in-time benchmark alignment: observations after the security's
        # last session are excluded even when a caller supplied a longer list.
        cutoff = bars[-1].session
        reference = {
            bar.session: bar.close for bar in benchmark if bar.session <= cutoff
            and (research_cutoff is None or bar.known_at <= research_cutoff)
        }
        first, last = bars[-64].session, bars[-1].session
        required_dates = [bar.session for bar in bars[-64:]]
        compatible = not benchmark or benchmark[-1].adjustment_policy == bars[-1].adjustment_policy
        if all(day in reference for day in required_dates) and compatible:
            relative = float(close[-1] / close[-64] - reference[last] / reference[first])
        q_reference = {bar.session: bar.close for bar in qqqm or [] if research_cutoff is None or bar.known_at <= research_cutoff}
        q_relative = None
        if qqqm and all(day in q_reference for day in required_dates) and qqqm[-1].adjustment_policy == bars[-1].adjustment_policy:
            q_relative = float(close[-1] / close[-64] - q_reference[last] / q_reference[first])
        fundamental_valid = fundamentals is not None and (research_cutoff is None or fundamentals.known_at <= research_cutoff)
        quality = fundamentals.return_on_equity if fundamentals is not None and fundamental_valid else None
        pe = fundamentals.pe_ratio if fundamentals is not None and fundamental_valid else None
        benchmark_window = [reference.get(bar.session) for bar in bars[-60:]]
        benchmark_window = [value for value in benchmark_window if value is not None]
        market_regime = None
        if len(benchmark_window) >= 60:
            market_regime = 1.0 if benchmark_window[-1] >= float(np.mean(benchmark_window)) else -1.0
        volume_ratio = (
            float(np.mean(volume[-5:]) / np.mean(volume[-20:]))
            if volume is not None and np.mean(volume[-20:]) > 0
            else None
        )
        volatility_20d = (
            float(np.std(returns[-20:], ddof=1) * np.sqrt(252))
            if len(returns) >= 20
            else None
        )
        return {
            "momentum_21d": float(close[-1] / close[-22] - 1),
            "momentum_63d": float(close[-1] / close[-64] - 1),
            "relative_strength_spy_63d": relative,
            "relative_strength_qqqm_63d": q_relative,
            "trend_20_60": float(np.mean(close[-20:]) / np.mean(close[-60:]) - 1),
            "volume_change_5_20": float(np.mean(volume[-5:]) / np.mean(volume[-20:]) - 1)
            if volume is not None and np.mean(volume[-20:]) > 0
            else None,
            # Canonical aliases consumed by opportunity archetypes. The
            # original fields remain for backwards compatibility.
            "volume_ratio": volume_ratio,
            "volatility_20d": volatility_20d,
            # 1 = benchmark above its 60-session mean, -1 = below, None when
            # no sufficiently complete, date-aligned benchmark exists.
            "market_regime": market_regime,
            "volatility_63d": float(np.std(returns[-63:], ddof=1) * np.sqrt(252)),
            "max_drawdown": float(np.min(close / np.maximum.accumulate(close) - 1)),
            "liquidity_20d_usd": float(np.mean(close[-20:] * volume)) if volume is not None else None,
            "quality_roe": quality,
            "growth_revenue": fundamentals.revenue_growth if fundamentals is not None and fundamental_valid else None,
            "value_earnings_yield": 1 / pe if pe is not None and pe > 0 else None,
        }
