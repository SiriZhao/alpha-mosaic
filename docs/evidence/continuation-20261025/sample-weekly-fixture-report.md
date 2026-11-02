# AlphaMosaic Research Report

## Executive Summary

Research only. FIXTURE. No demonstrated alpha. Experiment 2da66028a2f94c99a2e38a32323fb3a0.

## Research Question

Does a fixed daily or calendar-week baseline reconcile after costs, splits and closed-lot accounting?

## Data & Provenance

{
  "dataset_id": "7c075d0ebf8a28f8a9d24bbd164ed325e757c25299d4f7bcc7fa47438427129c",
  "hash": "7c075d0ebf8a28f8a9d24bbd164ed325e757c25299d4f7bcc7fa47438427129c",
  "basis": "RAW_WITH_CASH_ACTIONS",
  "dataset": {
    "adjustment_method": [
      "RAW"
    ],
    "calendar": "XNYS",
    "corporate_actions_complete": true,
    "cutoff": "2017-01-12T21:00:00+00:00",
    "data_quality": [
      "FIXTURE"
    ],
    "dataset_hash": "7c075d0ebf8a28f8a9d24bbd164ed325e757c25299d4f7bcc7fa47438427129c",
    "dataset_id": "7c075d0ebf8a28f8a9d24bbd164ed325e757c25299d4f7bcc7fa47438427129c",
    "dataset_version": "7c075d0ebf8a28f8a9d24bbd164ed325e757c25299d4f7bcc7fa47438427129c",
    "fetch_timestamp": "2017-01-12T21:00:00+00:00",
    "frequency": "DAILY",
    "historical_universe_verified": true,
    "instruments": [
      "QQQM",
      "SPY",
      "TLT"
    ],
    "license_scope": [
      "Project-generated synthetic data; Apache-2.0"
    ],
    "metadata": {},
    "price_series_kind": [
      "RAW_PRICE"
    ],
    "provider": [
      "FIXTURE synthetic_demo v1"
    ],
    "quality_policy": "REJECT",
    "quality_report": {
      "flags": [],
      "issues": [],
      "jump_threshold": 0.5,
      "repaired": false,
      "schema_version": 1,
      "valid": true
    },
    "schema_version": 1,
    "source_versions": [
      "NOT_REPORTED"
    ],
    "state": "AVAILABLE",
    "timezone": "UTC",
    "universe_selection_method": "EXPLICIT_FIXED_SYNTHETIC",
    "manifest_hash": "c08958bbf9846c52db90d7eec9cf1b363d36d5de6bf53dbe593bf35505c95c6f"
  },
  "code": {
    "git_sha": "d6e66095eed8204773fba6df98be11d4838e932a",
    "git_dirty": true,
    "python": "3.12.14",
    "lock_hash": "d959293b627ad12ce7b46a932a5d48bf00bac3adae82b11717a4d86660efb1dd",
    "source_hash": "af12390cfe9579db641a354fee171afaa6d409c3c6bd56fa770a6f06ceca8f07"
  }
}

## Strategy Definition

{
  "strategy": "weekly_trend",
  "symbols": [
    "SPY",
    "QQQM",
    "TLT"
  ],
  "start": "2016-01-04",
  "end": "2017-01-12"
}

## Backtest Assumptions

{
  "initial_cash": 100000.0,
  "fee_bps": 10.0,
  "slippage_bps": 5.0,
  "spread_bps": 2.0,
  "order_delay_sessions": 1,
  "lot_size": 1,
  "max_single_weight": 1.0,
  "max_gross_exposure": 1.0,
  "min_cash_buffer": 0.02,
  "max_turnover": 2.0,
  "volatility_target": 0.15,
  "max_positions": 10,
  "max_volume_fraction": 0.01,
  "lookback": 63,
  "rebalance_sessions": 21,
  "decision_frequency": "WEEKLY",
  "weekly_parameters": {
    "lookback_weeks": 12,
    "trend_short_weeks": 4,
    "trend_long_weeks": 12
  },
  "seed": 42
}

## Performance and Risk

