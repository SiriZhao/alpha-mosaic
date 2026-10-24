# Return and risk conventions

Core implementation: `evaluation/analytics.py`; tested independently from optional QuantStats. Daily simple return r_t = NAV_t/NAV_(t-1)-1, with initial cash as NAV_0. No external capital flows. Exactly252 exchange observations/year; weekly annualization is not implied. Missing/nonfinite returns are rejected; undefined ratios are null.

Total return = product(1+r)-1. CAGR = product(1+r)^(252/n)-1. Sample volatility = std(r,ddof=1)×sqrt252. Sharpe uses mean daily excess divided by sample standard deviation×sqrt252; annual risk-free0 is the explicit default, not a sourced Treasury series. Sortino uses sqrt(mean(min(excess,0)^2)) over **all** periods. Calmar = CAGR/abs(max drawdown) when denominator is nonzero.

Drawdowns include initial capital in the high-water mark; duration counts exchange observations underwater. Episodes expose recovery or an unrecovered end. Rolling volatility/Sharpe and, for compatible aligned benchmarks, beta/correlation/active statistics use trailing windows.

Beta = sample covariance(strategy,benchmark)/sample variance(benchmark). Annual descriptive alpha =252×(mean strategy−beta×mean benchmark), an arithmetic zero-RF OLS intercept. Tracking error =std(active,ddof1)×sqrt252; information ratio =mean(active)/std(active)×sqrt252. These regressions are associations, not causal factor attribution or independent evidence of excess returns.

Benchmark comparisons require matching dates, declared return basis and evidence class. Unknown/unequal price, total-return or raw-plus-cash-action bases are blocked; reports omit incompatible benchmark traces. Whole-experiment comparisons additionally require the same dataset/source hash and validation/benchmark metadata. Different cost models remain explicitly visible for sensitivity review.

Costs: commission/slippage/spread in USD, plus explicit cost sum / initial capital. This cost-drag measure is not a counterfactual strategy-return difference. Turnover follows engine notional accounting. Market exposure averages1−cash/NAV; HHI sums squared invested-asset weights and reports cash separately. Closed-trade count, win rate, profit factor and average holding period are **null** until a matched-lot engine exists; fill_count is a separate execution count. Asset P&L and cash-interest attribution are also null. No fabricated factor-return series or causal explanations.
