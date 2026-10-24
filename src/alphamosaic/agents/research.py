"""Deterministic independent checklist. No model-generated financial observations."""

from typing import Any, Protocol


class ModelAdapter(Protocol):
    def explain(self, evidence: dict[str, Any]) -> str: ...


def critique(experiment: dict[str, Any]) -> dict[str, Any]:
    config = experiment["config"]
    result = experiment.get("result", {})
    flags = list(experiment.get("warnings", []))
    if result.get("acceptance") == "FIXTURE":
        flags.append("SYNTHETIC_ONLY_NO_MARKET_INFERENCE")
    if not any(config["replay"].get(k, 0) for k in ("fee_bps", "slippage_bps", "spread_bps")):
        flags.append("ZERO_COST_CONTROL_NOT_PRIMARY_EVIDENCE")
    if config["validation"] != "PREDECLARED_HOLDOUT":
        flags.append("NO_HELD_OUT_EVALUATION")
    if config["replay"]["max_volume_fraction"] > 0.05:
        flags.append("HIGH_ASSUMED_PARTICIPATION")
    return {"kind": "DETERMINISTIC_CRITIC", "model_used": False,
        "Evidence": {"experiment_id": experiment["experiment_id"], "dataset_hash": experiment.get("dataset_hash"), "fill_count": len(result.get("fills", []))},
        "Inference": "This run checks declared assumptions; it does not establish investment merit.",
        "Hypothesis": config["question"], "Uncertainty": list(dict.fromkeys(flags)),
        "Actionable Research Question": "Would the unchanged rule survive a separately acquired licensed dataset and higher costs?",
        "evidence_grade": "Exploratory", "automatic_promotion": False}
