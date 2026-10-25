"""Predeclared folds, ablations and cost sensitivity, with no strategy promotion."""

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset, ReplayResult
from alphamosaic.backtesting.replay import PaperReplayEngine, validate_dataset
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import HistoricalBar
from alphamosaic.evaluation.quantstats_adapter import QuantStatsAdapter


def returns_of(result: ReplayResult) -> pd.Series:
    nav = pd.Series([result.config.initial_cash, *[p.nav for p in result.equity]], dtype=float)
    return pd.Series(
        nav.pct_change().iloc[1:].to_numpy(),
        index=pd.to_datetime([p.session for p in result.equity]),
    )


def summarize(
    result: ReplayResult, benchmarks: dict[str, list[HistoricalBar]], seed: int = 42
) -> dict[str, Any]:
    returns = returns_of(result)
    adapter = QuantStatsAdapter()
    metrics = adapter.metrics(returns)
    comparisons: dict[str, dict[str, float | None]] = {}
    comparisons_status: dict[str, str] = {}
    uncertainty: dict[str, Any] = {}
    for symbol, bars in benchmarks.items():
        if not bars or len({b.session for b in bars}) != len(bars):
            comparisons_status[symbol] = "BLOCKED_MISSING_OR_DUPLICATE_HISTORY"
            continue
        prices = pd.Series(
            [b.close for b in bars], index=pd.to_datetime([b.session for b in bars]), dtype=float
        )
        reference = prices.pct_change().reindex(returns.index)
        if returns.index[0] == prices.index[0]:
            reference.iloc[0] = bars[0].close / bars[0].open - 1
        if reference.isna().any():
            comparisons_status[symbol] = "BLOCKED_UNALIGNED_HISTORY"
            continue
        values = adapter.metrics(reference)
        excess = returns - reference
        std = float(excess.std(ddof=1))
        values["information_ratio"] = float(excess.mean() / std * np.sqrt(252)) if std > 0 else None
        values["excess_return"] = float(metrics["return"] or 0) - float(values["return"] or 0)
        comparisons[symbol] = values
        comparisons_status[symbol] = "PRICE_RETURN_DIAGNOSTIC_NOT_TOTAL_RETURN"
        if len(excess) >= 20:
            rng = np.random.default_rng(seed)
            x = excess.to_numpy()
            blocks = 5
            samples = []
            for _ in range(500):
                starts = rng.integers(0, len(x), size=(len(x) + blocks - 1) // blocks)
                draws = np.concatenate(
                    [x[(start + np.arange(blocks)) % len(x)] for start in starts]
                )[: len(x)]
                samples.append(float(draws.mean()))
            uncertainty[symbol] = {
                "mean_daily_excess_95pct_block_bootstrap": [
                    float(v) for v in np.quantile(samples, [0.025, 0.975])
                ],
                "seed": seed,
                "block_sessions": blocks,
                "resamples": 500,
                "interpretation": "Historical uncertainty diagnostic, no return probability",
            }
    return {
        "metrics": metrics,
        "benchmarks": comparisons,
        "benchmark_status": comparisons_status,
        "uncertainty": uncertainty,
        "observations": len(returns),
        "fill_count": len(result.fills),
        "turnover": result.turnover,
        "fees_usd": result.fees,
        "slippage_cost_usd": result.slippage_cost,
        "net_return_after_costs": metrics["return"],
    }


def walk_forward(
    data: ReplayDataset,
    config: ReplayConfig,
    strategy: str = "momentum",
    train_sessions: int = 126,
    test_sessions: int = 63,
) -> dict[str, Any]:
    validate_dataset(data)
    if train_sessions < config.lookback + 1 or test_sessions < 10:
        raise ValueError("train must cover lookback; test >=10 sessions")
    sessions = [b.session for b in next(iter(data.bars.values()))]
    if len(sessions) < train_sessions + test_sessions:
        return {"status": "BLOCKED", "reason": "INSUFFICIENT_OOS_SAMPLE", "folds": []}
    folds = []
    pooled: list[float] = []
    dates: list[date] = []
    for index in range(train_sessions, len(sessions) - test_sessions + 1, test_sessions):
        # Fixed predeclared signal. Training is warmup only; no optimization on holdout.
        fold_data = data.model_copy(
            update={
                "bars": {
                    s: b[index - train_sessions : index + test_sessions]
                    for s, b in data.bars.items()
                },
                "actions": [
                    a
                    for a in data.actions
                    if sessions[index - train_sessions]
                    <= a.effective_date
                    <= sessions[index + test_sessions - 1]
                ],
            }
        )
        result = PaperReplayEngine().run(
            fold_data,
            StrategyRegistry().get(strategy),
            strategy,
            config,
            start=sessions[index],
            end=sessions[index + test_sessions - 1],
        )
        returns = returns_of(result)
        pooled.extend(returns.to_list())
        dates.extend([p.session for p in result.equity])
        folds.append(
            {
                "train_start": str(sessions[index - train_sessions]),
                "train_end": str(sessions[index - 1]),
                "test_start": str(sessions[index]),
                "test_end": str(sessions[index + test_sessions - 1]),
                "metrics": QuantStatsAdapter().metrics(returns),
                "observations": len(returns),
                "fills": len(result.fills),
            }
        )
    return {
        "status": "COMPUTED",
        "folds": folds,
        "observations": len(pooled),
        "pooled_metrics": QuantStatsAdapter().metrics(
            pd.Series(pooled, index=pd.to_datetime(dates))
        ),
        "limitations": [
            "Each fold starts fresh cash; pooled returns describe reset fold experiments",
            "Predeclared parameters, no best strategy chosen",
            "Historical OOS is not forward performance",
        ],
    }


def regime_analysis(result: ReplayResult, benchmark: list[HistoricalBar]) -> dict[str, Any]:
    if len(benchmark) < 61:
        return {"status": "BLOCKED", "reason": "MISSING_BENCHMARK_REGIME_HISTORY"}
    series = pd.Series(
        [b.close for b in benchmark], index=pd.to_datetime([b.session for b in benchmark])
    )
    regime = (series > series.rolling(60).mean()).shift(1).reindex(returns_of(result).index)
    returns = returns_of(result)
    return {
        "definition": "Prior close vs prior SMA60; missing warmup excluded",
        "regimes": {
            label: {
                "observations": int(mask.sum()),
                "metrics": QuantStatsAdapter().metrics(pd.Series(returns.loc[mask]))
                if mask.sum() >= 2
                else None,
            }
            for label, mask in {"UPTREND": regime == True, "OTHER": regime == False}.items()  # noqa: E712
        },
    }


def experiment(
    data: ReplayDataset, benchmarks: dict[str, list[HistoricalBar]], config: ReplayConfig
) -> dict[str, Any]:
    registry, engine = StrategyRegistry(), PaperReplayEngine()
    config = ReplayConfig.model_validate(config.model_dump())
    daily_config = config.model_copy(update={"decision_frequency": "DAILY"})
    results: dict[str, Any] = {}
    replays: dict[str, ReplayResult] = {}
    requirements = {
        "quality": "quality",
        "value": "value",
        "ai_rating": "ai_rating",
        "signal_consensus": "consensus",
    }
    for item in registry.list():
        name = item["name"]
        required = requirements.get(name)
        if required and not any(
            s.metric == required
            and s.pit_verified
            and s.license_scope != "NOT_VERIFIED"
            and s.data_quality in {"REAL", "HISTORICAL", "FIXTURE"}
            for s in data.signals
        ):
            results[name] = {
                "status": "BLOCKED",
                "reason": "MISSING_LICENSED_VERIFIED_PIT_SIGNAL_SERIES",
            }
            continue
        strategy_config = config.model_copy(update={"decision_frequency": "WEEKLY" if name.startswith("weekly_") else "DAILY"})
        try:
            replay = engine.run(data, registry.get(name), name, strategy_config)
        except ValueError as exc:
            if not name.startswith("weekly_"):
                raise
            results[name] = {"status": "BLOCKED", "reason": str(exc), "decision_frequency": "WEEKLY"}
            continue
        replays[name] = replay
        results[name] = {
            "status": "COMPUTED",
            "acceptance": replay.acceptance,
            "decision_frequency": strategy_config.decision_frequency,
            **summarize(replay, benchmarks, config.seed),
        }
    momentum = replays["momentum"]
    sensitivity = []
    for slippage in (0, 5, 20):
        costs = ReplayConfig.model_validate({**daily_config.model_dump(), "slippage_bps": slippage})
        replay = engine.run(data, registry.get("momentum"), "momentum", costs)
        sensitivity.append({"slippage_bps": slippage, **summarize(replay, benchmarks, config.seed)})
    ablated = engine.run(data, registry.get("multi_factor", "trend"), "multi_factor", daily_config)
    summary = summarize(momentum, benchmarks, config.seed)
    equal_weight = engine.run(data, registry.get("buy_and_hold"), "buy_and_hold", daily_config)
    return {
        "status": "COMPUTED",
        "alpha_status": "INSUFFICIENT_EVIDENCE_NO_DEMONSTRATED_ALPHA",
        "engine": engine.name,
        "analytics": "QuantStats",
        "acceptance": momentum.acceptance,
        "strategies": results,
        "walk_forward": walk_forward(data, daily_config),
        "slippage_sensitivity": sensitivity,
        "ablation": {
            "removed_signal": "trend",
            "full": results["multi_factor"],
            "without_trend": summarize(ablated, benchmarks, config.seed),
        },
        "regimes": regime_analysis(momentum, benchmarks.get("SPY", [])),
        "survivorship": "VERIFIED"
        if data.historical_universe_verified
        else "NOT_VERIFIED_FIXED_CURRENT_UNIVERSE",
        "look_ahead": "STRICT_PIT_ENFORCED"
        if data.mode == "STRICT_PIT"
        else "CAUSAL_PRICE_CALCULATION_ONLY_REVISED_DATA_NOT_PIT",
        "overfitting": {
            "selection": "PREDECLARED_NO_OPTIMIZATION",
            "trials_reported": len(results),
            "correction": "NOT_ESTIMATED_NO_SIGNIFICANCE_CLAIM",
            "seed": config.seed,
        },
        "summary": summary,
        "replay": momentum.model_dump(mode="json"),
        "equal_weight_reference": summarize(equal_weight, benchmarks, config.seed),
        "limitations": momentum.diagnostics
        + [
            "Not real-account returns; no strategy automatically promoted",
            "No spread, borrow, impact, delisting or currency model beyond explicit daily assumptions",
        ],
    }
