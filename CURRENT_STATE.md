# Current state (2026-10-09)

Implemented and locally verified:

- Pydantic evidence contracts with UTC chronology and point-in-time guards.
- Isolated OpenBB V5 Nasdaq adapter with current-universe discovery, historical OHLCV, profile
  and optional fundamentals; no synthetic fallback.
- Deterministic momentum, relative strength, trend, volume, volatility, drawdown and liquidity
  factors; heuristic percentile ranking and risk filtering.
- Unique JSON/Markdown reports, historical diagnostic metrics, CLI commands and six read-only MCP
  tools through one `ApplicationService`.
- Python 3.12 environment contains OpenBB core 2.0.1, Nasdaq 2.0.0, SEC 2.0.0, MCP 2.3.0,
  QuantStats 0.0.86, ruff 0.16.10, pyright 1.1.414 and pytest 9.1.1.

Measured acceptance:

- `ruff check .`: passed.
- `pyright`: passed.
- Foundation tests: 4 passed.
- `alphamosaic doctor`, `providers` and `analyze AAPL --fundamentals`: passed against live
  Nasdaq data; AAPL returned 132 rows and recorded evidence.
- `python -m build --no-isolation --wheel --sdist`: passed after using a repository-owned temp
  directory; produced `alphamosaic-0.1.0-py3-none-any.whl` and `.tar.gz`.
- Clean Python 3.12 wheel environment: installed the wheel plus base dependencies with `uv`, and
  `alphamosaic doctor` completed with OpenBB/QuantStats correctly reported as optional absent.
- Live explicit scan of 10 symbols: 8 candidates, 2 exclusions, `REAL_DATA` report with unique
  JSON and Markdown run bundle under the ignored runtime report store.
- GitHub CLI authentication for SiriZhao is invalid, so private remote creation/push is blocked.

Known limitations: current screener is survivorship-biased, historical data is reconstructed and
adjustment policy is unknown, fundamentals are partial, news and multi-agent research are not
connected, and there is no demonstrated alpha or broker execution.
