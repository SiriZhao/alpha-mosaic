"""Source-linked Markdown and self-contained HTML research reports."""

import html
import json
from pathlib import Path
from typing import Any


def benchmark_display_points(item: dict[str, Any]) -> tuple[str, list[dict[str, Any]]] | None:
    """Return chart points for either a replay benchmark or a typed reference."""
    if item.get("benchmark_result") is not None:
        result = item["benchmark_result"]
        return str(item["config"].get("benchmark", "BENCHMARK")), result["equity"]
    reference = item.get("benchmark_reference")
    if reference is not None:
        spec = reference["spec"]
        return str(spec["name"]), [{"session": point["session"], "nav": point["nav"]}
            for point in reference["points"]]
    return None


def dividend_accounting_evidence(item: dict[str, Any]) -> dict[str, Any]:
    """Describe recorded accounting semantics without filling absent legacy evidence."""
    config, result = item["config"]["replay"], item["result"]
    model = config.get("dividend_accounting", "LEGACY_EX_DATE_CASH")
    evidence = {"accounting_schema_version": config.get("accounting_schema_version", 1),
                "dividend_accounting": model,
                "missing_legacy_fields": "dividend_accounting" not in config}
    if model == "PAY_DATE_RECEIVABLE":
        evidence.update(payment_availability=config.get("payment_availability", "NOT_RECORDED"),
                        entitlements=result.get("dividend_entitlements"),
                        payments=result.get("dividend_payments"),
                        final_receivables=result["equity"][-1].get("receivables"),
                        convention="Earned income accrues with a non-spendable ex-date receivable. Payment transfers that claim to cash without recognizing income twice. Declared payment timing is a simulation policy, not verified broker posting time.")
    else:
        evidence.update(convention="Legacy effective/ex-date cash credit. Payment-date availability and unpaid entitlements are not modeled; absent claim records are not evidence of zero pending dividends.")
    return evidence


def weekly_feature_evidence(item: dict[str, Any]) -> dict[str, Any]:
    """Keep the signal's price hypothesis distinct from portfolio return accounting."""
    config, result = item["config"]["replay"], item["result"]
    policy = config.get("weekly_feature_policy", "LEGACY_REJECT_RAW_ACTIONS")
    signals = result.get("signals", [])
    rows = [row for signal in signals for row in signal.get("feature_evidence", [])]
    return {"requested_policy": policy, "recorded_feature_rows": len(rows),
        "signals_with_features": sum(bool(signal.get("feature_evidence")) for signal in signals),
        "consumption_status": "RECORDED_DERIVED_PRICE_FEATURES" if rows else "NO_DERIVED_FEATURES_RECORDED",
        "portfolio_return_basis": item.get("return_basis", "NOT_RECORDED"),
        "feature_return_basis": "PRICE_ONLY_EXCLUDES_DIVIDENDS" if rows else "NOT_RECORDED",
        "feature_pit_status": "NOT_APPLICABLE" if rows else "NOT_RECORDED",
        "convention": "Split-only derived closes use the last complete available week's share units. Ordinary dividend income is excluded from the signal feature; portfolio dividend rights and cash follow the separate recorded accounting model. Raw observations determine fills, liquidity and marks. Derived features are not observed quotes or certified PIT data.",
        "artifact": "weekly_price_features.csv" if item.get("artifact_schema_version", 1) >= 4 else "Per-signal feature_evidence when recorded; no separate legacy feature export"}


