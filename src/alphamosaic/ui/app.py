"""Local Streamlit research terminal backed by the authoritative application service."""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from alphamosaic.core.service import ApplicationService
from alphamosaic.ui.views import comparison_views, evidence_caption, qualify_figure, risk_views

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
    st.caption(evidence_caption(item))
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
    qualify_figure(fig, [item])
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
        symbol = str(st.selectbox("Instrument", list(data.bars)))
        rows = [b.model_dump(mode="json") for b in data.bars[symbol]]
        st.caption("Provider: " + rows[0]["source"] + " · " + rows[0]["data_quality"] + " · adjustment: " + rows[0]["adjustment_policy"] + " · timezone: UTC · availability follows known_at")
        frequency = st.radio("Price view", ["Daily", "Complete calendar weeks"], horizontal=True)
        if frequency == "Complete calendar weeks":
            from alphamosaic.data.weekly import aggregate_weekly
            try:
                weekly_data = aggregate_weekly(data)
                rows = [b.model_dump(mode="json") for b in weekly_data.bars[symbol]]
                st.caption("XNYS complete natural weeks; available_at is the latest component availability. Incomplete boundary weeks are excluded.")
                st.json([w.model_dump(mode="json") for w in weekly_data.excluded_weeks[symbol]], expanded=False)
            except ValueError as exc:
                st.warning(str(exc))
                rows = []
        if rows:
            st.line_chart(pd.DataFrame(rows).set_index("last_session" if frequency == "Complete calendar weeks" else "session")[["close"]])
        st.dataframe(rows, width="stretch")
elif page == "Strategy Lab":
    datasets = [d for d in service.research_datasets() if d.get("state") == "AVAILABLE"]
    st.dataframe(service.research_strategies(), width="stretch", hide_index=True)
    if not datasets:
        st.warning("Create a dataset in Research Overview first.")
    else:
        dataset_id = st.selectbox("Dataset", [d["dataset_id"] for d in datasets])
        data = service.experiment_runner().datasets.load(dataset_id)
        strategy = str(st.selectbox("Strategy", [r["name"] for r in service.research_strategies()]))
        with st.form("experiment"):
            symbols = st.multiselect("Assets", list(data.bars), default=[next(iter(data.bars))])
            benchmark = st.selectbox("Benchmark", list(data.bars))
            period = next(iter(data.bars.values()))
            start = st.date_input("Evaluation start (earlier data is warmup)", value=period[min(80, len(period) - 2)].session, min_value=period[0].session, max_value=period[-2].session)
            end = st.date_input("Evaluation end", value=period[-1].session, min_value=period[1].session, max_value=period[-1].session)
            weekly_strategy = strategy.startswith("weekly_")
            lookback = 63
            weekly_parameters = {"lookback_weeks": 12, "trend_short_weeks": 4, "trend_long_weeks": 12}
            if weekly_strategy:
                st.caption("Signals use completed natural weeks; execution remains at a later daily open.")
                if strategy == "weekly_momentum":
                    weekly_parameters["lookback_weeks"] = int(st.number_input("Lookback weeks", 2, 104, 12))
                if strategy == "weekly_trend":
                    weekly_parameters["trend_short_weeks"] = int(st.number_input("Short trend weeks", 2, 103, 4))
                    weekly_parameters["trend_long_weeks"] = int(st.number_input("Long trend weeks", 3, 104, 12))
            else:
                lookback = st.number_input("Lookback sessions", 20, 252, 63)
            costs = st.selectbox("Cost scenario", ["realistic", "stress", "zero"])
            question = st.text_input("Research hypothesis", "Does this unchanged baseline survive explicit transaction costs?")
            submit = st.form_submit_button("Run local experiment", type="primary")
        if submit:
            if "job" in st.session_state and not st.session_state.job.done():
                st.warning("One experiment is already running.")
            else:
                from alphamosaic.backtesting.models import preset_config
                replay_config = preset_config(costs).model_dump(mode="json")
                replay_config.update(lookback=int(lookback), decision_frequency="WEEKLY" if weekly_strategy else "DAILY", weekly_parameters=weekly_parameters)
                config = {"dataset_id": dataset_id, "strategy": strategy, "symbols": symbols, "benchmark": benchmark, "start": str(start), "end": str(end), "question": question, "replay": replay_config}
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
        try:
            comparison = service.research_comparison(ids)
            comparison_views([service.research_result(key) for key in ids], comparison)
        except (ValueError, OSError, KeyError) as exc:
            st.error("Comparison evidence could not be loaded: " + str(exc))
