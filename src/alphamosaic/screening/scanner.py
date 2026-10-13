"""Validated factors -> percentile ranking -> risk filter -> research queue."""

import hashlib
import json
from datetime import datetime

import pandas as pd

from alphamosaic.core.contracts import DataBatch, FactorEvidence, OpportunityCandidate, Status
from alphamosaic.data.validation import validate_batch
from alphamosaic.factors.engine import FactorEngine
from alphamosaic.portfolio.risk import assess_risk
from alphamosaic.screening.archetypes import OpportunityArchetypeRegistry


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
        qqqm: DataBatch | None = None,
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
            and not validate_batch(benchmark.identity, benchmark.bars, cutoff, purpose="PRICE_BENCHMARK")
            else []
        )
        q_reference = qqqm.bars if qqqm and qqqm.status == Status.OK and not validate_batch(qqqm.identity, qqqm.bars, cutoff, purpose="PRICE_BENCHMARK") else []
        for symbol, batch in batches.items():
            flags = validate_batch(batch.identity, batch.bars, cutoff)
            if batch.status != Status.OK:
                flags.append(batch.status.value)
            if batch.fundamentals is not None and batch.fundamentals.known_at > cutoff:
                flags.append("FUTURE_FUNDAMENTALS")
            if flags:
                excluded[symbol] = flags
                continue
            factors = engine.calculate(batch.bars, reference, batch.fundamentals, q_reference, cutoff)
            risk = assess_risk(symbol, factors)
            if not risk.review_allowed:
                excluded[symbol] = risk.flags
                continue
            eligible[symbol] = factors
        ranked = CandidateRanker().rank(eligible)
        candidates = []
        archetypes = OpportunityArchetypeRegistry()
        research_scores: dict[str, float] = {}
        # Fixed total weight penalises missing inputs. The original baseline
        # score remains available verbatim and is never relabelled as improved.
        weights = {**CandidateRanker.WEIGHTS, "relative_strength_qqqm_63d": 0.1, "quality_roe": 0.1, "value_earnings_yield": 0.1, "growth_revenue": 0.1}
        frame = pd.DataFrame.from_dict(eligible, orient="index")
        if eligible:
            for symbol in eligible:
                research_scores[symbol] = sum(
                    float(frame[name].rank(pct=True, ascending=weight > 0).loc[symbol]) * abs(weight)
                    for name, weight in weights.items()
                    if eligible[symbol].get(name) is not None
                ) / sum(abs(weight) for weight in weights.values())
        research_ranks = {symbol: rank for rank, (symbol, _) in enumerate(sorted(research_scores.items(), key=lambda pair: (-pair[1], pair[0])), 1)}
        for rank, (symbol, score) in enumerate(ranked[:top], 1):
            batch = batches[symbol]
            assert batch.identity is not None
            factors = eligible[symbol]
            factor_evidence = {}
            for name, value in factors.items():
                dependency = batch
                group = "PRICE"
                if name.startswith("relative_strength_spy") or name == "market_regime":
                    dependency = benchmark
                elif name.startswith("relative_strength_qqqm"):
                    dependency = qqqm
                elif name.startswith("quality"):
                    group = "QUALITY"
                elif name.startswith("value"):
                    group = "VALUE"
                elif name.startswith("growth"):
                    group = "GROWTH"
                elif "volatility" in name or name == "max_drawdown":
                    group = "RISK"
                elif "volume" in name or "liquidity" in name:
                    group = "LIQUIDITY"
                fundamental = batch.fundamentals if group in {"QUALITY", "VALUE", "GROWTH"} else None
                source = fundamental.source if fundamental else "MISSING" if group in {"QUALITY", "VALUE", "GROWTH"} else dependency.bars[-1].source if dependency and dependency.bars else "MISSING"
                known = fundamental.known_at if fundamental else max((bar.known_at for bar in dependency.bars), default=cutoff) if dependency else cutoff
                fingerprint = hashlib.sha256(json.dumps({"symbol": symbol, "factor": name, "value": value, "source": source, "known_at": known.isoformat()}, sort_keys=True).encode()).hexdigest()
                factor_evidence[name] = FactorEvidence(
                    value=value, source=source, as_of=cutoff, known_at=known,
                    status="AVAILABLE" if value is not None else "MISSING",
                    missing_reason=None if value is not None else "dependency missing, invalid, or not date/adjustment aligned",
                    evidence_id=fingerprint, group=group,
                    independence="SHARED_FINANCIAL_FILING" if group in {"QUALITY", "VALUE", "GROWTH"} else "SHARED_PRICE_SERIES",
                )
            effective = sum(abs(weight) for name, weight in weights.items() if factors.get(name) is not None)
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
                    archetypes=[item.value for item in archetypes.categorize(factors)],
                    factor_evidence=factor_evidence,
                    effective_factor_weight=effective,
                    factor_coverage=effective / sum(abs(weight) for weight in weights.values()),
                    research_score=round(research_scores[symbol], 6),
                    research_rank=research_ranks[symbol],
                    ranking_status="DEGRADED_BENCHMARK" if factors["relative_strength_spy_63d"] is None or factors["relative_strength_qqqm_63d"] is None else "PRELIMINARY_RESEARCH_ONLY",
                )
            )
        return candidates, excluded, len(eligible)
