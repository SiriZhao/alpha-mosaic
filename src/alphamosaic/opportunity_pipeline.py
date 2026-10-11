"""Bounded opportunity discovery orchestration built on the existing scan service."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

from alphamosaic.core.contracts import (
    OpportunityPipelineReport,
    OpportunitySummary,
    ResearchDecision,
    Status,
)
from alphamosaic.screening.archetypes import OpportunityArchetypeRegistry
from alphamosaic.screening.universe import UniverseManager, UniversePool


class OpportunityDiscoveryPipeline:
    def __init__(self, service: Any) -> None:
        self.service = service
        self.registry = OpportunityArchetypeRegistry()
        self.root = (service.home / "opportunities").resolve()

    def _write(self, report: OpportunityPipelineReport) -> Path:
        directory = self.root / report.run_id
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "opportunity_report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        lines = [
            "# AlphaMosaic opportunity discovery",
            "",
            f"Run `{report.run_id}` | status `{report.status}` | acceptance `{report.acceptance}`",
            f"Universe: {report.universe_name} ({report.universe_count}); successful data batches: {report.data_success_count}; excluded: {report.excluded_count}",
            f"Initial scan: `{report.initial_run_id}` cutoff `{report.initial_cutoff.isoformat()}`",
            "",
            "Heuristic rankings are research prioritisation only and are not return probabilities.",
            "",
            "| Initial | Deep | Symbol | Archetypes | Trend | Action boundary |",
            "|---:|---:|---|---|---|---|",
        ]
        for item in report.summaries:
            lines.append(f"| {item.initial_rank} | {item.deep_rank or '-'} | {item.symbol} | {', '.join(a.value for a in item.archetypes)} | {item.trend} | {'NO_ACTION' if item.no_action_reasons else 'RESEARCH_ONLY'} |")
            lines += ["", f"## {item.symbol}", "", *[f"- {x}" for x in item.thesis + item.catalysts + item.invalidations]]
            if item.factors:
                lines += ["", "```json", json.dumps(item.factors, indent=2, allow_nan=False), "```"]
        lines += ["", "## Provider boundaries", "", *[f"- {k}: {v}" for k, v in report.provider_health.items()], "", "## Warnings", "", *[f"- {x}" for x in report.warnings]]
        (directory / "opportunity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return directory

    def run(self, mode: str = "FAST", universe_limit: int = 30, top: int = 10, deep: int = 3,
            pool: UniversePool = UniversePool.BROAD_LIQUIDITY, symbols: list[str] | None = None,
            resume: bool = False) -> OpportunityPipelineReport:
        mode = mode.upper()
        if mode not in {"FAST", "DEEP"}:
            raise ValueError("mode must be FAST or DEEP")
        if not 1 <= deep <= min(3, top):
            raise ValueError("deep must be between 1 and top (maximum 3)")
        started = datetime.now(UTC)
        started_clock = time.perf_counter()
        config_key = f"{mode}|{universe_limit}|{top}|{deep}|{pool.value}|{','.join(sorted(symbols or []))}"
        checkpoint = self.root / "checkpoints" / (hashlib.sha256(config_key.encode()).hexdigest() + ".json")
        if resume and checkpoint.exists():
            cached = OpportunityPipelineReport.model_validate_json(checkpoint.read_text(encoding="utf-8"))
            return cached.model_copy(update={"resume_count": cached.resume_count + 1})
        manager = UniverseManager(self.service.provider)
        if symbols:
            universe = manager.specified(symbols, "User watchlist")
        elif pool == UniversePool.BROAD_LIQUIDITY:
            universe = manager.discover(universe_limit)
        else:
            universe = manager.discover_pool(pool, universe_limit)
        scan = self.service.scan(universe_limit=len(universe.symbols), top=top, universe=universe, persist=True, evaluate=False)
        summaries: list[OpportunitySummary] = []
        deep_outcomes: dict[str, Any] = {}
        if mode == "DEEP":
            for candidate in scan.candidates[:deep]:
                try:
                    results = self.service.research([candidate.ticker], profile="BALANCED")
                    deep_outcomes[candidate.ticker] = results[0] if results else {"status": "EMPTY"}
                except Exception as exc:  # isolate optional research failures per symbol
                    deep_outcomes[candidate.ticker] = {"status": "FAILED", "diagnostics": [type(exc).__name__]}
        for candidate in scan.candidates:
            outcome = deep_outcomes.get(candidate.ticker, {})
            decision = None
            if isinstance(outcome, dict) and outcome.get("fused_signal"):
                try:
                    decision = ResearchDecision.model_validate(outcome)
                except (TypeError, ValueError):
                    decision = None
            verdict = outcome.get("verdict") if isinstance(outcome, dict) else None
            direction = verdict.get("verdict") if isinstance(verdict, dict) else None
            reasons = ["No deep-research call requested in FAST mode"] if mode == "FAST" else ["Deep research executed; no independent rerank score configured"]
            no_action: list[str] = []
            provider_statuses = {"openbb": scan.status.value}
            if decision is not None:
                provider_statuses.update({item.source: item.status.value for item in decision.outcomes})
                if all(item.status in {Status.NOT_CONFIGURED, Status.UNAVAILABLE, Status.TIMEOUT, Status.NETWORK_ERROR} for item in decision.outcomes if item.source != "OpenBB/Nasdaq"):
                    no_action.append("optional external research providers unavailable")
            elif mode == "DEEP":
                no_action.append("deep research returned no validated decision")
            if direction in {"BLOCKED", "INSUFFICIENT_EVIDENCE", "REVIEW"}:
                no_action.append(f"research verdict {direction}")
            trend = "positive" if (candidate.factors.get("trend_20_60") or 0) > 0 else "negative or unavailable"
            summaries.append(OpportunitySummary(
                symbol=candidate.ticker, initial_rank=candidate.rank,
                deep_rank=None, archetypes=self.registry.categorize(candidate.factors),
                business_drivers=["Business and earnings evidence not connected in scan provider"],
                thesis=candidate.reasons, expectations=["No consensus estimate or return forecast supplied"],
                overlooked_factors=["SEC/company filings and estimates require separately configured providers"],
                valuation_risks=["Valuation fields missing or unvalidated"] if candidate.factors.get("value_earnings_yield") is None else ["Valuation is a heuristic factor"],
                catalysts=["No primary-source catalyst feed connected"], trend=trend,
                scenarios={"bear": "Trend reversal or data-quality failure", "base": "Signal persists within stated horizon", "bull": "Independent fundamentals and catalyst confirmation"},
                holding_horizon="2-16 weeks (archetype dependent)", invalidations=["stale data", "identity or adjustment mismatch", "trend reversal"],
                factors=candidate.factors, evidence_ids=[], provider_statuses=provider_statuses,
                no_action_reasons=no_action, rerank_reason=reasons[0] if reasons else None,
                archetype_gaps={item.value: ["verified prerequisites unavailable"] for item in self.registry.categorize(candidate.factors)},
                archetype_scores={item.value: None for item in self.registry.categorize(candidate.factors)},
                fundamentals=None, deep_decision=decision, data_timestamp=candidate.data_timestamp, risks=candidate.risks,
            ))
        # Deep rank is deliberately unchanged until a validated independent score exists.
        warnings = list(scan.warnings) + ["Current universe is survivorship-biased and not historical index membership", "SEC, analyst estimates, news and paid research are optional and may be unavailable", "No candidate is an order or a guaranteed opportunity"]
        health = {item["name"]: item["status"] for item in self.service.providers()}
        completed = datetime.now(UTC)
        report = OpportunityPipelineReport(
            run_id=uuid4().hex, mode=cast(Literal["FAST", "DEEP"], mode), started_at=started, completed_at=completed, cutoff=completed,
            universe_name=universe.name, universe_source=universe.source, universe_count=len(universe.symbols),
            data_success_count=scan.eligible_count, excluded_count=len(scan.exclusions),
            preliminary_count=len(scan.candidates), deep_count=len(deep_outcomes), elapsed_seconds=time.perf_counter() - started_clock,
            initial_run_id=scan.run_id, initial_cutoff=scan.cutoff, summaries=summaries, archetypes=self.registry.specs(),
            provider_health=health, warnings=warnings, status="READY" if summaries and not scan.exclusions else "DEGRADED" if summaries else "NO_ACTION",
            acceptance=scan.acceptance, scan=scan, external_call_count=len(deep_outcomes),
        )
        self._write(report)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return report
