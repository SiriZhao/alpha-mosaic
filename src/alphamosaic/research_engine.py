"""Candidate research orchestration across deterministic and optional sources."""

from datetime import UTC, datetime, timedelta
from typing import cast

from alphamosaic.core.contracts import (
    DataQuality,
    FusionSignal,
    ResearchDecision,
    ResearchOutcome,
    SignalDirection,
    Status,
    utc_now,
)
from alphamosaic.factors.engine import FactorEngine
from alphamosaic.integrations.danelfin import DanelfinAdapter
from alphamosaic.integrations.tradingagents import Profile, TradingAgentsAdapter
from alphamosaic.providers.protocol import DataProvider
from alphamosaic.signals_fusion import SignalFusionEngine


class ResearchEngine:
    def __init__(self, provider: DataProvider, home):
        self.provider = provider
        self.tradingagents = TradingAgentsAdapter(home)
        self.danelfin = DanelfinAdapter()

    def _technical_signal(self, symbol: str, batch, benchmark) -> FusionSignal:
        factors = FactorEngine().calculate(batch.bars, benchmark.bars if benchmark else [])
        momentum = factors["momentum_63d"]
        direction = SignalDirection.BULLISH if momentum is not None and momentum > 0 else SignalDirection.BEARISH
        return FusionSignal(
            source="AlphaMosaic deterministic factors",
            symbol=symbol,
            direction=direction,
            strength=min(abs(float(momentum or 0)), 1.0),
            reliability=0.5,
            horizon="weeks-to-months",
            data_quality=batch.bars[-1].data_quality,
            evidence_ids=[f"{symbol}:ohlcv:{batch.evidence[0].completed_at.isoformat()}"],
            observed_at=batch.bars[-1].observed_at,
            known_at=batch.evidence[0].known_at,
            rationale=[f"63-session momentum {float(momentum or 0):.2%}"],
        )

    @staticmethod
    def _fundamental_signal(symbol: str, batch) -> FusionSignal | None:
        fundamentals = batch.fundamentals
        if fundamentals is None:
            return None
        positive = (fundamentals.net_income is not None and fundamentals.net_income > 0) or (
            fundamentals.return_on_equity is not None and fundamentals.return_on_equity > 0
        )
        return FusionSignal(
            source="OpenBB/Nasdaq fundamentals",
            symbol=symbol,
            direction=SignalDirection.BULLISH if positive else SignalDirection.NEUTRAL,
            strength=0.5 if positive else 0.0,
            reliability=0.35,
            horizon="quarters",
            data_quality=fundamentals.data_quality,
            evidence_ids=[f"{symbol}:fundamentals:{fundamentals.known_at.isoformat()}"],
            observed_at=fundamentals.observed_at,
            known_at=fundamentals.known_at,
            rationale=[
                "Positive reported net income/ROE" if positive else "Fundamental fields do not support a bullish view",
                *[f"Missing: {field}" for field in fundamentals.missing_fields],
            ],
        )

    def research(self, symbols: list[str], profile: str = "FAST") -> list[ResearchDecision]:
        if not symbols:
            return []
        if len(symbols) > 5:
            raise ValueError("deep research is limited to five candidates per run")
        end = datetime.now(UTC).date()
        start = end - timedelta(days=190)
        batches = {symbol: self.provider.history(symbol, start, end) for symbol in dict.fromkeys(symbols)}
        benchmark = self.provider.history("SPY", start, end)
        decisions: list[ResearchDecision] = []
        for symbol, batch in batches.items():
            outcomes: list[ResearchOutcome] = []
            signals: list[FusionSignal] = []
            if batch.status == Status.OK and len(batch.bars) >= 65 and batch.identity is not None:
                signals.append(self._technical_signal(symbol, batch, benchmark))
                fundamental = self._fundamental_signal(symbol, batch)
                if fundamental:
                    signals.append(fundamental)
            else:
                outcomes.append(ResearchOutcome(
                    symbol=symbol, status=batch.status, source="OpenBB/Nasdaq",
                    diagnostics=["candidate did not pass history/identity gate"],
                    requested_at=batch.evidence[0].requested_at,
                    completed_at=batch.evidence[0].completed_at,
                ))
            agent = self.tradingagents.research(symbol, cast(Profile, profile))
            outcomes.append(agent)
            if agent.verdict:
                signals.append(FusionSignal(
                    source="TradingAgents v0.6.0",
                    symbol=symbol,
                    direction=SignalDirection(agent.verdict.verdict),
                    strength=None,
                    reliability=0.25,
                    horizon=agent.verdict.time_horizon,
                    data_quality=DataQuality.MODEL_INFERENCE,
                    evidence_ids=[f"{symbol}:tradingagents:{agent.completed_at.isoformat()}"],
                    observed_at=agent.completed_at,
                    known_at=agent.completed_at,
                    rationale=agent.verdict.rationale[:2],
                ))
            score = self.danelfin.score_sync(symbol)
            danelfin_status = Status(score["status"])
            outcomes.append(ResearchOutcome(
                symbol=symbol, status=danelfin_status, source="Danelfin MCP",
                diagnostics=score.get("diagnostics", []), requested_at=utc_now(), completed_at=utc_now(),
            ))
            fused = SignalFusionEngine().fuse(symbol, signals)
            if batch.bars:
                candidate_reason = ["Passed deterministic history, identity and risk gates"]
                ref_price = batch.bars[-1].close if batch.bars[-1].observed_at >= utc_now() - timedelta(days=5) else None
            else:
                candidate_reason = ["Did not pass the deterministic data gate"]
                ref_price = None
            decisions.append(ResearchDecision(
                symbol=symbol,
                candidate_reason=candidate_reason,
                upside_drivers=[*fused.rationale[:3]],
                fundamental_support="Available fields reviewed; missing fields remain unknown" if batch.fundamentals else "NOT_AVAILABLE",
                valuation_view="NOT_AVAILABLE: no verified valuation field",
                trend_view="Supported by deterministic factors" if fused.direction == SignalDirection.BULLISH else "Not confirmed",
                catalysts=["No catalyst feed connected"],
                downside_risks=[*fused.risk_flags, "Provider adjustment policy/corporate actions may be incomplete"],
                invalidation_conditions=["New evidence invalidates identity, PIT, or risk checks", "Trend regime changes"],
                action="DEEP_RESEARCH" if fused.direction in {SignalDirection.BULLISH, SignalDirection.BEARISH} else "OBSERVE",
                trigger_conditions=["Require fresh, verified price and catalyst evidence before any trade research"],
                entry_reference_price=ref_price,
                holding_horizon=fused.horizon,
                fused_signal=fused,
                outcomes=outcomes,
            ))
        return decisions
