"""Small predeclared research controls; no automatic strategy promotion."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np


@dataclass(frozen=True)
class ChronologicalSplit:
    train: tuple[int, ...]
    validation: tuple[int, ...]
    holdout: tuple[int, ...]
    purged_or_embargoed: tuple[int, ...]


def chronological_split(
    count: int,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
    *,
    label_horizon_sessions: int = 0,
    embargo_sessions: int = 0,
) -> ChronologicalSplit:
    """Discard boundary labels reaching evaluation, plus an optional extra gap."""
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1 or train_fraction + validation_fraction >= 1:
        raise ValueError("positive train, validation and holdout fractions required")
    if count < 3 or label_horizon_sessions < 0 or embargo_sessions < 0:
        raise ValueError("at least three observations and nonnegative gaps required")
    train_end, validation_end = int(count * train_fraction), int(count * (train_fraction + validation_fraction))
    gap = label_horizon_sessions + embargo_sessions
    if train_end - gap < 1 or validation_end - train_end - gap < 1 or validation_end >= count:
        raise ValueError("insufficient observations after purging and embargo")
    return ChronologicalSplit(
        tuple(range(train_end - gap)),
        tuple(range(train_end, validation_end - gap)),
        tuple(range(validation_end, count)),
        tuple(range(train_end - gap, train_end)) + tuple(range(validation_end - gap, validation_end)),
    )


def walk_forward_folds(
    count: int,
    train_sessions: int = 126,
    test_sessions: int = 63,
    *,
    label_horizon_sessions: int = 0,
    embargo_sessions: int = 0,
    expanding: bool = False,
) -> list[dict[str, list[int]]]:
    """Non-overlapping test folds; training always precedes each evaluation gap."""
    if min(count, train_sessions, test_sessions) < 1 or min(label_horizon_sessions, embargo_sessions) < 0:
        raise ValueError("positive sizes and nonnegative gaps required")
    gap = label_horizon_sessions + embargo_sessions
    folds = []
    for start in range(train_sessions + gap, count - test_sessions + 1, test_sessions):
        end_train = start - gap
        begin_train = 0 if expanding else end_train - train_sessions
        folds.append({"train": list(range(begin_train, end_train)), "test": list(range(start, start + test_sessions)), "gap": list(range(end_train, start))})
    return folds


@dataclass(frozen=True)
class Standardizer:
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    training_indices: tuple[int, ...]

    def transform(self, values: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=float)
        if array.ndim != 2 or array.shape[1] != len(self.mean) or not np.isfinite(array).all():
            raise ValueError("finite two-dimensional features with fitted width required")
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            result = (array - self.mean) / self.scale
        if not np.isfinite(result).all():
            raise ValueError("non-finite standardized features")
        return result


def fit_standardizer(
    features: Sequence[Sequence[float]] | np.ndarray,
    split: ChronologicalSplit,
) -> Standardizer:
    """Only explicit training indices can influence fitted mean and scale."""
    array = np.asarray(features, dtype=float)
    all_indices = split.train + split.validation + split.holdout + split.purged_or_embargoed
    if array.ndim != 2 or not split.train or not np.isfinite(array).all():
        raise ValueError("finite feature matrix and nonempty training partition required")
    if sorted(all_indices) != list(range(len(array))) or len(set(all_indices)) != len(array):
        raise ValueError("split must partition the complete feature matrix exactly once")
    if max(split.train) >= min(split.validation) or max(split.validation) >= min(split.holdout):
        raise ValueError("chronological training, validation, holdout required")
    training = array[list(split.train)]
    with np.errstate(over="ignore", invalid="ignore"):
        mean = training.mean(axis=0)
        scale = training.std(axis=0, ddof=0)
    if not np.isfinite(mean).all() or not np.isfinite(scale).all():
        raise ValueError("non-finite fitted statistics from extreme feature magnitudes")
    scale[scale == 0] = 1
    return Standardizer(tuple(float(v) for v in mean), tuple(float(v) for v in scale), split.train)


def block_bootstrap_mean(
    values: Sequence[float] | np.ndarray,
    *,
    block_sessions: int = 5,
    resamples: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Circular fixed-block bootstrap of mean; stationary short-memory diagnostic."""
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or len(array) < 2 or not np.isfinite(array).all():
        raise ValueError("at least two finite observations required")
    if not 1 <= block_sessions <= len(array) or not 100 <= resamples <= 100_000:
        raise ValueError("valid block size and 100..100000 resamples required")
    rng = np.random.default_rng(seed)
    samples = np.empty(resamples)
    blocks = math.ceil(len(array) / block_sessions)
    with np.errstate(over="ignore", invalid="ignore"):
        mean = float(array.mean())
        for i in range(resamples):
            starts = rng.integers(0, len(array), size=blocks)
            indices = (starts[:, None] + np.arange(block_sessions)) % len(array)
            samples[i] = array[indices.ravel()[:len(array)]].mean()
    if not math.isfinite(mean) or not np.isfinite(samples).all():
        raise ValueError("non-finite bootstrap statistics from extreme magnitudes")
    return {
        "mean": mean,
        "mean_95pct_interval": [float(v) for v in np.quantile(samples, [0.025, 0.975])],
        "observations": len(array), "block_sessions": block_sessions, "resamples": resamples, "seed": seed,
        "method": "CIRCULAR_FIXED_BLOCK_PERCENTILE_BOOTSTRAP",
        "limitations": ["Assumes approximately stationary short-memory dependence", "Interval depends on predeclared block size", "Not corrected for strategy selection or repeated trials", "Not a future-return probability"],
    }


