# Data quality and decision-chain acceptance — 2026-10-13

## Baseline and root causes

Base: `0b670aaf2c608d53e9567f25f1a6eed9ad5c8697`, PR #2 continuation branch.
Work: isolated `codex/data-quality-20261013` under `runtime/data-quality-20261013`.
The original dirty worktree and all earlier daily reports are preserved.

The original evidence was read from
`runtime/daily/2026-10-13-e72c04c136c94cb4b35e807db5f6ff7b/reports/b80a981b18df4d3e8ad68fe182bb3e43/report.json`
and its preflight, verification and finalize script. The original report had 30
symbols, 29 eligible, 10 candidates, SPY INVALID_DATA, missing relative SPY factors,
missing quality/value, null evaluation and PARTIAL scan status.

The daily process imported Python 3.12.14 from the original workspace and
`src/alphamosaic/core/contracts.py` on the audit branch. Its HistoricalBar.volume
was a required float. The PR #2 baseline permits null volume, but its validator
still rejected missing volume for price benchmarks. Its ETF worker did not fetch
ETF profiles, leaving identity unverified. These are three distinct defects;
changing the Pydantic field alone was insufficient. Package version 0.1.0 was the
same across differing source trees, so version strings alone did not identify code.

The old finalize script required exactly one report, hardcoded 2026-10-13, used
assertions for checks and included an external-page result in generated text. The
new generator never claims a web check without execution evidence.

The original evaluation=null cannot establish whether evaluate was disabled:
there is no preserved invocation parameter in that old report. New reports have
DISABLED_BY_REQUEST, BLOCKED_NO_CANDIDATES, BLOCKED_DIAGNOSTIC or an explicit
RECONSTRUCTED_DIAGNOSTIC state.

## Implemented repairs

- Price-benchmark validation permits null volume; stock volume/liquidity factors
  abstain separately. Identity, currency, OHLC, finite values, completed sessions,
  duplicates, gaps, adjustment consistency, source and discontinuities are checked.
- The official OpenBB Nasdaq ETF-info Fetcher supplies symbol/name evidence. If it
  does not supply an exchange, UNKNOWN is retained. A symbol/name-verified ETF may
  serve only price-benchmark diagnostics; this is not a certified exchange mapping.
- SPY and QQQM are validated independently. Invalid dependency status propagates
  into factors, ranking, report and MCP. Candidates can remain preliminary while
  INVESTMENT_ACTION remains NO_ACTION; SOFTWARE_ACCEPTANCE is independent.
- Original percentile/available-weight baseline is preserved. A parallel fixed-
  denominator research score explicitly penalizes missing weights. Every factor
  records source, known_at, cutoff, missing reason, group and dependency marker.
  No score is a forecast probability, and no score-distribution change proves alpha.
- Source batches and runtime/source fingerprints are persisted for recomputation.
  MCP scan/ranking summaries omit raw price arrays; full local JSON retains the audit inputs.
- SEC annual metrics retain fiscal period, USD/ratio units, filing cutoff and
  evidence association; revenue growth, margins, operating cash flow, FCF and
  covered net debt are derived only from eligible facts. Missing average-equity,
  invested-capital and price/earnings inputs leave ROE/ROIC/PE null. Nasdaq income
  and ratio responses with unmatched periods are not silently merged.
- User-declared research strata are selected with deterministic budgeted round
  robin. Labels are not assertions of growth/quality, and current members are not
  historical index constituents. No new scraper or paid provider was added.
- Report publication uses a staging directory and atomic rename, explicit run IDs,
  immutable conflict checks and deterministic hash-addressed derived bundles.
  JSON and Markdown share one model. Legacy files are read without rewriting.
- Historical trend diagnostics include fees and slippage, dataset fingerprint,
  aligned benchmark returns and a permanent reconstructed/no-alpha boundary.
  The existing replay, walk-forward, ablation and bias tests remain in the suite.

## Real network acceptance

Bounded broad scan:
- Run: `2955da45109a443e9ac16ba8a2d5c6eb`
- Cutoff: 2026-10-13 14:28:34.901426 UTC; latest completed session: 2026-10-12
- Universe 30; eligible 29; candidates 10; ORCL excluded for DEEP_DRAWDOWN
- SPY and QQQM: VALID_PRICE_SERIES. SPY has one missing-volume bar, retained with
  MISSING_VOLUME diagnostics. All ten relative SPY/QQQM fields are present.
