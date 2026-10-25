"""Present persisted research evidence without recomputing strategy statistics."""

from html import escape
from textwrap import shorten
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def evidence_caption(item: dict[str, Any]) -> str:
    config, manifest = item["config"], item.get("dataset_manifest", {})
    points = item["result"]["equity"]
    costs = config["replay"]
    return (
        f"{item.get('acceptance', 'MISSING')} · {item.get('return_basis', 'MISSING')} · "
        f"{points[0]['session']} — {points[-1]['session']} · UTC · "
        f"provider {', '.join(manifest.get('provider', [])) or 'NOT_RECORDED'} · "
        f"dataset as-of {manifest.get('cutoff', 'NOT_RECORDED')} · "
        f"dataset {config['dataset_id']} · experiment {item['experiment_id']} · "
        f"benchmark {config['benchmark']} · fees/slippage/spread bps "
        f"{costs.get('fee_bps')}/{costs.get('slippage_bps')}/{costs.get('spread_bps')}"
    )


def qualify_figure(fig: go.Figure, items: list[dict[str, Any]]) -> None:
    """Keep provenance in exported figures as well as the surrounding terminal."""
    item = items[0]
    points, config = item["result"]["equity"], item["config"]
    provider = ", ".join(item.get("dataset_manifest", {}).get("provider", [])) or "NOT_RECORDED"
    costs = config["replay"]
    lines = [
        f"{item.get('acceptance', 'MISSING')} · {item.get('return_basis', 'MISSING')} · {points[0]['session']} — {points[-1]['session']} UTC · benchmark {config['benchmark']}",
        f"Provider {shorten(provider, width=85)} · dataset {config['dataset_id'][:12]}",
        f"Experiment {item['experiment_id']} · fees/slippage/spread bps {costs.get('fee_bps')}/{costs.get('slippage_bps')}/{costs.get('spread_bps')}"
        if len(items) == 1 else "Each legend records its experiment and fee/slippage/spread bps; full configurations and provenance accompany the chart.",
    ]
    fig.add_annotation(x=0, y=-0.22, xref="paper", yref="paper", xanchor="left", yanchor="top",
                       text="<br>".join(escape(line) for line in lines), showarrow=False, align="left", font=dict(size=10))
    fig.update_layout(meta={"research_provenance": [evidence_caption(record) for record in items]},
                      height=int(fig.layout.height or 360) + 100, margin=dict(b=140))


def _chart(frame: pd.DataFrame, columns: list[str], title: str, axis: str, item: dict[str, Any]) -> None:
    fig = go.Figure()
    for column in columns:
        fig.add_trace(go.Scatter(x=frame["session"], y=frame[column], name=column, connectgaps=False))
    fig.update_layout(template="plotly_dark", height=360, title=title, yaxis_title=axis,
                      margin=dict(l=20, r=20, t=50, b=20))
    qualify_figure(fig, [item])
    st.plotly_chart(fig, width="stretch")


