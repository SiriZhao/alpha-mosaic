"""Fixed offline experiment worker; no shell, model call or market acquisition tool."""

import argparse
import json
from pathlib import Path

from alphamosaic.common.locking import ResearchBusyError
from alphamosaic.common.paths import unredirected
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import ExperimentConfig, canonical, source_manifest


def main(home: Path, request_path: Path) -> int:
    home = unredirected(home)
    request_path = unredirected(request_path)
    plans = home / "research_plans"
    if request_path.parent.parent != plans or request_path.is_symlink():
        raise ValueError("worker request must belong to the local plan store")
    request = json.loads(request_path.read_bytes())
    name = request["response"]
    if Path(name).name != name or not name.endswith("-response.json"):
        raise ValueError("invalid worker response name")
    response = request_path.parent / name
    try:
        if source_manifest()["source_hash"] != request["expected_source_hash"]:
            raise ValueError("worker source differs from the frozen plan")
        config = ExperimentConfig.model_validate(request["config"])
        context = config.research_context
        if context is None or request_path.parent.name != context.plan_id or request_path.name != context.attempt_id + "-request.json" or name != context.attempt_id + "-response.json":
            raise ValueError("worker request requires its exact frozen plan and attempt identity")
        service = ApplicationService(home)
        if service.experiment_runner().datasets.manifest(config.dataset_id)["dataset_hash"] != request["dataset_hash"]:
            raise ValueError("worker dataset differs from the frozen plan")
        result = service.research_experiment(config.model_dump(mode="json"))
        payload = {"status": result["status"], "experiment_id": result["experiment_id"], "source_hash": result.get("reproducibility", {}).get("source_hash"), "error": result.get("error")}
    except ResearchBusyError:
        payload = {"status": "BUSY", "error_type": "GLOBAL_RESEARCH_WORKER_LEASE_HELD"}
    except Exception as exc:
        payload = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)[:1000]}
    with response.open("xb") as stream:
        stream.write(canonical(payload))
    return 0 if payload["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.home, args.request))
