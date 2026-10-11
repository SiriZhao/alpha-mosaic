"""Transparent opportunity archetypes; these are research hypotheses, not forecasts."""

from alphamosaic.core.contracts import OpportunityArchetype, OpportunityArchetypeSpec


class OpportunityArchetypeRegistry:
    _specs = (
        OpportunityArchetypeSpec(
            name=OpportunityArchetype.QUALITY_GROWTH,
            suitable_regimes=["expanding earnings", "stable or falling rates"],
            required_data=["revenue growth", "margin", "ROE/ROIC", "free cash flow"],
            prerequisites=["verified profitability and positive operating trend"],
            failure_risks=["multiple compression", "growth deceleration", "accounting revisions"],
            holding_period="6-24 months", research_priority="HIGH",
        ),
        OpportunityArchetypeSpec(
            name=OpportunityArchetype.EARNINGS_REVISION,
            suitable_regimes=["active estimate revision cycle"],
            required_data=["dated analyst estimates", "revision history", "earnings date"],
            prerequisites=["point-in-time estimate source"],
            failure_risks=["estimate noise", "guidance miss", "crowded positioning"],
            holding_period="1-6 months", research_priority="HIGH",
        ),
        OpportunityArchetypeSpec(
            name=OpportunityArchetype.VALUATION_DISLOCATION,
            suitable_regimes=["fundamental mispricing"],
            required_data=["price", "earnings or cash flow", "peer valuation"],
            prerequisites=["comparable valuation evidence and durable fundamentals"],
            failure_risks=["value trap", "balance sheet stress", "catalyst absence"],
            holding_period="6-36 months", research_priority="NORMAL",
        ),
        OpportunityArchetypeSpec(
            name=OpportunityArchetype.MOMENTUM_BREAKOUT,
            suitable_regimes=["persistent trend and adequate liquidity"],
            required_data=["adjusted price", "volume", "volatility", "market regime"],
            prerequisites=["fresh trend and verified liquidity"],
            failure_risks=["gap reversal", "slippage", "regime change"],
            holding_period="2-16 weeks", research_priority="HIGH",
        ),
        OpportunityArchetypeSpec(
            name=OpportunityArchetype.EVENT_CATALYST,
            suitable_regimes=["known corporate event"],
            required_data=["dated event", "issuer disclosure", "price reaction"],
            prerequisites=["primary-source event evidence"],
            failure_risks=["event cancellation", "binary outcome", "information decay"],
            holding_period="days to 3 months", research_priority="HIGH",
        ),
        OpportunityArchetypeSpec(
            name=OpportunityArchetype.MEAN_REVERSION,
            suitable_regimes=["range-bound or oversold market"],
            required_data=["drawdown", "volatility", "stabilisation evidence", "liquidity"],
            prerequisites=["drawdown plus independent stabilisation signal"],
            failure_risks=["continuing deterioration", "falling knife", "short horizon noise"],
            holding_period="1-12 weeks", research_priority="NORMAL",
        ),
    )

    def specs(self) -> list[OpportunityArchetypeSpec]:
        return list(self._specs)

    def categorize(self, factors: dict[str, float | None]) -> list[OpportunityArchetype]:
        result: list[OpportunityArchetype] = []
        momentum = factors.get("momentum_63d")
        trend = factors.get("trend_20_60")
        drawdown = factors.get("max_drawdown")
        roe = factors.get("quality_roe")
        earnings_yield = factors.get("value_earnings_yield")
        if momentum is not None and trend is not None and momentum > 0 and trend > 0:
            result.append(OpportunityArchetype.MOMENTUM_BREAKOUT)
        if drawdown is not None and drawdown < -0.20:
            # Categorisation only; no claim that stabilisation exists.
            result.append(OpportunityArchetype.MEAN_REVERSION)
        if roe is not None and roe > 0 and momentum is not None and momentum > 0:
            result.append(OpportunityArchetype.QUALITY_GROWTH)
        if earnings_yield is not None and earnings_yield > 0.05:
            result.append(OpportunityArchetype.VALUATION_DISLOCATION)
        return result or [OpportunityArchetype.MOMENTUM_BREAKOUT]