elif page == "AI Research":
    st.caption("Frozen offline research workflow · deterministic planner and independent critic · optional text adapter · broker disabled")
    datasets = [d for d in service.research_datasets() if d.get("state") == "AVAILABLE"]
    if datasets:
        dataset_id = st.selectbox("Plan dataset", [d["dataset_id"] for d in datasets])
        instruments = service.experiment_runner().datasets.manifest(dataset_id)["instruments"]
        with st.form("research_plan"):
            symbols = st.multiselect("Plan assets", instruments, default=[instruments[0]])
            benchmark = st.selectbox("Plan benchmark", instruments)
            strategies = st.multiselect("Predeclared strategies (up to 3)", [r["name"] for r in service.research_strategies()], default=["buy_and_hold", "trend"], max_selections=3)
            question = st.text_input("Frozen hypothesis", "Do unchanged baseline rules survive realistic and stress costs on this fixed dataset?")
            freeze = st.form_submit_button("Freeze research plan")
        if freeze:
            try:
                plan = service.plan_research({"dataset_id": dataset_id, "question": question, "symbols": symbols, "benchmark": benchmark, "strategies": strategies})
                st.success("Plan frozen: " + plan["plan_id"])
            except ValueError as exc:
                st.error(str(exc))
    try:
        plans = service.research_plans()
    except ValueError as exc:
        st.error(str(exc))
        plans = []
    if plans:
        plan_id = str(st.selectbox("Frozen plan", [p["plan_id"] for p in plans]))
        state = service.research_plan(plan_id)
        st.write("Status: " + state["status"])
        st.json(state["plan"], expanded=False)
        plan_busy = "plan_job" in st.session_state and not st.session_state.plan_job.done()
        if state["status"] == "FROZEN" and st.button("Execute frozen local plan", type="primary", disabled=plan_busy):
            st.session_state.plan_job = executor.submit(service.run_research_plan, plan_id)
            st.session_state.plan_job_plan_id = plan_id
            st.session_state.plan_job_label = "Executing frozen research trials"
        if state["status"] in {"INCOMPLETE_OR_RUNNING", "RECONCILIATION_IN_PROGRESS", "INTERRUPTED"}:
            st.caption("Saved state does not prove a process is running. Reconciliation inspects existing work and closes interrupted attempts without rerunning trials; active execution blocks it.")
            label = "Inspect late response evidence" if state["status"] == "INTERRUPTED" else "Reconcile saved attempts (no rerun)"
            if st.button(label, disabled=plan_busy):
                st.session_state.plan_job = executor.submit(service.reconcile_research_plan, plan_id)
                st.session_state.plan_job_plan_id = plan_id
                st.session_state.plan_job_label = "Reconciling saved evidence; no trials run"
        if "plan_job" in st.session_state:
            st.caption("Job plan: " + st.session_state.get("plan_job_plan_id", "previous selection"))
            if st.session_state.plan_job.done():
                try:
                    st.write(st.session_state.plan_job.result()["status"])
                except Exception as exc:
                    st.error(str(exc))
            else:
                st.status(st.session_state.get("plan_job_label", "Research job pending"))
                st.button("Refresh plan")
        try:
            report = service.research_plan_report(plan_id)
        except (ValueError, OSError) as exc:
            st.error("Computed plan report unavailable; saved audit remains available: " + str(exc))
            report = None
        if report is not None and report.get("reconciliation"):
            st.subheader("Interrupted-run evidence")
            st.caption("Recovered artifacts remain separate from original tool outcomes. A saved complete artifact does not prove the original process exited successfully.")
            summary = next((event["payload"] for event in report["reconciliation"] if event["kind"] == "RECONCILIATION_FINISHED"), None)
            if summary is not None:
                for column, title, value in zip(st.columns(4),
                    ["Recorded outcomes", "Recovered artifacts", "Unresolved attempts", "Trials not started"],
                    [summary["recorded_outcomes"], summary["recovered_completed_artifacts"], summary["unresolved_attempts"], len(summary["unattempted_ordinals"])], strict=True):
                    column.metric(title, value)
            records = [event["payload"] for event in report["reconciliation"] if event["kind"] == "RECOVERED_ATTEMPT"]
            if records:
                st.dataframe([{"Trial": record["ordinal"] + 1,
                    "Evidence": {"RECORDED_OUTCOME_PRESERVED": "Original outcome retained", "RECOVERED_COMPLETED_ARTIFACT": "Matched complete artifact", "INTERRUPTED_UNRESOLVED": "Unresolved attempt"}[record["classification"]],
                    "Original outcome": (record.get("recorded_outcome") or {}).get("status", "Not recorded"),
                    "Artifact": (record.get("artifact") or {}).get("experiment_id"),
                    "Process exit": "Not observed" if record["exit_status"] == "NOT_OBSERVED" else "Not reevaluated",
                    "Uncertainty": record.get("unresolved_reason", {}).get("reason")} for record in records], width="stretch")
        if report is not None:
            st.json(report, expanded=False)
        with st.expander("Audit events", expanded=False):
            st.dataframe(state["events"], width="stretch")
        st.download_button("Download plan evidence" if report is not None else "Download saved audit", data=json.dumps(report if report is not None else state, indent=2), file_name="research-plan.json", mime="application/json")
    else:
        st.info("Freeze a plan to inspect its hypothesis, fixed trials, dataset review and quota before execution.")
