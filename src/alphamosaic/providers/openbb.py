"""OpenBB V5 Nasdaq adapter; no synthetic fallback and no real-time claim."""

import json
import re
import subprocess
import sys
from datetime import date, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import exchange_calendars as xcals

from alphamosaic.core.contracts import (
    CompanyFundamentals,
    DataBatch,
    DataQuality,
    HistoricalBar,
    ProviderEvidence,
    ProviderHealth,
    SecurityIdentity,
    Status,
    utc_now,
)

SOURCE = "OpenBB V5 / Nasdaq public website"
LICENSE_SCOPE = (
    "Nasdaq website terms; personal noncommercial research; no data redistribution grant"
)


def classify_error(text: str) -> Status:
    lowered = text.lower()
    if "429" in lowered or "quota" in lowered or "rate limit" in lowered:
        return Status.QUOTA
    if "timeout" in lowered or "timed out" in lowered:
        return Status.TIMEOUT
    if "empty" in lowered or "no historical" in lowered or "no results" in lowered:
        return Status.EMPTY
    if "validation" in lowered or "jsondecode" in lowered:
        return Status.INVALID_DATA
    return Status.NETWORK_ERROR


class OpenBBDataProvider:
    def __init__(self, runtime: Path, timeout: float = 40, fundamentals: bool = False):
        self.runtime = runtime.resolve()
        self.timeout = timeout
        self.fundamentals = fundamentals
        self.last_universe_evidence: list[ProviderEvidence] = []

    def health(self) -> ProviderHealth:
        try:
            installed = version("openbb-core")
            nasdaq = version("openbb-nasdaq")
            status = Status.OK if installed == "2.0.1" and nasdaq == "2.0.0" else Status.UNSUPPORTED
        except PackageNotFoundError:
            installed, status = None, Status.NOT_INSTALLED
        return ProviderHealth(
            name="openbb-nasdaq",
            status=status,
            checked_at=utc_now(),
            version=installed,
            capabilities=[
                "US_UNIVERSE",
                "HISTORICAL_OHLCV",
                "PROFILE",
                "INCOME_STATEMENT",
                "RATIOS",
                "ETF_BENCHMARK",
                "INDEX_HISTORY",
            ],
            diagnostics=[
                "Installation health only; live access tested separately",
                "No API key required for selected website endpoints",
                "Macro providers need separate adapters; not connected",
            ],
        )

    def _request(
        self, operation: str, **params: Any
    ) -> tuple[dict[str, Any], datetime, datetime, Status]:
        requested = utc_now()
        if self.health().status != Status.OK:
            return (
                {"diagnostics": ["OpenBB extra missing or unsupported version"]},
                requested,
                utc_now(),
                self.health().status,
            )
        request = {
            "operation": operation,
            "runtime": str(self.runtime),
            "timeout": self.timeout,
            **params,
        }
        try:
            result = subprocess.run(
                [sys.executable, "-m", "alphamosaic.integrations.openbb_worker"],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout + 8,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode:
                response = {"diagnostics": [f"worker exited {result.returncode}"]}
                status = Status.UNAVAILABLE
            else:
                response = json.loads(result.stdout)
                status = (
                    Status.OK if response.get("status") == "OK" else classify_error(str(response))
                )
                if status != Status.OK:
                    response["diagnostics"] = [
                        f"{response.get('error_type')}: {response.get('error', '')}"
                    ]
        except subprocess.TimeoutExpired:
            response, status = (
                {"diagnostics": ["Isolated worker deadline exceeded"]},
                Status.TIMEOUT,
            )
        except (OSError, ValueError):
            response, status = (
                {"diagnostics": ["Worker transport/JSON failure"]},
                Status.INVALID_DATA,
            )
        return response, requested, utc_now(), status

    @staticmethod
    def _evidence(
        operation: str,
        symbol: str | None,
        requested: datetime,
        completed: datetime,
        status: Status,
        rows: list[dict[str, Any]],
        diagnostics: list[str],
    ) -> ProviderEvidence:
        url = (
            "https://api.nasdaq.com/api/screener/stocks?download=true"
            if symbol is None
            else f"https://www.nasdaq.com/market-activity/{'etf' if symbol in {'SPY', 'QQQM'} else 'stocks'}/{symbol.lower()}/historical"
        )
        return ProviderEvidence(
            symbol=symbol,
            source=SOURCE,
            source_url=url,
            observed_at=completed,
            known_at=completed,
            as_of=completed,
            currency="USD",
            data_quality=DataQuality.HISTORICAL,
            adjustment_policy="UNKNOWN",
            provenance={
                "adapter": "OpenBB Fetcher SDK",
                "openbb-core": "2.0.1",
                "openbb-nasdaq": "2.0.0",
            },
            license_scope=LICENSE_SCOPE,
            endpoint=operation,
            requested_at=requested,
            completed_at=completed,
            status=status,
            row_count=len(rows),
            fields=sorted({key for row in rows for key in row}),
            diagnostics=diagnostics,
        )

    def universe(self, limit: int) -> tuple[list[SecurityIdentity], str]:
        response, requested, completed, status = self._request("universe")
        rows = response.get("rows", [])
        self.last_universe_evidence = [
            self._evidence(
                "universe",
                None,
                requested,
                completed,
                status,
                rows,
                response.get("diagnostics", []),
            )
        ]
        if status != Status.OK:
            return [], "OpenBB Nasdaq current screener unavailable"
        # Bound the price-fetch budget AFTER discovery from the broad accessible pool.
        # Current large-cap sample is a research universe, not historical index membership.
        rows.sort(key=lambda row: float(row.get("market_cap") or 0), reverse=True)
        identities: list[SecurityIdentity] = []
        seen: set[str] = set()
        for row in rows:
            symbol = str(row.get("symbol", "")).upper()
            name = str(row.get("name", "")).lower()
            if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", symbol) or symbol in seen:
                continue
            if any(word in name for word in ("preferred", "warrant", "depositary shares", "units")):
                continue
            seen.add(symbol)
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    exchange=row["exchange"],
                    currency="USD",
                    active=True,
                    identity_source=SOURCE + " exchange-filtered screener",
                    identity_verified=True,
                    as_of=completed,
                )
            )
            if len(identities) == limit:
                break
        return (
            identities,
            "Nasdaq current Nasdaq/NYSE/AMEX screener; market-cap budget sample; survivorship-biased",
        )

    def history(self, symbol: str, start: date, end: date) -> DataBatch:
        response, requested, completed, status = self._request(
            "history", symbol=symbol, start=str(start), end=str(end), fundamentals=self.fundamentals
        )
        rows = response.get("rows", [])
        diagnostics = response.get("diagnostics", [])
        evidence = self._evidence(
            "history+profile" + ("+fundamentals" if self.fundamentals else ""),
            symbol,
            requested,
            completed,
            status,
            rows,
            diagnostics,
        )
        if status != Status.OK:
            return DataBatch(evidence=[evidence], status=status)
        try:
            profile = (response.get("profile") or [{}])[0]
            exchange = str(profile.get("exchange") or "").upper()
            etf = symbol in {"SPY", "QQQM"}
            identity = SecurityIdentity(
                symbol=symbol,
                exchange=exchange or "UNKNOWN",
                currency="USD",
                active=bool(profile.get("name")) or etf,
                identity_source=SOURCE + " current profile",
                identity_verified=bool(exchange and profile.get("name")),
                security_type="ETF" if etf else "STOCK",
                as_of=completed,
            )
            calendar = xcals.get_calendar("XNYS")
            bars = []
            for row in rows:
                session = date.fromisoformat(str(row["date"])[:10])
                if not start <= session <= end:
                    raise ValueError("bar outside requested date range")
                close_time = calendar.session_close(session).to_pydatetime()
                bars.append(
                    HistoricalBar(
                        symbol=symbol,
                        source=SOURCE,
                        source_url=evidence.source_url,
                        session=session,
                        observed_at=close_time,
                        known_at=completed,
                        as_of=completed,
                        currency="USD",
                        data_quality=DataQuality.HISTORICAL,
                        adjustment_policy="UNKNOWN",
                        provenance={
                            "retrieved_at": completed.isoformat(),
                            "pit": "reconstructed; revisions not certified",
                        },
                        license_scope=LICENSE_SCOPE,
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"],
                    )
                )
            fundamental = None
            raw = response.get("fundamentals") or {}
            if raw:
                fields = {
                    key: raw.get(key) for key in ("revenue", "net_income", "return_on_equity")
                }
                fundamental = CompanyFundamentals(
                    symbol=symbol,
                    source=SOURCE,
                    source_url=f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/financials",
                    observed_at=completed,
                    known_at=completed,
                    as_of=completed,
                    currency="USD",
                    data_quality=DataQuality.HISTORICAL,
                    adjustment_policy="NOT_APPLICABLE",
                    provenance={
                        "publication_time": "not supplied; conservatively known at retrieval"
                    },
                    license_scope=LICENSE_SCOPE,
                    fiscal_period=date.fromisoformat(str(raw["date"])[:10])
                    if raw.get("date")
                    else None,
                    revenue=fields["revenue"], net_income=fields["net_income"], return_on_equity=fields["return_on_equity"],
                    missing_fields=[key for key, value in fields.items() if value is None]
                    + ["pe_ratio", "equity", "debt", "market_cap", "published_at"],
                )
            return DataBatch(
                identity=identity,
                bars=bars,
                fundamentals=fundamental,
                evidence=[evidence],
                status=Status.OK if bars else Status.EMPTY,
            )
        except (ValueError, KeyError, TypeError) as exc:
            invalid = evidence.model_copy(
                update={
                    "status": Status.INVALID_DATA,
                    "diagnostics": diagnostics
                    + [f"Normalization rejected: {type(exc).__name__}: {exc}"],
                }
            )
            return DataBatch(evidence=[invalid], status=Status.INVALID_DATA)
