# AlphaMosaic Research Report

## Executive Summary

Research only. FIXTURE. No demonstrated alpha. Experiment 0d572bc5c4034a2ab7d8f53ede21babb.

## Research Question

Can a fixed synthetic baseline reproduce under explicit costs and independent accounting checks?

## Data & Provenance

{
  "dataset_id": "3a5edaeb21f5156e83a2be9a37d0543ed88248048ab208d0f867bc68abe2b38e",
  "hash": "3a5edaeb21f5156e83a2be9a37d0543ed88248048ab208d0f867bc68abe2b38e",
  "basis": "RAW_WITH_CASH_ACTIONS",
  "dataset": {
    "adjustment_method": [
      "RAW"
    ],
    "calendar": "XNYS",
    "corporate_actions_complete": true,
    "cutoff": "2018-01-02T21:00:00+00:00",
    "data_quality": [
      "FIXTURE"
    ],
    "dataset_hash": "3a5edaeb21f5156e83a2be9a37d0543ed88248048ab208d0f867bc68abe2b38e",
    "dataset_id": "3a5edaeb21f5156e83a2be9a37d0543ed88248048ab208d0f867bc68abe2b38e",
    "dataset_version": "3a5edaeb21f5156e83a2be9a37d0543ed88248048ab208d0f867bc68abe2b38e",
    "fetch_timestamp": "2018-01-02T21:00:00+00:00",
    "frequency": "DAILY",
    "historical_universe_verified": true,
    "instruments": [
      "QQQM",
      "SPY",
      "TLT"
    ],
    "license_scope": [
      "Project-generated synthetic data; Apache-2.0"
    ],
    "metadata": {},
    "price_series_kind": [
      "RAW_PRICE"
    ],
    "provider": [
      "FIXTURE synthetic_demo v1"
    ],
    "quality_policy": "REJECT",
    "quality_report": {
      "flags": [],
      "issues": [],
      "jump_threshold": 0.5,
      "repaired": false,
      "schema_version": 1,
      "valid": true
    },
    "schema_version": 1,
    "source_versions": [
      "NOT_REPORTED"
    ],
    "state": "AVAILABLE",
    "timezone": "UTC",
    "universe_selection_method": "EXPLICIT_FIXED_SYNTHETIC",
    "manifest_hash": "e4301b83d13552692c1142a759c596aa53cecb3c80dea3de0ab858a4f3629182"
  },
  "code": {
    "git_sha": "4ca05a66437975b6d243d0a5a4e6ac9b261a552e",
    "git_dirty": true,
    "python": "3.12.14",
    "lock_hash": "d959293b627ad12ce7b46a932a5d48bf00bac3adae82b11717a4d86660efb1dd",
    "source_hash": "06ee532642910d385759c6ca9ceb751d6946119914777e7690dcb680faba5a8e",
    "source_files": {
      "__init__.py": "4f4398e42753761a5d16a5f71439c0a40082dfc4a38aaa016f27e231ffbb2beb",
      "agents/__init__.py": "20856f0fe3752b75532561c7cbea29793d02ed8902a4a536bc5f12231c6bf571",
      "agents/research.py": "7e0aa91f3330320e8e1ec327fbe671a0014f0bc9822bee5304f764e391269a0c",
      "backtesting/adapters.py": "9ea4ef86ab5dc4fab9e234ccc669f8981d23af4856e5dc8f08a634300b48483d",
      "backtesting/diagnostic.py": "882a1c4db382e152c7d401f5ba427e0c36ec84f6c813b5466f3704ca8f110b88",
      "backtesting/engines.py": "10b3c715ea340542083ffeccc00cb48b77bc173086dc3f5bcc9ed1d2f6043e0d",
      "backtesting/models.py": "d7f5a3567508fb502fa112a33e02b7248a58d79b5cd97e336a7dd0ef050fc897",
      "backtesting/replay.py": "4198d903bc034a03d7d95dea86b65decb2f471dc7d3206ac99bdb901594ceda4",
      "backtesting/strategies.py": "216c20e04b46ddebf2a464bfc1e00f74cf209f6f068c91e8a813ba70b3c251d8",
      "cli/app.py": "b22a02be935f6e35df7d9eb33ee13f7603b04104e578946cbca3add7235b59a3",
      "core/contracts.py": "2473786424b587cfc3d3a523a9d22ca2db28ab09b7eb3400683d0f1a82f6c33c",
      "core/service.py": "8a04cbe4f61dc5388a4988ee3897cceff062504a1b822108f86661f48a9feffe",
      "data/datasets.py": "1f49616f605d1b40c73774c999d88d4f23909d7a24a96576fddaa46454fcd878",
      "data/validation.py": "71d99ce22c0ee1054d6ba2125c2ba2c75d112b15c8b33b350b04f6ece5e9bf6c",
      "evaluation/analytics.py": "6121c253af97c36d867d9fba1b08f9abf21b483bebdc0c28abe54d1d4bf8eaca",
      "evaluation/engine_comparison.py": "2a2074d65258fddaa827ce19fae080e86bd9be9291989398fefd66f5a08f4b61",
      "evaluation/quantstats_adapter.py": "b503199a94fbee6b47ee2039beb67a2b1bfa969e2846ef05f5234d3fd13f1fa0",
      "evaluation/registry.py": "4266a31806ac5e440c28a04508c0e9427148c8f644acc285da83a793ede2b26b",
      "evaluation/scientific.py": "94c64bfb5deb9e828e7f6bd2f5ff23c229af9f51c22ad4e2b6b5a912714ae0f3",
      "evaluation/validation.py": "c10ea72e1b41d037f49e8cdb301e777f0f50235dbc31d5b5c2513420663086e3",
      "experiments/__init__.py": "6e5ad1d221dde405f82a7641d7d75ca950c6b98922b6bdda2c2defa224f8018a",
      "experiments/runner.py": "410a201aef9a757dce1b0354dff89bf5032a79a6485bb510b30a9232952865ad",
      "factors/engine.py": "b05fa8551e4ed09c56603c0f33fa4874141cd4e9fc0a968b4b35e2ae318a9784",
      "integrations/danelfin.py": "19b5226e3a08623bb213048854c78d1e68a441ffb586c22dc839c0cc24c0c8f9",
      "integrations/frameworks.py": "d9adcbd6a59183ada6edb57153340a3439a3ca9eddb0a7f8dd4afffdc17bce77",
      "integrations/lean.py": "8a059921a19fee1ef7437d65cf099500edc65aebc6d45278be733eb463283a67",
      "integrations/openbb_worker.py": "066df6dbcebfaaa7497017c703a5b5b3e1d1fd223745cd1d16080e275bc8b0e4",
      "integrations/registry.py": "ffaf890f1adbf937842fa24299245cf338cc7dccfac8f99d97152b76cb7c263d",
      "integrations/tradingagents.py": "a3d6d659d3ad2e1ac05a5b8f24ca29a8960c99ab848e8d748f599e3488c366d2",
      "integrations/tradingagents_worker.py": "14e820d08299a0adfdcd8f0ccfc5aa45136b5df382e4054046eb6df74c9ceeb0",
      "mcp/remote.py": "f97f93f5844ce4134b2b617280c91ec51353d3ee2cdb27080be83b51a65be66d",
      "mcp/server.py": "fee7710dfa269e01c7c98f771f7f4c02f86978bd03434c49b4467803f630c187",
      "opportunity_pipeline.py": "350bec5baedbeb3d0d591e149e0eaeac8be5728c4702a12c6c506da4d8862048",
      "portfolio/construction.py": "aad3c77aa25b457e42500b74b7e1d6e3571f278857168ac52e3398ad73b70e2a",
      "portfolio/forward.py": "3a3e2e67dba0f7f2ba6467954a5d874e1b0318db3a5ecd1ad722fe9838d8f395",
      "portfolio/risk.py": "370c49b92ad5cc27e18397abb82f8363cc62a6a36a765a83e21c0c6c472eb67d",
      "providers/openbb.py": "a3ef859fdbcd7ba46af120e9531ec5aa554f3b10871760092d06a001ea08e725",
      "providers/protocol.py": "ddd55ebc9c36891dd57050dc6f846d0916175881a23f9a733229c9e230955d41",
      "providers/sec_edgar.py": "f195ba77db21cf168e7fc3c5c2925f9a9bd279c2f72f47b226b2cbbab22d42fa",
      "reporting/provenance.py": "1773ec3dd8fce37b2fc6d32990cb852731382fc2963b621d394875308b7f3f66",
      "reporting/research.py": "26c1c3fbc5579892bb8c4721120abe45f49bc5d1a3fbb343f6d40c0ef0c63ca3",
      "reporting/store.py": "e61d01f76d9c094dcf5642566782fef259686b3f98594022f3a4ec75171da208",
      "research_engine.py": "62a76374c80f44c8fedbf859b03072b0f2ba45991efef4f973420b83d396a8fb",
      "screening/archetypes.py": "aac7fd6efcb05d3650f3a17650e0296d7e0705f0ae7f2410e57c775d79d526ac",
      "screening/scanner.py": "da3b1db468823b6d323dd49f6fea80da8a39b3799746d5f046d34f459fde2ed9",
      "screening/universe.py": "4a82cc54574c5e0b7bcf159df59bb6be8e8488f564f4846434c4d0203b4cee6c",
      "signals_fusion.py": "8944bd26aa32a4f546ccd42225d679852d57a82abb144490b2958b3ef0aaf29d",
      "ui/__init__.py": "dc3ec423b1305814a3563d977eac3f8381fd6b8062e5e5e8f9a6cf9038f2414e",
      "ui/app.py": "f20313be5e2f446d82e6dc61f33121e8c8cf1edb3d08c3fe93ea1f1072c1d9de"
    },
    "installed_dependencies": {
      "aiohappyeyeballs": "2.7.1",
      "aiohttp": "3.14.4",
      "aiohttp-client-cache": "0.15.0",
      "aiosignal": "1.4.0",
      "aiosqlite": "0.22.1",
      "alphamosaic": "0.1.0",
      "altair": "6.3.0",
      "annotated-doc": "0.0.5",
      "annotated-types": "0.8.0",
      "anyio": "4.15.1",
      "async-lru": "2.3.0",
      "attrs": "26.1.0",
      "beautifulsoup4": "4.15.0",
      "boolean.py": "5.0",
      "build": "1.6.1",
      "CacheControl": "0.14.4",
      "certifi": "2026.10.23",
      "cffi": "2.1.1",
      "charset-normalizer": "3.5.2",
      "click": "8.5.0",
      "colorama": "0.4.6",
      "contourpy": "1.4.0",
      "coverage": "7.16.2",
      "cryptography": "50.0.2",
      "curl_cffi": "0.16.3",
      "cycler": "0.12.1",
      "cyclonedx-python-lib": "11.12.0",
      "defusedxml": "0.7.1",
      "exchange_calendars": "4.13.2",
      "fastapi": "0.143.0",
      "filelock": "4.2.4",
      "fonttools": "4.66.1",
      "frozenlist": "1.8.0",
      "greenlet": "3.5.6",
      "h11": "0.16.0",
      "httpcore": "1.0.9",
      "httpcore2": "2.13.1",
      "httpx": "0.28.1",
      "httpx2": "2.13.1",
      "hypothesis": "6.170.9",
      "idna": "3.20",
      "importlib_metadata": "9.0.1",
      "iniconfig": "2.3.1",
      "itsdangerous": "2.2.0",
      "Jinja2": "3.1.6",
      "jsonschema": "4.26.0",
      "jsonschema-specifications": "2025.9.1",
      "kiwisolver": "1.5.1",
      "korean_lunar_calendar": "0.4.0",
      "license-expression": "30.4.4",
      "lxml": "6.1.3",
      "markdown-it-py": "4.2.0",
      "MarkupSafe": "3.0.4",
      "matplotlib": "3.11.2",
      "mcp": "2.3.0",
      "mcp-types": "2.3.0",
      "mdurl": "0.1.2",
      "msgpack": "1.2.3",
      "multidict": "6.9.1",
      "multitasking": "0.0.13",
      "narwhals": "2.27.1",
      "nodeenv": "1.11.0",
      "numpy": "2.5.3",
      "openbb-core": "2.0.1",
      "openbb-nasdaq": "2.0.0",
      "opentelemetry-api": "1.45.1",
      "packageurl-python": "0.17.6",
      "packaging": "26.3",
      "pandas": "2.3.3",
      "pdfminer.six": "20260107",
      "pdfplumber": "0.11.10",
      "peewee": "4.5.3",
      "pillow": "13.0.0",
      "pip": "26.2.2",
      "pip_api": "0.0.35",
      "pip_audit": "2.10.1",
      "pip-requirements-parser": "32.0.1",
      "platformdirs": "4.12.4",
      "playwright": "1.64.1",
      "plotly": "6.9.0",
      "pluggy": "1.6.0",
      "propcache": "0.5.4",
      "protobuf": "7.36.2",
      "pyarrow": "26.0.0",
      "pycparser": "3.1",
      "pydantic": "2.14.0",
      "pydantic_core": "2.50.0",
      "pydeck": "0.9.3",
      "pyee": "14.0.0",
      "Pygments": "2.21.0",
      "PyJWT": "2.15.1",
      "pyluach": "2.3.0",
      "pyparsing": "3.3.3",
      "pypdfium2": "5.14.0",
      "pyproject_hooks": "1.3.3",
      "pyright": "1.1.414",
      "pytest": "9.1.1",
      "pytest-asyncio": "1.4.0",
      "pytest-cov": "7.1.0",
      "python-dateutil": "2.9.0.post0",
      "python-dotenv": "1.2.4",
      "python-multipart": "0.0.32",
      "pytz": "2026.5",
      "pywin32": "312",
      "py-serializable": "2.1.0",
      "quantstats": "0.0.86",
      "random-user-agent": "1.0.1",
      "referencing": "0.37.0",
      "requests": "2.34.2",
      "rich": "15.0.0",
      "rpds-py": "2026.9.1",
      "ruff": "0.16.10",
      "scipy": "1.18.1",
      "seaborn": "0.13.2",
      "shellingham": "1.5.4",
      "six": "1.17.0",
      "sortedcontainers": "2.4.0",
      "soupsieve": "2.10",
      "sse-starlette": "3.5.0",
      "starlette": "1.7.0",
      "streamlit": "1.66.1",
      "tabulate": "0.10.0",
      "tomli": "2.5.0",
      "tomli_w": "1.2.0",
      "toolz": "1.2.0",
      "truststore": "0.10.4",
      "typer": "0.27.3",
      "typing_extensions": "4.16.0",
      "typing-inspection": "0.4.4",
      "tzdata": "2026.5",
      "urllib3": "2.8.0",
      "url-normalize": "3.0.1",
      "uuid7": "0.1.0",
      "uv": "0.13.5",
      "uvicorn": "0.54.0",
      "watchdog": "6.0.0",
      "websockets": "17.2",
      "yarl": "1.25.1",
      "yfinance": "1.7.0",
      "zipp": "4.1.1"
    }
  }
}

## Strategy Definition

{
  "strategy": "trend",
  "symbols": [
    "SPY"
  ],
  "start": "2016-04-28",
  "end": "2018-01-02"
}

## Backtest Assumptions

{
  "initial_cash": 100000.0,
  "fee_bps": 10.0,
  "slippage_bps": 5.0,
  "spread_bps": 2.0,
  "order_delay_sessions": 1,
  "lot_size": 1,
  "max_single_weight": 1.0,
  "max_gross_exposure": 1.0,
  "min_cash_buffer": 0.02,
  "max_turnover": 2.0,
  "volatility_target": 0.15,
  "max_positions": 10,
  "max_volume_fraction": 0.01,
  "lookback": 63,
  "rebalance_sessions": 21,
  "seed": 42
}

## Performance and Risk