{
  "metrics": {
    "return": -0.019625491737614853,
    "cagr": -0.019027412784157094,
    "volatility": 0.09383769933525275,
    "sharpe": -0.15807880778506334,
    "sortino": -0.23721043795068586,
    "calmar": -0.22868085851160488,
    "max_drawdown": -0.08320509599272607,
    "drawdown_duration_sessions": 127.0,
    "beta": 0.3552933161279497,
    "alpha_annualized_arithmetic": -0.0009600624922828538,
    "tracking_error": 0.11969216084293223,
    "information_ratio": 0.20230898252998106,
    "correlation": 0.522934685429896,
    "turnover": 13.694261267748228,
    "fill_count": 39.0,
    "trade_count": 31,
    "win_rate": 0.3548387096774194,
    "profit_factor": 0.8248680596714837,
    "average_holding_period_sessions": 16.01455271966779,
    "market_exposure": 0.4256181124395654,
    "transaction_cost_drag_initial_capital": 0.02177459977964334,
    "closed_lot_match_count": 31,
    "completed_round_trip_count": 8
  },
  "conventions": {
    "periods_per_year": 252,
    "frequency": "DAILY_EXCHANGE_SESSION",
    "risk_free_annual": 0,
    "cagr": "geometric trading-period annualization",
    "return_basis": "RAW_WITH_CASH_ACTIONS",
    "alpha": "OLS arithmetic daily intercept times annual periods; risk free zero",
    "sample_start": "2016-01-04",
    "sample_end": "2017-01-12",
    "acceptance": "FIXTURE"
  },
  "benchmark_status": "COMPARABLE_SIMULATED_RETURNS",
  "drawdown_episodes": [
    {
      "start": "2016-03-29",
      "recovery": "2016-03-30",
      "underwater_sessions": 1,
      "maximum_drawdown": -0.004638319076169295
    },
    {
      "start": "2016-03-31",
      "recovery": "2016-04-07",
      "underwater_sessions": 5,
      "maximum_drawdown": -0.02187540347094763
    },
    {
      "start": "2016-04-08",
      "recovery": "2016-10-07",
      "underwater_sessions": 127,
      "maximum_drawdown": -0.08320509599272563
    },
    {
      "start": "2016-10-10",
      "recovery": "2016-10-19",
      "underwater_sessions": 7,
      "maximum_drawdown": -0.0171690881818074
    },
    {
      "start": "2016-10-20",
      "recovery": "2016-10-21",
      "underwater_sessions": 1,
      "maximum_drawdown": -0.001640769169549694
    },
    {
      "start": "2016-10-24",
      "recovery": null,
      "underwater_sessions": 56,
      "maximum_drawdown": -0.062096488656422366
    }
  ]
}

## Matched Trades and Accounting Contribution

{
  "status": "VERIFIED",
  "conventions": {
    "matching": "FIFO",
    "trade_count": "Each sell-to-entry-lot matching segment; not flat-to-flat episodes",
    "completed_round_trip_count": "Position transitions from positive to flat per symbol",
    "win_rate": "Fraction of closed matching segments with positive net execution P&L plus allocated posted dividends; breakeven is not a win",
    "profit_factor": "Sum positive closed-segment total P&L / absolute sum negative P&L; null if no losses",
    "average_holding_period_sessions": "Entry-cost-basis-weighted exchange sessions for closed matching segments only",
    "costs": "Execution prices already embed spread/slippage; commission counted once in cost basis/proceeds",
    "attribution": "Additive accounting P&L by held asset divided by initial capital; not a factor regression",
    "market_values": "Checked against supplied dataset prices",
    "evidence_class": "FIXTURE"
  },
  "reconciliation": {
    "status": "PASSED",
    "initial_cash_usd": 100000.0,
    "ending_cash_usd": 98037.45082623854,
    "ending_nav_usd": 98037.45082623854,
    "portfolio_pnl_usd": -1962.5491737614648,
    "attributed_pnl_usd": -1962.5491737614605,
    "allocated_commission_usd": 1360.9124378727777,
    "allocated_dividends_usd": 0.0,
    "residual_usd": -4.320099833421409e-12,
    "fill_count_checked": 39,
    "actions_checked": 0,
    "equity_points_checked": 260,
    "absolute_tolerance_usd": 1e-07,
    "relative_tolerance": 1e-10
  },
  "assets": [
    {
      "symbol": "QQQM",
      "realized_price_pnl_usd": 2777.2467876268956,
      "dividend_income_usd": 0.0,
      "fees_usd": 584.4474914838681,
      "slippage_usd": 292.22485945116716,
      "spread_usd": 58.44497189023344,
      "unrealized_price_pnl_usd": 0.0,
      "open_cost_basis_usd": 0.0,
      "ending_quantity": 0.0,
      "ending_market_value_usd": 0,
      "total_pnl_usd": 2777.2467876268956,
      "contribution_to_initial_capital": 0.027772467876268955
    },
    {
      "symbol": "SPY",
      "realized_price_pnl_usd": -1529.2389056613376,
      "dividend_income_usd": 0.0,
      "fees_usd": 393.98425216860005,
      "slippage_usd": 196.99185642497227,
      "spread_usd": 39.398371284994454,
      "unrealized_price_pnl_usd": 0.0,
      "open_cost_basis_usd": 0.0,
      "ending_quantity": 0.0,
      "ending_market_value_usd": 0,
      "total_pnl_usd": -1529.2389056613376,
      "contribution_to_initial_capital": -0.015292389056613377
    },
    {
      "symbol": "TLT",
      "realized_price_pnl_usd": -3210.5570557270185,
      "dividend_income_usd": 0.0,
      "fees_usd": 382.48069422030954,
      "slippage_usd": 191.23956753349066,
      "spread_usd": 38.24791350669813,
      "unrealized_price_pnl_usd": 0.0,
      "open_cost_basis_usd": 0.0,
      "ending_quantity": 0.0,
      "ending_market_value_usd": 0,
      "total_pnl_usd": -3210.5570557270185,
      "contribution_to_initial_capital": -0.03210557055727018
    }
  ]
}

## Weekly Research View

