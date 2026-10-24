"""Run from a clean base-wheel interpreter outside the source checkout."""

import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import alphamosaic
from alphamosaic.core.service import ApplicationService


def verify() -> dict:
    package = Path(alphamosaic.__file__).resolve()
    if not package.is_relative_to(Path(sys.prefix).resolve()):
        raise AssertionError("wheel smoke imported source outside the clean environment")
    optional = {}
    for name in ("openbb-core", "quantstats", "streamlit", "plotly"):
        try:
            optional[name] = version(name)
        except PackageNotFoundError:
            optional[name] = "NOT_INSTALLED"
    if set(optional.values()) != {"NOT_INSTALLED"}:
        raise AssertionError("base wheel smoke requires optional dependencies absent")
    service = ApplicationService(Path("wheel-research"))
    manifest = service.research_demo(100)
    result = service.research_experiment({"dataset_id": manifest["dataset_id"], "strategy": "buy_and_hold"})
    if result["status"] != "COMPLETED" or result["acceptance"] != "FIXTURE":
        raise AssertionError("base wheel offline experiment failed: " + str(result.get("error")))
    if service.status()["broker_enabled"] is not False:
        raise AssertionError("research boundary failed")
    return {"status": "PASSED", "package_path": str(package), "python": sys.version.split()[0], "optional": optional, "experiment_id": result["experiment_id"], "acceptance": result["acceptance"], "broker_enabled": False}


if __name__ == "__main__":
    print(json.dumps(verify()))