DEFAULT_RANKING_WEIGHTS = {"oos_stability": 0.20, "risk_adjusted_performance": 0.10, "data_reliability": 0.20, "execution_feasibility": 0.15, "cost_robustness": 0.15, "parameter_robustness": 0.10, "simplicity": 0.05, "drawdown_control": 0.05}


def rank_candidates(
    candidates: Sequence[Mapping[str, Any]],
    weights: Mapping[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Rank complete prevalidated research dimensions; missing evidence stays null."""
    chosen = dict(DEFAULT_RANKING_WEIGHTS if weights is None else weights)
    if not chosen or any(not math.isfinite(v) or v < 0 for v in chosen.values()) or sum(chosen.values()) <= 0:
        raise ValueError("finite nonnegative weights with positive total required")
    total = sum(chosen.values())
    if not math.isfinite(total):
        raise ValueError("sum of ranking weights must be finite")
    normalized = {key: value / total for key, value in chosen.items()}
    result = []
    for candidate in candidates:
        dimensions = candidate.get("dimensions", {})
        if not isinstance(dimensions, Mapping):
            raise ValueError("candidate dimensions must be a mapping")
        missing = [key for key, weight in normalized.items() if weight > 0 and dimensions.get(key) is None]
        for key in chosen:
            value = dimensions.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError("dimension scores must be finite in [0,1] or null")
        score = None if missing else sum(normalized[key] * float(dimensions.get(key) or 0) for key in normalized)
        result.append({**candidate, "research_priority_score": score, "weights": normalized, "missing_dimensions": missing, "status": "INSUFFICIENT_EVIDENCE" if missing else "RESEARCH_PRIORITY_ONLY", "interpretation": "Transparent research ordering, not a future-return probability or trade recommendation"})
    return sorted(result, key=lambda row: (row["research_priority_score"] is None, -(row["research_priority_score"] or 0), str(row.get("id", ""))))


class HoldoutAudit:
    """Persist immutable review events; tuning use permanently contaminates a holdout."""

    def __init__(self, root: Path):
        self.root = root

    def record(
        self,
        dataset_hash: str,
        holdout_sessions: Sequence[str],
        *,
        experiment_id: str,
        purpose: str,
        informs_tuning: bool = False,
    ) -> dict[str, Any]:
        if not dataset_hash or not experiment_id or not purpose or not holdout_sessions:
            raise ValueError("dataset identity, explicit holdout, experiment and purpose required")
        if len(dataset_hash) != 64 or any(c not in "0123456789abcdef" for c in dataset_hash):
            raise ValueError("full lowercase SHA256 dataset hash required")
        if not isinstance(informs_tuning, bool):
            raise ValueError("informs_tuning must be an explicit boolean")
        dates = list(holdout_sessions)
        if dates != sorted(set(dates)):
            raise ValueError("unique chronological holdout sessions required")
        try:
            if any(date.fromisoformat(value).isoformat() != value for value in dates):
                raise ValueError("ISO calendar dates required")
        except (TypeError, ValueError) as exc:
            raise ValueError("ISO calendar dates required") from exc
        holdout_id = hashlib.sha256(json.dumps({"dataset_hash": dataset_hash, "sessions": dates}, sort_keys=True).encode()).hexdigest()
        event = {"event_id": uuid4().hex, "holdout_id": holdout_id, "dataset_hash": dataset_hash, "holdout_sessions": dates, "experiment_id": experiment_id, "purpose": purpose, "informs_tuning": informs_tuning, "created_at": datetime.now(UTC).isoformat()}
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / f"{event['event_id']}.json").open("x", encoding="utf-8") as stream:
            json.dump(event, stream, sort_keys=True, allow_nan=False)
        return self.status(holdout_id)

    def status(self, holdout_id: str) -> dict[str, Any]:
        if len(holdout_id) != 64 or any(c not in "0123456789abcdef" for c in holdout_id):
            raise ValueError("SHA256 holdout ID required")
        all_events = []
        for path in sorted(self.root.glob("*.json")):
            event = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(event, dict) or not isinstance(event.get("informs_tuning"), bool):
                raise ValueError("malformed holdout audit event")
            expected = hashlib.sha256(json.dumps({"dataset_hash": event["dataset_hash"], "sessions": event["holdout_sessions"]}, sort_keys=True).encode()).hexdigest()
            if event.get("holdout_id") != expected:
                raise ValueError("holdout audit identity mismatch")
            all_events.append(event)
        events = [event for event in all_events if event["holdout_id"] == holdout_id]
        overlapping_tuning_events = []
        if events:
            target = events[0]
            sessions = set(target["holdout_sessions"])
            overlapping_tuning_events = [
                event for event in all_events
                if event["dataset_hash"] == target["dataset_hash"]
                and event["informs_tuning"]
                and sessions.intersection(event["holdout_sessions"])
            ]
        contaminated = bool(overlapping_tuning_events)
        return {"holdout_id": holdout_id, "uses": len(events), "contaminated": contaminated, "independent_validation": False, "status": "CONTAMINATED_BY_TUNING" if contaminated else "REPEATED_HOLDOUT_REVIEW" if len(events) > 1 else "HOLDOUT_REVIEW_RECORDED" if events else "UNSEEN", "events": events, "overlapping_tuning_event_ids": [event["event_id"] for event in overlapping_tuning_events], "limitations": "Local audit cannot prove absence of out-of-band test inspection or certify independent validation. Dataset revisions have distinct hash scopes and require contamination review."}
