"""Immutable run bundles; no arbitrary MCP file lookup."""

import json
import re
from pathlib import Path

from alphamosaic.core.contracts import ScanReport


def markdown(report: ScanReport) -> str:
    lines = [
        "# AlphaMosaic research opportunities",
        "",
        f"Run: {report.run_id} | {report.status} | {report.acceptance}",
        f"Cutoff: {report.cutoff.isoformat()}",
        f"Universe: {report.universe_name} ({report.universe_count} requested; {report.eligible_count} eligible)",
        f"Source: {report.universe_source}",
        "",
        "Research and human review only. Heuristic ranks are not return probabilities. NO_VALIDATED_ALPHA.",
        "",
        "| Rank | Ticker | Score | Momentum 63d | Trend | Risks | Missing |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for candidate in report.candidates:
        lines.append(
            f"| {candidate.rank} | {candidate.ticker} | {candidate.score:.4f} | {candidate.factors['momentum_63d']:.2%} | {candidate.factors['trend_20_60']:.2%} | {', '.join(candidate.risks)} | {', '.join(candidate.missing_fields)} |"
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
        if not re.fullmatch(r"[a-f0-9]{32}", report.run_id):
            raise ValueError("invalid run id")
        directory = self.root / report.run_id
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        (directory / "report.md").write_text(markdown(report), encoding="utf-8")
        return directory

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
                report = ScanReport.model_validate_json(path.read_text(encoding="utf-8"))
                if report.run_id == path.parent.name:
                    reports.append(report)
        return max(reports, key=lambda report: report.created_at) if reports else None
