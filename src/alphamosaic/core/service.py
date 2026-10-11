"""The single application orchestration boundary used by CLI and MCP."""

import os
import platform
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from uuid import uuid4

from alphamosaic import __version__
from alphamosaic.backtesting.diagnostic import trend_diagnostic
from alphamosaic.core.contracts import DataQuality, DecisionProposal, ScanReport, Status, utc_now
from alphamosaic.data.validation import completed_session, market_state, validate_batch
from alphamosaic.integrations.registry import IntegrationRegistry
from alphamosaic.portfolio.risk import assess_risk
from alphamosaic.providers.openbb import OpenBBDataProvider
from alphamosaic.providers.protocol import DataProvider
from alphamosaic.reporting.store import ReportStore
from alphamosaic.research_engine import ResearchEngine
from alphamosaic.screening.scanner import OpportunityScanner, ResearchQueue
from alphamosaic.screening.universe import (
    Universe,
    UniverseManager,
    UniversePool,
    normalize_symbols,
)


class ApplicationService:
    def __init__(self, home: Path | None = None, provider: DataProvider | None = None):
        self.home = (home or Path(os.environ.get("ALPHAMOSAIC_HOME", "runtime"))).resolve()
        self.provider = provider or OpenBBDataProvider(self.home)
        self.store = ReportStore(self.home / "reports")
        self.lock = threading.RLock()
        self.research_engine = ResearchEngine(self.provider, self.home)
        from alphamosaic.opportunity_pipeline import OpportunityDiscoveryPipeline
        self.opportunity_pipeline = OpportunityDiscoveryPipeline(self)

    def status(self) -> dict[str, Any]:
        now = utc_now()
        dependencies = {}
        for name in (
            "pydantic",
            "mcp",
            "openbb-core",
            "openbb-nasdaq",
            "openbb-sec",
            "quantstats",
            "exchange-calendars",
            "numpy",
            "pandas",
            "typer",
        ):
            try:
                dependencies[name] = version(name)
            except PackageNotFoundError:
                dependencies[name] = "NOT_INSTALLED"
        return {
            "name": "AlphaMosaic",
            "version": __version__,
            "python": platform.python_version(),
            "checked_at": now.isoformat(),
            "market": market_state(now),
            "completed_session": str(completed_session(now)),
            "broker_enabled": False,
            "mode": "RESEARCH_ONLY",
            "signal_validity": "NO_VALIDATED_ALPHA",
            "dependencies": dependencies,
            "providers": self.providers(),
            "integrations": self.integrations(),
        }

    def providers(self) -> list[dict[str, Any]]:
        from alphamosaic.providers.sec_edgar import SecEdgarAdapter
        return [self.provider.health().model_dump(mode="json"), SecEdgarAdapter(self.home / "sec-cache").health().model_dump(mode="json")]

    def discover_opportunities(
        self, mode: str = "FAST", universe_limit: int = 30, top: int = 10, deep: int = 3,
        pool: str = "BROAD_LIQUIDITY", symbols: list[str] | None = None, resume: bool = False,
    ) -> dict[str, Any]:
        report = self.opportunity_pipeline.run(mode, universe_limit, top, deep, UniversePool(pool), symbols, resume)
        return report.model_dump(mode="json")

    def provider_health(self) -> dict[str, Any]:
        return {"status": "READY" if self.provider.health().status == Status.OK else "DEGRADED", "providers": self.providers()}

    def integrations(self) -> list[dict[str, Any]]:
        return [item.model_dump(mode="json") for item in IntegrationRegistry().records()]

    def research(self, symbols: list[str], profile: str = "FAST") -> list[dict[str, Any]]:
        with self.lock:
            return [item.model_dump(mode="json") for item in self.research_engine.research(symbols, profile)]

    def compare(self, symbols: list[str]) -> dict[str, Any]:
        if not 2 <= len(symbols) <= 10:
            raise ValueError("compare requires 2..10 symbols")
        snapshots = [self.analyze(symbol) for symbol in dict.fromkeys(symbols)]
        return {"status": "READY" if any(item["status"] == "OK" for item in snapshots) else "DEGRADED", "symbols": snapshots}

    def research_portfolio(self, symbols: list[str], profile: str = "FAST") -> dict[str, Any]:
        if not 1 <= len(symbols) <= 5:
            raise ValueError("portfolio research requires 1..5 symbols")
        decisions = self.research(symbols, profile)
        return {"status": "READY" if decisions else "DEGRADED", "broker_enabled": False, "decisions": decisions}

    def run_backtest(
        self,
        symbol: str,
        strategy: str = "momentum",
        out_of_sample: bool = False,
        fee_bps: float = 10,
    ) -> dict[str, Any]:
        if strategy.lower() not in {"momentum", "trend", "buy_and_hold"}:
            return {"status": "BLOCKED", "diagnostics": ["strategy is not in the transparent baseline registry"]}
        end = completed_session(utc_now())
        start = end - timedelta(days=750)
        batch = self.provider.history(symbol.upper(), start, end)
        benchmarks = {
            name: self.provider.history(name, start, end).bars for name in ("SPY", "QQQM")
        }
        if batch.status != Status.OK or len(batch.bars) < 65:
            return {"status": "DEGRADED", "symbol": symbol.upper(), "diagnostics": [batch.status.value]}
        result = trend_diagnostic(batch.bars, benchmarks, fee_bps=fee_bps, out_of_sample=out_of_sample)
        return {"status": "READY", "symbol": symbol.upper(), "strategy": strategy.lower(), "result": result.model_dump(mode="json")}

    def evaluate_strategy(self, symbol: str, strategy: str = "momentum") -> dict[str, Any]:
        return self.run_backtest(symbol, strategy, out_of_sample=True)

    def signal_history(self, symbol: str | None = None) -> dict[str, Any]:
        return {"status": "NOT_CONFIGURED", "symbol": symbol, "signals": [], "diagnostics": ["forward signal store is not initialized"]}

    def forward_performance(self, symbol: str | None = None) -> dict[str, Any]:
        return {"status": "NOT_CONFIGURED", "symbol": symbol, "observations": [], "diagnostics": ["no forward observations have been recorded"]}

    def investment_report(self, symbols: list[str], profile: str = "FAST") -> dict[str, Any]:
        result = self.research_portfolio(symbols, profile)
        return {"status": result["status"], "report_type": "RESEARCH_ONLY", "broker_enabled": False, **result}

    def scan(
        self,
        universe_limit: int = 30,
        top: int = 10,
        symbols: list[str] | None = None,
        universe: Universe | None = None,
        persist: bool = True,
        evaluate: bool = True,
    ) -> ScanReport:
        if not 1 <= universe_limit <= 100 or not 1 <= top <= 10:
            raise ValueError("universe_limit 1..100 and top 1..10 required")
        with self.lock:
            manager = UniverseManager(self.provider)
            selected = universe or (
                manager.specified(symbols)
                if symbols is not None
                else manager.discover(universe_limit)
            )
            now = utc_now()
            end = completed_session(now)
            start = end - timedelta(days=190)
            requested = (
                list(dict.fromkeys([*selected.symbols, "SPY", "QQQM"])) if selected.symbols else []
            )
            # At most three bounded read-only workers; no retries or provider substitution.
            with ThreadPoolExecutor(max_workers=3) as executor:
                batches = dict(
                    zip(
                        requested,
                        executor.map(
                            lambda symbol: self.provider.history(symbol, start, end), requested
                        ),
                        strict=True,
                    )
                )
            cutoff = utc_now()
            candidates, exclusions, eligible = OpportunityScanner().scan(
                {symbol: batches[symbol] for symbol in selected.symbols},
                batches.get("SPY"),
                cutoff,
                top,
            )
            decisions = [
                DecisionProposal(
                    symbol=item.ticker,
                    action="RESEARCH",
                    rationale=item.reasons,
                    risk=assess_risk(item.ticker, item.factors),
                )
                for item in candidates
            ]
            evidence = (
                list(getattr(self.provider, "last_universe_evidence", []))
                if universe is None and symbols is None
                else []
            )
            evidence.extend(item for batch in batches.values() for item in batch.evidence)
            warnings = [
                "No broker execution; human review required",
                "Discovery samples currently listed US stocks, not a full-market profitability claim",
                "Historical data reconstructed at retrieval, not certified Point-in-Time",
                "Unknown adjustment, corporate actions and historical delistings prevent investment-grade backtest acceptance",
                "Fundamental/valuation factors remain null when unavailable",
                "News, AI multi-agent verdicts and forward performance not connected",
            ]
            evaluation = None
            if evaluate and candidates:
                try:
                    # Deterministic ticker choice, NOT selecting the highest-ranked winner.
                    target = sorted(item.ticker for item in candidates)[0]
                    evaluation = trend_diagnostic(
                        batches[target].bars,
                        {
                            symbol: batches[symbol].bars
                            for symbol in ("SPY", "QQQM")
                            if symbol in batches and batches[symbol].status == Status.OK
                        },
                    )
                    warnings.append(
                        f"Diagnostic instrument: {target}; current-universe selection is survivorship-biased"
                    )
                except (ImportError, ValueError) as exc:
                    warnings.append(f"Evaluation unavailable: {type(exc).__name__}")
            quality = {item.data_quality for item in candidates}
            if DataQuality.FIXTURE in quality and len(quality) > 1:
                raise ValueError("real and fixture candidates cannot be mixed")
            if len(candidates) < 10:
                warnings.append(
                    f"Only {len(candidates)} candidates qualified; no synthetic padding"
                )
            report = ScanReport(
                run_id=uuid4().hex,
                created_at=cutoff,
                cutoff=cutoff,
                status=Status.OK
                if candidates and not exclusions
                else Status.PARTIAL
                if candidates
                else Status.EMPTY,
                universe_name=selected.name,
                universe_source=selected.source,
                universe_count=len(selected.symbols),
                eligible_count=eligible,
                candidates=candidates,
                research_queue=ResearchQueue().build(candidates),
                decisions=decisions,
                evidence=evidence,
                exclusions=exclusions,
                evaluation=evaluation,
                acceptance="FIXTURE" if quality == {DataQuality.FIXTURE} else "REAL_DATA",
                warnings=warnings,
            )
            if persist:
                self.store.save(report)
            return report

    def analyze(self, symbol: str) -> dict[str, Any]:
        normalized = normalize_symbols([symbol])
        if len(normalized) != 1:
            raise ValueError("one symbol required")
        end = completed_session(utc_now())
        batch = self.provider.history(normalized[0], end - timedelta(days=190), end)
        flags = validate_batch(batch.identity, batch.bars, utc_now())
        return {
            "symbol": normalized[0],
            "status": batch.status.value,
            "identity": batch.identity.model_dump(mode="json") if batch.identity else None,
            "snapshot": batch.bars[-1].model_dump(mode="json") if batch.bars else None,
            "fundamentals": batch.fundamentals.model_dump(mode="json")
            if batch.fundamentals
            else None,
            "evidence": [item.model_dump(mode="json") for item in batch.evidence],
            "flags": flags,
            "verdict": "INSUFFICIENT_EVIDENCE",
            "broker_enabled": False,
        }

    def latest_report(self) -> dict[str, Any]:
        report = self.store.latest()
        return (
            report.model_dump(mode="json")
            if report
            else {"status": "NO_REPORT", "broker_enabled": False}
        )

    def ranking(self) -> dict[str, Any]:
        report = self.store.latest()
        return (
            {
                "status": report.status.value,
                "run_id": report.run_id,
                "cutoff": report.cutoff.isoformat(),
                "candidates": [item.model_dump(mode="json") for item in report.candidates],
            }
            if report
            else {"status": "NO_REPORT", "candidates": []}
        )
