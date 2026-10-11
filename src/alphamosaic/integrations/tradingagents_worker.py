"""JSON-only isolated bridge for the official TradingAgents Python API."""

import contextlib
import importlib
import io
import json
import sys
from pathlib import Path


def main() -> None:
    request = json.load(sys.stdin)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            config_module = importlib.import_module("tradingagents.default_config")
            graph_module = importlib.import_module("tradingagents.graph.trading_graph")
            config = config_module.DEFAULT_CONFIG.copy()
            requested = request.get("config", {})
            applied: dict[str, object] = {}
            for key, value in requested.items():
                if key in config:
                    config[key] = value
                    applied[key] = value
            for key in ("results_dir", "data_cache_dir", "memory_log_path"):
                value = config.get(key)
                if value:
                    Path(value).parent.mkdir(parents=True, exist_ok=True)
            config["checkpoint_enabled"] = False
            graph = graph_module.TradingAgentsGraph(debug=False, config=config)
            _, decision = graph.propagate(request["symbol"], request["date"])
        structured = decision if isinstance(decision, dict) else None
        print(json.dumps({"status": "OK", "decision": structured,
                          "diagnostics": [] if structured else ["unstructured upstream decision"],
                          "execution": {"upstream_version": request.get("upstream_version"), "applied_config": applied}}))
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": f"{type(exc).__name__}: {str(exc)[:800]}"}))


if __name__ == "__main__":
    main()
