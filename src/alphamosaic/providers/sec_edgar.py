"""Small, opt-in SEC companyfacts adapter with conservative PIT extraction."""

import math
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from alphamosaic.core.contracts import (
    CompanyFundamentals,
    DataQuality,
    FinancialField,
    ProviderHealth,
    Status,
    utc_now,
)


class SecEdgarAdapter:
    def __init__(self, cache_dir: Path | None = None, timeout: float = 15.0) -> None:
        self.cache_dir = (cache_dir or Path("runtime") / "sec-cache").resolve()
        self.timeout = timeout
        self.user_agent = os.environ.get("ALPHAMOSAIC_SEC_USER_AGENT", "").strip()

    def health(self) -> ProviderHealth:
        configured = "@" in self.user_agent and len(self.user_agent) >= 10
        return ProviderHealth(
            name="sec-edgar",
            status=Status.OK if configured else Status.NOT_CONFIGURED,
            checked_at=utc_now(),
            capabilities=["COMPANY_FACTS", "ANNUAL_FILINGS", "PIT_FACTS"],
            diagnostics=["official SEC JSON endpoints", "User-Agent with contact required"]
            if configured else ["set ALPHAMOSAIC_SEC_USER_AGENT='Name contact@example.com'"],
            version="SEC public data API",
        )

    def _get(self, url: str) -> dict[str, Any]:
        if self.health().status != Status.OK:
            raise RuntimeError("SEC provider is not configured")
        headers = {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}
        response = httpx.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("SEC response is not an object")
        return payload

    @staticmethod
    def _latest(units: list[dict[str, Any]], cutoff: datetime) -> tuple[float | None, dict[str, Any] | None]:
        eligible = []
        for item in units:
            try:
                filed = date.fromisoformat(str(item["filed"])[:10])
                end = date.fromisoformat(str(item["end"])[:10])
                if datetime.combine(filed + timedelta(days=1), datetime.min.time(), tzinfo=UTC) <= cutoff and filed >= date(2000, 1, 1):
                    # Annual values only: FY or duration >= 300 days avoids mixing quarters.
                    fp = str(item.get("fp", ""))
                    start = item.get("start")
                    duration = (end - date.fromisoformat(str(start)[:10])).days if start else 0
                    if (300 <= duration <= 400 if start else fp == "FY") and item.get("form", "10-K") in {"10-K", "10-K/A", "20-F", "20-F/A"}:
                        eligible.append((filed, end, item))
            except (KeyError, TypeError, ValueError):
                continue
        if not eligible:
            return None, None
        eligible.sort(key=lambda row: (row[1], row[0]))
        chosen = eligible[-1][2]
        try:
            number = float(chosen["val"])
            return (number if math.isfinite(number) else None), chosen
        except (KeyError, TypeError, ValueError):
            return None, chosen

    @classmethod
    def _same_annual_period(
        cls,
        units: list[dict[str, Any]],
        cutoff: datetime,
        anchor: dict[str, Any],
    ) -> tuple[float | None, dict[str, Any] | None]:
        """Select a fact from the anchor's fiscal year and annual period only."""
        anchor_end = str(anchor.get("end", ""))[:10]
        anchor_fy = anchor.get("fy")
        candidates: list[tuple[date, dict[str, Any]]] = []
        for item in units:
            try:
                filed = date.fromisoformat(str(item["filed"])[:10])
                end = date.fromisoformat(str(item["end"])[:10])
                start = item.get("start")
                duration = (end - date.fromisoformat(str(start)[:10])).days if start else 0
                if (
                    datetime.combine(filed + timedelta(days=1), datetime.min.time(), tzinfo=UTC) <= cutoff
                    and str(item.get("end", ""))[:10] == anchor_end
                    and (anchor_fy is None or item.get("fy") in {None, anchor_fy})
                    and (300 <= duration <= 400 if start else str(item.get("fp", "")) == "FY")
                    and item.get("form", "10-K") in {"10-K", "10-K/A", "20-F", "20-F/A"}
                    and (
                        not start
                        or not anchor.get("start")
                        or str(start)[:10] == str(anchor.get("start"))[:10]
                    )
                ):
                    candidates.append((filed, item))
            except (KeyError, TypeError, ValueError):
                continue
        if not candidates:
            return None, None
        candidates.sort(key=lambda row: row[0])
        chosen = candidates[-1][1]
        try:
            number = float(chosen["val"])
            return (number if math.isfinite(number) else None), chosen
        except (KeyError, TypeError, ValueError):
            return None, chosen

    def fundamentals(self, symbol: str, cutoff: datetime | None = None) -> CompanyFundamentals | None:
        cutoff = cutoff or utc_now()
        if cutoff.tzinfo is None:
            raise ValueError("cutoff must be timezone aware")
        symbol = symbol.upper()
        # SEC submissions are intentionally queried only after explicit opt-in UA.
        ticker_payload = self._get("https://www.sec.gov/files/company_tickers.json")
        cik = None
        for row in ticker_payload.values():
            if str(row.get("ticker", "")).upper() == symbol:
                cik = int(row["cik_str"])
                break
        if cik is None:
            return None
        facts = self._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        usgaap = facts.get("facts", {}).get("us-gaap", {})
        def value(*names: str) -> tuple[float | None, dict[str, Any] | None]:
            for name in names:
                units = usgaap.get(name, {}).get("units", {}).get("USD", [])
                item = self._latest(units, cutoff)
                if item[0] is not None:
                    return item
            return None, None
        revenue, rev_item = value("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax")
        if rev_item is None:
            _, rev_item = value("NetIncomeLoss", "Assets")
        if rev_item is None:
            return None

        def same_value(*names: str) -> tuple[float | None, dict[str, Any] | None]:
            for name in names:
                units = usgaap.get(name, {}).get("units", {}).get("USD", [])
                item = self._same_annual_period(units, cutoff, rev_item)
                if item[0] is not None:
                    return item
            return None, None

        # Every value below is constrained to the same fiscal end as the
        # revenue anchor. This prevents mixing a newly filed quarter or a
        # different fiscal year into one fundamentals object.
        net_income, net_income_item = same_value("NetIncomeLoss")
        assets, assets_item = same_value("Assets")
        equity, equity_item = same_value("StockholdersEquity")
        cash, cash_item = same_value("CashAndCashEquivalentsAtCarryingValue")
        debt_items = [same_value(name) for name in ("LongTermDebt", "LongTermDebtCurrent", "LongTermDebtNoncurrent", "ShortTermBorrowings")]
        # LongTermDebt may already include the current portion. Never add the
        # aggregate and its components. Report incomplete coverage as null.
        total_long, current_long, noncurrent_long, short = [item[0] for item in debt_items]
        long_debt = total_long if total_long is not None else (
            current_long + noncurrent_long
            if current_long is not None and noncurrent_long is not None else None
        )
        debt = long_debt + short if long_debt is not None and short is not None else None
        operating_income, operating_income_item = same_value("OperatingIncomeLoss")
        operating_cf, operating_cf_item = same_value("NetCashProvidedByUsedInOperatingActivities")
        capex, capex_item = same_value("PaymentsToAcquirePropertyPlantAndEquipment")
        if revenue is None and net_income is None:
            return None
        selected_items = [rev_item, net_income_item, assets_item, equity_item, cash_item, operating_income_item, operating_cf_item, capex_item]
        selected_items.extend(item[1] for item in debt_items if item[1] is not None)
        filed = max(
            date.fromisoformat(str(item.get("filed", cutoff.date()))[:10])
            for item in selected_items
            if item is not None
        )
        fiscal_year = (rev_item or {}).get("fy")
        fcf = operating_cf - abs(capex) if operating_cf is not None and capex is not None else None
        end_date = date.fromisoformat(str(rev_item["end"]))
        prior_units = []
        for name in ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"):
            for item in usgaap.get(name, {}).get("units", {}).get("USD", []):
                try:
                    if 300 <= (end_date - date.fromisoformat(item["end"])).days <= 400:
                        prior_units.append(item)
                except (KeyError, TypeError, ValueError):
                    continue
        prior_revenue, prior_item = self._latest(prior_units, cutoff)
        growth = revenue / prior_revenue - 1 if revenue is not None and prior_revenue is not None and prior_revenue > 0 else None
        if prior_item:
            selected_items.append(prior_item)
            filed = max(filed, date.fromisoformat(str(prior_item["filed"])))
        known = datetime.combine(filed + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
        source_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
        values = {
            "revenue": revenue, "net_income": net_income, "assets": assets,
            "equity": equity, "debt": debt, "operating_cash_flow": operating_cf,
            "free_cash_flow": fcf, "revenue_growth": growth,
            "net_margin": net_income / revenue if net_income is not None and revenue and revenue > 0 else None,
            "operating_margin": operating_income / revenue if operating_income is not None and revenue and revenue > 0 else None,
            "net_debt": debt - cash if debt is not None and cash is not None else None,
        }
        ids = sorted({str(item.get("accn", "UNAVAILABLE")) + ":" + str(item.get("end")) + ":" + str(item.get("filed")) for item in selected_items if item})
        evidence = {name: FinancialField(value=number, unit="ratio" if name in {"revenue_growth", "net_margin", "operating_margin"} else "USD", period_end=end_date, known_at=known, source_url=source_url, evidence_ids=ids, definition={"free_cash_flow": "annual operating cash flow minus absolute capex", "revenue_growth": "same-unit consecutive annual revenue ratio minus one", "net_margin": "same-period annual net income/revenue", "net_debt": "nonoverlapping covered debt minus cash"}.get(name, "same-period annual US-GAAP USD fact; no ROE/ROIC inferred")) for name, number in values.items()}
        observed = utc_now()
        return CompanyFundamentals(
            symbol=symbol, source="SEC EDGAR companyfacts", source_url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
            observed_at=observed, known_at=known, as_of=max(observed, cutoff),
            currency="USD", data_quality=DataQuality.HISTORICAL, adjustment_policy="NOT_APPLICABLE",
            provenance={"cik": f"{cik:010d}", "selection": "same fiscal end annual facts filed by cutoff", "anchor_end": str(rev_item.get("end"))}, license_scope="SEC public data; verify downstream use",
            fiscal_period=(rev_item or {}).get("end"), fiscal_year=int(fiscal_year) if fiscal_year else None,
            revenue=values["revenue"], net_income=values["net_income"], assets=values["assets"],
            equity=values["equity"], debt=values["debt"], operating_cash_flow=values["operating_cash_flow"],
            free_cash_flow=values["free_cash_flow"], revenue_growth=values["revenue_growth"],
            net_margin=values["net_margin"], operating_margin=values["operating_margin"], net_debt=values["net_debt"],
            filing_date=filed, field_evidence=evidence,
            missing_fields=[name for name, item in values.items() if item is None] + ["return_on_equity", "return_on_invested_capital", "pe_ratio"],
        )
