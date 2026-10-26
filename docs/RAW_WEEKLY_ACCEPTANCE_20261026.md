# Explicit RAW weekly price-feature acceptance

Full Renaissance objective remains ACTIVE. This is research software qualification on generated FIXTURE inputs, not real-market/PIT acceptance or evidence of alpha.

The registered weekly equal-weight, momentum and trend rules can explicitly select `RAW_SPLIT_PRICE_ONLY_V1`. The default `LEGACY_REJECT_RAW_ACTIONS` refusal stays unchanged. Derived close(t) is raw close(t) divided by eligible subsequent split ratios through the last complete available week L. Shares are in L's units. A current partial-week or announced future action cannot change L. Dividend income is excluded from the price hypothesis; the independent ex-date receivable/pay-date cash model retains earned economic rights. No derived value becomes an observed quote, raw execution price or certified PIT series.

`DerivedWeeklyClose` carries a decision timestamp, unit anchor, parent evidence quality, bounded raw-row fingerprints and applied split identities. Every signal retains its inputs. Opt-in artifact schema4 additionally seals `weekly_price_features.csv`; missing or changed exports fail loading. Existing schema3/default and older missing-field records remain readable without rewrite. Passive benchmarks never claim consumption merely because their configuration names the policy. Reports, exported figures and the terminal distinguish price features from portfolio return accounting. The UI table displays dated split ratios and share anchors explicitly.

Final Windows source is `1824b28cee25aaa1a585553b3f6c030eaab244d579c27346b35a771da102afee` (62 Python files). Final full-suite/package evidence is collected in [the machine bundle](evidence/raw-weekly-20261026/acceptance.json); source-bound publication/hosted CI remains a separate gate until observed. Independent core review passed28 cases, integrated review30, and the final readable-table review12 with unchanged source fingerprints in each scope. These are separate scopes, not a claimed count of unique tests.

The actual service suite retains eight experiment records: expected default refusal plus seven completed cases covering momentum/trend/equal-weight, explicit zero/realistic/stress costs, exact repeat, and unpaid entitlement cutoff. All11 criteria must pass, including raw next-open execution, price/income separation, no passive feature consumption and frozen source. No failed experiment is removed. Zero cost is a control; no FIXTURE return is investment evidence.

```powershell
uv sync --locked --all-extras --dev
uv run python scripts/run_raw_weekly_cases.py --home runtime/my-weekly-research
# The command prints the unique child home and summary path.
$env:ALPHAMOSAIC_HOME = '<printed research_home>'
uv run python -m streamlit run src/alphamosaic/ui/app.py --theme.base dark
# Inspect Backtest Results → Signal price features, or Reports → CSV download.
# Re-run any retained experiment using its complete config.json:
uv run alphamosaic experiment '<research_home>/experiments/<experiment_id>/config.json'
```

Every script invocation creates a unique child home. Same-case financial equality excludes IDs, timestamps and runtime provenance; differing source/environment identities remain explicit. Windows and Git/Linux LF byte hashes may differ; no cross-platform exact financial equivalence or relaxed comparison gate is asserted.

Original negative evidence is retained: invalid initial AppTest selector, old positional JSON selector after a new tab, collapsed browser JSON locator, independent fixture-import ordering, sandbox named-pipe restriction and a pre-execution verifier path typo. Financial assertions were not weakened. The readable-table repair followed actual screenshot inspection. Broader data qualification, special/due-bill/cash-in-lieu/delisting economics, dividend-inclusive signal indices, broader benchmarks/portfolio/statistical controls and PDF/Parquet remain separate work.

Profiling observed the eight-case predecessor source (only the final table presentation differs) under concurrent local tests/build: provenance/import/report overhead dominated the small fixture;45 derived-feature calls totaled roughly0.241 instrumented seconds. This is no standalone latency or optimization claim. Larger-history scaling remains unmeasured. Current lightweight baseline retains exact-repeat verification and a measured time in the bundle; no acceleration dependency was introduced.