{
  "metrics": {
    "return": 0.02312129995794998,
    "cagr": 0.013678147929176099,
    "volatility": 0.08929440652577217,
    "sharpe": 0.19666531208752372,
    "sortino": 0.283056141886203,
    "calmar": 0.14730557875967804,
    "max_drawdown": -0.09285560020432992,
    "drawdown_duration_sessions": 128.0,
    "beta": 0.3657464796417207,
    "alpha_annualized_arithmetic": 0.020371118387092043,
    "tracking_error": 0.11745849970822958,
    "information_ratio": 0.2149188554205016,
    "correlation": 0.6031867016750275,
    "turnover": 4.892680250637732,
    "fill_count": 7.0,
    "trade_count": null,
    "win_rate": null,
    "profit_factor": null,
    "average_holding_period_sessions": null,
    "market_exposure": 0.34876890881244577,
    "transaction_cost_drag_initial_capital": 0.00786261164189024
  },
  "rolling": [
    {
      "session": "2016-04-28",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-04-29",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-02",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-03",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-04",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-05",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-06",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-09",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-10",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-11",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-12",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-13",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-16",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-17",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-18",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-19",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-20",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-23",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-24",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-25",
      "return": 0.0,
      "drawdown": 0.0
    },
    {
      "session": "2016-05-26",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12010406192751517,
      "information_ratio": 5.70707047459972,
      "correlation": null
    },
    {
      "session": "2016-05-27",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12676812406817003,
      "information_ratio": 4.820537262646835,
      "correlation": null
    },
    {
      "session": "2016-05-31",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12677951593764755,
      "information_ratio": 4.809804987026988,
      "correlation": null
    },
    {
      "session": "2016-06-01",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12831105247995642,
      "information_ratio": 3.627740539031065,
      "correlation": null
    },
    {
      "session": "2016-06-02",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13582205614573412,
      "information_ratio": 4.476317913152452,
      "correlation": null
    },
    {
      "session": "2016-06-03",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13526082250789437,
      "information_ratio": 3.189428767198455,
      "correlation": null
    },
    {
      "session": "2016-06-06",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1302743370906435,
      "information_ratio": 4.88112310255142,
      "correlation": null
    },
    {
      "session": "2016-06-07",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12910146439985692,
      "information_ratio": 4.4954079900764645,
      "correlation": null
    },
    {
      "session": "2016-06-08",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1291432674421592,
      "information_ratio": 4.482595840343097,
      "correlation": null
    },
    {
      "session": "2016-06-09",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12168137195430377,
      "information_ratio": 7.427748819728778,
      "correlation": null
    },
    {
      "session": "2016-06-10",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12218089717688582,
      "information_ratio": 6.971760109591526,
      "correlation": null
    },
    {
      "session": "2016-06-13",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12101120802691363,
      "information_ratio": 7.617202505837911,
      "correlation": null
    },
    {
      "session": "2016-06-14",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12046613597184655,
      "information_ratio": 8.035722602709235,
      "correlation": null
    },
    {
      "session": "2016-06-15",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12295925031289734,
      "information_ratio": 8.547496915056175,
      "correlation": null
    },
    {
      "session": "2016-06-16",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12035245636950484,
      "information_ratio": 9.135436226209235,
      "correlation": null
    },
    {
      "session": "2016-06-17",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1188560480547955,
      "information_ratio": 7.9030890915913234,
      "correlation": null
    },
    {
      "session": "2016-06-20",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.11101253169870444,
      "information_ratio": 6.824083300434999,
      "correlation": null
    },
    {
      "session": "2016-06-21",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.10923267849440561,
      "information_ratio": 5.855587601124215,
      "correlation": null
    },
    {
      "session": "2016-06-22",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1184955686653089,
      "information_ratio": 3.236118618683934,
      "correlation": null
    },
    {
      "session": "2016-06-23",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.11358218844984859,
      "information_ratio": 4.508264950207424,
      "correlation": null
    },
    {
      "session": "2016-06-24",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.11333805792508161,
      "information_ratio": 4.464431925727138,
      "correlation": null
    },
    {
      "session": "2016-06-27",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.11119222726644931,
      "information_ratio": 3.151654713345762,
      "correlation": null
    },
    {
      "session": "2016-06-28",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.10302101542896769,
      "information_ratio": 4.341094571740862,
      "correlation": null
    },
    {
      "session": "2016-06-29",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12352199511254332,
      "information_ratio": 1.7557476812407833,
      "correlation": null
    },
    {
      "session": "2016-06-30",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12600253112056098,
      "information_ratio": 1.4123190911162335,
      "correlation": null
    },
    {
      "session": "2016-07-01",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1171427216437167,
      "information_ratio": 0.63135411519021,
      "correlation": null
    },
    {
      "session": "2016-07-05",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12940519749645582,
      "information_ratio": -0.48013174689302596,
      "correlation": null
    },
    {
      "session": "2016-07-06",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1276287049337284,
      "information_ratio": -0.750283410341363,
      "correlation": null
    },
    {
      "session": "2016-07-07",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13142020806824575,
      "information_ratio": -0.14722533822763414,
      "correlation": null
    },
    {
      "session": "2016-07-08",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1384797323680848,
      "information_ratio": 1.0657560257283964,
      "correlation": null
    },
    {
      "session": "2016-07-11",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13081059285885657,
      "information_ratio": 0.25700157083639646,
      "correlation": null
    },
    {
      "session": "2016-07-12",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13921596136766143,
      "information_ratio": 1.42081889190614,
      "correlation": null
    },
    {
      "session": "2016-07-13",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1394490241397013,
      "information_ratio": 0.6923968758150364,
      "correlation": null
    },
    {
      "session": "2016-07-14",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13871427852388388,
      "information_ratio": 0.36245045841634155,
      "correlation": null
    },
    {
      "session": "2016-07-15",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1381120601924251,
      "information_ratio": 0.30900104763510045,
      "correlation": null
    },
    {
      "session": "2016-07-18",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1407639812729635,
      "information_ratio": 0.9825999353809088,
      "correlation": null
    },
    {
      "session": "2016-07-19",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1406002547495235,
      "information_ratio": 1.2616136199312442,
      "correlation": null
    },
    {
      "session": "2016-07-20",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1417725372667593,
      "information_ratio": 0.8229822563911919,
      "correlation": null
    },
    {
      "session": "2016-07-21",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16079723167086435,
      "information_ratio": -0.8307544857610865,
      "correlation": null
    },
    {
      "session": "2016-07-22",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17303636265426064,
      "information_ratio": -1.4466286841707503,
      "correlation": null
    },
    {
      "session": "2016-07-25",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17246373886522487,
      "information_ratio": -1.696763887299797,
      "correlation": null
    },
    {
      "session": "2016-07-26",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17419344961113023,
      "information_ratio": -1.489177046679672,
      "correlation": null
    },
    {
      "session": "2016-07-27",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18154945844051712,
      "information_ratio": -0.28196663484919565,
      "correlation": null
    },
    {
      "session": "2016-07-28",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1812953995837879,
      "information_ratio": -0.024649892881028212,
      "correlation": null
    },
    {
      "session": "2016-07-29",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17109576466085058,
      "information_ratio": 1.796589816569244,
      "correlation": null
    },
    {
      "session": "2016-08-01",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1675386498061915,
      "information_ratio": 2.657603171906983,
      "correlation": null
    },
    {
      "session": "2016-08-02",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16683977613860987,
      "information_ratio": 2.2925303205628764,
      "correlation": null
    },
    {
      "session": "2016-08-03",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1540162565455527,
      "information_ratio": 3.7748207499625996,
      "correlation": null
    },
    {
      "session": "2016-08-04",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16317224494789345,
      "information_ratio": 2.214664900540712,
      "correlation": null
    },
    {
      "session": "2016-08-05",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1610832338584763,
      "information_ratio": 1.8555751257845678,
      "correlation": null
    },
    {
      "session": "2016-08-08",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15567330169355936,
      "information_ratio": 0.8844549412292713,
      "correlation": null
    },
    {
      "session": "2016-08-09",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15821318610942958,
      "information_ratio": 1.2607277111672583,
      "correlation": null
    },
    {
      "session": "2016-08-10",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16153217229786052,
      "information_ratio": 1.4509271363031093,
      "correlation": null
    },
    {
      "session": "2016-08-11",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16060149603871718,
      "information_ratio": 1.9220724542840224,
      "correlation": null
    },
    {
      "session": "2016-08-12",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16277321893436278,
      "information_ratio": 1.388133782854155,
      "correlation": null
    },
    {
      "session": "2016-08-15",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.165808683245446,
      "information_ratio": -0.3261515978034338,
      "correlation": null
    },
    {
      "session": "2016-08-16",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.163103808716096,
      "information_ratio": -0.9050915601104796,
      "correlation": null
    },
    {
      "session": "2016-08-17",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16674965799579786,
      "information_ratio": -1.7981836392268533,
      "correlation": null
    },
    {
      "session": "2016-08-18",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1683822370812788,
      "information_ratio": -0.9871807200070983,
      "correlation": null
    },
    {
      "session": "2016-08-19",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15832934015593889,
      "information_ratio": 1.6768512624865743,
      "correlation": null
    },
    {
      "session": "2016-08-22",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13552085022389596,
      "information_ratio": 4.706172502093943,
      "correlation": null
    },
    {
      "session": "2016-08-23",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1368808303302715,
      "information_ratio": 5.515482644744348,
      "correlation": null
    },
    {
      "session": "2016-08-24",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1520573371764743,
      "information_ratio": 2.8916779102298538,
      "correlation": null
    },
    {
      "session": "2016-08-25",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14591809631081504,
      "information_ratio": 2.2626360454078127,
      "correlation": null
    },
    {
      "session": "2016-08-26",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14741261460383878,
      "information_ratio": 1.781740307208185,
      "correlation": null
    },
    {
      "session": "2016-08-29",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1518490150084932,
      "information_ratio": 2.1606226044063166,
      "correlation": null
    },
    {
      "session": "2016-08-30",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1572870635727104,
      "information_ratio": 1.0295910138580906,
      "correlation": null
    },
    {
      "session": "2016-08-31",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1579499090612587,
      "information_ratio": 0.6954391080145704,
      "correlation": null
    },
    {
      "session": "2016-09-01",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15797290113521786,
      "information_ratio": 0.7617566510558803,
      "correlation": null
    },
    {
      "session": "2016-09-02",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14952271161192446,
      "information_ratio": 2.0849021885337273,
      "correlation": null
    },
    {
      "session": "2016-09-06",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14952519806786616,
      "information_ratio": 2.085764890903463,
      "correlation": null
    },
    {
      "session": "2016-09-07",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1509629101122148,
      "information_ratio": 1.729022158402915,
      "correlation": null
    },
    {
      "session": "2016-09-08",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14808189506933261,
      "information_ratio": 0.8686479078263984,
      "correlation": null
    },
    {
      "session": "2016-09-09",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1387044694677732,
      "information_ratio": 0.16255665877881242,
      "correlation": null
    },
    {
      "session": "2016-09-12",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14167081632658096,
      "information_ratio": 0.697679979559153,
      "correlation": null
    },
    {
      "session": "2016-09-13",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14050868901464847,
      "information_ratio": 0.8970179561248319,
      "correlation": null
    },
    {
      "session": "2016-09-14",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1443983549020134,
      "information_ratio": 0.6280118953173309,
      "correlation": null
    },
    {
      "session": "2016-09-15",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1446965117023555,
      "information_ratio": 0.4153946603031367,
      "correlation": null
    },
    {
      "session": "2016-09-16",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13942344635557258,
      "information_ratio": 1.1215673452291604,
      "correlation": null
    },
    {
      "session": "2016-09-19",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13871203658080644,
      "information_ratio": 0.17145319944322757,
      "correlation": null
    },
    {
      "session": "2016-09-20",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1335429943354591,
      "information_ratio": -2.1443579357518034,
      "correlation": null
    },
    {
      "session": "2016-09-21",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1287380780353253,
      "information_ratio": -3.332653817591,
      "correlation": null
    },
    {
      "session": "2016-09-22",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12524500503715796,
      "information_ratio": -3.800859259142893,
      "correlation": null
    },
    {
      "session": "2016-09-23",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1233174374649065,
      "information_ratio": -3.736034425638184,
      "correlation": null
    },
    {
      "session": "2016-09-26",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12087600618317909,
      "information_ratio": -4.5818381633487535,
      "correlation": null
    },
    {
      "session": "2016-09-27",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12363327846919994,
      "information_ratio": -4.993587339920101,
      "correlation": null
    },
    {
      "session": "2016-09-28",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1090719807585518,
      "information_ratio": -7.458780190669925,
      "correlation": null
    },
    {
      "session": "2016-09-29",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1139756001496591,
      "information_ratio": -4.998459333730197,
      "correlation": null
    },
    {
      "session": "2016-09-30",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.11985253235705051,
      "information_ratio": -3.538863116326642,
      "correlation": null
    },
    {
      "session": "2016-10-03",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1209775040766409,
      "information_ratio": -4.3688535490899465,
      "correlation": null
    },
    {
      "session": "2016-10-04",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1220411705219142,
      "information_ratio": -5.440474047268376,
      "correlation": null
    },
    {
      "session": "2016-10-05",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12090891484631502,
      "information_ratio": -5.68536888399536,
      "correlation": null
    },
    {
      "session": "2016-10-06",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13203341175896713,
      "information_ratio": -3.577955093749624,
      "correlation": null
    },
    {
      "session": "2016-10-07",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.133774096610157,
      "information_ratio": -4.110549259586613,
      "correlation": null
    },
    {
      "session": "2016-10-10",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1408920726107843,
      "information_ratio": -3.3938055374085514,
      "correlation": null
    },
    {
      "session": "2016-10-11",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14472786474826407,
      "information_ratio": -3.0084987354111212,
      "correlation": null
    },
    {
      "session": "2016-10-12",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14768838308443102,
      "information_ratio": -3.46121347193082,
      "correlation": null
    },
    {
      "session": "2016-10-13",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14011482877234707,
      "information_ratio": -1.905498068506056,
      "correlation": null
    },
    {
      "session": "2016-10-14",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1431698233715337,
      "information_ratio": -1.0337957694755693,
      "correlation": null
    },
    {
      "session": "2016-10-17",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1429239575911213,
      "information_ratio": -0.8785068320419861,
      "correlation": null
    },
    {
      "session": "2016-10-18",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14221260503690747,
      "information_ratio": -0.583596560711511,
      "correlation": null
    },
    {
      "session": "2016-10-19",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13913624574268604,
      "information_ratio": -0.27346750997688846,
      "correlation": null
    },
    {
      "session": "2016-10-20",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13870565612334274,
      "information_ratio": -0.0004753032972980066,
      "correlation": null
    },
    {
      "session": "2016-10-21",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14027275234825823,
      "information_ratio": -1.1690903672164836,
      "correlation": null
    },
    {
      "session": "2016-10-24",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14139085692170347,
      "information_ratio": 1.6628336550924514,
      "correlation": null
    },
    {
      "session": "2016-10-25",
      "return": 0.0,
      "drawdown": 0.0,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14098591239748262,
      "information_ratio": 1.793245709793532,
      "correlation": null
    },
    {
      "session": "2016-10-26",
      "return": -0.008708181888483546,
      "drawdown": -0.008708181888483546,
      "volatility": 0.030166026944809198,
      "sharpe": -3.4641016151377544,
      "beta": 0.027353061195361336,
      "alpha_annualized_arithmetic": -0.09218834128047078,
      "tracking_error": 0.13581740803484282,
      "information_ratio": 2.5441293532949163,
      "correlation": 0.12350210593872345
    },
    {
      "session": "2016-10-27",
      "return": -0.006037523129837741,
      "drawdown": -0.014693129168750763,
      "volatility": 0.035837388139625885,
      "sharpe": -4.937537845404563,
      "beta": 0.04072227336538836,
      "alpha_annualized_arithmetic": -0.15431489186637293,
      "tracking_error": 0.1350847869039093,
      "information_ratio": 2.804569720758734,
      "correlation": 0.15441935940394205
    },
    {
      "session": "2016-10-28",
      "return": -0.011903405458864702,
      "drawdown": -0.02642163635366024,
      "volatility": 0.05266860734969062,
      "sharpe": -6.071725489208523,
      "beta": 0.11421582217277292,
      "alpha_annualized_arithmetic": -0.25311438056097163,
      "tracking_error": 0.13193220582933582,
      "information_ratio": 2.0008264580317996,
      "correlation": 0.29863515350886777
    },
    {
      "session": "2016-10-31",
      "return": -0.0027256256772680842,
      "drawdown": -0.029075246540447353,
      "volatility": 0.052687456044065335,
      "sharpe": -6.69033694772883,
      "beta": 0.1237573651472457,
      "alpha_annualized_arithmetic": -0.28896660659502105,
      "tracking_error": 0.12907053988679762,
      "information_ratio": 1.246203724533604,
      "correlation": 0.3190510515395681
    },
    {
      "session": "2016-11-01",
      "return": 0.004695936895321884,
      "drawdown": -0.02451584516809535,
      "volatility": 0.05662261202956921,
      "sharpe": -5.2301647786035455,
      "beta": 0.14768813395746086,
      "alpha_annualized_arithmetic": -0.2153885313648657,
      "tracking_error": 0.12570218028444077,
      "information_ratio": 1.9940978983486006,
      "correlation": 0.34871830204036175
    },
    {
      "session": "2016-11-02",
      "return": -0.012984135034263766,
      "drawdown": -0.03718166315821758,
      "volatility": 0.06960354811092745,
      "sharpe": -6.493278342656738,
      "beta": 0.22340150457288685,
      "alpha_annualized_arithmetic": -0.27114721741340747,
      "tracking_error": 0.12053468520508263,
      "information_ratio": 2.965003595597816,
      "correlation": 0.4246598712380673
    },
    {
      "session": "2016-11-03",
      "return": -0.0034480031717948334,
      "drawdown": -0.04050146383751019,
      "volatility": 0.06950887943147555,
      "sharpe": -7.097384587657379,
      "beta": 0.2221112895406678,
      "alpha_annualized_arithmetic": -0.30953248955853707,
      "tracking_error": 0.12061787452862302,
      "information_ratio": 2.770536797735711,
      "correlation": 0.4225228344602506
    },
    {
      "session": "2016-11-04",
      "return": -0.002197618009319502,
      "drawdown": -0.042610075100496636,
      "volatility": 0.06914494381322336,
      "sharpe": -7.5161340371895,
      "beta": 0.2539463558306064,
      "alpha_annualized_arithmetic": -0.34215441620111614,
      "tracking_error": 0.11307734647360135,
      "information_ratio": 1.5870009006615517,
      "correlation": 0.46843019995364854
    },
    {
      "session": "2016-11-07",
      "return": -0.0021681794813965816,
      "drawdown": -0.044685868291359565,
      "volatility": 0.06873684904385635,
      "sharpe": -7.939276051520705,
      "beta": 0.2605033274579877,
      "alpha_annualized_arithmetic": -0.3315013034656141,
      "tracking_error": 0.10851319025718051,
      "information_ratio": 2.5490769251119985,
      "correlation": 0.45979527255893
    },
    {
      "session": "2016-11-08",
      "return": 0.0040289585854491605,
      "drawdown": -0.0408369472186112,
      "volatility": 0.07168970052918079,
      "sharpe": -6.937862939503287,
      "beta": 0.3379500805929503,
      "alpha_annualized_arithmetic": -0.2922615524740084,
      "tracking_error": 0.09797645780712973,
      "information_ratio": 1.1181855528318396,
      "correlation": 0.5529966512371068
    },
    {
      "session": "2016-11-09",
      "return": 0.006488425199062453,
      "drawdown": -0.03461348949693477,
      "volatility": 0.07724846960753454,
      "sharpe": -5.430686409557367,
      "beta": 0.4322077621658284,
      "alpha_annualized_arithmetic": -0.25391631276069143,
      "tracking_error": 0.088186107246243,
      "information_ratio": -0.41245308676030945,
      "correlation": 0.6463572181361821
    },
    {
      "session": "2016-11-10",
      "return": 0.016329575132552288,
      "drawdown": -0.018849137941722605,
      "volatility": 0.09925841005511081,
      "sharpe": -2.25227577534227,
      "beta": 0.612367086284688,
      "alpha_annualized_arithmetic": -0.031723562250394584,
      "tracking_error": 0.07978706357807713,
      "information_ratio": 1.1243505197090045,
      "correlation": 0.7684040295354786
    },
    {
      "session": "2016-11-11",
      "return": -0.004117454594395387,
      "drawdown": -0.022888982066499475,
      "volatility": 0.09981795653277514,
      "sharpe": -2.7346459202381275,
      "beta": 0.6230152203723365,
      "alpha_annualized_arithmetic": -0.07981845387481709,
      "tracking_error": 0.07843497631686902,
      "information_ratio": 0.4724302357669951,
      "correlation": 0.776869405949384
    },
    {
      "session": "2016-11-14",
      "return": -0.008906038840775121,
      "drawdown": -0.03159117074396445,
      "volatility": 0.10330696741716938,
      "sharpe": -3.6768017025832602,
      "beta": 0.6671228889548578,
      "alpha_annualized_arithmetic": -0.16267622030864226,
      "tracking_error": 0.07360790042695858,
      "information_ratio": -0.7379300146242505,
      "correlation": 0.8096490910540902
    },
    {
      "session": "2016-11-15",
      "return": 0.0009187656092017882,
      "drawdown": -0.03070143001599679,
      "volatility": 0.10352467050110203,
      "sharpe": -3.5625715550943413,
      "beta": 0.6689864290903642,
      "alpha_annualized_arithmetic": -0.14957943655083059,
      "tracking_error": 0.07354008595185407,
      "information_ratio": -0.5589121996774213,
      "correlation": 0.8099302502793728
    },
    {
      "session": "2016-11-16",
      "return": 0.005172909111123447,
      "drawdown": -0.025687336611927458,
      "volatility": 0.10596815285974766,
      "sharpe": -2.894635121650543,
      "beta": 0.6802960073191849,
      "alpha_annualized_arithmetic": -0.11852410747002477,
      "tracking_error": 0.07349146481831761,
      "information_ratio": -0.4092007574518022,
      "correlation": 0.8161758521522627
    },
    {
      "session": "2016-11-17",
      "return": 0.0035235968957634256,
      "drawdown": -0.022254251535710257,
      "volatility": 0.10717425413140358,
      "sharpe": -2.467532677865481,
      "beta": 0.7200177194150659,
      "alpha_annualized_arithmetic": -0.03051275039709571,
      "tracking_error": 0.06836420058335917,
      "information_ratio": 0.8843396585079367,
      "correlation": 0.8359246728388556
    },
    {
      "session": "2016-11-18",
      "return": -0.008006686442525113,
      "drawdown": -0.0300827551641758,
      "volatility": 0.10974453733870461,
      "sharpe": -3.285231505352072,
      "beta": 0.7304711591892241,
      "alpha_annualized_arithmetic": -0.053206024823029954,
      "tracking_error": 0.06836518944430664,
      "information_ratio": 0.8804553389722992,
      "correlation": 0.8416519046672644
    },
    {
      "session": "2016-11-21",
      "return": -0.004269571596977273,
      "drawdown": -0.0342238862841453,
      "volatility": 0.11003945137209514,
      "sharpe": -3.7420312954554342,
      "beta": 0.7866173008801396,
      "alpha_annualized_arithmetic": 0.038941975561216986,
      "tracking_error": 0.06071330201350806,
      "information_ratio": 2.6551874640996793,
      "correlation": 0.8665055392958038
    },
    {
      "session": "2016-11-22",
      "return": -0.0003433918879758302,
      "drawdown": -0.03455552596719613,
      "volatility": 0.10998161659839292,
      "sharpe": -3.7814662694357373,
      "beta": 1.0097766097500698,
      "alpha_annualized_arithmetic": -0.040925063129760256,
      "tracking_error": 0.009047947156069018,
      "information_ratio": -4.924373723047617,
      "correlation": 0.9966569727458008
    },
    {
      "session": "2016-11-23",
      "return": 0.02261064452931949,
      "drawdown": -0.012726204152044507,
      "volatility": 0.13846013522717857,
      "sharpe": -1.0440841967676038,
      "beta": 1.0110389331137135,
      "alpha_annualized_arithmetic": -0.026338253692526556,
      "tracking_error": 0.007962524933982834,
      "information_ratio": -3.46989064330981,
      "correlation": 0.9984045748565437
    },
    {
      "session": "2016-11-25",
      "return": -0.0017797546945151899,
      "drawdown": -0.014483309324976767,
      "volatility": 0.1353772119807329,
      "sharpe": -0.4537167802962589,
      "beta": 0.8253449990850663,
      "alpha_annualized_arithmetic": -0.19585422541437528,
      "tracking_error": 0.06473351611501933,
      "information_ratio": -3.465003278650656,
      "correlation": 0.8986173199013858
    },
    {
      "session": "2016-11-28",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.13372700363107157,
      "sharpe": 0.08246176548674587,
      "beta": 0.8016360917325831,
      "alpha_annualized_arithmetic": -0.11900910044013052,
      "tracking_error": 0.06907156315494627,
      "information_ratio": -2.188838126044176,
      "correlation": 0.8837643448359837
    },
    {
      "session": "2016-11-29",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.12648898437672154,
      "sharpe": 1.2164555757739508,
      "beta": 0.767915684994692,
      "alpha_annualized_arithmetic": -0.03136441157229131,
      "tracking_error": 0.0720277226890258,
      "information_ratio": -1.2126801184897416,
      "correlation": 0.8623610755587594
    },
    {
      "session": "2016-11-30",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.12593435266962336,
      "sharpe": 1.4815317226089022,
      "beta": 0.7094301210483489,
      "alpha_annualized_arithmetic": 0.08606678099728826,
      "tracking_error": 0.0820991570512353,
      "information_ratio": 0.5469010002685364,
      "correlation": 0.8312065608646293
    },
    {
      "session": "2016-12-01",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.1251239062043033,
      "sharpe": 1.040764308379007,
      "beta": 0.7021154391717475,
      "alpha_annualized_arithmetic": 0.09991448613030593,
      "tracking_error": 0.08290574996177863,
      "information_ratio": 1.0500471061734433,
      "correlation": 0.8271147075789008
    },
    {
      "session": "2016-12-02",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.11515879555624424,
      "sharpe": 2.4838234433762025,
      "beta": 0.6552433715883335,
      "alpha_annualized_arithmetic": 0.11947763352262834,
      "tracking_error": 0.0846773071485931,
      "information_ratio": 0.3760612824238401,
      "correlation": 0.7969646382925457
    },
    {
      "session": "2016-12-05",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.11404381771268889,
      "sharpe": 2.870915414283575,
      "beta": 0.5935076287329188,
      "alpha_annualized_arithmetic": 0.06268972958431988,
      "tracking_error": 0.0953874578018347,
      "information_ratio": -1.2435266050218443,
      "correlation": 0.7522293304652027
    },
    {
      "session": "2016-12-06",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.1134473022353709,
      "sharpe": 3.118466136399987,
      "beta": 0.5461443118731863,
      "alpha_annualized_arithmetic": 0.16989534647484064,
      "tracking_error": 0.10376050979966117,
      "information_ratio": 0.16463495281578638,
      "correlation": 0.7268869544358482
    },
    {
      "session": "2016-12-07",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.11283408598666232,
      "sharpe": 3.366001689494718,
      "beta": 0.5150882180040387,
      "alpha_annualized_arithmetic": 0.2560784294127775,
      "tracking_error": 0.10953869964095883,
      "information_ratio": 1.2744842281922306,
      "correlation": 0.7113794493553205
    },
    {
      "session": "2016-12-08",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.11256234539226774,
      "sharpe": 2.944610117026544,
      "beta": 0.4421267022214164,
      "alpha_annualized_arithmetic": 0.3466445746508191,
      "tracking_error": 0.12650458220020538,
      "information_ratio": 2.8917072040910017,
      "correlation": 0.666538862176909
    },
    {
      "session": "2016-12-09",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.11103885068701251,
      "sharpe": 2.2838053265191016,
      "beta": 0.4334325294667347,
      "alpha_annualized_arithmetic": 0.2938305343273984,
      "tracking_error": 0.12685941881202117,
      "information_ratio": 2.730818568873913,
      "correlation": 0.6563072447217838
    },
    {
      "session": "2016-12-12",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.09604105146997613,
      "sharpe": 0.6001206377561245,
      "beta": 0.34504196381774627,
      "alpha_annualized_arithmetic": 0.2036787781684215,
      "tracking_error": 0.13122719662833526,
      "information_ratio": 3.6646100640496524,
      "correlation": 0.5770961648615803
    },
    {
      "session": "2016-12-13",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.09474369007980499,
      "sharpe": 1.1298448698959078,
      "beta": 0.33684980866991193,
      "alpha_annualized_arithmetic": 0.26206094755340414,
      "tracking_error": 0.13226642275348574,
      "information_ratio": 4.288592182192637,
      "correlation": 0.574443143023779
    },
    {
      "session": "2016-12-14",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.08851011327023442,
      "sharpe": 2.4168779179826982,
      "beta": 0.31115941191171237,
      "alpha_annualized_arithmetic": 0.3413882116877345,
      "tracking_error": 0.132252248817112,
      "information_ratio": 4.715078789099234,
      "correlation": 0.5621340372525284
    },
    {
      "session": "2016-12-15",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.08855818253975195,
      "sharpe": 2.291069499754933,
      "beta": 0.3115761782936383,
      "alpha_annualized_arithmetic": 0.3368280657629144,
      "tracking_error": 0.1320985348978859,
      "information_ratio": 4.790031114862977,
      "correlation": 0.5617682568385772
    },
    {
      "session": "2016-12-16",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.08714521056111,
      "sharpe": 1.615901100363128,
      "beta": 0.29965909581650946,
      "alpha_annualized_arithmetic": 0.3178001567261038,
      "tracking_error": 0.13320324302397238,
      "information_ratio": 5.491079259479585,
      "correlation": 0.5472576268678145
    },
    {
      "session": "2016-12-19",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.08648710089991213,
      "sharpe": 1.1393014433671824,
      "beta": 0.28035133005797747,
      "alpha_annualized_arithmetic": 0.3234256077876426,
      "tracking_error": 0.1382085931204684,
      "information_ratio": 6.5170298343297794,
      "correlation": 0.5272358010687681
    },
    {
      "session": "2016-12-20",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.08096241144733231,
      "sharpe": 2.403771240494924,
      "beta": 0.21254112545763096,
      "alpha_annualized_arithmetic": 0.29876894310843044,
      "tracking_error": 0.15690756390016564,
      "information_ratio": 4.363434858471152,
      "correlation": 0.4653465789752074
    },
    {
      "session": "2016-12-21",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.07893791079522092,
      "sharpe": 3.114472791150003,
      "beta": 0.203450951717737,
      "alpha_annualized_arithmetic": 0.3655822283303052,
      "tracking_error": 0.16009647065266303,
      "information_ratio": 5.2115870847260695,
      "correlation": 0.4661312125854613
    },
    {
      "session": "2016-12-22",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.07887455200851042,
      "sharpe": 3.1692183556323754,
      "beta": 0.20417015329981966,
      "alpha_annualized_arithmetic": 0.3911391845910094,
      "tracking_error": 0.16075223938239902,
      "information_ratio": 5.856194956321783,
      "correlation": 0.47137856213086404
    },
    {
      "session": "2016-12-23",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.006165251111819071,
      "sharpe": -3.4641016151377544,
      "beta": -0.014437282017912749,
      "alpha_annualized_arithmetic": -0.03202744754568812,
      "tracking_error": 0.17817090126470905,
      "information_ratio": 4.028316708729624,
      "correlation": -0.4110835234322004
    },
    {
      "session": "2016-12-27",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18985130585610926,
      "information_ratio": 3.3458842851209805,
      "correlation": null
    },
    {
      "session": "2016-12-28",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18957188974813965,
      "information_ratio": 3.257731008649595,
      "correlation": null
    },
    {
      "session": "2016-12-29",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18986721697525732,
      "information_ratio": 2.793514605830622,
      "correlation": null
    },
    {
      "session": "2016-12-30",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1893782741389398,
      "information_ratio": 1.6698692574959493,
      "correlation": null
    },
    {
      "session": "2017-01-03",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1976357814367678,
      "information_ratio": 0.45423869613545537,
      "correlation": null
    },
    {
      "session": "2017-01-04",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.19744818109078555,
      "information_ratio": 1.0522601969294043,
      "correlation": null
    },
    {
      "session": "2017-01-05",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.19136879862913672,
      "information_ratio": 1.9837453924444364,
      "correlation": null
    },
    {
      "session": "2017-01-06",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.19286087747652841,
      "information_ratio": 0.5571353984933277,
      "correlation": null
    },
    {
      "session": "2017-01-09",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1909594959917895,
      "information_ratio": -0.5024218376654286,
      "correlation": null
    },
    {
      "session": "2017-01-10",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17894437214926093,
      "information_ratio": -1.479013970703185,
      "correlation": null
    },
    {
      "session": "2017-01-11",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1794464119074768,
      "information_ratio": -1.697896464342399,
      "correlation": null
    },
    {
      "session": "2017-01-12",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17860380269330453,
      "information_ratio": -1.7731115370195691,
      "correlation": null
    },
    {
      "session": "2017-01-13",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1760058779499497,
      "information_ratio": -2.3112979913493694,
      "correlation": null
    },
    {
      "session": "2017-01-17",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17613266285570114,
      "information_ratio": -2.2908455427371517,
      "correlation": null
    },
    {
      "session": "2017-01-18",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17592380313116235,
      "information_ratio": -2.4787594946115044,
      "correlation": null
    },
    {
      "session": "2017-01-19",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.175192997048839,
      "information_ratio": -2.562905772144453,
      "correlation": null
    },
    {
      "session": "2017-01-20",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1657095733945544,
      "information_ratio": -3.699280448431354,
      "correlation": null
    },
    {
      "session": "2017-01-23",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16217059605031284,
      "information_ratio": -3.5370372131145675,
      "correlation": null
    },
    {
      "session": "2017-01-24",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15403334006778152,
      "information_ratio": -5.321165109779345,
      "correlation": null
    },
    {
      "session": "2017-01-25",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1483736721539343,
      "information_ratio": -6.9258659231165955,
      "correlation": null
    },
    {
      "session": "2017-01-26",
      "return": 0.0,
      "drawdown": -0.014483309324976767,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1389640587332077,
      "information_ratio": -5.848627083275033,
      "correlation": null
    },
    {
      "session": "2017-01-27",
      "return": 0.0026960339100476904,
      "drawdown": -0.01182632290799901,
      "volatility": 0.009339335422262361,
      "sharpe": 3.4641016151377544,
      "beta": -0.002335047207893357,
      "alpha_annualized_arithmetic": 0.033567283285141365,
      "tracking_error": 0.11343027437210682,
      "information_ratio": -4.301556534680671,
      "correlation": -0.028198100567628184
    },
    {
      "session": "2017-01-30",
      "return": -0.003549205277436407,
      "drawdown": -0.01533355413775761,
      "volatility": 0.015807214070927878,
      "sharpe": -0.6476825304399528,
      "beta": 0.017670847811087024,
      "alpha_annualized_arithmetic": -0.019657261821020015,
      "tracking_error": 0.11117861079256428,
      "information_ratio": -4.88650172986805,
      "correlation": 0.12525699594514833
    },
    {
      "session": "2017-01-31",
      "return": 0.0020090777319099473,
      "drawdown": -0.013355282708016891,
      "volatility": 0.017330944630725875,
      "sharpe": 0.8003531642275991,
      "beta": 0.01745359243568302,
      "alpha_annualized_arithmetic": 0.004558730153524805,
      "tracking_error": 0.11142935710490788,
      "information_ratio": -4.663642019710985,
      "correlation": 0.11283925121123178
    },
    {
      "session": "2017-02-01",
      "return": 0.0005893989930105814,
      "drawdown": -0.012773755305185763,
      "volatility": 0.01742735745350145,
      "sharpe": 1.2017693644181158,
      "beta": 0.017451192608788406,
      "alpha_annualized_arithmetic": 0.012939952996807792,
      "tracking_error": 0.11025208596983362,
      "information_ratio": -3.9699057887130587,
      "correlation": 0.11096864572246984
    },
    {
      "session": "2017-02-02",
      "return": 0.022023607119999955,
      "drawdown": 0.0,
      "volatility": 0.07796190435928955,
      "sharpe": 3.658542618660328,
      "beta": 0.379395317666225,
      "alpha_annualized_arithmetic": 0.08086849989519079,
      "tracking_error": 0.09857601688781105,
      "information_ratio": -2.5707629287351965,
      "correlation": 0.5977419978044916
    },
    {
      "session": "2017-02-03",
      "return": 0.014485581822266003,
      "drawdown": 0.0,
      "volatility": 0.09045924866069965,
      "sharpe": 5.074704227529262,
      "beta": 0.4675505768687275,
      "alpha_annualized_arithmetic": 0.09674222700352782,
      "tracking_error": 0.09605941075391869,
      "information_ratio": -3.2881789484977393,
      "correlation": 0.6557202175187037
    },
    {
      "session": "2017-02-06",
      "return": -0.0005421858807324043,
      "drawdown": -0.0005421858807324043,
      "volatility": 0.09061618238830287,
      "sharpe": 4.994115720849451,
      "beta": 0.47123441289573104,
      "alpha_annualized_arithmetic": 0.08039919338962696,
      "tracking_error": 0.0955490096861673,
      "information_ratio": -3.5289060272957213,
      "correlation": 0.6570173138215178
    },
    {
      "session": "2017-02-07",
      "return": -0.0057960567315744616,
      "drawdown": -0.006335100072183075,
      "volatility": 0.09421636274633174,
      "sharpe": 4.06505843662281,
      "beta": 0.5336453525770937,
      "alpha_annualized_arithmetic": 0.07152282139806715,
      "tracking_error": 0.08834337924782741,
      "information_ratio": -2.2715214986813903,
      "correlation": 0.7149583698195634
    },
    {
      "session": "2017-02-08",
      "return": -0.009337625794942461,
      "drawdown": -0.015613571073278099,
      "volatility": 0.10139351307172889,
      "sharpe": 2.672197683089524,
      "beta": 0.5852872646120805,
      "alpha_annualized_arithmetic": 0.042255080427446676,
      "tracking_error": 0.08567161597272938,
      "information_ratio": -1.398187883946563,
      "correlation": 0.7579677132462199
    },
    {
      "session": "2017-02-09",
      "return": 0.014378610303412254,
      "drawdown": -0.0014594622237730226,
      "volatility": 0.1112294861475184,
      "sharpe": 3.987133715275398,
      "beta": 0.6451049577229023,
      "alpha_annualized_arithmetic": 0.043000737978226164,
      "tracking_error": 0.08353608890103326,
      "information_ratio": -2.1226852191551147,
      "correlation": 0.7906759731185976
    },
    {
      "session": "2017-02-10",
      "return": 0.007061474676589796,
      "drawdown": 0.0,
      "volatility": 0.11250424249298771,
      "sharpe": 4.695152100628824,
      "beta": 0.6575018819865615,
      "alpha_annualized_arithmetic": 0.10330319415368412,
      "tracking_error": 0.08212178808547374,
      "information_ratio": -1.4373994352324369,
      "correlation": 0.8007226598267096
    },
    {
      "session": "2017-02-13",
      "return": 0.005855881873630953,
      "drawdown": 0.0,
      "volatility": 0.11295742013616022,
      "sharpe": 5.298413439619497,
      "beta": 0.72528416551039,
      "alpha_annualized_arithmetic": -0.010273040535263369,
      "tracking_error": 0.07238882519195936,
      "information_ratio": -3.3272554481390566,
      "correlation": 0.8294686552033301
    },
    {
      "session": "2017-02-14",
      "return": -0.014763867563952537,
      "drawdown": -0.014763867563952537,
      "volatility": 0.12750941317291442,
      "sharpe": 3.3042948885302037,
      "beta": 0.7677869939075397,
      "alpha_annualized_arithmetic": -0.08415304881722467,
      "tracking_error": 0.07243234444741073,
      "information_ratio": -3.2724780718595934,
      "correlation": 0.863427602201212
    },
    {
      "session": "2017-02-15",
      "return": 0.006796966814652805,
      "drawdown": -0.008067250267187687,
      "volatility": 0.1285560571174011,
      "sharpe": 3.9118522708216297,
      "beta": 0.7933684438593872,
      "alpha_annualized_arithmetic": -0.13129260852024582,
      "tracking_error": 0.06931844456345278,
      "information_ratio": -4.276856868326138,
      "correlation": 0.8722769023866223
    },
    {
      "session": "2017-02-16",
      "return": 0.0004993983392354018,
      "drawdown": -0.007571880699338007,
      "volatility": 0.12846998967792422,
      "sharpe": 3.961120299839568,
      "beta": 0.7916031090487956,
      "alpha_annualized_arithmetic": -0.11012126673422222,
      "tracking_error": 0.06937361784301424,
      "information_ratio": -3.93637325111218,
      "correlation": 0.8724411663185181
    },
    {
      "session": "2017-02-17",
      "return": -0.012126623562138117,
      "drawdown": -0.01960668291457779,
      "volatility": 0.13742745002766224,
      "sharpe": 2.6440540169711917,
      "beta": 0.8454962657467201,
      "alpha_annualized_arithmetic": -0.2473734162532942,
      "tracking_error": 0.06278089872411474,
      "information_ratio": -5.717953134173491,
      "correlation": 0.9047893807539278
    },
    {
      "session": "2017-02-21",
      "return": -0.00514976355524599,
      "drawdown": -0.024655476688711042,
      "volatility": 0.13925397477371712,
      "sharpe": 2.1656002215723777,
      "beta": 0.8470554631926445,
      "alpha_annualized_arithmetic": -0.262501842574698,
      "tracking_error": 0.06263178086787857,
      "information_ratio": -5.817342286352727,
      "correlation": 0.9080712740994437
    },
    {
      "session": "2017-02-22",
      "return": -0.005343048786065063,
      "drawdown": -0.029866790059984605,
      "volatility": 0.14105097313465542,
      "sharpe": 1.683447110750027,
      "beta": 0.9356680449175329,
      "alpha_annualized_arithmetic": -0.16019756484630007,
      "tracking_error": 0.0399163400958153,
      "information_ratio": -4.698276246278462,
      "correlation": 0.9613972608687226
    },
    {
      "session": "2017-02-23",
      "return": -0.0007207784634287728,
      "drawdown": -0.030566041184366455,
      "volatility": 0.14113371779819878,
      "sharpe": 1.6211754016005253,
      "beta": 0.9635402478081523,
      "alpha_annualized_arithmetic": -0.07944758517427461,
      "tracking_error": 0.029860512904187026,
      "information_ratio": -3.0512393986981103,
      "correlation": 0.9780619940633204
    },
    {
      "session": "2017-02-24",
      "return": -0.0020766971160091074,
      "drawdown": -0.03257926189080018,
      "volatility": 0.14148495927866409,
      "sharpe": 1.4410163969245755,
      "beta": 1.0007009172403856,
      "alpha_annualized_arithmetic": 0.009693056196227654,
      "tracking_error": 0.005846338472165881,
      "information_ratio": 1.6812354243204268,
      "correlation": 0.999146156599778
    },
    {
      "session": "2017-02-27",
      "return": -0.002187721032690715,
      "drawdown": -0.03469570858702287,
      "volatility": 0.1418450947612903,
      "sharpe": 1.2522780159962748,
      "beta": 1.0007938451194252,
      "alpha_annualized_arithmetic": 0.017984526017834814,
      "tracking_error": 0.005215685468047501,
      "information_ratio": 3.472440771298087,
      "correlation": 0.9993240585569652
    },
    {
      "session": "2017-02-28",
      "return": -0.004352098017220474,
      "drawdown": -0.038896807479695705,
      "volatility": 0.14269719694161526,
      "sharpe": 0.6520934728474488,
      "beta": 1.0002917437555525,
      "alpha_annualized_arithmetic": -0.00010107789295687097,
      "tracking_error": 5.086744998250348e-05,
      "information_ratio": -1.452972708355773,
      "correlation": 0.999999978996506
    },
    {
      "session": "2017-03-01",
      "return": 0.001847279031282012,
      "drawdown": -0.0371213817052547,
      "volatility": 0.14205308092855823,
      "sharpe": 1.1109208008184028,
      "beta": 1.0002946186193744,
      "alpha_annualized_arithmetic": -8.11197223264423e-05,
      "tracking_error": 5.158035297026852e-05,
      "information_ratio": -0.6711051653845088,
      "correlation": 0.9999999774514494
    },
    {
      "session": "2017-03-02",
      "return": 0.020959690954030608,
      "drawdown": -0.016939743439552957,
      "volatility": 0.1585842792484965,
      "sharpe": 2.4291000527593303,
      "beta": 1.0004919413388227,
      "alpha_annualized_arithmetic": 8.294974857004419e-05,
      "tracking_error": 0.00010466190079264748,
      "information_ratio": 2.6019018158060883,
      "correlation": 0.9999999030996434
    },
    {
      "session": "2017-03-03",
      "return": -0.019621120155379423,
      "drawdown": -0.03622848685350355,
      "volatility": 0.17472525419158716,
      "sharpe": 0.8166584273626631,
      "beta": 1.000613978068441,
      "alpha_annualized_arithmetic": -0.0001047196987577566,
      "tracking_error": 0.00013599059921826106,
      "information_ratio": -0.12574506230974486,
      "correlation": 0.9999998853691874
    },
    {
      "session": "2017-03-06",
      "return": 5.8176314008839825e-05,
      "drawdown": -0.03617241817932193,
      "volatility": 0.15633745808141788,
      "sharpe": -0.7732908021332326,
      "beta": 1.000696490193868,
      "alpha_annualized_arithmetic": -4.1973494145930174e-06,
      "tracking_error": 0.0001341911546018147,
      "information_ratio": -0.6582962244223701,
      "correlation": 0.999999873835404
    },
    {
      "session": "2017-03-07",
      "return": 0.002966341251709581,
      "drawdown": -0.03331337666383183,
      "volatility": 0.14727358704058682,
      "sharpe": -1.7594818624096904,
      "beta": 1.0007562846861215,
      "alpha_annualized_arithmetic": 0.00010549056472058862,
      "tracking_error": 0.00013412396629641242,
      "information_ratio": -0.6741038453674557,
      "correlation": 0.9999998708520423
    },
    {
      "session": "2017-03-08",
      "return": 0.00021383001686103853,
      "drawdown": -0.03310667004686452,
      "volatility": 0.14732830321716764,
      "sharpe": -1.697250351619255,
      "beta": 1.0007561037693389,
      "alpha_annualized_arithmetic": 0.00010348604953999609,
      "tracking_error": 0.000134139705447781,
      "information_ratio": -0.6375093673526839,
      "correlation": 0.999999870926255
    },
    {
      "session": "2017-03-09",
      "return": -0.0032882746085431958,
      "drawdown": -0.036286080832919176,
      "volatility": 0.14655209379272535,
      "sharpe": -1.5008972118373745,
      "beta": 1.000766021134204,
      "alpha_annualized_arithmetic": 5.2217653899325114e-05,
      "tracking_error": 0.0001347156044268465,
      "information_ratio": -0.8624618454681738,
      "correlation": 0.99999987044995
    },
    {
      "session": "2017-03-10",
      "return": -0.014292068561158722,
      "drawdown": -0.050059546238998,
      "volatility": 0.1510924132910333,
      "sharpe": -1.849285057210798,
      "beta": 1.0008378465390857,
      "alpha_annualized_arithmetic": -6.626542751128096e-05,
      "tracking_error": 0.00014746056419363598,
      "information_ratio": -2.035250183202672,
      "correlation": 0.9999998741542713
    },
    {
      "session": "2017-03-13",
      "return": 0.004484489573769013,
      "drawdown": -0.04579954817840548,
      "volatility": 0.1419230105304782,
      "sharpe": -2.805340652122392,
      "beta": 1.0009254681127444,
      "alpha_annualized_arithmetic": 8.996147000650372e-05,
      "tracking_error": 0.00014837690024483376,
      "information_ratio": -1.8752858833185306,
      "correlation": 0.9999998809453964
    },
    {
      "session": "2017-03-14",
      "return": 0.023054131801850453,
      "drawdown": -0.023801285196725308,
      "volatility": 0.16338279379063603,
      "sharpe": -1.2622535128998185,
      "beta": 1.001026914212526,
      "alpha_annualized_arithmetic": 0.0002592427430683996,
      "tracking_error": 0.000181332564013374,
      "information_ratio": 0.2614699525366021,
      "correlation": 0.9999999102967778
    },
    {
      "session": "2017-03-15",
      "return": -0.008074409450288145,
      "drawdown": -0.03168351332489194,
      "volatility": 0.16333897288062035,
      "sharpe": -2.2860067913464155,
      "beta": 1.0010543725527927,
      "alpha_annualized_arithmetic": 0.00030348842141295854,
      "tracking_error": 0.00018457894014866188,
      "information_ratio": -0.4882082009763349,
      "correlation": 0.999999916189524
    },
    {
      "session": "2017-03-16",
      "return": 0.006117869410935839,
      "drawdown": -0.02575947951095736,
      "volatility": 0.15786974327958087,
      "sharpe": -0.7779398068728631,
      "beta": 1.0011302205617192,
      "alpha_annualized_arithmetic": 0.00018584088800033434,
      "tracking_error": 0.00018609877429290968,
      "information_ratio": 0.2524564300821041,
      "correlation": 0.9999999424588227
    },
    {
      "session": "2017-03-17",
      "return": -0.005342091903917656,
      "drawdown": -0.030963961907930382,
      "volatility": 0.1564059843843921,
      "sharpe": -1.7165702660135762,
      "beta": 1.0011599369051871,
      "alpha_annualized_arithmetic": 0.00025782368611247664,
      "tracking_error": 0.000187443947147295,
      "information_ratio": -0.28561197312641146,
      "correlation": 0.9999999530337833
    },
    {
      "session": "2017-03-20",
      "return": 0.0007521775913981177,
      "drawdown": -0.030235074714820454,
      "volatility": 0.15644029714196264,
      "sharpe": -1.6968039312402727,
      "beta": 1.0011602190215987,
      "alpha_annualized_arithmetic": 0.0002639996562176705,
      "tracking_error": 0.00018748294970427108,
      "information_ratio": -0.23430285227307968,
      "correlation": 0.9999999533761608
    },
    {
      "session": "2017-03-21",
      "return": -0.010806358442584485,
      "drawdown": -0.04071470210249828,
      "volatility": 0.15532568682106535,
      "sharpe": -1.6069803705280212,
      "beta": 1.0012273256706714,
      "alpha_annualized_arithmetic": 0.00013985975907584904,
      "tracking_error": 0.00019279383834613833,
      "information_ratio": -0.8624922221526313,
      "correlation": 0.9999999810013099
    },
    {
      "session": "2017-03-22",
      "return": -0.0058921693778017925,
      "drawdown": -0.04636697355934538,
      "volatility": 0.15559722729656592,
      "sharpe": -1.6614319170236918,
      "beta": 1.0012385727045228,
      "alpha_annualized_arithmetic": 8.153986072836645e-05,
      "tracking_error": 0.00019418874623701967,
      "information_ratio": -1.2274323671208445,
      "correlation": 0.9999999863553044
    },
    {
      "session": "2017-03-23",
      "return": 0.006611362573012869,
      "drawdown": -0.040062159859946656,
      "volatility": 0.15692301100862402,
      "sharpe": -0.733233848767062,
      "beta": 1.0012501161713119,
      "alpha_annualized_arithmetic": 2.229239031607236e-05,
      "tracking_error": 0.00019680310177715767,
      "information_ratio": -0.6168388389683406,
      "correlation": 0.9999999930142114
    },
    {
      "session": "2017-03-24",
      "return": 0.0064053919542954585,
      "drawdown": -0.0339133817420898,
      "volatility": 0.15870342348810557,
      "sharpe": -0.1861788338264369,
      "beta": 1.0012500526608596,
      "alpha_annualized_arithmetic": 1.3940410197249369e-05,
      "tracking_error": 0.00019899357388502136,
      "information_ratio": -0.11541307057918722,
      "correlation": 0.9999999932702262
    },
    {
      "session": "2017-03-27",
      "return": 0.014153857437452233,
      "drawdown": -0.020239529475037044,
      "volatility": 0.16597142639349174,
      "sharpe": 0.9954691594958556,
      "beta": 1.00125166235317,
      "alpha_annualized_arithmetic": -1.1812055775456236e-05,
      "tracking_error": 0.0002081708440686997,
      "information_ratio": 0.9354967114048779,
      "correlation": 0.999999994791595
    },
    {
      "session": "2017-03-28",
      "return": 0.004409128697342668,
      "drawdown": -0.015919639467923408,
      "volatility": 0.16612060266578418,
      "sharpe": 1.4711097189090157,
      "beta": 1.0012547349433434,
      "alpha_annualized_arithmetic": -3.9676534829668174e-05,
      "tracking_error": 0.00020871081148136092,
      "information_ratio": 1.277476219427,
      "correlation": 0.9999999959612595
    },
    {
      "session": "2017-03-29",
      "return": 0.004772531879804864,
      "drawdown": -0.011223084574994324,
      "volatility": 0.1654431852170741,
      "sharpe": 2.1389650555424704,
      "beta": 1.0012440137217604,
      "alpha_annualized_arithmetic": 1.2596928167878628e-05,
      "tracking_error": 0.0002055677352405175,
      "information_ratio": 2.200065051588831,
      "correlation": 0.9999999999259541
    },
    {
      "session": "2017-03-30",
      "return": 0.01877192267893313,
      "drawdown": 0.0,
      "volatility": 0.17606167141138315,
      "sharpe": 3.1635103266023226,
      "beta": 1.0012400583925258,
      "alpha_annualized_arithmetic": 8.22362251772131e-06,
      "tracking_error": 0.0002180740001510096,
      "information_ratio": 3.2009178255355453,
      "correlation": 0.9999999998758377
    },
    {
      "session": "2017-03-31",
      "return": 0.004126446179395948,
      "drawdown": 0.0,
      "volatility": 0.16261771647225845,
      "sharpe": 2.1828739576091385,
      "beta": 1.0012384954451896,
      "alpha_annualized_arithmetic": 4.427184904457621e-06,
      "tracking_error": 0.0002011719774875983,
      "information_ratio": 2.2046388305736326,
      "correlation": 0.9999999998493642
    },
    {
      "session": "2017-04-03",
      "return": 0.011814966041565844,
      "drawdown": 0.0,
      "volatility": 0.14711801310564426,
      "sharpe": 4.977004496184371,
      "beta": 1.001239203892271,
      "alpha_annualized_arithmetic": -6.98604778096891e-06,
      "tracking_error": 0.00018211398773523027,
      "information_ratio": 4.937859991989864,
      "correlation": 0.9999999997441292
    },
    {
      "session": "2017-04-04",
      "return": -0.004558336926865136,
      "drawdown": -0.004558336926865136,
      "volatility": 0.14909967284895348,
      "sharpe": 4.539304754153695,
      "beta": 1.0012379162438834,
      "alpha_annualized_arithmetic": -2.5725167953818268e-06,
      "tracking_error": 0.00018437804837114174,
      "information_ratio": 4.5245486704579125,
      "correlation": 0.999999999723469
    },
    {
      "session": "2017-04-05",
      "return": -0.000309345769929692,
      "drawdown": -0.004866272594548637,
      "volatility": 0.14945337683530815,
      "sharpe": 4.2655483806755665,
      "beta": 1.001237861924836,
      "alpha_annualized_arithmetic": -2.6408440123755483e-06,
      "tracking_error": 0.00018480716807245506,
      "information_ratio": 4.250508921854001,
      "correlation": 0.9999999997249361
    },
    {
      "session": "2017-04-06",
      "return": -0.00010611522294157183,
      "drawdown": -0.00497187143188893,
      "volatility": 0.14951994089523346,
      "sharpe": 4.23797162354893,
      "beta": 1.001237852443556,
      "alpha_annualized_arithmetic": -2.574931607279146e-06,
      "tracking_error": 0.0001848880393928306,
      "information_ratio": 4.223299984637157,
      "correlation": 0.9999999997251415
    },
    {
      "session": "2017-04-07",
      "return": 0.004028091851421944,
      "drawdown": -0.0009638067352680801,
      "volatility": 0.1480833763247915,
      "sharpe": 4.87196930603419,
      "beta": 1.0012376806508811,
      "alpha_annualized_arithmetic": -5.037995992978467e-06,
      "tracking_error": 0.00018308855041863044,
      "information_ratio": 4.843550401592874,
      "correlation": 0.9999999997062802
    },
    {
      "session": "2017-04-10",
      "return": -0.018834787288943833,
      "drawdown": -0.019780440929365484,
      "volatility": 0.15537105890917943,
      "sharpe": 4.292595056874323,
      "beta": 1.001223294951464,
      "alpha_annualized_arithmetic": 2.02097104204102e-05,
      "tracking_error": 0.00018989722676387522,
      "information_ratio": 4.397424339702082,
      "correlation": 0.9999999994902162
    },
    {
      "session": "2017-04-11",
      "return": 0.0023667174642316713,
      "drawdown": -0.017460538180131602,
      "volatility": 0.15522854638358294,
      "sharpe": 4.132820857287069,
      "beta": 1.0012231993533725,
      "alpha_annualized_arithmetic": 1.730424747414458e-05,
      "tracking_error": 0.00018970853974028385,
      "information_ratio": 4.222507122418579,
      "correlation": 0.9999999994879131
    },
    {
      "session": "2017-04-12",
      "return": -0.0025065464175069163,
      "drawdown": -0.01992331894821542,
      "volatility": 0.13684313145030563,
      "sharpe": 2.4466236044132024,
      "beta": 1.0012119778059425,
      "alpha_annualized_arithmetic": 1.1878532086373114e-05,
      "tracking_error": 0.00016569405563086903,
      "information_ratio": 2.5175769434193755,
      "correlation": 0.9999999996108879
    },
    {
      "session": "2017-04-13",
      "return": 0.010728006778268906,
      "drawdown": -0.009409049670668579,
      "volatility": 0.1360627697167122,
      "sharpe": 4.1189271056120855,
      "beta": 1.0012094322750118,
      "alpha_annualized_arithmetic": 1.3371641140456567e-05,
      "tracking_error": 0.00016440379918574295,
      "information_ratio": 4.199063729807143,
      "correlation": 0.9999999996104119
    },
    {
      "session": "2017-04-17",
      "return": 0.004481067900868219,
      "drawdown": -0.004970144360257334,
      "volatility": 0.1355898677479202,
      "sharpe": 3.9884323298803763,
      "beta": 1.00120879206547,
      "alpha_annualized_arithmetic": 1.0104498765269032e-05,
      "tracking_error": 0.00016374617076310332,
      "information_ratio": 4.048992063021934,
      "correlation": 0.9999999996073005
    },
    {
      "session": "2017-04-18",
      "return": 0.019422553036248624,
      "drawdown": 0.0,
      "volatility": 0.1451584648961994,
      "sharpe": 5.772772204578094,
      "beta": 1.0012021511379234,
      "alpha_annualized_arithmetic": 1.0573996308564995e-05,
      "tracking_error": 0.00017434311402771954,
      "information_ratio": 5.8316867936815715,
      "correlation": 0.9999999995844799
    },
    {
      "session": "2017-04-19",
      "return": -0.0004861824682992344,
      "drawdown": -0.0004861824682992344,
      "volatility": 0.14549804072147784,
      "sharpe": 5.657165049193223,
      "beta": 1.0012021765734955,
      "alpha_annualized_arithmetic": 1.0469595231875004e-05,
      "tracking_error": 0.0001747544273712378,
      "information_ratio": 5.715381057998847,
      "correlation": 0.9999999995863476
    },
    {
      "session": "2017-04-20",
      "return": -0.014560799824276827,
      "drawdown": -0.015039903086977113,
      "volatility": 0.15056649909679815,
      "sharpe": 5.167504981404421,
      "beta": 1.0011928881627052,
      "alpha_annualized_arithmetic": 3.0165089779168874e-05,
      "tracking_error": 0.00017944226503640765,
      "information_ratio": 5.334048173794723,
      "correlation": 0.9999999996259019
    },
    {
      "session": "2017-04-21",
      "return": 0.001980965090509157,
      "drawdown": -0.013088731519447894,
      "volatility": 0.14707994390058615,
      "sharpe": 5.93235708822964,
      "beta": 1.0011904456425593,
      "alpha_annualized_arithmetic": 3.610672204854698e-05,
      "tracking_error": 0.00017492326504303367,
      "information_ratio": 6.137143451452067,
      "correlation": 0.9999999996703274
    },
    {
      "session": "2017-04-24",
      "return": -0.014367097268672024,
      "drawdown": -0.027267781709256478,
      "volatility": 0.1588991818864488,
      "sharpe": 3.9068119940256483,
      "beta": 1.0011888862188332,
      "alpha_annualized_arithmetic": 3.455101465126703e-05,
      "tracking_error": 0.00018872329757730483,
      "information_ratio": 4.088956388363067,
      "correlation": 0.9999999997415591
    },
    {
      "session": "2017-04-25",
      "return": -0.002792674817125862,
      "drawdown": -0.02998430647908401,
      "volatility": 0.1592183885541497,
      "sharpe": 3.2057379365084815,
      "beta": 1.0011886426272425,
      "alpha_annualized_arithmetic": 2.979427783392566e-05,
      "tracking_error": 0.00018906162098327256,
      "information_ratio": 3.3625893016690678,
      "correlation": 0.9999999997573008
    },
    {
      "session": "2017-04-26",
      "return": 0.012131070134326905,
      "drawdown": -0.018216978069584,
      "volatility": 0.15742096025282448,
      "sharpe": 3.088146457495383,
      "beta": 1.0011841977803237,
      "alpha_annualized_arithmetic": 2.326097345646625e-05,
      "tracking_error": 0.00018621315106554743,
      "information_ratio": 3.212647660694614,
      "correlation": 0.9999999998790745
    },
    {
      "session": "2017-04-27",
      "return": 0.0042753957176169255,
      "drawdown": -0.014019467141993869,
      "volatility": 0.15739509377783756,
      "sharpe": 3.07845799607636,
      "beta": 1.0011839415828332,
      "alpha_annualized_arithmetic": 2.088316619853082e-05,
      "tracking_error": 0.0001861423968696828,
      "information_ratio": 3.1902472188454376,
      "correlation": 0.9999999998785587
    },
    {
      "session": "2017-04-28",
      "return": -0.01089708823737423,
      "drawdown": -0.024763784008880685,
      "volatility": 0.16307775860254586,
      "sharpe": 1.8181433576117019,
      "beta": 1.00115464395851,
      "alpha_annualized_arithmetic": 8.944632030501339e-05,
      "tracking_error": 0.00018885972141562634,
      "information_ratio": 2.2836992636022515,
      "correlation": 0.9999999944712906
    },
    {
      "session": "2017-05-01",
      "return": -0.0005344300793628243,
      "drawdown": -0.025284979577190336,
      "volatility": 0.15002230455616067,
      "sharpe": 0.43208581996956114,
      "beta": 1.0011464353484207,
      "alpha_annualized_arithmetic": 8.235301853222183e-05,
      "tracking_error": 0.00017262092511390815,
      "information_ratio": 0.9065438152647735,
      "correlation": 0.999999993672273
    },
    {
      "session": "2017-05-02",
      "return": 0.006258738720998025,
      "drawdown": -0.019184492936931807,
      "volatility": 0.15089453066612002,
      "sharpe": 0.5991603577544137,
      "beta": 1.001126495127201,
      "alpha_annualized_arithmetic": 1.1604214154460352e-05,
      "tracking_error": 0.00017194133299470256,
      "information_ratio": 0.6590794804790043,
      "correlation": 0.9999999838609288
    },
    {
      "session": "2017-05-03",
      "return": -0.010287009998749652,
      "drawdown": -0.02927415186501836,
      "volatility": 0.1491655868719844,
      "sharpe": -1.171943845578245,
      "beta": 1.0010705878310655,
      "alpha_annualized_arithmetic": 0.00010626432479156908,
      "tracking_error": 0.00016483831272439336,
      "information_ratio": -0.490192956024688,
      "correlation": 0.9999999612649177
    },
    {
      "session": "2017-05-04",
      "return": 0.0017306206409717362,
      "drawdown": -0.02759419367551108,
      "volatility": 0.14870275928117083,
      "sharpe": -0.668085791903837,
      "beta": 1.0010661514078287,
      "alpha_annualized_arithmetic": 9.365687906783492e-05,
      "tracking_error": 0.0001638285273244054,
      "information_ratio": -0.07476203611283579,
      "correlation": 0.9999999602379998
    },
    {
      "session": "2017-05-05",
      "return": -0.00014669061173600006,
      "drawdown": -0.02773683647809655,
      "volatility": 0.14870499667117107,
      "sharpe": -0.6549500082346854,
      "beta": 1.001066135674735,
      "alpha_annualized_arithmetic": 9.558031124285988e-05,
      "tracking_error": 0.00016382449849638186,
      "information_ratio": -0.05033725771430023,
      "correlation": 0.9999999602693899
    },
    {
      "session": "2017-05-08",
      "return": 0.01616858393093934,
      "drawdown": -0.012016717915732,
      "volatility": 0.15939432910235712,
      "sharpe": 0.6142128870179535,
      "beta": 1.000954762468521,
      "alpha_annualized_arithmetic": -5.91626277316494e-05,
      "tracking_error": 0.00016425867731249797,
      "information_ratio": 0.20868211994274607,
      "correlation": 0.9999999239331601
    },
    {
      "session": "2017-05-09",
      "return": 0.007988042941040385,
      "drawdown": -0.0041246650334128,
      "volatility": 0.1611146310719446,
      "sharpe": 0.9025962642879587,
      "beta": 1.0009322095231008,
      "alpha_annualized_arithmetic": -0.00013831933488926218,
      "tracking_error": 0.00016351309591656156,
      "information_ratio": -0.016839595122988934,
      "correlation": 0.9999999187007464
    },
    {
      "session": "2017-05-10",
      "return": -0.01993294906687615,
      "drawdown": -0.023975397362259954,
      "volatility": 0.16281766888884902,
      "sharpe": 0.8122184999636677,
      "beta": 1.000748998651968,
      "alpha_annualized_arithmetic": 0.0001143266189044716,
      "tracking_error": 0.0001435259652007977,
      "information_ratio": 1.485564925892863,
      "correlation": 0.9999998915467254
    },
    {
      "session": "2017-05-11",
      "return": 0.0015675860640274042,
      "drawdown": -0.022445394797017126,
      "volatility": 0.162727266952453,
      "sharpe": 0.7537393596481219,
      "beta": 1.0007477864265846,
      "alpha_annualized_arithmetic": 9.161534745997721e-05,
      "tracking_error": 0.00014335138229415304,
      "information_ratio": 1.2779598497341917,
      "correlation": 0.9999998911554128
    },
    {
      "session": "2017-05-12",
      "return": 0.004893884216491395,
      "drawdown": -0.017661355743855855,
      "volatility": 0.1630311096502433,
      "sharpe": 1.2970476251536391,
      "beta": 1.00073967096789,
      "alpha_annualized_arithmetic": 7.521274049191763e-05,
      "tracking_error": 0.0001427122786732674,
      "information_ratio": 1.6218065590272812,
      "correlation": 0.9999998900173669
    },
    {
      "session": "2017-05-15",
      "return": 0.006092453694281241,
      "drawdown": -0.011676503041622155,
      "volatility": 0.16025549527397986,
      "sharpe": 0.9724002058321968,
      "beta": 1.0007072921571678,
      "alpha_annualized_arithmetic": -1.7459802171849396e-05,
      "tracking_error": 0.00013600729552781744,
      "information_ratio": 0.6815349459606258,
      "correlation": 0.9999998896399085
    },
    {
      "session": "2017-05-16",
      "return": 0.011699911058062229,
      "drawdown": -0.00011320603061604206,
      "volatility": 0.16434671851672203,
      "sharpe": 1.4752871043897173,
      "beta": 1.0006747268336251,
      "alpha_annualized_arithmetic": -0.0001053244657778403,
      "tracking_error": 0.00013505404739009146,
      "information_ratio": 0.4311574960825776,
      "correlation": 0.9999998896740421
    },
    {
      "session": "2017-05-17",
      "return": -0.012619180127177776,
      "drawdown": -0.012730957590502023,
      "volatility": 0.15628186785261244,
      "sharpe": -0.9088847313917975,
      "beta": 1.0005298985031557,
      "alpha_annualized_arithmetic": -0.00017249443964269858,
      "tracking_error": 0.00010713992174244347,
      "information_ratio": -2.3112875876689993,
      "correlation": 0.9999999052542142
    },
    {
      "session": "2017-05-18",
      "return": -0.006292988452558657,
      "drawdown": -0.018943830273953632,
      "volatility": 0.1575351161860698,
      "sharpe": -1.3439789198851968,
      "beta": 1.0005223255993654,
      "alpha_annualized_arithmetic": -0.0001461545035731848,
      "tracking_error": 0.00010713427120597922,
      "information_ratio": -2.395211795046074,
      "correlation": 0.9999999050247339
    },
    {
      "session": "2017-05-19",
      "return": 0.005285982359434671,
      "drawdown": -0.013757984667167156,
      "volatility": 0.15060488433017896,
      "sharpe": 0.1755421879335237,
      "beta": 1.0004486338711889,
      "alpha_annualized_arithmetic": -5.305928355226982e-05,
      "tracking_error": 9.047262534623531e-05,
      "information_ratio": -0.4551658114003339,
      "correlation": 0.9999999201086368
    },
    {
      "session": "2017-05-22",
      "return": -0.009839641558998968,
      "drawdown": -0.023462252588467014,
      "volatility": 0.1542715604209754,
      "sharpe": -0.7480949085519917,
      "beta": 1.0004337172435358,
      "alpha_annualized_arithmetic": -4.368343385156457e-05,
      "tracking_error": 9.022550516466144e-05,
      "information_ratio": -1.038486867758105,
      "correlation": 0.999999922949834
    },
    {
      "session": "2017-05-23",
      "return": 0.015434121590374827,
      "drawdown": -0.008390250257326537,
      "volatility": 0.15495626681359279,
      "sharpe": 1.5630529981380097,
      "beta": 1.0003249730758936,
      "alpha_annualized_arithmetic": 6.862092367086866e-05,
      "tracking_error": 6.818916905144009e-05,
      "information_ratio": 2.159919532456234,
      "correlation": 0.9999999559455549
    },
    {
      "session": "2017-05-24",
      "return": 0.0020799398477715503,
      "drawdown": -0.006327761625398054,
      "volatility": 0.15438725265545133,
      "sharpe": 1.947545721751088,
      "beta": 1.000319074507796,
      "alpha_annualized_arithmetic": 9.641563096358333e-05,
      "tracking_error": 6.670513570569387e-05,
      "information_ratio": 2.8827225146337816,
      "correlation": 0.9999999575322536
    },
    {
      "session": "2017-05-25",
      "return": 0.005936490725284793,
      "drawdown": -0.00042883559831419227,
      "volatility": 0.15029455254443833,
      "sharpe": 1.5059845926657904,
      "beta": 1.0002521939393558,
      "alpha_annualized_arithmetic": -2.356573368787274e-05,
      "tracking_error": 4.453470883697172e-05,
      "information_ratio": 0.7523955115239399,
      "correlation": 0.9999999878832146
    },
    {
      "session": "2017-05-26",
      "return": -0.0022801836669327225,
      "drawdown": -0.002708041441319864,
      "volatility": 0.1501540604202252,
      "sharpe": 0.9834854113544589,
      "beta": 1.0002435278034174,
      "alpha_annualized_arithmetic": -6.851337941247938e-05,
      "tracking_error": 4.082792356672737e-05,
      "information_ratio": -0.7970684482597329,
      "correlation": 0.9999999926717794
    },
    {
      "session": "2017-05-30",
      "return": 0.0069189007941621306,
      "drawdown": 0.0,
      "volatility": 0.14560106602785694,
      "sharpe": 2.482579325265426,
      "beta": 1.0002083988324344,
      "alpha_annualized_arithmetic": 1.945289166241891e-06,
      "tracking_error": 3.0338024265731866e-05,
      "information_ratio": 2.546583825299382,
      "correlation": 0.9999999999982053
    },
    {
      "session": "2017-05-31",
      "return": 0.007018402330000173,
      "drawdown": 0.0,
      "volatility": 0.1466611249934137,
      "sharpe": 3.0826177365680434,
      "beta": 1.0002082846683515,
      "alpha_annualized_arithmetic": 1.705851534075306e-06,
      "tracking_error": 3.0542349683274687e-05,
      "information_ratio": 3.1383120577062305,
      "correlation": 0.9999999999979456
    },
    {
      "session": "2017-06-01",
      "return": 0.005971287680895054,
      "drawdown": 0.0,
      "volatility": 0.14655420822452306,
      "sharpe": 3.0613298527814705,
      "beta": 1.0002081692567946,
      "alpha_annualized_arithmetic": 1.202582539066091e-06,
      "tracking_error": 3.0503406968508442e-05,
      "information_ratio": 3.1005779870948214,
      "correlation": 0.9999999999976201
    },
    {
      "session": "2017-06-02",
      "return": -6.128609108058125e-05,
      "drawdown": -6.128609108058125e-05,
      "volatility": 0.14008319557112203,
      "sharpe": 4.078715203854887,
      "beta": 1.0002080156534865,
      "alpha_annualized_arithmetic": 1.4759168781505738e-06,
      "tracking_error": 2.9135100281841277e-05,
      "information_ratio": 4.129129546492747,
      "correlation": 0.999999999997531
    },
    {
      "session": "2017-06-05",
      "return": 0.0011118315789255817,
      "drawdown": 0.0,
      "volatility": 0.14012945861866866,
      "sharpe": 4.02437857389131,
      "beta": 1.0002080248437784,
      "alpha_annualized_arithmetic": 1.313389326436723e-06,
      "tracking_error": 2.9146039682290096e-05,
      "information_ratio": 4.069197702681302,
      "correlation": 0.999999999997486
    },
    {
      "session": "2017-06-06",
      "return": -0.007924161211026015,
      "drawdown": -0.007924161211026015,
      "volatility": 0.14432422522773136,
      "sharpe": 3.2607439458060856,
      "beta": 1.0002077617867273,
      "alpha_annualized_arithmetic": 2.0244580588787975e-06,
      "tracking_error": 2.9980814798689322e-05,
      "information_ratio": 3.3280392174212245,
      "correlation": 0.9999999999971442
    },
    {
      "session": "2017-06-07",
      "return": -0.0023315159539872843,
      "drawdown": -0.010237201856727829,
      "volatility": 0.13516402830055566,
      "sharpe": 1.8392700199239138,
      "beta": 1.0002072120439423,
      "alpha_annualized_arithmetic": 1.5581879451095904e-06,
      "tracking_error": 2.80032014924727e-05,
      "information_ratio": 1.8948104538058799,
      "correlation": 0.9999999999978705
    },
    {
      "session": "2017-06-08",
      "return": -0.002007359674513931,
      "drawdown": -0.012224011785054723,
      "volatility": 0.13305877989327813,
      "sharpe": 0.9669284036867019,
      "beta": 1.0002072060513936,
      "alpha_annualized_arithmetic": 1.5496972082381863e-06,
      "tracking_error": 2.756628378252933e-05,
      "information_ratio": 1.0230843889649457,
      "correlation": 0.9999999999978029
    },
    {
      "session": "2017-06-09",
      "return": 0.0030513387149151416,
      "drawdown": -0.009209972670550903,
      "volatility": 0.11046724348983607,
      "sharpe": 3.6614452777344613,
      "beta": 1.0002073750278384,
      "alpha_annualized_arithmetic": 1.2021999225416899e-06,
      "tracking_error": 2.2905120598046745e-05,
      "information_ratio": 3.713645126873707,
      "correlation": 0.9999999999967667
    },
    {
      "session": "2017-06-12",
      "return": 0.0037532437361533777,
      "drawdown": -0.005491296206633467,
      "volatility": 0.11071709098782728,
      "sharpe": 3.890073838130986,
      "beta": 1.0002073367679016,
      "alpha_annualized_arithmetic": 9.952416862432298e-07,
      "tracking_error": 2.295277042246502e-05,
      "information_ratio": 3.9331193172495102,
      "correlation": 0.99999999999662
    },
    {
      "session": "2017-06-13",
      "return": -0.010892910607490425,
      "drawdown": -0.016324390615425677,
      "volatility": 0.11824534698854298,
      "sharpe": 2.040301181756511,
      "beta": 1.0002068393925374,
      "alpha_annualized_arithmetic": 1.5025127305108403e-06,
      "tracking_error": 2.4454795567316598e-05,
      "information_ratio": 2.101557218712446,
      "correlation": 0.9999999999964011
    },
    {
      "session": "2017-06-14",
      "return": -0.005209288954518554,
      "drawdown": -0.021448641102222,
      "volatility": 0.1185420664747207,
      "sharpe": 0.8911200264495329,
      "beta": 1.0002067817143507,
      "alpha_annualized_arithmetic": 1.426490504112055e-06,
      "tracking_error": 2.4509295614961904e-05,
      "information_ratio": 0.9492361497642892,
      "correlation": 0.9999999999964568
    },
    {
      "session": "2017-06-15",
      "return": 0.01186148858769509,
      "drawdown": -0.009841565326182522,
      "volatility": 0.11873696619310879,
      "sharpe": 0.9059869324349732,
      "beta": 1.0002065780729523,
      "alpha_annualized_arithmetic": 1.2077705456704866e-06,
      "tracking_error": 2.4525410478047992e-05,
      "information_ratio": 0.955147718629081,
      "correlation": 0.9999999999964814
    },
    {
      "session": "2017-06-16",
      "return": -0.003923749670047605,
      "drawdown": -0.013726699157528777,
      "volatility": 0.11021377865056588,
      "sharpe": 1.9228022834185237,
      "beta": 1.0002066487875454,
      "alpha_annualized_arithmetic": 1.1757769398258039e-06,
      "tracking_error": 2.277301029869814e-05,
      "information_ratio": 1.9742384973405918,
      "correlation": 0.999999999995928
    },
    {
      "session": "2017-06-19",
      "return": -0.010151493012594548,
      "drawdown": -0.023738845679539655,
      "volatility": 0.11410257348202595,
      "sharpe": 1.4514769078293401,
      "beta": 1.0002063930098808,
      "alpha_annualized_arithmetic": 1.5750808186197791e-06,
      "tracking_error": 2.354718583867897e-05,
      "information_ratio": 1.5182258020342845,
      "correlation": 0.9999999999962532
    },
    {
      "session": "2017-06-20",
      "return": 0.003443704321642427,
      "drawdown": -0.020376890923354707,
      "volatility": 0.11333681025117914,
      "sharpe": 1.266225101637366,
      "beta": 1.000206330382492,
      "alpha_annualized_arithmetic": 1.399259205421468e-06,
      "tracking_error": 2.338206147770841e-05,
      "information_ratio": 1.3259445824302016,
      "correlation": 0.9999999999962536
    },
    {
      "session": "2017-06-21",
      "return": 0.006344055802419923,
      "drawdown": -0.01416210725403233,
      "volatility": 0.10836527255048987,
      "sharpe": 3.1164438059179154,
      "beta": 1.0002059723192687,
      "alpha_annualized_arithmetic": 1.7576118970788132e-06,
      "tracking_error": 2.2317579217860662e-05,
      "information_ratio": 3.194912800085177,
      "correlation": 0.999999999996334
    },
    {
      "session": "2017-06-22",
      "return": -0.007385266137975299,
      "drawdown": -0.021442782460862064,
      "volatility": 0.09943339240061555,
      "sharpe": 0.6424565041389845,
      "beta": 1.0002047232945848,
      "alpha_annualized_arithmetic": 1.091621178349149e-06,
      "tracking_error": 2.035258768321183e-05,
      "information_ratio": 0.6960676853509663,
      "correlation": 0.9999999999991303
    },
    {
      "session": "2017-06-23",
      "return": 0.005023590820747881,
      "drawdown": -0.016526911405255973,
      "volatility": 0.10063034294920681,
      "sharpe": 0.9858402390834472,
      "beta": 1.00020474258776,
      "alpha_annualized_arithmetic": 1.121184329910688e-06,
      "tracking_error": 2.0599520548704802e-05,
      "information_ratio": 1.0402366288297804,
      "correlation": 0.999999999999143
    },
    {
      "session": "2017-06-26",
      "return": 0.005548109344523544,
      "drawdown": -0.011070495172336048,
      "volatility": 0.10036945387793621,
      "sharpe": 0.9419685086454747,
      "beta": 1.0002046747944144,
      "alpha_annualized_arithmetic": 1.0095401768339847e-06,
      "tracking_error": 2.0539291856212196e-05,
      "information_ratio": 0.9910918377907363,
      "correlation": 0.999999999999188
    },
    {
      "session": "2017-06-27",
      "return": 0.008534559088449356,
      "drawdown": -0.0026304178790733657,
      "volatility": 0.10370082665151763,
      "sharpe": 2.163162870450102,
      "beta": 1.0002045767999266,
      "alpha_annualized_arithmetic": 1.0080747725829155e-06,
      "tracking_error": 2.1210835819284344e-05,
      "information_ratio": 2.210639605684139,
      "correlation": 0.9999999999992275
    },
    {
      "session": "2017-06-28",
      "return": 0.0017680568491984516,
      "drawdown": -0.0008670117582222359,
      "volatility": 0.10143815023589423,
      "sharpe": 1.602076241828746,
      "beta": 1.0002045119728629,
      "alpha_annualized_arithmetic": 8.408061274722822e-07,
      "tracking_error": 2.074147406570664e-05,
      "information_ratio": 1.642574518787034,
      "correlation": 0.9999999999991944
    },
    {
      "session": "2017-06-29",
      "return": 0.02052234646877027,
      "drawdown": 0.0,
      "volatility": 0.12102429356817238,
      "sharpe": 2.681767194041912,
      "beta": 1.0002036409262942,
      "alpha_annualized_arithmetic": 5.055072660464788e-07,
      "tracking_error": 2.4641280739791216e-05,
      "information_ratio": 2.702190677839649,
      "correlation": 0.9999999999986554
    },
    {
      "session": "2017-06-30",
      "return": -0.0001830799230161384,
      "drawdown": -0.0001830799230161384,
      "volatility": 0.11989600769801691,
      "sharpe": 2.091033502614572,
      "beta": 1.0002036587914742,
      "alpha_annualized_arithmetic": 5.356613718447353e-07,
      "tracking_error": 2.4413707081078884e-05,
      "information_ratio": 2.1129012713217956,
      "correlation": 0.9999999999986362
    },
    {
      "session": "2017-07-03",
      "return": -0.017292680738294486,
      "drawdown": -0.017472594718652368,
      "volatility": 0.13563450487346618,
      "sharpe": 0.32388390550548596,
      "beta": 1.0002025252884685,
      "alpha_annualized_arithmetic": 1.7462450830477757e-06,
      "tracking_error": 2.7466092759248597e-05,
      "information_ratio": 0.38742285768006046,
      "correlation": 0.9999999999966597
    },
    {
      "session": "2017-07-05",
      "return": 0.00874176567682805,
      "drawdown": -0.008883570370620819,
      "volatility": 0.13883647990838197,
      "sharpe": 0.975889351443942,
      "beta": 1.000202444859445,
      "alpha_annualized_arithmetic": 1.659380700632252e-06,
      "tracking_error": 2.8103268518894018e-05,
      "information_ratio": 1.0348459361384188,
      "correlation": 0.9999999999967548
    },
    {
      "session": "2017-07-06",
      "return": -0.005159627819311674,
      "drawdown": -0.013997362273113434,
      "volatility": 0.13703202897599814,
      "sharpe": 1.2308322681602057,
      "beta": 1.0002024036112827,
      "alpha_annualized_arithmetic": 1.7794694370559978e-06,
      "tracking_error": 2.773242895034061e-05,
      "information_ratio": 1.2948844506344235,
      "correlation": 0.9999999999966563
    },
    {
      "session": "2017-07-07",
      "return": -0.006289164007916681,
      "drawdown": -0.020198494574016346,
      "volatility": 0.13879845896399365,
      "sharpe": 0.8730044071988131,
      "beta": 1.0002023733591128,
      "alpha_annualized_arithmetic": 1.932954115680839e-06,
      "tracking_error": 2.8085641487202065e-05,
      "information_ratio": 0.9417452190307787,
      "correlation": 0.9999999999967717
    },
    {
      "session": "2017-07-10",
      "return": 0.015140953257175571,
      "drawdown": -0.005363365779051277,
      "volatility": 0.14737212599148866,
      "sharpe": 2.2185431564387343,
      "beta": 1.0002022580569403,
      "alpha_annualized_arithmetic": 1.960920506534347e-06,
      "tracking_error": 2.9803258171346496e-05,
      "information_ratio": 2.2841700895370365,
      "correlation": 0.9999999999971375
    },
    {
      "session": "2017-07-11",
      "return": -0.010424984661101089,
      "drawdown": -0.01573243743417385,
      "volatility": 0.1526507270924436,
      "sharpe": 1.0824418868046697,
      "beta": 1.0002021083762427,
      "alpha_annualized_arithmetic": 2.3031479119213667e-06,
      "tracking_error": 3.084788615320811e-05,
      "information_ratio": 1.1570135178749301,
      "correlation": 0.9999999999971809
    },
    {
      "session": "2017-07-12",
      "return": -0.01330171436814287,
      "drawdown": -0.028824883413252733,
      "volatility": 0.1595663639565391,
      "sharpe": -0.24706933979045553,
      "beta": 1.0002020936294092,
      "alpha_annualized_arithmetic": 2.3739511741442893e-06,
      "tracking_error": 3.224286746358041e-05,
      "information_ratio": -0.17344143065054496,
      "correlation": 0.99999999999742
    },
    {
      "session": "2017-07-13",
      "return": -0.021181843773474096,
      "drawdown": -0.04939616300947869,
      "volatility": 0.17180085339144419,
      "sharpe": -0.9481393774928816,
      "beta": 1.000202425931418,
      "alpha_annualized_arithmetic": 2.09095394489503e-06,
      "tracking_error": 3.477208730526522e-05,
      "information_ratio": -0.8879590474031295,
      "correlation": 0.9999999999974345
    },
    {
      "session": "2017-07-14",
      "return": -0.016169591803682493,
      "drawdown": -0.06476703902062975,
      "volatility": 0.1794918999331479,
      "sharpe": -1.640267825383387,
      "beta": 1.00020299652904,
      "alpha_annualized_arithmetic": 1.2942881027246111e-06,
      "tracking_error": 3.643247801871028e-05,
      "information_ratio": -1.6045854752653093,
      "correlation": 0.9999999999958835
    },
    {
      "session": "2017-07-17",
      "return": 0.003573287909938605,
      "drawdown": -0.06142518238818606,
      "volatility": 0.17412706417759305,
      "sharpe": -2.261987235417015,
      "beta": 1.000202859870592,
      "alpha_annualized_arithmetic": 1.1398285935807287e-06,
      "tracking_error": 3.531988519956879e-05,
      "information_ratio": -2.229488073968155,
      "correlation": 0.9999999999957417
    },
    {
      "session": "2017-07-18",
      "return": 0.0023855210522236714,
      "drawdown": -0.05918619240168599,
      "volatility": 0.17442067346998108,
      "sharpe": -1.8241068648198815,
      "beta": 1.000202872747563,
      "alpha_annualized_arithmetic": 1.426166471044099e-06,
      "tracking_error": 3.5381694474862775e-05,
      "information_ratio": -1.783617778032577,
      "correlation": 0.9999999999957313
    },
    {
      "session": "2017-07-19",
      "return": -0.0011856177460158879,
      "drawdown": -0.060301637947671294,
      "volatility": 0.17140258309643247,
      "sharpe": -1.228519668957885,
      "beta": 1.0002027773758573,
      "alpha_annualized_arithmetic": 1.5229765123595841e-06,
      "tracking_error": 3.4753182739327804e-05,
      "information_ratio": -1.1845764134266012,
      "correlation": 0.9999999999956672
    },
    {
      "session": "2017-07-20",
      "return": -0.012305007279248215,
      "drawdown": -0.07186463313302283,
      "volatility": 0.17509080834135796,
      "sharpe": -2.281992913505013,
      "beta": 1.000203218815105,
      "alpha_annualized_arithmetic": 3.5832680293258756e-07,
      "tracking_error": 3.557980570858832e-05,
      "information_ratio": -2.2715846962428174,
      "correlation": 0.9999999999938626
    },
    {
      "session": "2017-07-21",
      "return": -0.02214753825148874,
      "drawdown": -0.09242054667326871,
      "volatility": 0.18629193927832657,
      "sharpe": -3.9800708252544834,
      "beta": 1.0002047369230371,
      "alpha_annualized_arithmetic": -1.4296590887391547e-06,
      "tracking_error": 3.814483198040002e-05,
      "information_ratio": -4.016311605751426,
      "correlation": 0.9999999999870317
    },
    {
      "session": "2017-07-24",
      "return": 0.004749170030691419,
      "drawdown": -0.08811029753305821,
      "volatility": 0.18738466021932157,
      "sharpe": -3.1797793788475137,
      "beta": 1.0002049236939927,
      "alpha_annualized_arithmetic": -5.454486352429039e-07,
      "tracking_error": 3.8404151260501906e-05,
      "information_ratio": -3.192947510635178,
      "correlation": 0.9999999999863727
    },
    {
      "session": "2017-07-25",
      "return": -0.005203812104067174,
      "drawdown": -0.09285560020432992,
      "volatility": 0.1856450478511649,
      "sharpe": -3.870669979581782,
      "beta": 1.0002049499251644,
      "alpha_annualized_arithmetic": -1.3753466049787333e-06,
      "tracking_error": 3.8053291073333604e-05,
      "information_ratio": -3.9054677681682772,
      "correlation": 0.9999999999854843
    },
    {
      "session": "2017-07-26",
      "return": 0.004907197973125443,
      "drawdown": -0.08840406304432058,
      "volatility": 0.18529261090948654,
      "sharpe": -3.919539189757953,
      "beta": 1.0002051297146615,
      "alpha_annualized_arithmetic": -4.82876980947497e-07,
      "tracking_error": 3.801516528739148e-05,
      "information_ratio": -3.930801519460228,
      "correlation": 0.999999999984568
    },
    {
      "session": "2017-07-27",
      "return": 0.005808904054636965,
      "drawdown": -0.08310868970994822,
      "volatility": 0.18340757639333988,
      "sharpe": -4.138157895998531,
      "beta": 1.0002053952932777,
      "alpha_annualized_arithmetic": 6.598030047478415e-07,
      "tracking_error": 3.76781659394455e-05,
      "information_ratio": -4.119019107222053,
      "correlation": 0.9999999999833711
    },
    {
      "session": "2017-07-28",
      "return": 0.0006507032626343889,
      "drawdown": -0.08251206554286128,
      "volatility": 0.18308122069451788,
      "sharpe": -4.218771048973839,
      "beta": 1.0014753579641027,
      "alpha_annualized_arithmetic": 0.018171716056069577,
      "tracking_error": 0.004958009399401891,
      "information_ratio": 3.4302256146020076,
      "correlation": 0.9996343291481009
    },
    {
      "session": "2017-07-31",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.1624014546865899,
      "sharpe": -6.272394006986556,
      "beta": 0.9351604784599162,
      "alpha_annualized_arithmetic": -0.16984787162761267,
      "tracking_error": 0.037510191037753146,
      "information_ratio": -2.959097312003394,
      "correlation": 0.9753075494411929
    },
    {
      "session": "2017-08-01",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.16245750030334283,
      "sharpe": -6.2567068318049,
      "beta": 0.9313291326490624,
      "alpha_annualized_arithmetic": -0.19557247543076342,
      "tracking_error": 0.03785458041640257,
      "information_ratio": -3.56748778620706,
      "correlation": 0.9751281831957502
    },
    {
      "session": "2017-08-02",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.15557270413632177,
      "sharpe": -5.199734668476938,
      "beta": 0.9026251891070775,
      "alpha_annualized_arithmetic": -0.2787696688928764,
      "tracking_error": 0.044273715945063345,
      "information_ratio": -5.00467303441847,
      "correlation": 0.9642782571419461
    },
    {
      "session": "2017-08-03",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.1499566234794105,
      "sharpe": -6.094015389815357,
      "beta": 0.8934564319958772,
      "alpha_annualized_arithmetic": -0.28604922246839226,
      "tracking_error": 0.044591238150453946,
      "information_ratio": -4.736046899270069,
      "correlation": 0.9616269250936168
    },
    {
      "session": "2017-08-04",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.1503565365568107,
      "sharpe": -5.666015305790474,
      "beta": 0.892433696990608,
      "alpha_annualized_arithmetic": -0.24223582581837816,
      "tracking_error": 0.047042998802948155,
      "information_ratio": -3.5871316777392965,
      "correlation": 0.9567691929256494
    },
    {
      "session": "2017-08-07",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.15040202382532797,
      "sharpe": -5.162513439734566,
      "beta": 0.8595927359005939,
      "alpha_annualized_arithmetic": -0.34358417016016396,
      "tracking_error": 0.054501972371049465,
      "information_ratio": -5.006768599983679,
      "correlation": 0.944720279405571
    },
    {
      "session": "2017-08-08",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.13571685956865306,
      "sharpe": -7.059873854235177,
      "beta": 0.8093118590200981,
      "alpha_annualized_arithmetic": -0.46561179627298926,
      "tracking_error": 0.05732039550277209,
      "information_ratio": -6.098397349694691,
      "correlation": 0.9326906505853184
    },
    {
      "session": "2017-08-09",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.13410201153456108,
      "sharpe": -6.212017873421188,
      "beta": 0.7913105499655388,
      "alpha_annualized_arithmetic": -0.3863523293631476,
      "tracking_error": 0.06378259362270035,
      "information_ratio": -4.210364017855559,
      "correlation": 0.9119314572975218
    },
    {
      "session": "2017-08-10",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.12944454784712733,
      "sharpe": -5.202409304191163,
      "beta": 0.7788809883444662,
      "alpha_annualized_arithmetic": -0.3932873676281301,
      "tracking_error": 0.0643244132224913,
      "information_ratio": -4.877753325435893,
      "correlation": 0.9050292975623343
    },
    {
      "session": "2017-08-11",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.11072432195527501,
      "sharpe": -3.786353236684248,
      "beta": 0.7327817887704867,
      "alpha_annualized_arithmetic": -0.34627494298860206,
      "tracking_error": 0.06422728973246354,
      "information_ratio": -4.977117957741281,
      "correlation": 0.874809983334814
    },
    {
      "session": "2017-08-14",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.09739895516124432,
      "sharpe": -2.3122044050473076,
      "beta": 0.6582284895305808,
      "alpha_annualized_arithmetic": -0.23674078885422337,
      "tracking_error": 0.06944657587153592,
      "information_ratio": -3.495202373883465,
      "correlation": 0.8204114598624225
    },
    {
      "session": "2017-08-15",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.09611212760316255,
      "sharpe": -2.7893019827528645,
      "beta": 0.6296920200061309,
      "alpha_annualized_arithmetic": -0.3073331998067883,
      "tracking_error": 0.0727050957105173,
      "information_ratio": -4.544574995215333,
      "correlation": 0.8086487565408563
    },
    {
      "session": "2017-08-16",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.09538590709168543,
      "sharpe": -3.110648205416556,
      "beta": 0.5239721756097118,
      "alpha_annualized_arithmetic": -0.22384432086130515,
      "tracking_error": 0.090826043753418,
      "information_ratio": -1.7356713114738607,
      "correlation": 0.7310296241365131
    },
    {
      "session": "2017-08-17",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.09547300598834518,
      "sharpe": -2.9587901296317742,
      "beta": 0.4772019104645943,
      "alpha_annualized_arithmetic": -0.15765820917097206,
      "tracking_error": 0.09993533481629814,
      "information_ratio": -0.2091831820708452,
      "correlation": 0.6912094792662262
    },
    {
      "session": "2017-08-18",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.08639466458435634,
      "sharpe": -1.560565123578538,
      "beta": 0.41078586396604205,
      "alpha_annualized_arithmetic": -0.05089252919613018,
      "tracking_error": 0.10336030465035173,
      "information_ratio": 0.6723663904995716,
      "correlation": 0.6386728223199859
    },
    {
      "session": "2017-08-21",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.03588681650304182,
      "sharpe": 3.6488597029260967,
      "beta": 0.09619672125567574,
      "alpha_annualized_arithmetic": 0.14181523242527716,
      "tracking_error": 0.11452674320953062,
      "information_ratio": 2.129948142389948,
      "correlation": 0.3244071834124826
    },
    {
      "session": "2017-08-22",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.03243965366655184,
      "sharpe": 2.27979987074309,
      "beta": 0.07777970226176512,
      "alpha_annualized_arithmetic": 0.09280330140473948,
      "tracking_error": 0.11578230889940928,
      "information_ratio": 2.7316212932371395,
      "correlation": 0.2899983064843753
    },
    {
      "session": "2017-08-23",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.025620194032967582,
      "sharpe": 5.323990259763157,
      "beta": 0.048859896432674944,
      "alpha_annualized_arithmetic": 0.13978589029493857,
      "tracking_error": 0.12131295518459997,
      "information_ratio": 1.6953305579390334,
      "correlation": 0.23806680788153833
    },
    {
      "session": "2017-08-24",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.020136174543317578,
      "sharpe": 3.849553828633284,
      "beta": 0.02877225207771436,
      "alpha_annualized_arithmetic": 0.07985474856845272,
      "tracking_error": 0.12239217399833627,
      "information_ratio": 1.297672051945348,
      "correlation": 0.17768938706750304
    },
    {
      "session": "2017-08-25",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0022541022230671928,
      "sharpe": 3.4641016151377557,
      "beta": 3.3451529886007016e-05,
      "alpha_annualized_arithmetic": 0.007815536088595174,
      "tracking_error": 0.12333121093611922,
      "information_ratio": 1.7835247407069597,
      "correlation": 0.001830026391797201
    },
    {
      "session": "2017-08-28",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1282028934372314,
      "information_ratio": 0.7134869147604544,
      "correlation": null
    },
    {
      "session": "2017-08-29",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12754749498796955,
      "information_ratio": 0.7754716052377969,
      "correlation": null
    },
    {
      "session": "2017-08-30",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12758535036175844,
      "information_ratio": 0.7606505498194893,
      "correlation": null
    },
    {
      "session": "2017-08-31",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13278673981696185,
      "information_ratio": 0.2512543093280927,
      "correlation": null
    },
    {
      "session": "2017-09-01",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13278385108346147,
      "information_ratio": 0.11559178725543785,
      "correlation": null
    },
    {
      "session": "2017-09-05",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1331129064716897,
      "information_ratio": 0.19559198560829882,
      "correlation": null
    },
    {
      "session": "2017-09-06",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12992880164165632,
      "information_ratio": 1.412503382248103,
      "correlation": null
    },
    {
      "session": "2017-09-07",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13317596579066482,
      "information_ratio": 3.066785111239969,
      "correlation": null
    },
    {
      "session": "2017-09-08",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13325751484113685,
      "information_ratio": 3.079818663437326,
      "correlation": null
    },
    {
      "session": "2017-09-11",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13182072158212718,
      "information_ratio": 3.68675619872303,
      "correlation": null
    },
    {
      "session": "2017-09-12",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13535401874308334,
      "information_ratio": 2.9981757267982636,
      "correlation": null
    },
    {
      "session": "2017-09-13",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14788200293663561,
      "information_ratio": 0.8813901299580076,
      "correlation": null
    },
    {
      "session": "2017-09-14",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14832828251907343,
      "information_ratio": 2.2600896400727435,
      "correlation": null
    },
    {
      "session": "2017-09-15",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14634961521756618,
      "information_ratio": 0.19651504854026938,
      "correlation": null
    },
    {
      "session": "2017-09-18",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14276145609947902,
      "information_ratio": -0.17735239827420865,
      "correlation": null
    },
    {
      "session": "2017-09-19",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14122490003254456,
      "information_ratio": -1.308495135990688,
      "correlation": null
    },
    {
      "session": "2017-09-20",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13336340257588844,
      "information_ratio": -2.038179579020228,
      "correlation": null
    },
    {
      "session": "2017-09-21",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14931471431852375,
      "information_ratio": -0.7508869455332057,
      "correlation": null
    },
    {
      "session": "2017-09-22",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15242534445357564,
      "information_ratio": -1.015684341622498,
      "correlation": null
    },
    {
      "session": "2017-09-25",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.152073712184463,
      "information_ratio": -0.8821975185323753,
      "correlation": null
    },
    {
      "session": "2017-09-26",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15248468989612365,
      "information_ratio": -0.8149045527178056,
      "correlation": null
    },
    {
      "session": "2017-09-27",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14947472721150948,
      "information_ratio": 0.15435308281967888,
      "correlation": null
    },
    {
      "session": "2017-09-28",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1449078265048839,
      "information_ratio": 1.1311786507085795,
      "correlation": null
    },
    {
      "session": "2017-09-29",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14775822915325035,
      "information_ratio": 0.630677090030457,
      "correlation": null
    },
    {
      "session": "2017-10-02",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14013162746939484,
      "information_ratio": 1.781729113462058,
      "correlation": null
    },
    {
      "session": "2017-10-03",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14015337214004683,
      "information_ratio": 1.7692177703234597,
      "correlation": null
    },
    {
      "session": "2017-10-04",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1407119478032054,
      "information_ratio": 1.0180062045976668,
      "correlation": null
    },
    {
      "session": "2017-10-05",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1406761601566818,
      "information_ratio": 0.3326758625422743,
      "correlation": null
    },
    {
      "session": "2017-10-06",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1335906884624755,
      "information_ratio": -0.6947155994493465,
      "correlation": null
    },
    {
      "session": "2017-10-09",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1608239328809534,
      "information_ratio": 0.8636806316638406,
      "correlation": null
    },
    {
      "session": "2017-10-10",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16250214738391536,
      "information_ratio": 0.1817761059225254,
      "correlation": null
    },
    {
      "session": "2017-10-11",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1605076229923361,
      "information_ratio": 0.9236775189599787,
      "correlation": null
    },
    {
      "session": "2017-10-12",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15408239416677208,
      "information_ratio": 1.3929319359350394,
      "correlation": null
    },
    {
      "session": "2017-10-13",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15070212053500995,
      "information_ratio": 0.7854808744840749,
      "correlation": null
    },
    {
      "session": "2017-10-16",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14502218013794016,
      "information_ratio": 2.0687070232736597,
      "correlation": null
    },
    {
      "session": "2017-10-17",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1456018398901409,
      "information_ratio": 0.985641450778194,
      "correlation": null
    },
    {
      "session": "2017-10-18",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15718496672071677,
      "information_ratio": 0.020008155878106386,
      "correlation": null
    },
    {
      "session": "2017-10-19",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17860534652511173,
      "information_ratio": -2.218031875478628,
      "correlation": null
    },
    {
      "session": "2017-10-20",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16175088986983327,
      "information_ratio": -3.929968248802001,
      "correlation": null
    },
    {
      "session": "2017-10-23",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1573929721072242,
      "information_ratio": -3.206353823490027,
      "correlation": null
    },
    {
      "session": "2017-10-24",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1608106780148486,
      "information_ratio": -3.8347649308766503,
      "correlation": null
    },
    {
      "session": "2017-10-25",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16215768191630275,
      "information_ratio": -3.664893091117543,
      "correlation": null
    },
    {
      "session": "2017-10-26",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16183328731432423,
      "information_ratio": -3.734611901977261,
      "correlation": null
    },
    {
      "session": "2017-10-27",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16167582318682297,
      "information_ratio": -3.7773022973057206,
      "correlation": null
    },
    {
      "session": "2017-10-30",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16149882798067708,
      "information_ratio": -3.750386762706037,
      "correlation": null
    },
    {
      "session": "2017-10-31",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16746701580764112,
      "information_ratio": -2.8940814086527653,
      "correlation": null
    },
    {
      "session": "2017-11-01",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17927821894095433,
      "information_ratio": -1.544821285443327,
      "correlation": null
    },
    {
      "session": "2017-11-02",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.19261720505060975,
      "information_ratio": 0.05545228865064055,
      "correlation": null
    },
    {
      "session": "2017-11-03",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1959669638561147,
      "information_ratio": 0.9673872774349592,
      "correlation": null
    },
    {
      "session": "2017-11-06",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1959882076369788,
      "information_ratio": 0.9182973667011389,
      "correlation": null
    },
    {
      "session": "2017-11-07",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17335331774967608,
      "information_ratio": -0.5004580109082498,
      "correlation": null
    },
    {
      "session": "2017-11-08",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18427224314307897,
      "information_ratio": -1.2938969253963224,
      "correlation": null
    },
    {
      "session": "2017-11-09",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18658813771845825,
      "information_ratio": -2.122716090405772,
      "correlation": null
    },
    {
      "session": "2017-11-10",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18794585310085235,
      "information_ratio": -0.7166868133841255,
      "correlation": null
    },
    {
      "session": "2017-11-13",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1877963012266033,
      "information_ratio": -0.9360379763201241,
      "correlation": null
    },
    {
      "session": "2017-11-14",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18973098630196356,
      "information_ratio": -0.654507726087289,
      "correlation": null
    },
    {
      "session": "2017-11-15",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18864699841358398,
      "information_ratio": -0.34829557536841604,
      "correlation": null
    },
    {
      "session": "2017-11-16",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17798009921821586,
      "information_ratio": 0.8292516470832921,
      "correlation": null
    },
    {
      "session": "2017-11-17",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15031170373936695,
      "information_ratio": 2.835488608613979,
      "correlation": null
    },
    {
      "session": "2017-11-20",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1503186588897763,
      "information_ratio": 2.83251585681182,
      "correlation": null
    },
    {
      "session": "2017-11-21",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15386608074627695,
      "information_ratio": 2.263171046186957,
      "correlation": null
    },
    {
      "session": "2017-11-22",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1494088524253175,
      "information_ratio": 4.093861214896267,
      "correlation": null
    },
    {
      "session": "2017-11-24",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1493054203301511,
      "information_ratio": 3.210988476223891,
      "correlation": null
    },
    {
      "session": "2017-11-27",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17375890873293354,
      "information_ratio": 0.9683959452939055,
      "correlation": null
    },
    {
      "session": "2017-11-28",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17405325317262646,
      "information_ratio": 0.7259388573588715,
      "correlation": null
    },
    {
      "session": "2017-11-29",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.18011538315932066,
      "information_ratio": 0.21328004543921947,
      "correlation": null
    },
    {
      "session": "2017-11-30",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.17649081163196245,
      "information_ratio": -0.28593842640546624,
      "correlation": null
    },
    {
      "session": "2017-12-01",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.16654812495090246,
      "information_ratio": -1.9252663393330494,
      "correlation": null
    },
    {
      "session": "2017-12-04",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14967398775198215,
      "information_ratio": -3.4056199451304976,
      "correlation": null
    },
    {
      "session": "2017-12-05",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1421175853892315,
      "information_ratio": -4.471716615370347,
      "correlation": null
    },
    {
      "session": "2017-12-06",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14546707808098144,
      "information_ratio": -3.8115131741954618,
      "correlation": null
    },
    {
      "session": "2017-12-07",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14449438804639694,
      "information_ratio": -4.737828105869407,
      "correlation": null
    },
    {
      "session": "2017-12-08",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13202177303920395,
      "information_ratio": -3.281690149349746,
      "correlation": null
    },
    {
      "session": "2017-12-11",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.13444324043252953,
      "information_ratio": -3.4527249900489805,
      "correlation": null
    },
    {
      "session": "2017-12-12",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12947125340056326,
      "information_ratio": -5.564245555846218,
      "correlation": null
    },
    {
      "session": "2017-12-13",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12981015350401517,
      "information_ratio": -5.939668657402243,
      "correlation": null
    },
    {
      "session": "2017-12-14",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12433667663239246,
      "information_ratio": -6.857602578148426,
      "correlation": null
    },
    {
      "session": "2017-12-15",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12425652436203367,
      "information_ratio": -7.248491970189031,
      "correlation": null
    },
    {
      "session": "2017-12-18",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12424674715857409,
      "information_ratio": -7.251461702054334,
      "correlation": null
    },
    {
      "session": "2017-12-19",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.12587084690442782,
      "information_ratio": -7.79821853930644,
      "correlation": null
    },
    {
      "session": "2017-12-20",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.1452959368854513,
      "information_ratio": -5.283356499728613,
      "correlation": null
    },
    {
      "session": "2017-12-21",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.14712985586678162,
      "information_ratio": -4.057683038657327,
      "correlation": null
    },
    {
      "session": "2017-12-22",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15596915393767413,
      "information_ratio": -3.3156988450214886,
      "correlation": null
    },
    {
      "session": "2017-12-26",
      "return": 0.0,
      "drawdown": -0.08251206554286128,
      "volatility": 0.0,
      "sharpe": null,
      "beta": 0.0,
      "alpha_annualized_arithmetic": 0.0,
      "tracking_error": 0.15944182144032046,
      "information_ratio": -2.4250026488678023,
      "correlation": null
    },
    {
      "session": "2017-12-27",
      "return": 0.010818042249714832,
      "drawdown": -0.07258664230430034,
      "volatility": 0.037474797629865615,
      "sharpe": 3.4641016151377553,
      "beta": 0.06426986415730801,
      "alpha_annualized_arithmetic": 0.11531194145265428,
      "tracking_error": 0.13744048936650666,
      "information_ratio": -0.6975070609003662,
      "correlation": 0.2429314041320064
    },
    {
      "session": "2017-12-28",
      "return": 0.00936918630753203,
      "drawdown": -0.0638975337719555,
      "volatility": 0.04833335057905599,
      "sharpe": 5.01199978451181,
      "beta": 0.10539534303485601,
      "alpha_annualized_arithmetic": 0.2095568161112162,
      "tracking_error": 0.1372619777962072,
      "information_ratio": -0.49480612674735613,
      "correlation": 0.3153426642397472
    },
    {
      "session": "2017-12-29",
      "return": -0.005589104431545033,
      "drawdown": -0.06912950821433095,
      "volatility": 0.05335132681261482,
      "sharpe": 3.2834701585528623,
      "beta": 0.15179565765530878,
      "alpha_annualized_arithmetic": 0.16552908335311584,
      "tracking_error": 0.1264394819700815,
      "information_ratio": 0.882759733682305,
      "correlation": 0.3908312460979239
    },
    {
      "session": "2018-01-02",
      "return": -0.015172460012180422,
      "drawdown": -0.08325310352746773,
      "volatility": 0.07664589964232313,
      "sharpe": -0.0899204089182276,
      "beta": 0.26851998307777636,
      "alpha_annualized_arithmetic": 0.014605089439043088,
      "tracking_error": 0.12604644101347784,
      "information_ratio": 0.5804667899148964,
      "correlation": 0.5152291873383448
    }
  ],
  "drawdown_episodes": [
    {
      "start": "2016-10-26",
      "recovery": "2017-02-02",
      "underwater_sessions": 67,
      "maximum_drawdown": -0.044685868291359565
    },
    {
      "start": "2017-02-06",
      "recovery": "2017-02-10",
      "underwater_sessions": 4,
      "maximum_drawdown": -0.015613571073278099
    },
    {
      "start": "2017-02-14",
      "recovery": "2017-03-30",
      "underwater_sessions": 31,
      "maximum_drawdown": -0.050059546238998
    },
    {
      "start": "2017-04-04",
      "recovery": "2017-04-18",
      "underwater_sessions": 9,
      "maximum_drawdown": -0.01992331894821542
    },
    {
      "start": "2017-04-19",
      "recovery": "2017-05-30",
      "underwater_sessions": 28,
      "maximum_drawdown": -0.02998430647908401
    },
    {
      "start": "2017-06-02",
      "recovery": "2017-06-05",
      "underwater_sessions": 1,
      "maximum_drawdown": -6.128609108058125e-05
    },
    {
      "start": "2017-06-06",
      "recovery": "2017-06-29",
      "underwater_sessions": 17,
      "maximum_drawdown": -0.023738845679539655
    },
    {
      "start": "2017-06-30",
      "recovery": null,
      "underwater_sessions": 128,
      "maximum_drawdown": -0.09285560020432992
    }
  ],
  "exposures": [
    {
      "session": "2016-10-26",
      "concentration_hhi": 0.9592527099734108,
      "cash_weight": 0.020585526973686787
    },
    {
      "session": "2016-10-27",
      "concentration_hhi": 0.9590077925982898,
      "cash_weight": 0.0207105675040244
    },
    {
      "session": "2016-10-28",
      "concentration_hhi": 0.9585191969878426,
      "cash_weight": 0.020960063639974623
    },
    {
      "session": "2016-10-31",
      "concentration_hhi": 0.9584070308292575,
      "cash_weight": 0.021017349066257723
    },
    {
      "session": "2016-11-01",
      "concentration_hhi": 0.958599380888105,
      "cash_weight": 0.020919114225946646
    },
    {
      "session": "2016-11-02",
      "concentration_hhi": 0.9580605906588173,
      "cash_weight": 0.02119430393013272
    },
    {
      "session": "2016-11-03",
      "concentration_hhi": 0.9579170426853119,
      "cash_weight": 0.021267634802387927
    },
    {
      "session": "2016-11-04",
      "concentration_hhi": 0.9578253551250973,
      "cash_weight": 0.021314475878437586
    },
    {
      "session": "2016-11-07",
      "concentration_hhi": 0.9577347035357264,
      "cash_weight": 0.02136078990481563
    },
    {
      "session": "2016-11-08",
      "concentration_hhi": 0.9579024817236119,
      "cash_weight": 0.02127507351472243
    },
    {
      "session": "2016-11-09",
      "concentration_hhi": 0.9581709683514795,
      "cash_weight": 0.02113792169096695
    },
    {
      "session": "2016-11-10",
      "concentration_hhi": 0.9588359802886166,
      "cash_weight": 0.02079829438025563
    },
    {
      "session": "2016-11-11",
      "concentration_hhi": 0.9586675843913404,
      "cash_weight": 0.020884284473310925
    },
    {
      "session": "2016-11-14",
      "concentration_hhi": 0.9583001229709062,
      "cash_weight": 0.021071952097138996
    },
    {
      "session": "2016-11-15",
      "concentration_hhi": 0.9583379930077247,
      "cash_weight": 0.021052609683377962
    },
    {
      "session": "2016-11-16",
      "concentration_hhi": 0.9585501285270721,
      "cash_weight": 0.020944266894334453
    },
    {
      "session": "2016-11-17",
      "concentration_hhi": 0.958694133508038,
      "cash_weight": 0.02087072686593731
    },
    {
      "session": "2016-11-18",
      "concentration_hhi": 0.9583642851544962,
      "cash_weight": 0.02103918099114091
    },
    {
      "session": "2016-11-21",
      "concentration_hhi": 0.9581876624028518,
      "cash_weight": 0.021129394453561164
    },
    {
      "session": "2016-11-22",
      "concentration_hhi": 0.958173452866285,
      "cash_weight": 0.021136652608605925
    },
    {
      "session": "2016-11-23",
      "concentration_hhi": 0.9590886076781064,
      "cash_weight": 0.02066930627182603
    },
    {
      "session": "2017-01-27",
      "concentration_hhi": 0.9563039263633337,
      "cash_weight": 0.02209206651989286
    },
    {
      "session": "2017-01-30",
      "concentration_hhi": 0.9561500322191933,
      "cash_weight": 0.02217075508083049
    },
    {
      "session": "2017-01-31",
      "concentration_hhi": 0.9562369699815129,
      "cash_weight": 0.02212630162095431
    },
    {
      "session": "2017-02-01",
      "concentration_hhi": 0.9562624604592831,
      "cash_weight": 0.022113268083014007
    },
    {
      "session": "2017-02-02",
      "concentration_hhi": 0.9571946512448569,
      "cash_weight": 0.02163674882748339
    },
    {
      "session": "2017-02-03",
      "concentration_hhi": 0.9577992688102901,
      "cash_weight": 0.021327803189295662
    },
    {
      "session": "2017-02-06",
      "concentration_hhi": 0.9577766226519502,
      "cash_weight": 0.021339373096092046
    },
    {
      "session": "2017-02-07",
      "concentration_hhi": 0.9575331370356204,
      "cash_weight": 0.021463778373217154
    },
    {
      "session": "2017-02-08",
      "concentration_hhi": 0.9571372429832842,
      "cash_weight": 0.02166608819724323
    },
    {
      "session": "2017-02-09",
      "concentration_hhi": 0.9577382542323,
      "cash_weight": 0.02135897580762537
    },
    {
      "session": "2017-02-10",
      "concentration_hhi": 0.9580314154323281,
      "cash_weight": 0.021209207525771597
    },
    {
      "session": "2017-02-13",
      "concentration_hhi": 0.9582731441524456,
      "cash_weight": 0.021085731970135444
    },
    {
      "session": "2017-02-14",
      "concentration_hhi": 0.9576546251454017,
      "cash_weight": 0.021401703892040456
    },
    {
      "session": "2017-02-15",
      "concentration_hhi": 0.9579374308153629,
      "cash_weight": 0.021257219278035845
    },
    {
      "session": "2017-02-16",
      "concentration_hhi": 0.9579582008698525,
      "cash_weight": 0.021246608756908262
    },
    {
      "session": "2017-02-17",
      "concentration_hhi": 0.9574477268506827,
      "cash_weight": 0.021507421157072444
    },
    {
      "session": "2017-02-21",
      "concentration_hhi": 0.9572298652220422,
      "cash_weight": 0.021618752621432175
    },
    {
      "session": "2017-02-22",
      "concentration_hhi": 0.9570026388210308,
      "cash_weight": 0.02173488316252899
    },
    {
      "session": "2017-02-23",
      "concentration_hhi": 0.9569719658857746,
      "cash_weight": 0.02175056049810353
    },
    {
      "session": "2017-02-24",
      "concentration_hhi": 0.9568834102909509,
      "cash_weight": 0.02179582382257692
    },
    {
      "session": "2017-02-27",
      "concentration_hhi": 0.9567899202635969,
      "cash_weight": 0.02184361155099696
    },
    {
      "session": "2017-02-28",
      "concentration_hhi": 0.958478211031355,
      "cash_weight": 0.020980995571916843
    },
    {
      "session": "2017-03-01",
      "concentration_hhi": 0.9585539617518863,
      "cash_weight": 0.02094230928311153
    },
    {
      "session": "2017-03-02",
      "concentration_hhi": 0.9593960051443164,
      "cash_weight": 0.020512376216873063
    },
    {
      "session": "2017-03-03",
      "concentration_hhi": 0.9585919538593274,
      "cash_weight": 0.020922907090903522
    },
    {
      "session": "2017-03-06",
      "concentration_hhi": 0.9585943372219174,
      "cash_weight": 0.020921689944099736
    },
    {
      "session": "2017-03-07",
      "concentration_hhi": 0.9587155065397649,
      "cash_weight": 0.02085981262141789
    },
    {
      "session": "2017-03-08",
      "concentration_hhi": 0.9587242395119808,
      "cash_weight": 0.020855353120908405
    },
    {
      "session": "2017-03-09",
      "concentration_hhi": 0.958589505373527,
      "cash_weight": 0.02092415749671
    },
    {
      "session": "2017-03-10",
      "concentration_hhi": 0.9579955225884677,
      "cash_weight": 0.021227542996602383
    },
    {
      "session": "2017-03-13",
      "concentration_hhi": 0.9581810475169503,
      "cash_weight": 0.021132773295095702
    },
    {
      "session": "2017-03-14",
      "concentration_hhi": 0.9591135845021211,
      "cash_weight": 0.020656554368120954
    },
    {
      "session": "2017-03-15",
      "concentration_hhi": 0.9587842651240324,
      "cash_weight": 0.020824701534994543
    },
    {
      "session": "2017-03-16",
      "concentration_hhi": 0.9590322633940469,
      "cash_weight": 0.020698073424724118
    },
    {
      "session": "2017-03-17",
      "concentration_hhi": 0.9588145478219118,
      "cash_weight": 0.020809238288109724
    },
    {
      "session": "2017-03-20",
      "concentration_hhi": 0.9588451780902899,
      "cash_weight": 0.020793597809792654
    },
    {
      "session": "2017-03-21",
      "concentration_hhi": 0.9584003609075246,
      "cash_weight": 0.021020755629862928
    },
    {
      "session": "2017-03-22",
      "concentration_hhi": 0.9581564305261595,
      "cash_weight": 0.02114534759947151
    },
    {
      "session": "2017-03-23",
      "concentration_hhi": 0.9584283391540437,
      "cash_weight": 0.02100646623481539
    },
    {
      "session": "2017-03-24",
      "concentration_hhi": 0.9586901364933964,
      "cash_weight": 0.020872767974765952
    },
    {
      "session": "2017-03-27",
      "concentration_hhi": 0.9592606747108887,
      "cash_weight": 0.02058146091117469
    },
    {
      "session": "2017-03-28",
      "concentration_hhi": 0.9594376597962252,
      "cash_weight": 0.02049111295699551
    },
    {
      "session": "2017-03-29",
      "concentration_hhi": 0.9596283404289664,
      "cash_weight": 0.020393782977585165
    },
    {
      "session": "2017-03-30",
      "concentration_hhi": 0.9603647075700344,
      "cash_weight": 0.020018006507244786
    },
    {
      "session": "2017-03-31",
      "concentration_hhi": 0.9605259483629253,
      "cash_weight": 0.019935742737791005
    },
    {
      "session": "2017-04-03",
      "concentration_hhi": 0.9609823003236354,
      "cash_weight": 0.019702953016976853
    },
    {
      "session": "2017-04-04",
      "concentration_hhi": 0.9608054158821511,
      "cash_weight": 0.01979317698653455
    },
    {
      "session": "2017-04-05",
      "concentration_hhi": 0.9607934087188342,
      "cash_weight": 0.01979930181679914
    },
    {
      "session": "2017-04-06",
      "concentration_hhi": 0.9607892894684374,
      "cash_weight": 0.01980140304709804
    },
    {
      "session": "2017-04-07",
      "concentration_hhi": 0.9609450334006453,
      "cash_weight": 0.019721961175990968
    },
    {
      "session": "2017-04-10",
      "concentration_hhi": 0.9602029305929989,
      "cash_weight": 0.020100550774213903
    },
    {
      "session": "2017-04-11",
      "concentration_hhi": 0.9602959449014588,
      "cash_weight": 0.020053090774067098
    },
    {
      "session": "2017-04-12",
      "concentration_hhi": 0.9601971877865286,
      "cash_weight": 0.02010348108255399
    },
    {
      "session": "2017-04-13",
      "concentration_hhi": 0.9606154161654125,
      "cash_weight": 0.019890099955411886
    },
    {
      "session": "2017-04-17",
      "concentration_hhi": 0.9607893568458428,
      "cash_weight": 0.01980136867783638
    },
    {
      "session": "2017-04-18",
      "concentration_hhi": 0.9615290897636238,
      "cash_weight": 0.01942410300700134
    },
    {
      "session": "2017-04-19",
      "concentration_hhi": 0.9615105603966925,
      "cash_weight": 0.01943355125892022
    },
    {
      "session": "2017-04-20",
      "concentration_hhi": 0.9609475051649007,
      "cash_weight": 0.01972070043028006
    },
    {
      "session": "2017-04-21",
      "concentration_hhi": 0.961023946480166,
      "cash_weight": 0.019681711646586702
    },
    {
      "session": "2017-04-24",
      "concentration_hhi": 0.9604615400837673,
      "cash_weight": 0.01996860250103857
    },
    {
      "session": "2017-04-25",
      "concentration_hhi": 0.9603519326083094,
      "cash_weight": 0.02002452448629637
    },
    {
      "session": "2017-04-26",
      "concentration_hhi": 0.960822392874689,
      "cash_weight": 0.019784517121521402
    },
    {
      "session": "2017-04-27",
      "concentration_hhi": 0.9609875202820256,
      "cash_weight": 0.019700290583524793
    },
    {
      "session": "2017-04-28",
      "concentration_hhi": 0.9586895700562861,
      "cash_weight": 0.020873057230940118
    },
    {
      "session": "2017-05-01",
      "concentration_hhi": 0.9586677138067119,
      "cash_weight": 0.02088421838542927
    },
    {
      "session": "2017-05-02",
      "concentration_hhi": 0.958922096895485,
      "cash_weight": 0.020754322503548236
    },
    {
      "session": "2017-05-03",
      "concentration_hhi": 0.9584996595808966,
      "cash_weight": 0.020970041530446133
    },
    {
      "session": "2017-05-04",
      "concentration_hhi": 0.9585705984454521,
      "cash_weight": 0.020933813041502266
    },
    {
      "session": "2017-05-05",
      "concentration_hhi": 0.9585645845518679,
      "cash_weight": 0.020936884285866004
    },
    {
      "session": "2017-05-08",
      "concentration_hhi": 0.9592170129243519,
      "cash_weight": 0.020603750811576865
    },
    {
      "session": "2017-05-09",
      "concentration_hhi": 0.9595368699771816,
      "cash_weight": 0.0204404714479158
    },
    {
      "session": "2017-05-10",
      "concentration_hhi": 0.9587225870323373,
      "cash_weight": 0.02085619695964106
    },
    {
      "session": "2017-05-11",
      "concentration_hhi": 0.9587865119190423,
      "cash_weight": 0.020823554246201196
    },
    {
      "session": "2017-05-12",
      "concentration_hhi": 0.9589851222285982,
      "cash_weight": 0.020722142480185533
    },
    {
      "session": "2017-05-15",
      "concentration_hhi": 0.9592309057462965,
      "cash_weight": 0.02059665829327681
    },
    {
      "session": "2017-05-16",
      "concentration_hhi": 0.9596975350375595,
      "cash_weight": 0.0203584660511992
    },
    {
      "session": "2017-05-17",
      "concentration_hhi": 0.9591878158142424,
      "cash_weight": 0.020618656592723193
    },
    {
      "session": "2017-05-18",
      "concentration_hhi": 0.9589320680671558,
      "cash_weight": 0.020749231265476304
    },
    {
      "session": "2017-05-19",
      "concentration_hhi": 0.9591457590534239,
      "cash_weight": 0.02064012791342944
    },
    {
      "session": "2017-05-22",
      "concentration_hhi": 0.9587440487708966,
      "cash_weight": 0.02084523757942314
    },
    {
      "session": "2017-05-23",
      "concentration_hhi": 0.9593646156738678,
      "cash_weight": 0.02052839976144911
    },
    {
      "session": "2017-05-24",
      "concentration_hhi": 0.9594480865156882,
      "cash_weight": 0.02048579054937237
    },
    {
      "session": "2017-05-25",
      "concentration_hhi": 0.9596849398460918,
      "cash_weight": 0.02036489454180355
    },
    {
      "session": "2017-05-26",
      "concentration_hhi": 0.9595937540032619,
      "cash_weight": 0.020411436365623082
    },
    {
      "session": "2017-05-30",
      "concentration_hhi": 0.9598685566866012,
      "cash_weight": 0.02027118206791478
    },
    {
      "session": "2017-05-31",
      "concentration_hhi": 0.9601454083379812,
      "cash_weight": 0.020129902314607265
    },
    {
      "session": "2017-06-01",
      "concentration_hhi": 0.9603795879358749,
      "cash_weight": 0.020010414373767584
    },
    {
      "session": "2017-06-02",
      "concentration_hhi": 0.9603771841498511,
      "cash_weight": 0.020011640809008878
    },
    {
      "session": "2017-06-05",
      "concentration_hhi": 0.9604207448595935,
      "cash_weight": 0.019989415945116818
    },
    {
      "session": "2017-06-06",
      "concentration_hhi": 0.9601078244306688,
      "cash_weight": 0.02014908050731069
    },
    {
      "session": "2017-06-07",
      "concentration_hhi": 0.9600155488184512,
      "cash_weight": 0.0201961681956683
    },
    {
      "session": "2017-06-08",
      "concentration_hhi": 0.9599359462717981,
      "cash_weight": 0.020236790713287732
    },
    {
      "session": "2017-06-09",
      "concentration_hhi": 0.960056581365141,
      "cash_weight": 0.020175229255179113
    },
    {
      "session": "2017-06-12",
      "concentration_hhi": 0.9602044218621153,
      "cash_weight": 0.020099789844845947
    },
    {
      "session": "2017-06-13",
      "concentration_hhi": 0.9597706564366012,
      "cash_weight": 0.020321146274657528
    },
    {
      "session": "2017-06-14",
      "concentration_hhi": 0.9595621665126123,
      "cash_weight": 0.020427559333863192
    },
    {
      "session": "2017-06-15",
      "concentration_hhi": 0.9600313624490622,
      "cash_weight": 0.020188098434673056
    },
    {
      "session": "2017-06-16",
      "concentration_hhi": 0.9598755295314652,
      "cash_weight": 0.020267623515755652
    },
    {
      "session": "2017-06-19",
      "concentration_hhi": 0.959468284869757,
      "cash_weight": 0.020475480210037363
    },
    {
      "session": "2017-06-20",
      "concentration_hhi": 0.9596059512280738,
      "cash_weight": 0.020405210697773415
    },
    {
      "session": "2017-06-21",
      "concentration_hhi": 0.9598579895433983,
      "cash_weight": 0.02027657497465227
    },
    {
      "session": "2017-06-22",
      "concentration_hhi": 0.9595624061164392,
      "cash_weight": 0.020427437033662604
    },
    {
      "session": "2017-06-23",
      "concentration_hhi": 0.959762457299736,
      "cash_weight": 0.020325330887985056
    },
    {
      "session": "2017-06-26",
      "concentration_hhi": 0.9599822010405551,
      "cash_weight": 0.020213185922287026
    },
    {
      "session": "2017-06-27",
      "concentration_hhi": 0.9603174169093731,
      "cash_weight": 0.0200421351357126
    },
    {
      "session": "2017-06-28",
      "concentration_hhi": 0.9603867464413431,
      "cash_weight": 0.020006762043052097
    },
    {
      "session": "2017-06-29",
      "concentration_hhi": 0.9611754676458788,
      "cash_weight": 0.019604433075159845
    },
    {
      "session": "2017-06-30",
      "concentration_hhi": 0.9611684287414887,
      "cash_weight": 0.019608022910484798
    },
    {
      "session": "2017-07-03",
      "concentration_hhi": 0.960491995015756,
      "cash_weight": 0.01995306489140229
    },
    {
      "session": "2017-07-05",
      "concentration_hhi": 0.9608309515062053,
      "cash_weight": 0.019780151442440302
    },
    {
      "session": "2017-07-06",
      "concentration_hhi": 0.9606298453580056,
      "cash_weight": 0.01988273897558283
    },
    {
      "session": "2017-07-07",
      "concentration_hhi": 0.9603831907356153,
      "cash_weight": 0.020008576192824402
    },
    {
      "session": "2017-07-10",
      "concentration_hhi": 0.9609681982540731,
      "cash_weight": 0.01971014579662558
    },
    {
      "session": "2017-07-11",
      "concentration_hhi": 0.960561141425065,
      "cash_weight": 0.019917788435549238
    },
    {
      "session": "2017-07-12",
      "concentration_hhi": 0.960034885054707,
      "cash_weight": 0.02018630084351913
    },
    {
      "session": "2017-07-13",
      "concentration_hhi": 0.9591790399606799,
      "cash_weight": 0.020623136907615202
    },
    {
      "session": "2017-07-14",
      "concentration_hhi": 0.9585152384792947,
      "cash_weight": 0.020962085269781557
    },
    {
      "session": "2017-07-17",
      "concentration_hhi": 0.9586613886949177,
      "cash_weight": 0.020887448402933887
    },
    {
      "session": "2017-07-18",
      "concentration_hhi": 0.9587587323158177,
      "cash_weight": 0.020837739536588597
    },
    {
      "session": "2017-07-19",
      "concentration_hhi": 0.9587102939273894,
      "cash_weight": 0.020862474456530063
    },
    {
      "session": "2017-07-20",
      "concentration_hhi": 0.9582013840426258,
      "cash_weight": 0.021122385564658272
    },
    {
      "session": "2017-07-21",
      "concentration_hhi": 0.9572650143538588,
      "cash_weight": 0.021600789884896384
    },
    {
      "session": "2017-07-24",
      "concentration_hhi": 0.9574648157155917,
      "cash_weight": 0.02149868895560925
    },
    {
      "session": "2017-07-25",
      "concentration_hhi": 0.9572447431427533,
      "cash_weight": 0.021611149316002668
    },
    {
      "session": "2017-07-26",
      "concentration_hhi": 0.9574512575706338,
      "cash_weight": 0.021505616995869725
    },
    {
      "session": "2017-07-27",
      "concentration_hhi": 0.9576943360602076,
      "cash_weight": 0.021381414411003774
    },
    {
      "session": "2017-12-27",
      "concentration_hhi": 0.9597613539397984,
      "cash_weight": 0.0203258940138316
    },
    {
      "session": "2017-12-28",
      "concentration_hhi": 0.9601310586051984,
      "cash_weight": 0.020137224604792676
    },
    {
      "session": "2017-12-29",
      "concentration_hhi": 0.9599092664727881,
      "cash_weight": 0.020250406240049527
    },
    {
      "session": "2018-01-02",
      "concentration_hhi": 0.9592980353035272,
      "cash_weight": 0.020562388253581927
    }
  ],
  "benchmark_status": "COMPARABLE_SIMULATED_RETURNS",
  "attribution": {
    "fees_usd": 491.43507735848664,
    "slippage_usd": 245.6884056921146,
    "spread_usd": 49.13768113842292,
    "asset_pnl": null,
    "cash_interest": null
  },
  "warnings": [
    "DAILY_OPEN_FILL_APPROXIMATION_NO_AUCTION_OR_ORDER_BOOK_DATA",
    "SAME_DAY_VOLUME_IS_EX_POST_CAPACITY_CAP_NOT_OPEN_KNOWN_LIQUIDITY",
    "GROSS_WEIGHT_DRIFT_BETWEEN_REBALANCES",
    "Trade statistics requiring matched closed lots are unavailable; fill_count counts execution records and trade_count is null.",
    "Cost drag is explicit simulated costs divided by initial capital, not a counterfactual return difference.",
    "Regression alpha is descriptive association, not causal attribution or demonstrated alpha."
  ],
  "conventions": {
    "periods_per_year": 252,
    "frequency": "DAILY_EXCHANGE_SESSION",
    "risk_free_annual": 0,
    "cagr": "geometric trading-period annualization",
    "return_basis": "RAW_WITH_CASH_ACTIONS",
    "alpha": "OLS arithmetic daily intercept times annual periods; risk free zero",
    "sample_start": "2016-04-28",
    "sample_end": "2018-01-02",
    "acceptance": "FIXTURE"
  }
}

