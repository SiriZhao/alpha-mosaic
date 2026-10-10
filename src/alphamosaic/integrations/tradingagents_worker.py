"""JSON-only isolated bridge for the official TradingAgents Python API."""

import contextlib
import importlib
import io
import json
import sys


def main() -> None:
    request = json.load(sys.stdin)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            config_module = importlib.import_module("tradingagents.default_config")
            graph_module = importlib.import_module("tradingagents.graph.trading_graph")
            config = config_module.DEFAULT_CONFIG.copy()
            graph = graph_module.TradingAgentsGraph(debug=False, config=config)
            _, decision = graph.propagate(request["symbol"], request["date"])
        print(json.dumps({"status": "OK", "decision": str(decision)[:4000]}))
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": f"{type(exc).__name__}: {str(exc)[:800]}"}))


if __name__ == "__main__":
    main()
