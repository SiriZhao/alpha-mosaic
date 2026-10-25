"""Accounting disclosure must preserve missing evidence and distinct cash/claim records."""

from alphamosaic.reporting.research import dividend_accounting_evidence


def test_legacy_report_does_not_infer_zero_unpaid_claims_from_absent_fields() -> None:
    item = {"config": {"replay": {}}, "result": {"equity": [{"cash": 100}]}}
    evidence = dividend_accounting_evidence(item)
    assert evidence["accounting_schema_version"] == 1
    assert evidence["dividend_accounting"] == "LEGACY_EX_DATE_CASH"
    assert evidence["missing_legacy_fields"] is True
    assert "final_receivables" not in evidence and "payments" not in evidence
    assert "not modeled" in evidence["convention"]


def test_payment_disclosure_retains_claim_while_cash_and_payment_evidence_are_distinct() -> None:
    item = {"config": {"replay": {"accounting_schema_version": 2,
                "dividend_accounting": "PAY_DATE_RECEIVABLE",
                "payment_availability": "NEXT_XNYS_OPEN_AFTER_PAY_DATE"}},
            "result": {"equity": [{"cash": 0, "receivables": {"manual-fixture-claim": 10}}],
                       "dividend_entitlements": [{"entitlement_id": "manual-fixture-claim", "amount": 10}],
                       "dividend_payments": []}}
    evidence = dividend_accounting_evidence(item)
    assert evidence["final_receivables"] == {"manual-fixture-claim": 10}
    assert evidence["payments"] == []
    assert item["result"]["equity"][0]["cash"] == 0
    del item["result"]["dividend_payments"]
    assert dividend_accounting_evidence(item)["payments"] is None