def risk_views(item: dict[str, Any]) -> None:
    analysis = item["analysis"]
    st.subheader("Persisted risk evidence")
    st.caption(evidence_caption(item))
    metrics = analysis["metrics"]
    for col, label, key, percent in zip(st.columns(4),
        ("Maximum drawdown", "Annualized volatility", "Sharpe", "Average market exposure"),
        ("max_drawdown", "volatility", "sharpe", "market_exposure"), (True, True, False, True), strict=True):
        value = metrics.get(key)
        col.metric(label, "Undefined / missing" if value is None else f"{value:.2%}" if percent else f"{value:.3f}")
    rolling_tab, exposure_tab, accounting_tab, drawdown_tab = st.tabs(
        ["Rolling risk", "Exposure and concentration", "Costs and asset accounting", "Drawdown episodes"])
    with rolling_tab:
        conventions = analysis.get("conventions", {})
        st.caption(f"Daily exchange-session returns; {conventions.get('periods_per_year', 'NOT_RECORDED')} periods/year. "
                   f"Window: {conventions.get('rolling_window_sessions', 'NOT_RECORDED')} sessions. "
                   f"Risk-free annual rate: {conventions.get('risk_free_annual', 'NOT_RECORDED')}. "
                   "Warmup and undefined ratios remain gaps; weekly strategy decisions do not change this daily risk convention.")
        rolling = pd.DataFrame(analysis.get("rolling", []))
        choices = [key for key in ("volatility", "sharpe", "beta", "correlation", "tracking_error", "information_ratio")
                   if key in rolling and not rolling[key].dropna().empty]
        if choices:
            metric = str(st.selectbox("Rolling statistic", choices))
            _chart(rolling, [metric], "Rolling " + metric.replace("_", " "), metric, item)
        else:
            st.info("No qualified rolling statistics for this sample or benchmark.")
        st.caption("Beta and correlation describe association with the recorded simulated benchmark; they do not establish causal attribution.")
    with exposure_tab:
        exposure = pd.DataFrame(analysis.get("exposures", []))
        if not exposure.empty:
            sessions = [point["session"] for point in item["result"]["equity"]]
            missing_sessions = len(set(sessions) - set(exposure["session"]))
            # Preserve old artifacts: absent legacy rows are unknown, never inferred zeros.
            exposure = pd.DataFrame({"session": sessions}).merge(exposure, on="session", how="left", validate="one_to_one")
            for field in ("cash_weight", "concentration_hhi"):
                if field not in exposure:
                    exposure[field] = None
            if missing_sessions:
                st.warning(f"Legacy exposure coverage omits {missing_sessions} equity sessions; explicit gaps preserve the original evidence.")
            _chart(exposure, ["cash_weight"], "Cash weight", "Cash / NAV", item)
            _chart(exposure, ["concentration_hhi"], "Invested-asset concentration", "Sum of squared asset weights in total NAV", item)
            st.caption("HHI uses asset weights in total NAV; cash is shown separately. No sector or factor exposures are inferred.")
            if len(exposure["concentration_hhi"].dropna()) < len(exposure):
                st.warning("Some concentration observations lack reconciled position marks; missing sessions remain explicit gaps.")
            st.dataframe(exposure, width="stretch", hide_index=True)
        else:
            st.info("Position-level exposure evidence is unavailable in this experiment.")
    with accounting_tab:
        attribution = analysis.get("attribution", {})
        costs = {key: attribution.get(key) for key in ("fees_usd", "slippage_usd", "spread_usd")}
        known = {key: value for key, value in costs.items() if value is not None}
        missing = [key for key, value in costs.items() if value is None]
        if missing:
            st.warning("Cost components not recorded: " + ", ".join(missing))
        if known:
            fig = go.Figure(go.Bar(x=list(known), y=list(known.values())))
            fig.update_layout(template="plotly_dark", title="Simulated explicit execution costs", yaxis_title="USD", height=330)
            qualify_figure(fig, [item])
            st.plotly_chart(fig, width="stretch")
        st.caption("Slippage and spread are already in fill prices; only fees are separately debited. "
                   "This decomposition must not be subtracted from NAV again or interpreted as a counterfactual return difference.")
        trades = analysis.get("trade_analysis", {})
        if trades.get("status") == "VERIFIED":
            st.dataframe(trades["asset_attribution"], width="stretch", hide_index=True)
            st.json(trades["reconciliation"], expanded=False)
        else:
            st.info("Independently reconciled asset accounting is unavailable for this legacy result.")
        st.caption("Cost sensitivity requires separate predeclared realistic/stress experiments, available through a frozen research plan. "
                   "No cash interest or factor contribution is invented.")
    with drawdown_tab:
        episodes = analysis.get("drawdown_episodes")
        if episodes is None:
            st.info("Drawdown episodes were not recorded for this experiment.")
        elif episodes:
            st.dataframe(episodes, width="stretch", hide_index=True)
            st.caption("Unrecovered episodes retain a missing recovery date. Duration counts daily underwater exchange sessions.")
        else:
            st.info("No drawdown episodes in this recorded simulation.")
        st.write(analysis.get("warnings", []))


def comparison_views(items: list[dict[str, Any]], comparison: dict[str, Any]) -> None:
    rows = []
    for entry in comparison["experiments"]:
        costs = entry["cost_model"]
        rows.append({"experiment_id": entry["experiment_id"], "strategy": entry["strategy"],
                     "fees_bps": costs["fee_bps"], "slippage_bps": costs["slippage_bps"],
                     "spread_bps": costs.get("spread_bps"), **entry["metrics"]})
    st.dataframe(rows, width="stretch", hide_index=True)
    configurations = [{"experiment_id": item["experiment_id"], "strategy": item["config"]["strategy"],
                       **item["config"]["replay"]} for item in items]
    st.subheader("Simulation assumptions")
    st.dataframe(configurations, width="stretch", hide_index=True)
    st.caption("Realistic and stress presets may jointly change fees, cash buffers and participation limits. "
               "Compare the full configurations; their difference is not a fee-only counterfactual.")
    if comparison["status"] != "COMPARABLE":
        st.warning("Dataset, code, evidence, dates, return basis, validation or benchmark differ; overlaid curves and pooled ranking are blocked.")
        st.json(comparison, expanded=False)
        return
    st.success("Comparable dataset, code, dates, return basis, evidence, validation and benchmark; costs may intentionally differ.")
    kind = st.radio("Comparison curve", ["Normalized equity", "Underwater"], horizontal=True)
    fig = go.Figure()
    for item in items:
        points = item["result"]["equity"]
        if kind == "Underwater":
            rolling = item["analysis"]["rolling"]
            values = [row["drawdown"] for row in rolling]
            sessions = [row["session"] for row in rolling]
        else:
            values = [point["nav"] / item["config"]["replay"]["initial_cash"] for point in points]
            sessions = [point["session"] for point in points]
        costs = item["config"]["replay"]
        label = f"{item['config']['strategy']} · {item['experiment_id'][:8]} · {costs.get('fee_bps')}/{costs.get('slippage_bps')}/{costs.get('spread_bps')} bps"
        fig.add_trace(go.Scatter(x=sessions, y=values, name=label, connectgaps=False))
        st.caption(evidence_caption(item))
    fig.update_layout(template="plotly_dark", height=440, yaxis_title="NAV / own initial cash" if kind == "Normalized equity" else "Drawdown", title="Qualified experiment comparison")
    qualify_figure(fig, items)
    st.plotly_chart(fig, width="stretch")
    st.caption("All selected outcomes remain visible. Sorting metrics is exploratory research, not a future-return probability or strategy promotion.")