## Transaction Costs

{
  "fees": 491.43507735848664,
  "slippage_cost": 245.6884056921146,
  "spread_cost": 49.13768113842292,
  "turnover": 4.892680250637732
}

## Robustness

Run the cost and parameter cases separately; no best-result selection or automatic promotion.

## Out-of-Sample Validation

EXPLORATORY; declared dates are not a certification of an untouched holdout. {}

## Comparison to Benchmarks

SPY; comparison status: COMPARABLE_SIMULATED_RETURNS; compare only when compatible; no fabricated risk-free series.

## Counterarguments and Limitations

DAILY_OPEN_FILL_APPROXIMATION_NO_AUCTION_OR_ORDER_BOOK_DATA
SAME_DAY_VOLUME_IS_EX_POST_CAPACITY_CAP_NOT_OPEN_KNOWN_LIQUIDITY
GROSS_WEIGHT_DRIFT_BETWEEN_REBALANCES
Trade statistics requiring matched closed lots are unavailable; fill_count counts execution records and trade_count is null.
Cost drag is explicit simulated costs divided by initial capital, not a counterfactual return difference.
Regression alpha is descriptive association, not causal attribution or demonstrated alpha.
No demonstrated alpha; fixed historical rules are research diagnostics
Daily bars cannot establish executable opening-auction liquidity
Holdout labels describe declared dates, not independent prospective validation
Source files must be frozen and the service restarted before acceptance; a disk hash cannot certify stale in-memory modules

## Further Research

Acquire independently reviewed PIT/corporate-action/delisting data; freeze hypothesis before a new holdout.