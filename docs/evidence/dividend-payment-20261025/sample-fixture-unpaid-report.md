# AlphaMosaic Research Report

## Executive Summary

Research only. FIXTURE. No demonstrated alpha. Experiment 93ef9ab1f883487ea97dd28e2f176797.

## Research Question

Do frozen synthetic dividend rights reconcile across splits, cash availability and an unpaid evaluation boundary?

## Data & Provenance

{
  "dataset_id": "fdee48d841419674715267b5f7f300aebca08ff9b8f3c74e6c38e89cf94cc6e2",
  "hash": "fdee48d841419674715267b5f7f300aebca08ff9b8f3c74e6c38e89cf94cc6e2",
  "basis": "RAW_WITH_CASH_ACTIONS",
  "dataset": {
    "adjustment_method": [
      "RAW"
    ],
    "calendar": "XNYS",
    "corporate_actions_complete": true,
    "cutoff": "2016-07-01T20:00:00+00:00",
    "data_quality": [
      "FIXTURE"
    ],
    "dataset_hash": "fdee48d841419674715267b5f7f300aebca08ff9b8f3c74e6c38e89cf94cc6e2",
    "dataset_id": "fdee48d841419674715267b5f7f300aebca08ff9b8f3c74e6c38e89cf94cc6e2",
    "dataset_version": "fdee48d841419674715267b5f7f300aebca08ff9b8f3c74e6c38e89cf94cc6e2",
    "fetch_timestamp": "2016-07-01T20:00:00+00:00",
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
    "metadata": {
      "purpose": "FIXTURE_ONLY_DIVIDEND_ACCOUNTING",
      "quality_review": "Known generated two-for-one split; raw price and volume units explicitly transformed; no anomaly repaired or real provider data accepted",
      "reviewed_flags": [
        "SPLIT_REQUIRES_REVIEW"
      ]
    },
    "price_series_kind": [
      "RAW_PRICE"
    ],
    "provider": [
      "FIXTURE ordinary-dividend-cases v1",
      "FIXTURE synthetic_demo v1"
    ],
    "quality_policy": "ACCEPT_WITH_PROVENANCE",
    "quality_report": {
      "flags": [
        "SPLIT_REQUIRES_REVIEW"
      ],
      "issues": [
        {
          "code": "SPLIT_REQUIRES_REVIEW",
          "session": "2016-02-09",
          "severity": "WARNING",
          "symbol": "SPY"
        }
      ],
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
    "manifest_hash": "434c36d68a56906e4756af725658f5e8d852be32aac9c9908eafe914641da6c7"
  },
  "code": {
    "git_sha": "22c761794716961d33627135ce2ac01eef1b168a",
    "git_dirty": true,
    "python": "3.12.14",
    "lock_hash": "d959293b627ad12ce7b46a932a5d48bf00bac3adae82b11717a4d86660efb1dd",
    "source_hash": "0c934375a1f29c85cdd4740bafec9015916bc0a43aaf3c5178e77fb34cbdffb2"
  }
}

## Strategy Definition

{
  "strategy": "buy_and_hold",
  "symbols": [
    "SPY"
  ],
  "start": "2016-01-04",
  "end": "2016-02-10"
}

## Backtest Assumptions

{
  "accounting_schema_version": 2,
  "dividend_accounting": "PAY_DATE_RECEIVABLE",
  "payment_availability": "NEXT_XNYS_OPEN_AFTER_PAY_DATE",
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
  "decision_frequency": "DAILY",
  "weekly_parameters": {
    "lookback_weeks": 12,
    "trend_short_weeks": 4,
    "trend_long_weeks": 12
  },
  "seed": 42
}

## Dividend Accounting

{
  "accounting_schema_version": 2,
  "dividend_accounting": "PAY_DATE_RECEIVABLE",
  "missing_legacy_fields": false,
  "payment_availability": "NEXT_XNYS_OPEN_AFTER_PAY_DATE",
  "entitlements": [
    {
      "entitlement_id": "dividend-entitlement-000000",
      "action_reference": "0:SPY:DIVIDEND:2016-02-02",
      "source_action_id": "fixture-SPY-ordinary-dividend-v1",
      "symbol": "SPY",
      "ex_date": "2016-02-02",
      "payment_date": "2016-02-17",
      "accrued_at": "2016-02-02T14:30:00Z",
      "entitled_quantity": 968.0,
      "cash_per_share": 1.0,
      "amount": 968.0,
      "available_at": null,
      "schedule_status": "AFTER_EVALUATION_END"
    }
  ],
  "payments": [],
  "final_receivables": {
    "dividend-entitlement-000000": 968.0
  },
  "convention": "Earned income accrues with a non-spendable ex-date receivable. Payment transfers that claim to cash without recognizing income twice. Declared payment timing is a simulation policy, not verified broker posting time."
}

## Performance and Risk

{
  "metrics": {
    "return": -0.018605820321594746,
    "cagr": -0.1607865004103074,
    "volatility": 0.14243049627369048,
    "sharpe": -1.16170613885384,
    "sortino": -1.6182042813577378,
    "calmar": -3.2414013746301094,
    "max_drawdown": -0.049604008213470774,
    "drawdown_duration_sessions": 13.0,
    "beta": 1.0,
    "alpha_annualized_arithmetic": 0.0,
    "tracking_error": 0.0,
    "information_ratio": null,
    "correlation": 0.9999999999999999,
    "turnover": 0.9787058222107844,
    "fill_count": 1.0,
    "trade_count": 0,
    "win_rate": null,
    "profit_factor": null,
    "average_holding_period_sessions": null,
    "market_exposure": 0.9404529296315497,
    "transaction_cost_drag_initial_capital": 0.0015655771927149524,
    "closed_lot_match_count": 0,
    "completed_round_trip_count": 0
  },
  "conventions": {
    "periods_per_year": 252,
    "rolling_window_sessions": 21,
    "frequency": "DAILY_EXCHANGE_SESSION",
    "risk_free_annual": 0,
    "cagr": "geometric trading-period annualization",
    "return_basis": "RAW_WITH_CASH_ACTIONS",
    "alpha": "OLS arithmetic daily intercept times annual periods; risk free zero",
    "sample_start": "2016-01-04",
    "sample_end": "2016-02-10",
    "acceptance": "FIXTURE"
  },
  "benchmark_status": "COMPARABLE_SIMULATED_RETURNS",
  "drawdown_episodes": [
    {
      "start": "2016-01-05",
      "recovery": "2016-01-25",
      "underwater_sessions": 13,
      "maximum_drawdown": -0.04960400821347033
    },
    {
      "start": "2016-01-26",
      "recovery": null,
      "underwater_sessions": 12,
      "maximum_drawdown": -0.024095557719548855
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
    "win_rate": "Closed matching-segment economic P&L includes earned dividends, including unpaid receivables; this is not cash-realized profit",
    "profit_factor": "Sum positive closed-segment total P&L / absolute sum negative P&L; null if no losses",
    "average_holding_period_sessions": "Entry-cost-basis-weighted exchange sessions for closed matching segments only",
    "costs": "Execution prices already embed spread/slippage; commission counted once in cost basis/proceeds",
    "attribution": "Additive accounting P&L by held asset divided by initial capital; not a factor regression",
    "market_values": "Checked against supplied dataset prices",
    "evidence_class": "FIXTURE",
    "dividend_accounting": "PAY_DATE_RECEIVABLE",
    "payment_availability": "NEXT_XNYS_OPEN_AFTER_PAY_DATE",
    "dividend_income_usd": "Earned accrual; cash received and unpaid receivable are disclosed separately"
  },
  "reconciliation": {
    "status": "PASSED",
    "initial_cash_usd": 100000.0,
    "ending_cash_usd": 2031.547196700485,
    "ending_nav_usd": 98139.41796784055,
    "portfolio_pnl_usd": -1860.582032159451,
    "attributed_pnl_usd": -1860.582032159451,
    "allocated_commission_usd": 97.87058222107844,
    "allocated_dividends_usd": 968.0,
    "residual_usd": 0.0,
    "fill_count_checked": 1,
    "actions_checked": 2,
    "equity_points_checked": 27,
    "absolute_tolerance_usd": 1e-07,
    "relative_tolerance": 1e-10,
    "paid_dividends_usd": 0.0,
    "outstanding_dividend_receivables_usd": 968.0,
    "dividend_payments_checked": 0,
    "dividend_entitlements_checked": 1
  },
  "assets": [
    {
      "symbol": "SPY",
      "realized_price_pnl_usd": 0.0,
      "dividend_income_usd": 968.0,
      "fees_usd": 97.87058222107844,
      "slippage_usd": 48.90594754201401,
      "spread_usd": 9.781189508402802,
      "paid_dividends_usd": 0.0,
      "unrealized_price_pnl_usd": -2828.582032159451,
      "open_cost_basis_usd": 97968.45280329951,
      "ending_quantity": 1936.0,
      "ending_market_value_usd": 95139.87077114006,
      "total_pnl_usd": -1860.582032159451,
      "outstanding_dividend_receivables_usd": 968.0,
      "contribution_to_initial_capital": -0.01860582032159451
    }
  ]
}

## Weekly Research View

{
  "status": "COMPLETE_WEEKS_AVAILABLE",
  "metrics": {
    "return": -0.008748604153902995,
    "cagr": -0.08733447965091501,
    "volatility": 0.20821214476827068,
    "sharpe": -0.3561553234171036,
    "sortino": -0.6238363816762637,
    "calmar": -1.7606335212886828,
    "max_drawdown": -0.04960400821347033,
    "drawdown_duration_weeks": 5.0,
    "beta": 1.0,
    "alpha_annualized_arithmetic": 0.0,
    "tracking_error": 0.0,
    "information_ratio": null,
    "correlation": 1.0
  },
  "conventions": {
    "frequency": "WEEKLY_XNYS",
    "periods_per_year": 52,
    "metrics_scope": "COMPLETE_CALENDAR_WEEKS_ONLY",
    "risk_free_annual": 0,
    "observations": 5,
    "partial_intervals": 1,
    "acceptance": "FIXTURE",
    "return_basis": "RAW_WITH_CASH_ACTIONS",
    "nav_timestamp_semantics": "SIMULATED_VALUATION_TIME_NOT_PROVIDER_AVAILABILITY",
    "pit_certification": "NOT_ESTABLISHED_BY_WEEKLY_NAV_AGGREGATION",
    "decision_frequency": "NOT_INFERRED_FROM_RETURN_SAMPLING"
  },
  "partial_intervals": [
    {
      "week_start": "2016-02-08",
      "first_session": "2016-02-08",
      "last_session": "2016-02-10",
      "starting_nav": 99125.1395846097,
      "nav": 98139.41796784055,
      "return_value": -0.00994421416100777,
      "reason": "WEEK_NOT_CLOSED_AT_CUTOFF"
    }
  ],
  "inception_return_through_last_completed_week": -0.008748604153902995,
  "decision_frequency": "DAILY",
  "warnings": [
    "DAILY_OPEN_FILL_APPROXIMATION_NO_AUCTION_OR_ORDER_BOOK_DATA",
    "SAME_DAY_VOLUME_IS_EX_POST_CAPACITY_CAP_NOT_OPEN_KNOWN_LIQUIDITY",
    "DIVIDEND_ACCRUAL_AT_EX_OPEN_CASH_NEXT_XNYS_OPEN_AFTER_SOURCED_PAY_DATE",
    "DIVIDEND_RECEIVABLE_FACE_VALUE_NO_TAX_DEFAULT_OR_IMPAIRMENT_MODEL",
    "Weekly analysis aggregates the supplied daily replay; it does not turn a daily decision rule into a weekly strategy.",
    "Annualization uses 52 complete exchange-calendar weeks, not 252 sessions or five-day blocks.",
    "Partial initial/final intervals remain separate and are excluded from annualized weekly metrics.",
    "Week-end sampled drawdown and volatility do not capture all intraweek daily losses; retain the daily risk report.",
    "Weekly NAV available_at is the simulated XNYS valuation time, not independently verified market-data availability or PIT certification."
  ]
}

## Transaction Costs

{
  "fees": 97.87058222107844,
  "slippage_cost": 48.90594754201401,
  "spread_cost": 9.781189508402802,
  "turnover": 0.9787058222107844
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
DIVIDEND_ACCRUAL_AT_EX_OPEN_CASH_NEXT_XNYS_OPEN_AFTER_SOURCED_PAY_DATE
DIVIDEND_RECEIVABLE_FACE_VALUE_NO_TAX_DEFAULT_OR_IMPAIRMENT_MODEL
Cost drag is explicit simulated costs divided by initial capital, not a counterfactual return difference.
Regression alpha is descriptive association, not causal attribution or demonstrated alpha.
FIFO matching segments are not independent trades or tax lots
Ordinary dividend income accrues at ex-open; cash is available only at the first XNYS open strictly after the sourced pay date; unpaid claims assume full collection without taxes/default/impairment
Cash interest, taxes and external funding are not modeled; no factor-causality or alpha claim
Ledger reconciliation does not independently certify original dataset identity, source adjustment claims or PIT authenticity
No demonstrated alpha; fixed historical rules are research diagnostics
Daily bars cannot establish executable opening-auction liquidity
Holdout labels describe declared dates, not independent prospective validation
Source files must be frozen and the service restarted before acceptance; a disk hash cannot certify stale in-memory modules

## Further Research

Acquire independently reviewed PIT/corporate-action/delisting data; freeze hypothesis before a new holdout.

## Audit Artifacts

Complete numeric evidence is in experiment.json; full configuration in config.json. CSV exports retain daily/weekly equity, signals, orders, fills, cash, split revisions, closed/open FIFO matches and asset accounting contributions; payment-model artifacts additionally retain entitlement/payment records. No best-case-only selection.