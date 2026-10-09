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
    "FAST": {"max_calls": 8, "timeout": 90, "max_concurrency": 1, "cache_hours": 6},
    "BALANCED": {"max_calls": 16, "timeout": 180, "max_concurrency": 1, "cache_hours": 12},
    "DEEP": {"max_calls": 32, "timeout": 300, "max_concurrency": 1, "cache_hours": 24},
}
Profile = Literal["FAST", "BALANCED", "DEEP"]
Verdict = Literal["BULLISH", "BEARISH", "NEUTRAL", "CONFLICTED", "INSUFFICIENT_EVIDENCE"]


def _verdict(text: str) -> Verdict:
    value = text.upper()
    if "CONFLICT" in value or ("BULL" in value and "BEAR" in value):
        return "CONFLICTED"
    if "BULL" in value or "BUY" in value:
        return "BULLISH"
    if "BEAR" in value or "SELL" in value:
        return "BEARISH"
    if "NEUTRAL" in value or "HOLD" in value:
        return "NEUTRAL"
    return cast(Verdict, "INSUFFICIENT_EVIDENCE")


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
            )
        request = {
            "symbol": symbol,
            "date": (as_of or datetime.now(UTC)).date().isoformat(),
            "profile": profile,
            "runtime": str(self.home / "tradingagents"),
        }
        try:
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
                raw = ""
            else:
                response: dict[str, Any] = json.loads(result.stdout)
                raw = str(response.get("decision", ""))
                status = Status.OK if response.get("status") == "OK" else Status.UNAVAILABLE
                diagnostics = [str(response.get("error"))] if status != Status.OK else []
            verdict = None
            if status == Status.OK:
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
                    verdict=_verdict(raw),
                    rationale=["Normalized from upstream research output; no return probability parsed", raw[:2000]],
                    time_horizon="research-defined",
                )
            return ResearchOutcome(
                symbol=symbol, status=status, verdict=verdict, source="TradingAgents v0.6.0",
                cost_profile=profile, diagnostics=diagnostics, requested_at=requested,
                completed_at=datetime.now(UTC),
            )
        except subprocess.TimeoutExpired:
            return ResearchOutcome(
                symbol=symbol, status=Status.TIMEOUT, source="TradingAgents v0.6.0",
                cost_profile=profile, diagnostics=["bounded worker timeout"], requested_at=requested,
                completed_at=datetime.now(UTC),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return ResearchOutcome(
                symbol=symbol, status=Status.INVALID_DATA, source="TradingAgents v0.6.0",
                cost_profile=profile, diagnostics=[f"worker transport/JSON failure: {type(exc).__name__}"],
                requested_at=requested, completed_at=datetime.now(UTC),
            )