else:
    item = select_result()
    if item:
        if page in {"Backtest Results", "Risk Lab"}:
            plot_result(item, page == "Risk Lab")
            if page == "Backtest Results":
                st.json(item["analysis"], expanded=False)
            if page == "Backtest Results":
                tabs = st.tabs(["Fills", "Orders", "Positions", "Cash ledger", "Warnings", "Closed FIFO matches", "Asset accounting", "Weekly view", "Dividend accounting"])
                for tab, key in zip(tabs[:5], ["fills", "orders", "equity", "cash_ledger", "diagnostics"], strict=True):
                    tab.dataframe(item["result"].get(key, []), width="stretch")
                trades = item["analysis"].get("trade_analysis", {})
                tabs[5].caption("Each closed row is a FIFO sell-to-entry matching segment; open lots do not count as wins or losses.")
                tabs[5].dataframe(trades.get("closed_lots", []), width="stretch")
                tabs[5].json(trades.get("conventions", {}), expanded=False)
                tabs[6].dataframe(trades.get("asset_attribution", []), width="stretch")
                tabs[6].json(trades.get("reconciliation", {"status": "NOT_EVALUATED_LEGACY_RESULT"}))
                weekly = item["analysis"].get("weekly", {})
                tabs[7].caption("52 completed-week periods/year; boundary intervals and daily risk remain separate.")
                tabs[7].json(weekly, expanded=False)
                from alphamosaic.reporting.research import dividend_accounting_evidence
                dividend_evidence = dividend_accounting_evidence(item)
                with tabs[8]:
                    st.subheader("Dividend rights and cash availability")
                    st.caption(dividend_evidence["convention"])
                    if dividend_evidence["dividend_accounting"] == "PAY_DATE_RECEIVABLE":
                        reconciliation = trades.get("reconciliation", {})
                        outstanding = reconciliation.get("outstanding_dividend_receivables_usd")
                        cash_col, claim_col = st.columns(2)
                        cash_col.metric("Cash at final valuation", f"${item['result']['equity'][-1]['cash']:,.2f}")
                        claim_col.metric("Unpaid dividend claims", "Not reconciled" if outstanding is None else f"${outstanding:,.2f}")
                        st.caption("Earned dividend rights are separate from spendable cash. Sold shares retain their frozen entitlement.")
                        entitlements = dividend_evidence.get("entitlements")
                        payments = dividend_evidence.get("payments")
                        if entitlements is None:
                            st.warning("Entitlement records were not recorded.")
                        elif entitlements:
                            st.dataframe(entitlements, width="stretch", hide_index=True)
                        else:
                            st.info("No dividend entitlement events in this evaluated period.")
                        if payments is None:
                            st.warning("Payment records were not recorded.")
                        elif payments:
                            st.dataframe(payments, width="stretch", hide_index=True)
                        else:
                            st.info("No dividend cash payments in this evaluated period; inspect outstanding claims separately.")
                    st.json(dividend_evidence, expanded=False)
            else:
                risk_views(item)
                st.warning("Cost stress is a separate experiment. Factor causality, capacity certification and executable opening liquidity remain unverified.")
        elif page == "Reports":
            path = service.experiment_runner().store.path(item["experiment_id"])
            for name, mime in (("report.html", "text/html"), ("report.md", "text/markdown"), ("experiment.json", "application/json")):
                st.download_button("Download " + name, (path / name).read_bytes(), file_name=name, mime=mime)
            st.markdown((path / "report.md").read_text(encoding="utf-8"))
