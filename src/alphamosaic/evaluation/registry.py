"""Evidence-gated lifecycle. No tool exposes promotion authority to an LLM."""

from enum import StrEnum

from pydantic import Field

from alphamosaic.core.contracts import Contract


class StrategyState(StrEnum):
    RESEARCH = "RESEARCH"
    BACKTESTED = "BACKTESTED"
    OUT_OF_SAMPLE_PASSED = "OUT_OF_SAMPLE_PASSED"
    FORWARD_TESTING = "FORWARD_TESTING"
    ELIGIBLE_FOR_ADVISORY = "ELIGIBLE_FOR_ADVISORY"
    REJECTED = "REJECTED"


class EvaluationEvidence(Contract):
    strategy: str
    run_id: str
    acceptance: str
    replay_completed: bool = False
    qualified_data: bool = False
    oos_folds: int = Field(default=0, ge=0)
    oos_observations: int = Field(default=0, ge=0)
    excess_lower_bound: float | None = None
    maximum_drawdown: float | None = None
    independent_replication: bool = False
    forward_initialized: bool = False
    qualified_forward_observations: int = Field(default=0, ge=0)
    forward_excess_lower_bound: float | None = None
    rejected: bool = False


class PromotionRules(Contract):
    minimum_folds: int = Field(default=3, ge=2)
    minimum_oos_observations: int = Field(default=252, ge=126)
    minimum_forward_observations: int = Field(default=126, ge=63)
    drawdown_limit: float = Field(default=-0.25, ge=-1, lt=0)


class EvaluationRegistry:
    """Recompute a state from one complete evidence bundle; never union unrelated runs.

    These gates are necessary conditions, not a certification of future performance.
    Production evidence import and independent review are still required.
    """

    def __init__(self, rules: PromotionRules | None = None):
        self.rules = rules or PromotionRules()
        self.records: dict[str, dict[str, str]] = {}
        self.evidence: list[dict[str, object]] = []

    def record_evaluation(
        self,
        *,
        strategy: str,
        strategy_version: str,
        engine: str,
        data_fingerprint: str,
        acceptance: str,
        metrics: dict[str, float | None],
        failure_evidence: list[str] | None = None,
    ) -> dict[str, object]:
        """Append run evidence without changing promotion state.

        The registry deliberately stores failure evidence alongside metrics so a later
        review cannot silently select only successful runs.
        """
        item: dict[str, object] = {
            "strategy": strategy,
            "strategy_version": strategy_version,
            "engine": engine,
            "data_fingerprint": data_fingerprint,
            "acceptance": acceptance,
            "metrics": dict(metrics),
            "failure_evidence": list(failure_evidence or []),
            "broker_submission": "DISABLED",
        }
        self.evidence.append(item)
        return item

    def evaluate(self, evidence: EvaluationEvidence) -> dict[str, str]:
        state = StrategyState.RESEARCH
        reason = "NO_QUALIFIED_REPLAY"
        if evidence.rejected:
            state, reason = StrategyState.REJECTED, "EXPLICIT_EVIDENCE_REJECTION"
        elif evidence.replay_completed:
            state, reason = StrategyState.BACKTESTED, "ENGINEERING_REPLAY_ONLY"
            qualified = (
                evidence.acceptance == "REAL_PIT"
                and evidence.qualified_data
                and evidence.independent_replication
                and evidence.oos_folds >= self.rules.minimum_folds
                and evidence.oos_observations >= self.rules.minimum_oos_observations
                and evidence.excess_lower_bound is not None
                and evidence.excess_lower_bound > 0
                and evidence.maximum_drawdown is not None
                and self.rules.drawdown_limit <= evidence.maximum_drawdown <= 0
            )
            if qualified:
                state, reason = StrategyState.OUT_OF_SAMPLE_PASSED, "QUALIFIED_OOS_RULES_PASSED"
                if evidence.forward_initialized:
                    state, reason = StrategyState.FORWARD_TESTING, "QUALIFIED_OOS_FORWARD_STARTED"
                    if (
                        evidence.qualified_forward_observations
                        >= self.rules.minimum_forward_observations
                        and evidence.forward_excess_lower_bound is not None
                        and evidence.forward_excess_lower_bound > 0
                    ):
                        state, reason = (
                            StrategyState.ELIGIBLE_FOR_ADVISORY,
                            "QUALIFIED_FORWARD_RULES_PASSED_HUMAN_REVIEW_REQUIRED",
                        )
        record = {
            "strategy": evidence.strategy,
            "run_id": evidence.run_id,
            "state": state.value,
            "reason": reason,
            "broker_submission": "DISABLED",
        }
        self.records[evidence.strategy] = record
        return record


class StrategyEvaluationRegistry(EvaluationRegistry):
    """Named Batch 5 facade for long-lived strategy experiment evidence."""
