# Reproduce the local research prototype

Ordinary-dividend/split/cost/unpaid-cutoff cases and four frozen daily worker trials:

```powershell
uv run python scripts/run_dividend_cases.py --home runtime/dividend-research
```

The generated suite retains every case, an explicitly legacy diagnostic, model-comparison gates and an expected FAILED action-aware RAW weekly control. This generator's known synthetic split is accepted only with preserved review provenance; no real provider data exception is introduced. New experiments use explicit payment-accounting schema2; old saved configurations without accounting fields retain schema1 legacy behavior. Inspect Dividend accounting and cash/market/claim weights in the terminal. See docs/DIVIDEND_PAYMENT_ACCEPTANCE_20261025.md for model boundaries and actual verification.

Continuation examples include actual calendar-week rules, FIFO accounting reconciliation and a frozen6-trial supervised workflow:

```powershell
uv run python scripts/run_extended_research.py --home runtime/extended-research
$env:ALPHAMOSAIC_HOME = (Join-Path (Get-Location) 'runtime/extended-research')
uv run alphamosaic research-plans
uv run python -m streamlit run src/alphamosaic/ui/app.py --theme.base dark
```

The script retains four daily/weekly cases and every outcome from the explicit daily/weekly strategy×realistic/stress plan. Every new experiment exports qualified FIFO matches, asset contributions and complete-week NAV alongside daily records. FIXTURE prices remain software demonstrations, not market results. The AI Research page can freeze and execute a plan, inspect its immutable configuration/events/critics and export JSON evidence. CLI equivalents are plan-research CONFIG.json and run-research-plan PLAN_ID; plan source or dataset changes require a newly reviewed plan rather than silent mutation.

Use Python3.12 and the reviewed Renaissance checkout. Freeze files/environment and restart the service before acceptance. No broker, paid API or model key is required.

```powershell
uv sync --locked --all-extras --dev
uv run alphamosaic doctor
uv run python scripts/run_research_cases.py --home runtime/renaissance-demo
$env:ALPHAMOSAIC_HOME = (Join-Path (Get-Location) 'runtime/renaissance-demo')
uv run python -m streamlit run src/alphamosaic/ui/app.py --theme.base dark
```

The script creates deterministic NumPy PCG64 FIXTURE bars for SPY/QQQM/TLT labels; they are not those funds' market history. Same seed/data/config give equal replay/accounting/analytics, while experiment IDs, wall-clock metadata and elapsed time intentionally differ. Cases: A buy-and-hold, B trend, C low-vol allocation, zero/stress controls, two fixed lookbacks, declared70/30 holdout and missing-dataset failure. Sensitivity cases are controls, not optimization. Defaults use504 XNYS sessions from2016 onward.

Each unique local experiment contains `config.json`, `experiment.json`, checksums, source/dependency fingerprints, dataset manifest/hash, strategy/universe/seed/date/cost/execution/validation settings, equity/fill/order/event/signal/cash/unfilled/order-adjustment CSVs, HTML and Markdown reports. Position and average-cost histories are in equity records. Failed attempts retain configuration/error; interrupted runs remain RUNNING with INCOMPLETE integrity. No result directory is reused.

Re-run one saved configuration:

```powershell
uv run alphamosaic experiment runtime/renaissance-demo/experiments/EXPERIMENT_ID/config.json
uv run alphamosaic experiments
uv run python scripts/benchmark_replay.py --sessions 100
uv run python scripts/mcp_smoke.py --home runtime/mcp-check
```

Substitute the actual generated ID. Source hashes use canonical relative POSIX paths; package versions/lock hash/Git dirty state are recorded. A source change during computation fails the run. Disk fingerprints cannot certify old in-memory imports: restart after any code change. Wheel installs may have no Git checkout/lock and record unavailable fields explicitly.

Optional browser verification, after installing Playwright's browser locally:

```powershell
uv run python -m playwright install chromium --only-shell
uv run python scripts/terminal_smoke.py --start-server --url http://127.0.0.1:8522 --home runtime/renaissance-demo --output runtime/browser-check
```

Browser QA starts/stops only its own local service. Some Windows sandboxes isolate localhost across process trees; run server/browser together in the allowed environment. No remote deployment is implicit. JSON/CSV/HTML/Markdown export is implemented; Parquet and PDF export are not claimed.
