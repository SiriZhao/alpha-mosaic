# Ordinary cash dividends: entitlement, receivable and payment design

Status: **design reviewed, not implemented**. Consulted on 2026-10-25 (Asia/Shanghai).
Code inspected: main integration `d0f12488c6788bbcfbf083a79adffacc8a4639db`.
This document does not change the engine, migrate data, or certify payment-date accounting.

## 1. Source-backed entitlement boundary

The SEC explains that purchasing on or after the ex-dividend date does not confer the upcoming ordinary cash dividend; a purchase before that date does. A seller on the ex-date therefore retains the relevant entitlement. The record date is not a substitute for a sourced ex-date. [SEC Investor.gov](https://www.investor.gov/introduction-investing/investing-basics/glossary/ex-dividend-dates-when-are-you-entitled-stock-and)

FINRA Rule 11140 distinguishes ordinary distributions from certain large distributions whose ex-date follows payment, and provides separate treatment for late information, foreign securities and ADRs. Source actual exchange-designated dates; do not infer historical ex-dates from today's settlement convention, a record date, a price drop, or an assumed amount threshold. [FINRA Rule 11140](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140)

The initial implementation should support only explicitly identified **ordinary USD cash dividends** on the existing long-only US stock/ETF boundary. Special distributions, due bills, stock dividends, return of capital, withholding tax, foreign-currency payments, cancellations and receivable impairment require separate verified contracts. Reject an unknown distribution type; do not silently treat it as ordinary. The accounting model below is an engineering proposal derived from those entitlement rules, not a claim that a provider or brokerage has supplied the required evidence.

## 2. Current incompatible contracts

- `core/contracts.py::CorporateAction` currently has generic `effective_date` and `cash_amount`, but no explicit ex-date role, payment date, distribution type, or per-share amount basis.
- `backtesting/replay.py` immediately increases cash by current shares times cash_amount at effective-date open. Moving this same expression to the payment date is **incorrect**: intervening sales or splits would change the wrong shareholder quantity.
- `CashEntry.kind` currently permits FILL and DIVIDEND; its DIVIDEND entry denotes the legacy immediate cash credit. An accrual is not a cash movement and must not be inserted as such.
- `LedgerEvent` snapshots and `EquityPoint` only contain cash and positions/market values. Their current invariant is NAV = cash + marked holdings. They cannot represent an unpaid entitlement.
- Replay opening NAV, decision NAV, after-cost buy constraints and closing NAV all currently omit receivables. Buy funding must continue to use spendable simulated cash even after NAV includes receivables.
- `evaluation/analytics.py` computes market exposure as 1 - cash/NAV. With a receivable this wrongly classifies that asset as equity-market exposure. Use marked stock value/NAV; show cash and receivable weights separately.
- `evaluation/trades.py` currently accrues lot dividends and consumes a DIVIDEND cash record in one step. Its action-date/reference coverage, allocated dividend identity and final NAV checks must distinguish accrual from settlement.
- Independent accounting tests, result exports, report assumptions, benchmark compatibility and the UI all currently encode the legacy cash equation. Passing those unchanged tests is not proof of the new model.

## 3. Minimum explicit inputs and immutable records

For a new ordinary cash dividend contract require: a stable source action ID/reference, symbol, currency USD, sourced ex-date, sourced payment date, positive or explicitly zero cash amount per entitled share, distribution type ORDINARY_CASH, per-share unit basis, source/evidence class and aware UTC availability timestamps. The existing effective_date may remain an explicitly declared ex-date alias for versioned parsing; a generic old effective_date must not be relabeled as an ex-date without evidence.

Per-share units must be unambiguous. A split between ex-date and payment does not rescale the frozen cash entitlement. A split on the ex-date is unsupported unless the source explicitly establishes whether the dividend amount uses pre- or post-split shares and the action ordering is reviewed. Do not silently apply the current split-first convention to ambiguous terms.

Create an immutable entitlement record at accrual with: entitlement ID, source action/reference, dataset identity, symbol, ex-date, captured timestamp, entitled share quantity, amount per share, fixed gross USD amount, declared payment date and settlement convention. Link its per-lot rights to entry fill IDs. Settlements append distinct events referring to that entitlement ID; never overwrite its original quantity or cash amount.

For STRICT_PIT, the terms used for entitlement and scheduling must be known before the entitlement event, not merely before the research cutoff. Reject late-known or revised terms when their historical availability cannot be established. If amendments are later supported, give each a separate known_at and append-only adjustment event; do not backdate it or rewrite historical cash, NAV, decisions or finalized experiments.

## 4. State transitions and invariants

At the sourced ordinary ex-date open, before that open's simulated fills, freeze the already-held entitlement quantity. Shares bought at that open get no right; shares sold at that open retain the right. Establish the non-spendable receivable and recognize dividend income. Spendable cash does not change.

The portfolio equation becomes:

```text
NAV = spendable simulated cash + marked stock/ETF holdings + dividend receivables
```

A proportional ex-date price decline can therefore be offset by the accrued receivable without inventing cash. Buy affordability uses spendable cash only. Exposure/target/turnover denominators must consistently use full NAV; cash buffers cannot be funded by an unpaid receivable. The existing immediate reuse of sale proceeds is a separate execution/settlement approximation: this dividend change must not be advertised as a complete US cash-account settlement model.

At modeled cash availability, transfer the fixed claim amount from receivable to cash, independent of current shares. This is a balance-sheet reclassification, not another income event. Splits, full exits, later repurchases or symbol-level target changes do not cancel or multiply the prior claim.

For every interval independently reconcile:

```text
closing receivables = opening receivables + dividend accruals - dividend payments
closing cash = opening cash + net fill cash flows + dividend payments
earned dividend income = paid dividend amounts + outstanding dividend receivables
portfolio P&L = realized price P&L + unrealized price P&L + earned dividend income
```

Taxes, interest, external flows and impairments are excluded from these initial equations; they must not be silently inferred as zero-valued observed financial data. The declared simulator assumes their absence. Record that assumption.

## 5. Payment timing, absent dates and evaluation bounds

A calendar payment date is not proof that funds are available at the session open. For a first daily-bar implementation, an explicit conservative model can release cash at the **first XNYS open strictly after the sourced calendar payment date**. This also gives a deterministic next-session rule for weekends and exchange holidays. Label it NEXT_XNYS_OPEN_AFTER_PAY_DATE, not verified broker posting time. Record original payment date and modeled availability separately; do not overwrite the source date with a trading session.

An actual intraday or pre-open payment-availability model would need a sourced, historically available timestamp and additional event ordering; it is outside this minimum design. Do not quietly switch conventions when convenient for a result.

- Missing/unknown payment date: new strict payment-accounting replay must fail before simulation. No invented date, instant payment, or zero-filled entitlement.
- Ordinary payment before ex-date: reject as incompatible/possibly special-distribution evidence rather than trying to repair dates.
- Non-session ex-date: reject unsupported entitlement timing; non-session payment date follows the explicit availability convention above.
- Payment after evaluation end or source price coverage: retain the unpaid receivable in final NAV and export it. Do not accelerate cash, drop income or require an invented post-end price. If the distant date is outside the loaded calendar range, preserve the sourced future date and unresolved out-of-range schedule; never make it spendable inside this run.
- Evaluation starts after ex-date: the existing simulator starts fresh with cash and no carried positions. It has no historical right merely because an old dividend pays during the evaluation. Warmup signal history is not entitlement ownership. Starting receivables would need an explicit separately validated initial-state contract.
- An amount or payment amendment becoming known later requires a new dated source event. Historical unpaid receivables are not evidence of guaranteed collection; impairment/default behavior remains unsupported and must be disclosed.

## 6. FIFO and reporting semantics

At ex-date allocate earned income and the fixed claim across the then-existing FIFO lots. Keep entitlement ownership after those lots are partially or fully sold. Closed matching segments retain their proportionate accrued income; the remainder belongs to open lots. A later payment clears the separate claim ledger, rather than looking for the original lot among current holdings or crediting newly purchased shares.

Keep earned dividend income, cash dividend payments and outstanding receivable amounts as separate fields. Closed-lot economic P&L can include earned but unpaid income only if this definition and the unpaid portion are visible. It must not be called cash-realized profit. Payment alone must not increase prior economic P&L, win rate or asset contribution a second time. Existing moving-average acquisition-cost display and FIFO realized/unrealized decomposition remain separate conventions.

New independent lot analysis must prove both: closed-plus-open allocated earned income equals all accruals, and total paid plus final unpaid claim amounts equals all accruals. Per-entitlement and per-symbol amounts, cash snapshots, receivable snapshots and NAV all need reconciliation. Portfolio contribution is additive accounting, not causal factor attribution or evidence of alpha.

## 7. Schema and migration gate

Version new dataset/action and result/experiment semantics. At minimum add a noncash dividend entitlement/accrual ledger, a payment-event identity, outstanding receivable state in every relevant snapshot, and explicit cash-payment records. A separate DIVIDEND_PAYMENT event avoids pretending that a payment has the ex-date action's effective timestamp. Existing applied_actions can continue to mean source actions accrued; payment coverage needs its own references and uniqueness check.

Configuration must record the dividend accounting model, payment-availability convention, amount basis and initial-state policy. Compatible benchmarks must use the same rules and dividend basis. A legacy ex-date-cash run and a payment-accounting run must be visibly incompatible for ordinary pooled ranking, or explicitly identified as a controlled assumption-sensitivity comparison.

Preserve all existing source snapshots, report hashes, finalized experiments and legacy tests/evidence. Read old records under their original legacy semantics. Do not fill missing pay dates, rewrite hashes or reinterpret old DIVIDEND cash records. Newly saved inputs with additional verified terms have new content hashes/schema identity. Retained legacy-mode regression cases remain explicitly legacy diagnostics and cannot qualify the payment-date acceptance gate. New ordinary-cash research should use the new model and fail closed if required evidence is absent.

## 8. Independent financial acceptance cases

1. **Hand-worked NAV conservation:** hold 10 shares at USD100, no other cash; ordinary dividend USD1, ex-price USD99. At ex-date cash stays0, receivable10, shares990, NAV1000. At modeled payment availability cash10/receivable0/NAV1000. Neither event creates a second return.
2. **Spendability:** a proposed pre-payment purchase cannot use that USD10 claim. After availability it can use only paid cash subject to the existing costs and cash reserve.
3. **Ex-open boundary:** before-ex buyers qualify; ex-open buyers do not; ex-open sellers qualify. Event order is explicit and independently checked.
4. **Sold before payment:** sell all shares after ex-date and before payment. The right survives; payment credits the frozen amount with current holdings zero.
5. **Repurchase:** repurchase before payment after a complete exit. The prior claim is paid once; replacement shares acquire none of that old entitlement.
6. **Partial exit and multiple lots:** independently split the earned amount among closed segments and open lots. Aggregate income and cash/receivable reconciliation must agree with a manual ledger.
7. **Split/reverse split between ex and pay:** share count and acquisition-cost units change; the already fixed USD claim does not. No doubled or halved payout. Fractional holdings follow the stated existing policy.
8. **Ambiguous same-day split/ex-date:** missing share-unit basis is rejected, not resolved by source-list order.
9. **Non-session payment date:** weekend/holiday source date remains intact; modeled availability is deterministic and never earlier than the documented policy.
10. **Unknown/invalid dates:** absent pay date, non-session ex-date, ordinary pay-before-ex, or unsupported special/due-bill type fails with an auditable reason and no invented success.
11. **Late knowledge and amendments:** information known only after a historical event cannot be backfilled into strict decisions or past cash/NAV. Future unavailable evidence and later prices cannot rewrite earlier events.
12. **Evaluation truncation:** end-before-pay retains the claim; start-after-ex creates no entitlement without an explicit initial-state record. Extending the run to payment only reclassifies assets.
13. **RAW-only economics:** cash actions on split-adjusted or total-return price series are rejected under the raw-action model. Benchmark and strategy use matching dividend semantics.
14. **Identity and idempotence:** duplicate accrual/payment, unknown claim, wrong symbol/currency, amount mismatch, missing cash event or missing receivable snapshot fails independent reconstruction.
15. **Rounding and extremes:** finite small/large amounts, fractional split holdings and zero-valued declared dividends produce finite consistent ledgers or an explicit rejection; tolerance and any rounding convention are recorded.
16. **Unchanged observations:** no-dividend runs preserve their previous economic results; genuine dividend runs preserve immutable old legacy artifacts while new-model outputs carry a distinct schema/configuration.

Implementation acceptance additionally requires full unit/property/integration and independent-accounting regression, report/UI exposure and receivable disclosure, persisted CSV/JSON artifacts, clean wheel/core operation, CLI/MCP smoke, dependency/security checks and real CI. This review supplies a design and a test specification only; none of these new payment-model gates is claimed passed.
