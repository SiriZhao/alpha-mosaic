"""Fail-closed TradingAgents v0.6 adapter with bounded cost profiles."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from alphamosaic.core.contracts import DataQuality, ResearchOutcome, ResearchVerdict, Status

PROFILES: dict[str, dict[str, int]] = {
    "FAST": {"max_calls": 8, "timeout": 90, "max_concurrency": 1, "debate_rounds": 1, "risk_rounds": 1, "tool_rounds": 6, "recur_limit": 40, "cache_hours": 6},
    "BALANCED": {"max_calls": 16, "timeout": 180, "max_concurrency": 1, "debate_rounds": 2, "risk_rounds": 1, "tool_rounds": 12, "recur_limit": 70, "cache_hours": 12},
    "DEEP": {"max_calls": 32, "timeout": 300, "max_concurrency": 1, "debate_rounds": 3, "risk_rounds": 2, "tool_rounds": 20, "recur_limit": 100, "cache_hours": 24},
}
Profile = Literal["FAST", "BALANCED", "DEEP"]
Verdict = Literal["BULLISH", "BEARISH", "NEUTRAL", "CONFLICTED", "INSUFFICIENT_EVIDENCE"]


def _structured_verdict(payload: Any) -> tuple[Verdict, list[str]] | None:
    """Accept only an explicit bounded field; never infer direction from prose."""
    if not isinstance(payload, dict):
        return None
    value = payload.get("verdict", payload.get("final_rating"))
    mapping = {"BUY": "BULLISH", "BULLISH": "BULLISH", "SELL": "BEARISH", "BEARISH": "BEARISH", "HOLD": "NEUTRAL", "NEUTRAL": "NEUTRAL", "CONFLICTED": "CONFLICTED", "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE"}
    if not isinstance(value, str) or value.upper() not in mapping:
        return None
    rationale = payload.get("rationale", payload.get("investment_thesis", []))
    if isinstance(rationale, str):
        rationale = [rationale]
    if not isinstance(rationale, list) or not all(isinstance(item, str) for item in rationale):
        return None
    return cast(Verdict, mapping[value.upper()]), [str(item) for item in rationale[:10]]


class TradingAgentsAdapter:
    name = "TradingAgents"

    def __init__(self, home: Path, package_available: bool | None = None):
        self.home = home.resolve()
        self.package_available = package_available

    def _available(self) -> bool:
        if self.package_available is not None:
            return self.package_available
        try:
            __import__("importlib.metadata").metadata.version("tradingagents")
            return True
        except Exception:
            return False

    def research(self, symbol: str, profile: Profile = "FAST", as_of: datetime | None = None) -> ResearchOutcome:
        if profile not in PROFILES:
            raise ValueError("profile must be FAST, BALANCED or DEEP")
        requested = datetime.now(UTC)
        if not self._available():
            return ResearchOutcome(
                symbol=symbol,
                status=Status.NOT_CONFIGURED,
                source="TradingAgents v0.6.0",
                cost_profile=profile,
                diagnostics=["optional tradingagents package is not installed; no model call made"],
                requested_at=requested,
                completed_at=datetime.now(UTC),
                execution={"profile": profile, "upstream_version": "0.6.0"},
            )
        if not any(os.environ.get(key) for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")):
            return ResearchOutcome(
                symbol=symbol,
                status=Status.NOT_CONFIGURED,
                source="TradingAgents v0.6.0",
                cost_profile=profile,
                diagnostics=["no supported LLM credential found in environment; no model call made"],
                requested_at=requested,
                completed_at=datetime.now(UTC),
                execution={"profile": profile, "upstream_version": "0.6.0"},
            )
        request = {
            "symbol": symbol,
            "date": (as_of or datetime.now(UTC)).date().isoformat(),
            "profile": profile,
            "runtime": str(self.home / "tradingagents"),
            "config": {
                "max_debate_rounds": PROFILES[profile]["debate_rounds"],
                "max_risk_discuss_rounds": PROFILES[profile]["risk_rounds"],
                "max_tool_rounds": PROFILES[profile]["tool_rounds"],
                "max_recur_limit": PROFILES[profile]["recur_limit"],
                "results_dir": str(self.home / "tradingagents" / "results"),
                "data_cache_dir": str(self.home / "tradingagents" / "cache"),
                "memory_log_path": str(self.home / "tradingagents" / "memory.md"),
            },
            "upstream_version": "0.6.0",
        }
        try:
            response: dict[str, Any] = {}
            result = subprocess.run(
                [sys.executable, "-m", "alphamosaic.integrations.tradingagents_worker"],
                input=json.dumps(request), capture_output=True, text=True, encoding="utf-8",
                timeout=PROFILES[profile]["timeout"], check=False,
                cwd=str(self.home),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode:
                status = Status.UNAVAILABLE
                diagnostics = [f"isolated worker exited {result.returncode}"]
                payload = None
            else:
                response: dict[str, Any] = json.loads(result.stdout)
                payload = response.get("decision")
                status = Status.OK if response.get("status") == "OK" else Status.UNAVAILABLE
                diagnostics = [str(response.get("error"))] if status != Status.OK else []
            verdict = None
            normalized = _structured_verdict(payload)
            if status == Status.OK and normalized:
                completed = datetime.now(UTC)
                verdict = ResearchVerdict(
                    symbol=symbol,
                    source="TradingAgents v0.6.0",
                    source_url="https://github.com/TauricResearch/TradingAgents/releases/tag/v0.6.0",
                    observed_at=completed,
                    known_at=completed,
                    as_of=completed,
                    data_quality=DataQuality.MODEL_INFERENCE,
                    adjustment_policy="NOT_APPLICABLE",
                    provenance={"adapter": "isolated official Python API", "profile": profile},
                    license_scope="Upstream TradingAgents license and model-provider terms",
                    verdict=normalized[0],
                    rationale=["Normalized from an explicit upstream structured field; no return probability parsed", *normalized[1]],
                    time_horizon="research-defined",
                )
            elif status == Status.OK:
                diagnostics.append("upstream output lacked a supported structured verdict; retained as opinion only")
            return ResearchOutcome(
                symbol=symbol, status=status, verdict=verdict, source="TradingAgents v0.6.0",
                cost_profile=profile, diagnostics=diagnostics, requested_at=requested,
                completed_at=datetime.now(UTC),
                execution={
                    "profile": profile,
                    "upstream_version": "0.6.0",
                    "timeout_seconds": PROFILES[profile]["timeout"],
                    "debate_rounds": PROFILES[profile]["debate_rounds"],
                    "risk_rounds": PROFILES[profile]["risk_rounds"],
                    "tool_rounds": PROFILES[profile]["tool_rounds"],
                    "worker_execution": json.dumps(response.get("execution", {}), sort_keys=True)[:1000],
                },
            )
        except subprocess.TimeoutExpired:
            return ResearchOutcome(
                symbol=symbol, status=Status.TIMEOUT, source="TradingAgents v0.6.0",
                cost_profile=profile, diagnostics=["bounded worker timeout"], requested_at=requested,
                completed_at=datetime.now(UTC),
                execution={"profile": profile, "timeout_seconds": PROFILES[profile]["timeout"]},
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return ResearchOutcome(
                symbol=symbol, status=Status.INVALID_DATA, source="TradingAgents v0.6.0",
                cost_profile=profile, diagnostics=[f"worker transport/JSON failure: {type(exc).__name__}"],
                requested_at=requested, completed_at=datetime.now(UTC),
                execution={"profile": profile},
            )
