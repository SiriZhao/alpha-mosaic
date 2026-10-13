"""Immutable run bundles; no arbitrary MCP file lookup."""

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from alphamosaic.core.contracts import ScanReport
from alphamosaic.data.validation import completed_session


def verify(report: ScanReport) -> None:
    if not re.fullmatch(r"[a-f0-9]{32}", report.run_id):
        raise ValueError("invalid run id")
    if report.eligible_count > report.universe_count or len(report.candidates) > report.eligible_count:
        raise ValueError("inconsistent universe/candidate counts")
    if [item.rank for item in report.candidates] != list(range(1, len(report.candidates) + 1)):
        raise ValueError("invalid ranking sequence")
    if len({item.ticker for item in report.candidates}) != len(report.candidates):
        raise ValueError("duplicate candidate")
    if any(item.known_at > report.cutoff for item in report.evidence):
        raise ValueError("future provider evidence")
    if any(item.data_timestamp > report.cutoff for item in report.candidates):
        raise ValueError("future candidate observation")
    if any(fact.known_at > report.cutoff for item in report.candidates for fact in item.factor_evidence.values()):
        raise ValueError("future factor evidence")
    if report.acceptance == "REAL_DATA" and any(item.data_quality.value == "FIXTURE" for item in report.candidates):
        raise ValueError("fixture candidate in real report")


