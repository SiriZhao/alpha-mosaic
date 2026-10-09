# Integrations

## OpenBB V5

The pinned optional integration uses `openbb-core==2.0.1`, `openbb-nasdaq==2.0.0` and
`openbb-sec==2.0.0`, corresponding to the OpenBB V5 foundation. OpenBB core is Apache-2.0;
provider website terms still govern retrieved data. The Nasdaq adapter currently supports a
current screener, historical OHLCV, profile and optional financial fields. It does not claim
free real-time data, unlimited quotas, complete historical index membership, or redistribution
rights.

The first live acceptance request was an AAPL historical/profile/fundamental request on 2026-10-09
UTC. It returned 132 historical rows and recorded request/completion timestamps, source URL,
fields, `HISTORICAL` quality, unknown adjustment policy and reconstructed PIT status in the
snapshot evidence. Provider health and signal validity remain separate.

## Analytics

`quantstats==0.0.86` is an optional adapter for finite return, volatility, drawdown, Sharpe and
Sortino metrics. The diagnostic is historical or fixed chronological holdout only; it is not a
claim of live performance or demonstrated alpha.