- Weighted factor coverage: 0.785714; missing quality/value/growth evidence keeps
  overall status PARTIAL, PRELIMINARY_RESEARCH_ONLY and NO_ACTION.
- evaluate=False was explicit. Full snapshots recomputed all candidate factors;
  report generation was repeated without altering the original. Same-run MCP
  ranking was invoked through a real stdio ClientSession.

Frozen-source sample:
- Source commit: `7c17e6ed3b42d6b52961b43a48cd94bdf205ef65`
- Run: `1a7d0349fbd646a7ba5b3b5dae3c1201`
- AAPL, MSFT, GOOGL, AVGO, AMZN, NVDA: 6/6 eligible; SPY/QQQM both usable
- Cutoff: 2026-10-13 14:41:24.153744 UTC; evaluate=True produced a 111-observation
  RECONSTRUCTED_DIAGNOSTIC with both benchmarks. Six-candidate factors replayed
  exactly; daily JSON/Markdown generation and MCP run-ID query passed.
- The subsequent accounting commit separates fees from slippage in diagnostics;
  earlier immutable outputs remain tied to their original source version.

Provider data is kept in ignored runtime directories, not redistributed in Git.
The report snapshot input hash for the broad scan is
`785596d07b5f67d45733b441f8f2e61e6c11d08bd442087ebe2eb00db092f6d8`.
The real runs use OpenBB historical reconstruction and may use its HTTP cache;
there is no fixture replacement, certified PIT history or live-account return.

## Engineering validation

Python 3.12.14; pydantic 2.14.0; MCP 2.3.0; OpenBB core 2.0.1/Nasdaq 2.0.0;
QuantStats 0.0.86; exchange-calendars 4.13.2; numpy 2.5.3; pandas 2.3.3.

- uv lock --check: PASS
- uv sync --locked --all-extras --dev: PASS (repository cache)
- Ruff: PASS; Pyright: PASS (zero errors)
- Full pytest: 72 passed, 7 warnings. Warnings include dependency deprecations,
  QuantStats degenerate-sample division and an inherited MCP timeout cleanup warning.
- Wheel/sdist build: PASS
- Independent wheel install and doctor: PASS. Locked requirements were installed
  with uv pip sync from cache, avoiding an unpinned/offline resolver mismatch.
- Real stdio MCP handshake: PASS; protocol 2025-11-25, 22 tools, system-status and
  explicit run-ID ranking invocation. Remote ChatGPT integration: NOT_VERIFIED.
- Secret scan and diff checks: PASS
- Local pip-audit: NOT_VERIFIED; the online request did not complete within the bounded validation window. The tool and vulnerability service
  can complete; no claim that a secret scan is a dependency vulnerability audit.
- GitHub CI: recorded separately after branch publication; no historical CI result
  is treated as the new branch's acceptance.

## Remaining limits

SEC User-Agent, Danelfin and model keys are absent; no contact email or credential
was fabricated. Financial/live external acceptance remains NOT_CONFIGURED.
Sector exposures are NOT_CONFIGURED; price-style concentration is explicitly
flagged. User strata improve reproducibility, not demonstrated diversification.
ETF exchange fields remain UNKNOWN. Adjustment and corporate actions, historical
constituents, delistings and strict PIT data are incomplete. No strategy promotion,
qualified forward outcome, advisory eligibility, trading instruction or broker
operation is claimed. broker_enabled remains false.

## Remote CI checkpoint

PR #3 is stacked on the continuation development branch. Source/engineering checks
passed in https://github.com/SiriZhao/alpha-mosaic/actions/runs/38417014880 and
https://github.com/SiriZhao/alpha-mosaic/actions/runs/38416829439, including the actual
MCP protocol handshake. The original CI dependency audit reported no known
vulnerabilities for its exported base/dev dependencies and skipped the unpublished
AlphaMosaic package. A follow-up CI change exports all extras and omits the project
itself, so optional OpenBB/analytics dependencies are included without pretending to
perform a PyPI vulnerability audit of this source repository. Final check status is
verified on the published HEAD separately. These CI results do not promote any
financial-data or strategy-validation state.
