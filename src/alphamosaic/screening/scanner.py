"""Validated factors -> percentile ranking -> risk filter -> research queue."""

from datetime import datetime

import pandas as pd

from alphamosaic.core.contracts import DataBatch, OpportunityCandidate, Status
from alphamosaic.data.validation import validate_batch
from alphamosaic.factors.engine import FactorEngine
from alphamosaic.portfolio.risk import assess_risk


class CandidateRanker:
    WEIGHTS = {
        "momentum_63d": 0.25,
        "relative_strength_spy_63d": 0.2,
        "trend_20_60": 0.15,
        "liquidity_20d_usd": 0.10,
        "volatility_63d": -0.15,
        "max_drawdown": 0.15,
    }

    def rank(self, factors: dict[str, dict[str, float | None]]) -> list[tuple[str, float]]:
        if not factors:
            return []
        frame = pd.DataFrame.from_dict(factors, orient="index")
        scores = pd.Series(0.0, index=frame.index)
        total = pd.Series(0.0, index=frame.index)
        for name, weight in self.WEIGHTS.items():
            values = frame[name].rank(pct=True, ascending=weight > 0)
            scores += values.fillna(0) * abs(weight)
            total += values.notna().astype(float) * abs(weight)
        # Missing factors are excluded from the denominator, never invented.
        scores = scores / total.replace(0, float("nan"))
        return sorted(
            ((str(symbol), float(value)) for symbol, value in scores.dropna().items()),
            key=lambda row: (-row[1], row[0]),
        )


class ResearchQueue:
    def build(self, candidates: list[OpportunityCandidate], limit: int = 5) -> list[str]:
        return [candidate.ticker for candidate in candidates[:limit]]


class OpportunityScanner:
    def scan(
        self,
        batches: dict[str, DataBatch],
        benchmark: DataBatch | None,
        cutoff: datetime,
        top: int = 10,
    ) -> tuple[list[OpportunityCandidate], dict[str, list[str]], int]:
        if not 1 <= top <= 10:
            raise ValueError("top must be 1..10")
        eligible: dict[str, dict[str, float | None]] = {}
        excluded: dict[str, list[str]] = {}
        engine = FactorEngine()
        reference = (
            benchmark.bars
            if benchmark
            and benchmark.status == Status.OK
            and not any(bar.known_at > cutoff for bar in benchmark.bars)
            else []
        )
        for symbol, batch in batches.items():
            flags = validate_batch(batch.identity, batch.bars, cutoff)
            if batch.status != Status.OK:
                flags.append(batch.status.value)
            if batch.fundamentals is not None and batch.fundamentals.known_at > cutoff:
                flags.append("FUTURE_FUNDAMENTALS")
            if flags:
                excluded[symbol] = flags
                continue
            factors = engine.calculate(batch.bars, reference, batch.fundamentals)
            risk = assess_risk(symbol, factors)
            if not risk.review_allowed:
                excluded[symbol] = risk.flags
                continue
            eligible[symbol] = factors
        ranked = CandidateRanker().rank(eligible)
        candidates = []
        for rank, (symbol, score) in enumerate(ranked[:top], 1):
            batch = batches[symbol]
            assert batch.identity is not None
            factors = eligible[symbol]
            risks = [
                "HEURISTIC_SCORE_NOT_RETURN_PROBABILITY",
                "NO_VALIDATED_ALPHA",
                "CURRENT_UNIVERSE_SURVIVORSHIP",
                "CORPORATE_ACTIONS_NOT_VERIFIED",
                "DELISTING_HISTORY_NOT_VERIFIED",
            ]
            if batch.bars[-1].adjustment_policy == "UNKNOWN":
                risks.append("ADJUSTMENT_POLICY_UNKNOWN")
            candidates.append(
                OpportunityCandidate(
                    ticker=symbol,
                    rank=rank,
                    score=round(score, 6),
                    factors=factors,
                    reasons=[
                        f"63-session price momentum: {factors['momentum_63d']:.2%}",
                        f"Trend 20/60: {factors['trend_20_60']:.2%}",
                    ],
                    risks=risks,
                    data_timestamp=batch.bars[-1].observed_at,
                    source=batch.bars[-1].source,
                    missing_fields=[key for key, value in factors.items() if value is None],
                    research_priority="HIGH" if rank <= 3 else "NORMAL",
                    identity=batch.identity,
                    data_quality=batch.bars[-1].data_quality,
                )
            )
        return candidates, excluded, len(eligible)
