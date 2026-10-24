"""Local Streamlit research terminal backed by the authoritative application service."""

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from alphamosaic.core.service import ApplicationService

st.set_page_config(page_title="AlphaMosaic Research", page_icon="◈", layout="wide")
st.markdown("""<style>
.stApp{background:#0b111b}div[data-testid="stMetric"]{background:#131f30;border:1px solid #26394e;border-radius:9px;padding:16px}
h1,h2,h3{letter-spacing:-.025em}div[data-testid="stSidebar"]{background:#101b2b}
</style>""", unsafe_allow_html=True)


@st.cache_resource
def resources() -> tuple[ApplicationService, ThreadPoolExecutor]:
    return ApplicationService(), ThreadPoolExecutor(max_workers=1, thread_name_prefix="research-ui")


service, executor = resources()
st.sidebar.markdown("# ◈ AlphaMosaic\nRENAISSANCE / RESEARCH TERMINAL")
page = st.sidebar.radio("Workspace", ["Research Overview", "Data Explorer", "Strategy Lab", "Backtest Results", "Experiment Comparison", "Risk Lab", "AI Research", "Reports"])
st.sidebar.caption("Long only · Cash funded · USD\n\nResearch only · Broker disabled")
st.title(page)
st.caption("Versioned evidence → reproducible experiments → independent review")
st.info("Historical / synthetic research. No live quotes. FIXTURE results establish software behavior only; no demonstrated alpha.")


def plot_result(item: dict[str, Any], risk: bool = False) -> None:
    result, config = item["result"], item["config"]
    st.caption(f"{result['acceptance']} · {item['return_basis']} · {result['equity'][0]['session']} — {result['equity'][-1]['session']} · UTC · dataset {config['dataset_id']} · experiment {item['experiment_id']}")
    fig = go.Figure()
    traces = [(config["strategy"], result["equity"])]
    if item["analysis"]["benchmark_status"] == "COMPARABLE_SIMULATED_RETURNS":
        traces.append((config["benchmark"], item["benchmark_result"]["equity"]))
    else:
        st.warning("Benchmark comparison blocked: " + item["analysis"]["benchmark_status"])
    for label, points in traces:
        values = [p["nav"] / config["replay"]["initial_cash"] for p in points]
        if risk:
            peak = 1.0
            underwater = []
            for value in values:
                peak = max(peak, value)
                underwater.append(value / peak - 1)
            values = underwater
        fig.add_trace(go.Scatter(x=[p["session"] for p in points], y=values, name=label))
    fig.update_layout(template="plotly_dark", height=440, margin=dict(l=20, r=20, t=35, b=20), yaxis_title="Drawdown" if risk else "NAV / initial cash", title="Costs: " + str({k: config["replay"].get(k) for k in ("fee_bps", "slippage_bps", "spread_bps")}))
    st.plotly_chart(fig, width="stretch")


def select_result() -> dict[str, Any] | None:
    rows = [r for r in service.research_experiments() if r["status"] == "COMPLETED"]
    if not rows:
        st.warning("No completed experiments. Create a dataset, then run Strategy Lab.")
        return None
    selected = st.selectbox("Experiment", [r["experiment_id"] for r in rows])
    return service.research_result(str(selected))


if page == "Research Overview":
    datasets, experiments = service.research_datasets(), service.research_experiments()
    cols = st.columns(4)
    for col, label, value in zip(cols, ["Datasets", "Experiments", "Strategies", "Failed / interrupted"], [len(datasets), len(experiments), len(service.research_strategies()), sum(e["status"] != "COMPLETED" for e in experiments)], strict=True):
        col.metric(label, value)
    st.subheader("Latest experiments")
    st.dataframe(experiments, width="stretch")
    st.subheader("Research queue")
    st.write("Review data provenance and cost assumptions. Freeze a hypothesis before holdout evaluation. Acquire licensed corporate-action and delisting coverage before interpreting real historical performance.")
    if st.button("Create deterministic synthetic dataset", type="primary"):
        with st.spinner("Generating 504 exchange sessions; no market API calls"):
            manifest = service.research_demo()
        st.success("FIXTURE dataset registered: " + manifest["dataset_id"])
