# Ordinary cash-dividend accounting acceptance

Full Renaissance goal: **ACTIVE, not complete**. This checkpoint implements the ordinary USD cash-dividend boundary in the [reviewed design](DIVIDEND_PAYMENT_ACCOUNTING_DESIGN.md); it does not establish real provider/PIT qualification, broker posting time or investment performance.

## Implemented contract

At sourced ex-date open, before fills, existing shares acquire a fixed earned-income entitlement. The receivable contributes to NAV but cannot fund purchases. At the first XNYS open **strictly after** the sourced calendar payment date, a payment event transfers the fixed claim to cash without recognizing income again. Selling, repurchasing or splitting shares between those events does not change the original dollar right.

```text
NAV = spendable simulated cash + marked stock/ETF holdings + outstanding dividend receivables
earned dividend income = modeled cash dividend payments + outstanding claims
```

New experiments and cost presets explicitly use accounting schema2 / PAY_DATE_RECEIVABLE / NEXT_XNYS_OPEN_AFTER_PAY_DATE. Required action terms include ORDINARY_CASH, EX_DATE role, EX_DATE_SHARES amount basis, payment date and stable source action ID. Terms must be available by ex-open. Special/due-bill/unknown distributions, unknown dates/units, late terms and ambiguous same-day split/dividend units fail closed. RAW cash actions cannot augment total-return or adjusted prices.

Old missing-field replay configurations remain schema1 / LEGACY_EX_DATE_CASH. Stored old artifacts are read without rewriting bytes or introducing new claims. Legacy dividends are limited to explicit reconstructed diagnostics or FIXTURE controls; they cannot enter strict real replay. Daily, weekly and experiment comparison gates reject mismatched accounting models even if their NAV paths happen to be equal.

Result events/equity retain receivable snapshots, entitlement records and payment records. Artifact schema3 requires dividend_entitlements.csv, dividend_payments.csv and receivables.csv in addition to prior outputs. Independent FIFO reconstruction checks cash, claims, source terms, due-payment coverage, lot allocations and additive NAV/P&L. Closed-lot economic P&L can include earned unpaid income and is explicitly distinguished from cash-realized profit. Market exposure excludes receivables; cash, stock and claim weights remain separate.

Reports and the terminal show model/payment assumptions, recorded claims/payments, final spendable cash and independently reconciled unpaid claims. Missing legacy evidence is not converted to zero.

## Actual verification

Replay and independent accounting also reject corporate-action values marked MODEL_INFERENCE/MISSING and mixed observed/FIXTURE inputs. Dated features require observed/FIXTURE evidence, nonempty source/identity and strict PIT availability; a PIT flag alone cannot promote model comments or unknown numeric values. The strategy kernel independently refuses unqualified/mixed feature values. These checks follow reproduced negative tests; an explicit observed-FIXTURE positive control continues to allocate.

Frozen source SHA256: `0c934375a1f29c85cdd4740bafec9015916bc0a43aaf3c5178e77fb34cbdffb2`.

The final full regression passed **346 tests**, zero failed/error/skipped, with RuntimeWarning treated as error. Four upstream exchange-calendar deprecation warnings remain visible. Ruff/Pyright passed. Financial coverage includes hand-worked10-share/one-dollar accrual, ex-open buy/sell boundaries, sale before payment, replacement lots, partial FIFO exits across multiple entries, forward/reverse/fractional splits, multiple claims settling together, duplicate source IDs, zero/unrepresentable dividends, missing/late/special terms, holiday/weekend dates, distant out-of-calendar payment, evaluation truncation, no warmup ownership, future-price perturbations, corrupted ledgers and immutable old-artifact reading. Actual AppTest actions validate separate0/.99/.01 cash/stock/claim weights and a visible unpaid-claim metric.

`scripts/run_dividend_cases.py` retains four deterministic FIXTURE cases: realistic full, stress full, unpaid evaluation cutoff and an explicitly legacy diagnostic. Four additional predeclared daily strategy/cost trials complete through isolated frozen-plan workers with retained critics. An unsupported action-aware RAW weekly experiment is retained FAILED; it is not hidden as a successful weekly result. Default REJECT initially stopped the generated two-for-one jump. The script now permits only the explicitly reviewed SPLIT_REQUIRES_REVIEW fixture warning with ACCEPT_WITH_PROVENANCE metadata; unrelated flags and structural errors still reject. No acquired market data receives that exception.

Browser QA rendered all eight pages and mobile reports, selected actual compatible IDs and an unpaid result, and retained13 screenshots without browser errors. The selected experiment value and rendered provenance are asserted; clicking a dropdown alone is insufficient. The readable claim panel and cash/market/receivable plot were visually inspected. Final base-wheel/build/MCP and hosted CI evidence are recorded separately in `evidence/dividend-payment-20261025/`; older346-test or wheel records are not silently promoted across source changes.

The current local bundle verifies both built and installed Python bytes against the frozen source. Its fresh base wheel had OpenBB/QuantStats/Streamlit/Plotly absent and still completed the ordinary-payment suite, four isolated worker trials and actual31-tool stdio MCP. Source-specific hosted CI remains pending publication; no older run is substituted.

## Independent review and retained failures

Additional counterexamples exposed three unqualified/mixed action-evidence cases in replay, three in independent reconstruction, and ten invalid feature-signal/PIT/source cases. Repaired gates and the positive control pass without weakening existing financial assertions. These test-only metadata counterexamples are not real provider evidence or accepted real-data experiments.

Independent engineering/validation worktrees and a frozen implementation snapshot remain intact. The independent first run passed37/38 and exposed a false daily benchmark compatibility claim. Parent reproduction also demonstrated the same weekly defect; both now return BLOCKED_ACCOUNTING_MODEL_MISMATCH. A further negative test reproduced legacy cash entering strict real research, then verified its refusal. Original failing JUnit records are retained. Sub-agents reached their usage limit; the parent recovered their uncommitted code and completed integration without buying resources or discarding assertions.

Browser QA failures included a comparison-loop variable shadowing the requested result and controlled selectbox re-selection without an asserted selected value. These were diagnosed and fixed; all earlier runtime attempts remain preserved. The final smoke asserts both the selected value and visible result provenance and verifies the active dividend panel.

## Reproduce

```powershell
uv run pytest -q -W error::RuntimeWarning
uv run python scripts/run_dividend_cases.py --home runtime/new-dividend-run
$env:ALPHAMOSAIC_HOME = (Join-Path (Get-Location) 'runtime/new-dividend-run')
uv run python -m streamlit run src/alphamosaic/ui/app.py --theme.base dark
```

Select the unpaid-cutoff experiment in Backtest Results → Dividend accounting or Risk Lab. The suite JSON records all actual IDs, the incompatible legacy comparison, frozen plan and expected weekly failure. FIXTURE prices and results are software evidence only.

## Remaining scope

Claims are valued at declared face amount under a full-collection/no-tax/no-impairment simulation assumption. Actual payment intraday timing, amendments, withholding, special distributions/due bills, cash-in-lieu, delisting economics and broker settlement are not implemented or certified. Action-aware RAW weekly signals still require a reviewed causal adjustment model. Licensed real actions/PIT/universe/delisting evidence, broader benchmark/portfolio/factor capabilities, advanced independently checked selection statistics, PDF export, robust scenario controls, interrupted-plan reconciliation and adaptive model planning still prevent full-platform completion. No brokerage path, paid model requirement, automatic promotion or alpha claim is introduced.
