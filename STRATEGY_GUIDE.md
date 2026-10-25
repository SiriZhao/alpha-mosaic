# Fixed baseline strategies

## Calendar-week rules (continuation)

The registry also includes weekly_equal_weight, weekly_momentum and weekly_trend. They require an explicit ReplayConfig.decision_frequency=WEEKLY. WeeklyStrategyParameters records lookback_weeks (default12), trend_short_weeks4 and trend_long_weeks12. A constructor cannot override the parameters recorded in the replay configuration. Bounds are2..104 weeks with short<long. Registry callers and the terminal use the recorded configuration as the sole authority.

Signals are scheduled at the actual last XNYS session of each natural week, including holiday-shortened weeks, and use only complete available weekly bars. Fills still use the canonical daily simulator at a later eligible open. A five-session rebalance is not called a calendar week. RAW corporate-action history affecting the weekly research interval is rejected until an explicit adjustment model qualifies it. Weekly return sampling is separately disclosed and does not transform a daily decision rule into a weekly strategy.

Registry API: `Strategy.allocation(history, signals, at, config) -> TargetAllocation`. Only available past bars and dated signals enter history. Engine owns constraints, orders, costs and accounting; strategies have no execution authority. `StrategyRegistry.list()` exposes the exact current formulas and state.

Hypotheses and requirements:

- buy_and_hold: eligible explicit basket provides a passive comparator; first allocation then hold. Current constituents still have survivor selection risk.
- equal_weight: periodically reset eligible asset weights; dispersion may diversify but turnover/cash drag can dominate.
- trend: SMA20>SMA60 and price>SMA60. Required60+history; whipsaw/range-bound markets can fail.
- momentum / cross_sectional_momentum: rank positive trailing lookback price return, equal weight selected assets. Required aligned multi-asset history; reversal/crowding/selection risk. Fixed default63 sessions, configured20..252.
- time_series_momentum: positive trailing price return per asset; flat otherwise. Trend persistence hypothesis; can miss rebounds.
- mean_reversion: fixed short-run negative deviation rule; rebounds are a hypothesis, persistent declines a failure mode. No search for a profitable threshold.
- volatility_targeting: past realized-volatility scale bounded long-only exposure toward configured annual target; no leverage. Estimation lag and volatility jumps can fail.
- risk_adjusted_momentum: positive momentum relative to realized risk; denominator instability and regime changes remain risks.
- low_volatility: inverse-volatility allocation across eligible assets. Diagonal approximation only; correlations and low-vol traps can invalidate a diversification hypothesis.
- ensemble: fixed trend/momentum/inverse-vol capital sleeves; no fitted best-strategy weights. Correlated failures can eliminate diversification.
- multi_factor: fixed ranks of past momentum/trend/inverse-vol; predefined ablation checks only.
- quality/value/ai_rating/signal_consensus: require suitable sourced PIT dated signals. No current ratings/fundamentals backfilled into past dates; absent inputs imply no qualifying signal, not invented scores.

All use daily available observations and default21-session rebalancing unless buy-and-hold. Configuration bounds are software safety limits, not evidence that every parameter in the range is economically defensible. Prespecify hypotheses, interval, assets, benchmark, costs, lookback and rebalancing before reading holdout results. Compare passive/cash baselines; retain failed experiments. Evidence grade remains Exploratory until separate qualified validation. No registry entry is a buy recommendation or demonstrated alpha.