elif page == "Data Explorer":
    datasets = [d for d in service.research_datasets() if d.get("state") == "AVAILABLE"]
    if not datasets:
        st.warning("No local datasets. Create the offline demo in Research Overview.")
    else:
        dataset_id = st.selectbox("Versioned dataset", [d["dataset_id"] for d in datasets])
        store = service.experiment_runner().datasets
        manifest = store.manifest(dataset_id)
        st.json(manifest, expanded=False)
        data = store.load(dataset_id)
        symbol = st.selectbox("Instrument", list(data.bars))
        rows = [b.model_dump(mode="json") for b in data.bars[symbol]]
        st.caption("Provider: " + rows[0]["source"] + " · " + rows[0]["data_quality"] + " · adjustment: " + rows[0]["adjustment_policy"] + " · timezone: UTC · availability follows known_at")
        st.line_chart(pd.DataFrame(rows).set_index("session")[["close"]])
        st.dataframe(rows, width="stretch")
elif page == "Strategy Lab":
    datasets = [d for d in service.research_datasets() if d.get("state") == "AVAILABLE"]
    st.dataframe(service.research_strategies(), width="stretch", hide_index=True)
    if not datasets:
        st.warning("Create a dataset in Research Overview first.")
    else:
        dataset_id = st.selectbox("Dataset", [d["dataset_id"] for d in datasets])
        data = service.experiment_runner().datasets.load(dataset_id)
        with st.form("experiment"):
            strategy = st.selectbox("Strategy", [r["name"] for r in service.research_strategies()])
            symbols = st.multiselect("Assets", list(data.bars), default=[next(iter(data.bars))])
            benchmark = st.selectbox("Benchmark", list(data.bars))
            period = next(iter(data.bars.values()))
            start = st.date_input("Evaluation start (earlier data is warmup)", value=period[min(80, len(period) - 2)].session, min_value=period[0].session, max_value=period[-2].session)
            end = st.date_input("Evaluation end", value=period[-1].session, min_value=period[1].session, max_value=period[-1].session)
            lookback = st.number_input("Lookback sessions", 20, 252, 63)
            costs = st.selectbox("Cost scenario", ["realistic", "stress", "zero"])
            question = st.text_input("Research hypothesis", "Does this unchanged baseline survive explicit transaction costs?")
            submit = st.form_submit_button("Run local experiment", type="primary")
        if submit:
            if "job" in st.session_state and not st.session_state.job.done():
                st.warning("One experiment is already running.")
            else:
                from alphamosaic.backtesting.models import preset_config
                config = {"dataset_id": dataset_id, "strategy": strategy, "symbols": symbols, "benchmark": benchmark, "start": str(start), "end": str(end), "question": question, "replay": preset_config(costs).model_copy(update={"lookback": int(lookback)}).model_dump(mode="json")}
                st.session_state.job = executor.submit(service.research_experiment, config)
        if "job" in st.session_state:
            if st.session_state.job.done():
                try:
                    item = st.session_state.job.result()
                    st.success(f"{item['status']} · {item['experiment_id']}") if item["status"] == "COMPLETED" else st.error(item.get("error"))
                except Exception as exc:
                    st.error(str(exc))
            else:
                st.status("Experiment running in background; use Refresh for current status.")
                st.button("Refresh")
elif page == "Experiment Comparison":
    rows = service.research_experiments()
    ids = st.multiselect("Compare up to 10 experiments", [r["experiment_id"] for r in rows], max_selections=10)
    if ids:
        comparison = service.research_comparison(ids)
        st.success("Comparable dataset, dates, return basis and benchmark") if comparison["status"] == "COMPARABLE" else st.warning("Incompatible experiment assumptions; no pooled ranking")
        st.json(comparison)
else:
    item = select_result()
    if item:
        if page in {"Backtest Results", "Risk Lab"}:
            plot_result(item, page == "Risk Lab")
            st.json(item["analysis"], expanded=False)
            if page == "Backtest Results":
                tabs = st.tabs(["Fills", "Orders", "Positions", "Cash ledger", "Warnings"])
                for tab, key in zip(tabs, ["fills", "orders", "equity", "cash_ledger", "diagnostics"], strict=True):
                    tab.dataframe(item["result"].get(key, []), width="stretch")
            else:
                st.json({k: item["result"].get(k) for k in ("fees", "slippage_cost", "spread_cost", "turnover")})
                st.warning("Cost stress is a separate experiment. Factor causality, capacity certification and executable opening liquidity remain unverified.")
        elif page == "AI Research":
            st.caption("Optional model adapter · deterministic critic · no paid LLM required")
            st.json(item["review"])
        elif page == "Reports":
            path = service.experiment_runner().store.path(item["experiment_id"])
            for name, mime in (("report.html", "text/html"), ("report.md", "text/markdown"), ("experiment.json", "application/json")):
                st.download_button("Download " + name, (path / name).read_bytes(), file_name=name, mime=mime)
            st.markdown((path / "report.md").read_text(encoding="utf-8"))
