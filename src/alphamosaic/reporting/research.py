"""Source-linked Markdown and self-contained HTML research reports."""

import html
import json
from pathlib import Path
from typing import Any


def write_report(path: Path, item: dict[str, Any]) -> None:
    c, r = item["config"], item["result"]
    sections = {
        "Executive Summary": f"Research only. {r['acceptance']}. No demonstrated alpha. Experiment {item['experiment_id']}.",
        "Research Question": c["question"],
        "Data & Provenance": json.dumps({"dataset_id": c["dataset_id"], "hash": item["dataset_hash"], "basis": item["return_basis"], "dataset": item["dataset_manifest"], "code": item["reproducibility"]}, indent=2),
        "Strategy Definition": json.dumps({"strategy": c["strategy"], "symbols": c["symbols"], "start": r["equity"][0]["session"], "end": r["equity"][-1]["session"]}, indent=2),
        "Backtest Assumptions": json.dumps(c["replay"], indent=2),
        "Performance and Risk": json.dumps(item["analysis"], indent=2),
        "Transaction Costs": json.dumps({k: r[k] for k in ("fees", "slippage_cost", "spread_cost", "turnover")}, indent=2),
        "Robustness": "Run the cost and parameter cases separately; no best-result selection or automatic promotion.",
        "Out-of-Sample Validation": c["validation"] + "; declared dates are not a certification of an untouched holdout. " + json.dumps(item.get("holdout_audit", {})),
        "Comparison to Benchmarks": c["benchmark"] + "; comparison status: " + item["analysis"]["benchmark_status"] + "; compare only when compatible; no fabricated risk-free series.",
        "Counterarguments and Limitations": "\n".join(item["warnings"]),
        "Further Research": "Acquire independently reviewed PIT/corporate-action/delisting data; freeze hypothesis before a new holdout.",
    }
    (path / "report.md").write_text("# AlphaMosaic Research Report\n\n" + "\n\n".join(f"## {k}\n\n{v}" for k, v in sections.items()), encoding="utf-8")
    chart = ""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.08)
        traces = [(c["strategy"], r["equity"])]
        if item["analysis"]["benchmark_status"] == "COMPARABLE_SIMULATED_RETURNS":
            traces.append((c["benchmark"], item["benchmark_result"]["equity"]))
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
        fig.update_layout(template="plotly_dark", title=f"{r['acceptance']} · {item['return_basis']} · {c['strategy']} · {item['experiment_id'][:8]}<br>{r['equity'][0]['session']} — {r['equity'][-1]['session']} · UTC · {provider}<br>{costs} · benchmark {c['benchmark']} · {c['validation']}", height=700)
        fig.update_yaxes(title_text="NAV / initial cash", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown", tickformat=".0%", row=2, col=1)
        chart = fig.to_html(full_html=False, include_plotlyjs=True)
    except ImportError:
        chart = "<p>Optional Plotly unavailable; complete numeric evidence is in experiment.json and CSV artifacts.</p>"
    body = "".join(f"<section><h2>{html.escape(k)}</h2><pre>{html.escape(v)}</pre></section>" for k, v in sections.items())
    (path / "report.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AlphaMosaic research</title><style>body{background:#101721;color:#dee6ef;font:15px system-ui;margin:4vw auto;max-width:1200px;padding:24px}h1,h2{color:#73dfbf}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{border-top:1px solid #304153;padding:16px 0}</style><h1>AlphaMosaic · Research Report</h1>' + chart + body + '</html>', encoding="utf-8")
