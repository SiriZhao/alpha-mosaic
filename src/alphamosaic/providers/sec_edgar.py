"""Small, opt-in SEC companyfacts adapter with conservative PIT extraction."""

import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx

from alphamosaic.core.contracts import (
    CompanyFundamentals,
    DataQuality,
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
                if datetime.combine(filed, datetime.min.time(), tzinfo=UTC) <= cutoff and filed >= date(2000, 1, 1):
                    # Annual values only: FY or duration >= 300 days avoids mixing quarters.
                    fp = str(item.get("fp", ""))
                    start = item.get("start")
                    duration = (end - date.fromisoformat(str(start)[:10])).days if start else 0
                    if fp == "FY" or duration >= 300:
                        eligible.append((filed, end, item))
            except (KeyError, TypeError, ValueError):
                continue
        if not eligible:
            return None, None
        eligible.sort(key=lambda row: (row[0], row[1]))
        chosen = eligible[-1][2]
        try:
            return float(chosen["val"]), chosen
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
        net_income, _ = value("NetIncomeLoss")
        assets, _ = value("Assets")
        liabilities, _ = value("Liabilities")
        operating_cf, _ = value("NetCashProvidedByUsedInOperatingActivities")
        capex, _ = value("PaymentsToAcquirePropertyPlantAndEquipment")
        if revenue is None and net_income is None:
            return None
        filed = date.fromisoformat(str((rev_item or {}).get("filed", cutoff.date()))[:10])
        fiscal_year = (rev_item or {}).get("fy")
        fcf = operating_cf - abs(capex) if operating_cf is not None and capex is not None else None
        return CompanyFundamentals(
            symbol=symbol, source="SEC EDGAR companyfacts", source_url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
            observed_at=min(utc_now(), cutoff), known_at=datetime.combine(filed, datetime.min.time(), tzinfo=UTC), as_of=cutoff,
            currency="USD", data_quality=DataQuality.HISTORICAL, adjustment_policy="NOT_APPLICABLE",
            provenance={"cik": f"{cik:010d}", "selection": "latest filed annual fact at cutoff"}, license_scope="SEC public data; verify downstream use",
            fiscal_period=(rev_item or {}).get("end"), fiscal_year=int(fiscal_year) if fiscal_year else None,
            revenue=revenue, net_income=net_income, debt=liabilities, net_debt=None,
            free_cash_flow=fcf, filing_date=filed,
            operating_margin=(net_income / revenue) if revenue and net_income is not None else None,
            missing_fields=[name for name, item in {"revenue": revenue, "net_income": net_income, "assets": assets, "free_cash_flow": fcf}.items() if item is None],
        )
