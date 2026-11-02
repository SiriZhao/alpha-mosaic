"""Small offline profiling baseline; no machine-independent speed claim."""

import argparse
import cProfile
import json
import pstats
import time
from pathlib import Path
from uuid import uuid4

from alphamosaic.backtesting.models import ReplayConfig
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.data.datasets import synthetic_demo


def benchmark(sessions: int = 126) -> dict:
    data = synthetic_demo(sessions)
    config = ReplayConfig()
    started = time.perf_counter()
    engine = PaperReplayEngine()
    first = engine.run(data, StrategyRegistry().get("equal_weight"), "equal_weight", config)
    elapsed = time.perf_counter() - started
    second = engine.run(data, StrategyRegistry().get("equal_weight"), "equal_weight", config)
    if first != second:
        raise AssertionError("determinism regression")
    return {"status": "PASSED", "sessions": sessions, "assets": 3, "data_quality": "FIXTURE", "first_replay_seconds": elapsed, "fills": len(first.fills), "exact_repeat": True, "optimization": "BASELINE_ONLY_NO_SPEEDUP_CLAIM"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=126)
    parser.add_argument("--output", type=Path, default=Path("runtime/performance"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    key = uuid4().hex
    profiler = cProfile.Profile()
    result = profiler.runcall(benchmark, args.sessions)
    with (args.output / (key + ".txt")).open("x") as stream:
        pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(20)
    (args.output / (key + ".json")).write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