def write_report(path: Path, item: dict[str, Any]) -> None:
    c, r = item["config"], item["result"]
    analysis = item["analysis"]
    trades, weekly = analysis.get("trade_analysis", {}), analysis.get("weekly", {})
    code = {key: item["reproducibility"].get(key) for key in ("git_sha", "git_dirty", "python", "lock_hash", "source_hash")}
    sections = {
        "Executive Summary": f"Research only. {r['acceptance']}. No demonstrated alpha. Experiment {item['experiment_id']}.",
        "Research Question": c["question"],
        "Data & Provenance": json.dumps({"dataset_id": c["dataset_id"], "hash": item["dataset_hash"], "basis": item["return_basis"], "benchmark_basis": item.get("benchmark_return_basis", "NOT_RECORDED"), "dataset": item["dataset_manifest"], "code": code}, indent=2),
        "Strategy Definition": json.dumps({"strategy": c["strategy"], "symbols": c["symbols"], "start": r["equity"][0]["session"], "end": r["equity"][-1]["session"]}, indent=2),
        "Backtest Assumptions": json.dumps(c["replay"], indent=2),
        "Dividend Accounting": json.dumps(dividend_accounting_evidence(item), indent=2),
        "Weekly Signal Price Features": json.dumps(weekly_feature_evidence(item), indent=2),
        "Performance and Risk": json.dumps({k: analysis.get(k) for k in ("metrics", "conventions", "benchmark_status", "drawdown_episodes")}, indent=2),
        "Matched Trades and Accounting Contribution": json.dumps({"status": trades.get("status", "NOT_EVALUATED"), "conventions": trades.get("conventions"), "reconciliation": trades.get("reconciliation"), "assets": trades.get("asset_attribution")}, indent=2),
        "Weekly Research View": json.dumps({"status": weekly.get("status", "NOT_EVALUATED"), "metrics": weekly.get("metrics"), "conventions": weekly.get("conventions"), "partial_intervals": weekly.get("weekly_equity", {}).get("partial_intervals", []), "inception_return_through_last_completed_week": weekly.get("weekly_equity", {}).get("inception_return_through_last_completed_week"), "decision_frequency": c["replay"].get("decision_frequency", "DAILY"), "warnings": weekly.get("warnings", [])}, indent=2),
        "Transaction Costs": json.dumps({k: r[k] for k in ("fees", "slippage_cost", "spread_cost", "turnover")}, indent=2),
        "Robustness": "Run the cost and parameter cases separately; no best-result selection or automatic promotion.",
        "Out-of-Sample Validation": c["validation"] + "; declared dates are not a certification of an untouched holdout. " + json.dumps(item.get("holdout_audit", {})),
        "Comparison to Benchmarks": c["benchmark"] + "; comparison status: " + item["analysis"]["benchmark_status"] + "; compare only when compatible; no fabricated risk-free series.",
        "Counterarguments and Limitations": "\n".join(item["warnings"]),
        "Further Research": "Acquire independently reviewed PIT/corporate-action/delisting data; freeze hypothesis before a new holdout.",
        "Audit Artifacts": "Complete numeric evidence is in experiment.json; full configuration in config.json. CSV exports retain daily/weekly equity, signals, orders, fills, cash, split revisions, closed/open FIFO matches and asset accounting contributions; payment-model artifacts additionally retain entitlement/payment records. No best-case-only selection.",
    }
    (path / "report.md").write_text("# AlphaMosaic Research Report\n\n" + "\n\n".join(f"## {k}\n\n{v}" for k, v in sections.items()), encoding="utf-8")
    chart = ""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.08)
        traces = [(c["strategy"], r["equity"])]
        benchmark_points = benchmark_display_points(item)
        if benchmark_points is not None and item["analysis"]["benchmark_status"].startswith("COMPARABLE"):
            traces.append(benchmark_points)
        for label, points in traces:
            fig.add_trace(go.Scatter(x=[p["session"] for p in points], y=[p["nav"] / c["replay"]["initial_cash"] for p in points], name=label), row=1, col=1)
        peak = c["replay"]["initial_cash"]
        underwater = []
        for p in r["equity"]:
            peak = max(peak, p["nav"])
            underwater.append(p["nav"] / peak - 1)
        fig.add_trace(go.Scatter(x=[p["session"] for p in r["equity"]], y=underwater, name="Drawdown", fill="tozeroy"), row=2, col=1)
        provider = html.escape(", ".join(item["dataset_manifest"]["provider"]))
        costs = ", ".join(f"{k}={c['replay'][k]}" for k in ("fee_bps", "slippage_bps", "spread_bps"))
        model = html.escape(c["replay"].get("dividend_accounting", "LEGACY_EX_DATE_CASH"))
        feature = html.escape(c["replay"].get("weekly_feature_policy", "LEGACY_REJECT_RAW_ACTIONS"))
        benchmark = html.escape((c.get("benchmark_spec") or {}).get("name", c.get("benchmark", "NOT_RECORDED")))
        fig.update_layout(template="plotly_dark", title=f"{r['acceptance']} · {item['return_basis']} · {c['strategy']} · {item['experiment_id'][:8]}<br>{r['equity'][0]['session']} — {r['equity'][-1]['session']} · UTC · {provider}<br>{costs} · benchmark {benchmark} · {c['validation']}<br>Dividend model: {model} · signal policy: {feature}", height=720)
        fig.update_yaxes(title_text="NAV / initial cash", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown", tickformat=".0%", row=2, col=1)
        chart = fig.to_html(full_html=False, include_plotlyjs=True)
    except ImportError:
        chart = "<p>Optional Plotly unavailable; complete numeric evidence is in experiment.json and CSV artifacts.</p>"
    body = "".join(f"<section><h2>{html.escape(k)}</h2><pre>{html.escape(v)}</pre></section>" for k, v in sections.items())
    (path / "report.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AlphaMosaic research</title><style>body{background:#101721;color:#dee6ef;font:15px system-ui;margin:4vw auto;max-width:1200px;padding:24px}h1,h2{color:#73dfbf}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{border-top:1px solid #304153;padding:16px 0}</style><h1>AlphaMosaic · Research Report</h1>' + chart + body + '</html>', encoding="utf-8")