def _publish(root: Path, name: str, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    directory = root / name
    if directory.exists():
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("unsafe report directory")
        if all((directory / key).is_file() and not (directory / key).is_symlink() and (directory / key).read_text(encoding="utf-8") == value for key, value in files.items()):
            return directory
        raise FileExistsError("immutable report conflict")
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
    try:
        for key, value in files.items():
            with (staging / key).open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
        if directory.exists():
            raise FileExistsError("concurrent report publication")
        os.rename(staging, directory)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return directory


def markdown(report: ScanReport) -> str:
    lines = [
        "# AlphaMosaic research opportunities",
        "",
        f"Conclusion: {report.assessment.get('RESEARCH_READINESS', 'LEGACY_NOT_VERIFIED')} | investment action: NO_ACTION",
        f"Benchmark validity: {report.assessment.get('BENCHMARK_VALIDITY', 'LEGACY_NOT_VERIFIED')} | factor coverage: {report.assessment.get('FACTOR_COVERAGE', 'LEGACY_NOT_VERIFIED')}",
        f"Run: {report.run_id} | {report.status} | {report.acceptance}",
        f"Cutoff: {report.cutoff.isoformat()}",
        f"Universe: {report.universe_name} ({report.universe_count} requested; {report.eligible_count} eligible)",
        f"Source: {report.universe_source}",
        "",
        "Research and human review only. Heuristic ranks are not return probabilities. NO_VALIDATED_ALPHA.",
        "",
        "## Research contract",
        "",
        f"- Objective: bounded evidence-first opportunity research for `{report.universe_name}`.",
        f"- Cutoff: `{report.cutoff.isoformat()}`; created: `{report.created_at.isoformat()}`.",
        f"- Acceptance: `{report.acceptance}`; broker enabled: `{report.broker_enabled}`.",
        "- Values are sourced or missing; no synthetic prices, returns, news, or inferred fills are permitted.",
        "- Ranking is a heuristic ordering, not a return probability or investment advice.",
        "",
        "| Baseline rank | Ticker | Baseline score | Research score | Weight coverage | Missing |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for candidate in report.candidates:
        lines.append(
            f"| {candidate.rank} | {candidate.ticker} | {candidate.score:.4f} | {candidate.research_score} | {candidate.factor_coverage} | {', '.join(candidate.missing_fields)} |"
        )
    if len(report.candidates) < 10:
        lines += ["", f"Only {len(report.candidates)} qualifying candidates available; no padding."]
    for candidate in report.candidates:
        lines += [
            "",
            f"## {candidate.ticker}",
            f"Data: {candidate.data_timestamp.isoformat()} | {candidate.source} | {candidate.data_quality}",
            f"Research priority: {candidate.research_priority}",
            *[f"- {reason}" for reason in candidate.reasons],
            "- Hypothesis (research only): test whether the observed trend persists; historical momentum is not a return forecast.",
            f"- Fundamental/valuation support: ROE={candidate.factors.get('quality_roe')}; earnings yield={candidate.factors.get('value_earnings_yield')}; revenue growth={candidate.factors.get('growth_revenue')}. Null means missing evidence.",
            "- Catalyst evidence: NOT_CONFIGURED. Do not infer an event from price movement.",
            "- Downside scenario/invalidation: trend reversal, insufficient liquidity, stale prices or contradictory issuer disclosures. These are research conditions, not verified forecasts.",
            "",
            "```json",
            json.dumps(candidate.factors, indent=2, allow_nan=False),
            "```",
        ]
    lines += ["", "## Request evidence", ""]
    for evidence in report.evidence:
        lines.append(
            f"- {evidence.symbol or 'UNIVERSE'}: {evidence.status}; {evidence.row_count} rows; requested {evidence.requested_at.isoformat()}; completed {evidence.completed_at.isoformat()}; {evidence.source_url}; fields: {', '.join(evidence.fields)}; diagnostics: {'; '.join(evidence.diagnostics)}"
        )
    lines += [
        "",
        "## Exclusions",
        "",
        "```json",
        json.dumps(report.exclusions, indent=2),
        "```",
        "",
        "## Limitations",
        "",
        *[f"- {warning}" for warning in report.warnings],
        "",
        "## Reproducibility and provider status",
        "",
        f"- Reproducible run ID: `{report.run_id}`.",
        "- Model version: deterministic AlphaMosaic factor pipeline (repository source hash is recorded by the run environment).",
        "- Provider availability is reported per evidence row and is independent of signal validity.",
        "- Historical, out-of-sample, and forward evidence levels are preserved in the evaluation object; missing evaluation means `NOT_RUN`.",
        f"- Evaluation state: {report.evaluation_status}; {report.evaluation_diagnostics}",
        f"- Source manifest: {json.dumps(report.runtime_manifest, sort_keys=True)}",
        "- Known limitations include survivorship, corporate actions, licensing, point-in-time availability, and provider outages where applicable.",
    ]
    if report.evaluation:
        lines += [
            "",
            "## Historical implementation diagnostic",
            "",
            "```json",
            report.evaluation.model_dump_json(indent=2),
            "```",
        ]
    return "\n".join(lines) + "\n"


class ReportStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def save(self, report: ScanReport) -> Path:
        verify(report)
        payload = {
            "schema_version": "2.0",
            "report": report.model_dump(mode="json"),
            "contract": {
                "research_only": True,
                "broker_enabled": False,
                "missing_values": "preserved",
                "synthetic_data": False,
            },
        }
        return _publish(self.root, report.run_id, {"report.json": json.dumps(payload, indent=2, allow_nan=False), "report.md": markdown(report)})

    def get(self, run_id: str) -> ScanReport | None:
        if not re.fullmatch(r"[a-f0-9]{32}", run_id):
            raise ValueError("invalid run id")
        directory = self.root / run_id
        path = directory / "report.json"
        if directory.is_symlink() or path.is_symlink():
            raise ValueError("symlink report rejected")
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        report = ScanReport.model_validate(raw.get("report", raw))
        if report.run_id != run_id:
            raise ValueError("report/run id mismatch")
        verify(report)
        return report

    def finalize(self, run_id: str, timezone: str = "Asia/Shanghai") -> Path:
        report = self.get(run_id)
        if report is None:
            raise ValueError("unknown report run id")
        zone = ZoneInfo(timezone)
        input_path = self.root / run_id / "report.json"
        input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
        rendered = markdown(report)
        bundle = {
            "run_id": run_id, "report_date": report.cutoff.astimezone(zone).date().isoformat(),
            "completed_session": completed_session(report.cutoff).isoformat(),
            "timezone": timezone, "report_verification": "PASSED",
            "software_acceptance": "NOT_VERIFIED", "investment_action": "NO_ACTION",
            "generator_version": "daily-v2", "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "input_path": str(input_path), "input_sha256": input_hash,
            "source_version": report.runtime_manifest,
            "external_web_check": "NOT_RUN", "report": report.model_dump(mode="json"),
        }
        raw = json.dumps(bundle, sort_keys=True, indent=2, allow_nan=False)
        hashes = json.dumps({"daily.json": hashlib.sha256(raw.encode()).hexdigest(), "daily.md": hashlib.sha256(rendered.encode()).hexdigest()}, indent=2)
        key = hashlib.sha256(raw.encode()).hexdigest()
        return _publish(self.root / run_id / "derived", key, {"daily.json": raw, "daily.md": rendered, "sha256.json": hashes})

    def latest(self) -> ScanReport | None:
        if not self.root.exists():
            return None
        # Only generated, validated run IDs in this configured report root.
        paths = [
            item / "report.json"
            for item in self.root.iterdir()
            if item.is_dir() and not item.is_symlink() and re.fullmatch(r"[a-f0-9]{32}", item.name)
        ]
        reports = []
        for path in paths:
            if path.is_file() and not path.is_symlink():
                raw = json.loads(path.read_text(encoding="utf-8"))
                # Read both the versioned envelope and pre-1.0 bundles.
                report = ScanReport.model_validate(raw.get("report", raw))
                if report.run_id == path.parent.name:
                    reports.append(report)
        return max(reports, key=lambda report: report.created_at) if reports else None
