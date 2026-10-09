"""Evidence-aware signal fusion; no probabilistic return claims."""

from datetime import UTC, datetime

from alphamosaic.core.contracts import DataQuality, FusedSignal, FusionSignal, SignalDirection


class SignalFusionEngine:
    def fuse(self, symbol: str, signals: list[FusionSignal], cutoff: datetime | None = None) -> FusedSignal:
        cutoff = (cutoff or datetime.now(UTC)).astimezone(UTC)
        valid = [
            signal for signal in signals
            if signal.symbol == symbol and signal.known_at <= cutoff and signal.observed_at <= cutoff
        ]
        reasons: list[str] = []
        conflicts: list[str] = []
        evidence_ids: list[str] = []
        for signal in signals:
            if signal.symbol != symbol:
                conflicts.append(f"identity mismatch from {signal.source}")
            elif signal.known_at > cutoff or signal.observed_at > cutoff:
                conflicts.append(f"future information from {signal.source}")
        deduped: list[FusionSignal] = []
        seen_evidence: set[str] = set()
        for signal in valid:
            overlap = set(signal.evidence_ids) & seen_evidence
            if overlap:
                conflicts.append(f"dependent evidence overlap from {signal.source}: {sorted(overlap)}")
                continue
            deduped.append(signal)
            seen_evidence.update(signal.evidence_ids)
            evidence_ids.extend(signal.evidence_ids)
        directions = {signal.direction for signal in deduped if signal.direction not in {
            SignalDirection.NEUTRAL, SignalDirection.INSUFFICIENT_EVIDENCE
        }}
        if len(directions) > 1:
            direction = SignalDirection.CONFLICTED
            conflicts.extend(sorted({item.value for item in directions}))
        elif not deduped or not directions:
            direction = SignalDirection.INSUFFICIENT_EVIDENCE
        else:
            direction = next(iter(directions))
        sources = [signal.source for signal in deduped]
        for signal in deduped:
            reasons.extend(f"{signal.source}: {reason}" for reason in signal.rationale)
        confidence = None
        if deduped and direction not in {SignalDirection.CONFLICTED, SignalDirection.INSUFFICIENT_EVIDENCE}:
            qualities = [signal for signal in deduped if signal.data_quality in {
                DataQuality.REAL, DataQuality.HISTORICAL, DataQuality.DELAYED
            }]
            if qualities:
                confidence = round(sum((item.strength or 0) * (item.reliability or 0.5) for item in qualities) / len(qualities), 4)
        if conflicts:
            reasons.append("Sources are dependent or disagree; confidence is reduced")
        return FusedSignal(
            symbol=symbol,
            direction=direction,
            research_confidence=confidence,
            rationale=reasons or ["No time-valid, independently attributable signal"],
            conflicts=conflicts,
            sources=sources,
            horizon=next((item.horizon for item in deduped if item.horizon), None),
            risk_flags=["NO_VALIDATED_ALPHA"] if confidence is not None else ["INSUFFICIENT_EVIDENCE"],
            evidence_ids=evidence_ids,
        )
