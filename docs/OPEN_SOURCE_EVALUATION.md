# Open-source component evaluation

Verified 2026-10-24 against primary PyPI metadata and repository license text. `framework-primary-sources-20261024.json` retains source URLs, capture time, status and license content hash. Several GitHub API requests returned 403; release/maintenance information that could not be refreshed is not asserted as current. Package metadata is not an installation or compatibility test. No evaluated engine source was copied.

## Microsoft Qlib — Reference / Adapt concepts

PyPI `pyqlib` 0.9.7, Python >=3.8 (metadata includes 3.12), MIT [license](https://raw.githubusercontent.com/microsoft/qlib/main/LICENSE), [source](https://github.com/microsoft/qlib), [package](https://pypi.org/pypi/pyqlib/json). Broad feature/ML/workflow research, binary data format, dataset/recorder concepts and repository tests are useful references. Its training/data dependencies and market assumptions add substantial review work. Adapt chronological workflow concepts in small independent modules; do not introduce its complete runtime. Alternative: existing ReplayDataset, local experiments and training-only standardizer. Maintenance and Windows wheel compatibility were not exercised here.

## QuantConnect LEAN — Reference

Apache-2.0 [license](https://raw.githubusercontent.com/QuantConnect/Lean/master/LICENSE), [source](https://github.com/QuantConnect/Lean). C#/Python event engine, security models, corporate actions, fill/cost abstractions and extensive test organization are relevant references. Local .NET/Docker/CLI/data setup adds deployment and licensing overhead; bundled broker/live paths do not belong in the agent tool surface. The previous release snapshot records an old 2017 tag; latest engine build/commit was **not refreshed** after API denial and is not presented as a tested version. Existing optional operator-only adapter remains unconfigured. No paid cloud or data purchase. Alternative: audited local daily replay, then a separately pinned licensed-data cross-validation project.

## VectorBT Community — Reject runtime adoption / Reference documentation

PyPI 1.2.0, Python >=3.11,<3.15. Current [license](https://raw.githubusercontent.com/polakowo/vectorbt/master/LICENSE.md) is Apache-2.0 **with Commons Clause**; it must not be described as ordinary permissive Apache. [Source](https://github.com/polakowo/vectorbt), [package](https://pypi.org/pypi/vectorbt/json). Efficient array/Numba parameter research is attractive, but a matrix replay does not independently certify daily execution, selection or cash/corporate-action logic. License restrictions, proprietary PRO separation and large parameter-search overfitting risk outweigh a second engine now. Alternative: NumPy/Pandas calculations and bounded fixed experiment suites. No commercial component installed.

## Zipline Reloaded — Reference

PyPI 3.2.0, Python >=3.11,<3.15, Apache-2.0 [license](https://raw.githubusercontent.com/stefan-jansen/zipline-reloaded/main/LICENSE), [source](https://github.com/stefan-jansen/zipline-reloaded), [package](https://pypi.org/pypi/zipline-reloaded/json). Event scheduling, exchange sessions, adjusted asset bundles and pipeline design are relevant. Native dependencies, bundle conventions and migrations add Windows/NumPy compatibility risk. Metadata compatibility does not establish successful local installation. Reference its concepts; retain independent small contracts and existing exchange-calendars. Alternative: separately isolated engine comparison when licensed adjusted datasets exist.

## Backtesting.py — Reject runtime adoption

PyPI 0.6.6, Python >=3.9, AGPL-3.0 [license](https://raw.githubusercontent.com/kernc/backtesting.py/master/LICENSE.md), [source](https://github.com/kernc/backtesting.py), [package](https://pypi.org/pypi/backtesting/json). Concise single-strategy OHLCV research and visual diagnostics are useful, but portfolio/multi-asset accounting remains our responsibility. Do not copy or link the runtime into this Apache-2.0 project without a separate compatibility/licensing decision. Alternative: current small replay and Plotly reports. No inference that a software license grants data rights.

## Adopt existing mature components

NumPy/Pandas: vector calculations; Pydantic: finite validated schemas; exchange-calendars: exchange sessions; Pytest/Hypothesis: correctness checks; Plotly: optional interactive charts; Streamlit: local terminal; AnyIO: scoped asynchronous lifecycle. Exact installed/locked versions are recorded per experiment and in uv.lock. Their version-specific licenses remain distributable upstream metadata, not licenses for market data. QuantStats 0.0.86 is retained as optional analytics with explicit annualization and undefined-ratio handling; core Renaissance metrics work without it. Parquet/PyArrow is available transitively with the terminal, but this milestone deliberately persists canonical JSON/CSV rather than claiming a Parquet lake. No MLflow server, Kubernetes, GPU runtime or paid hosting was introduced.