{
  "status": "COMPLETE_WEEKS_AVAILABLE",
  "metrics": {
    "return": -0.019625491737614742,
    "cagr": -0.019258788466717802,
    "volatility": 0.1140187843934342,
    "sharpe": -0.11529025078782941,
    "sortino": -0.18833345462533543,
    "calmar": -0.2953297530084971,
    "max_drawdown": -0.0652111352497684,
    "drawdown_duration_weeks": 25.0,
    "beta": 0.4396373550908958,
    "alpha_annualized_arithmetic": 0.004438772370762942,
    "tracking_error": 0.12676148466692908,
    "information_ratio": 0.21182623136770998,
    "correlation": 0.614695782432834
  },
  "conventions": {
    "frequency": "WEEKLY_XNYS",
    "periods_per_year": 52,
    "metrics_scope": "COMPLETE_CALENDAR_WEEKS_ONLY",
    "risk_free_annual": 0,
    "observations": 53,
    "partial_intervals": 1,
    "acceptance": "FIXTURE",
    "return_basis": "RAW_WITH_CASH_ACTIONS",
    "nav_timestamp_semantics": "SIMULATED_VALUATION_TIME_NOT_PROVIDER_AVAILABILITY",
    "pit_certification": "NOT_ESTABLISHED_BY_WEEKLY_NAV_AGGREGATION",
    "decision_frequency": "NOT_INFERRED_FROM_RETURN_SAMPLING"
  },
  "partial_intervals": [
    {
      "week_start": "2017-01-09",
      "first_session": "2017-01-09",
      "last_session": "2017-01-12",
      "starting_nav": 98037.45082623854,
      "nav": 98037.45082623854,
      "return_value": 0.0,
      "reason": "WEEK_NOT_CLOSED_AT_CUTOFF"
    }
  ],
  "inception_return_through_last_completed_week": -0.01962549173761463,
  "decision_frequency": "WEEKLY",
  "warnings": [
    "DAILY_OPEN_FILL_APPROXIMATION_NO_AUCTION_OR_ORDER_BOOK_DATA",
    "SAME_DAY_VOLUME_IS_EX_POST_CAPACITY_CAP_NOT_OPEN_KNOWN_LIQUIDITY",
    "WEEKLY_COMPLETED_XNYS_WEEK_SIGNAL_NEXT_ELIGIBLE_DAILY_OPEN_FILL",
    "GROSS_WEIGHT_DRIFT_BETWEEN_REBALANCES",
    "Weekly analysis aggregates the supplied daily replay; it does not turn a daily decision rule into a weekly strategy.",
    "Annualization uses 52 complete exchange-calendar weeks, not 252 sessions or five-day blocks.",
    "Partial initial/final intervals remain separate and are excluded from annualized weekly metrics.",
    "Week-end sampled drawdown and volatility do not capture all intraweek daily losses; retain the daily risk report.",
    "Weekly NAV available_at is the simulated XNYS valuation time, not independently verified market-data availability or PIT certification."
  ]
}

## Transaction Costs

{
  "fees": 1360.9124378727777,
  "slippage_cost": 680.4562834096301,
  "spread_cost": 136.091256681926,
  "turnover": 13.694261267748228
}

## Robustness

Run the cost and parameter cases separately; no best-result selection or automatic promotion.

## Out-of-Sample Validation

EXPLORATORY; declared dates are not a certification of an untouched holdout. {}

## Comparison to Benchmarks

SPY; comparison status: COMPARABLE_SIMULATED_RETURNS; compare only when compatible; no fabricated risk-free series.

## Counterarguments and Limitations

DAILY_OPEN_FILL_APPROXIMATION_NO_AUCTION_OR_ORDER_BOOK_DATA
SAME_DAY_VOLUME_IS_EX_POST_CAPACITY_CAP_NOT_OPEN_KNOWN_LIQUIDITY
WEEKLY_COMPLETED_XNYS_WEEK_SIGNAL_NEXT_ELIGIBLE_DAILY_OPEN_FILL
GROSS_WEIGHT_DRIFT_BETWEEN_REBALANCES
Cost drag is explicit simulated costs divided by initial capital, not a counterfactual return difference.
Regression alpha is descriptive association, not causal attribution or demonstrated alpha.
FIFO matching segments are not independent trades or tax lots
Dividend income is credited under the replay effective-open convention; payment-date lag is not modeled
Cash interest, taxes and external funding are not modeled; no factor-causality or alpha claim
Ledger reconciliation does not independently certify original dataset identity, source adjustment claims or PIT authenticity
No demonstrated alpha; fixed historical rules are research diagnostics
Daily bars cannot establish executable opening-auction liquidity
Holdout labels describe declared dates, not independent prospective validation
Source files must be frozen and the service restarted before acceptance; a disk hash cannot certify stale in-memory modules

## Further Research

Acquire independently reviewed PIT/corporate-action/delisting data; freeze hypothesis before a new holdout.

## Audit Artifacts

Complete numeric evidence is in experiment.json; full configuration in config.json. CSV exports retain daily/weekly equity, signals, orders, fills, cash, split revisions, closed/open FIFO matches and asset accounting contributions. No best-case-only selection.