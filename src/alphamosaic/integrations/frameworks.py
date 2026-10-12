"""Auditable inventory of external research frameworks.

The matrix intentionally separates adapter presence, installation, startup,
computation, and validation. A package being importable never certifies an
investment result.
"""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import asdict, dataclass, replace
from importlib.metadata import PackageNotFoundError, version
from typing import ClassVar


@dataclass(frozen=True)
class FrameworkRecord:
    name: str
    official_url: str
    version: str | None
    license_spdx: str
    python_compatibility: str
    windows_compatible: str
    cpu_gpu_requirements: str
    dependency_conflicts: str
    formal_interface: str
    data_requirements: str
    reproducibility: str
    runtime_cost: str
    research_value: str
    adapter_present: bool
    dependency_installed: bool
    engine_started: bool
    computation_succeeded: bool
    validation_passed: bool
    status: str
    diagnostics: tuple[str, ...] = ()


class FrameworkIntegrationMatrix:
    """Deterministic matrix; no package installation or network calls occur."""

    _SPECS: ClassVar[tuple[dict[str, str], ...]] = (
        dict(
            name="QuantConnect LEAN",
            package="lean",
            url="https://github.com/QuantConnect/Lean",
            license="Apache-2.0",
            py=">=3.8",
            win="SUPPORTED when Docker/CLI configured",
            compute="Docker/CLI and licensed data",
            api="LEAN CLI",
            cpu="CPU; Docker",
            conflict="isolated",
            repro="project + data required",
            cost="local CPU; QuantConnect cloud paid",
            value="professional order/event model",
        ),
        dict(
            name="QuantStats",
            package="quantstats",
            url="https://github.com/ranaroussi/quantstats",
            license="Apache-2.0",
            py=">=3.8",
            win="SUPPORTED",
            compute="returns series",
            api="Python API",
            cpu="CPU",
            conflict="optional extra",
            repro="high for supplied returns",
            cost="local",
            value="performance statistics",
        ),
        dict(
            name="VectorBT",
            package="vectorbt",
            url="https://github.com/polakowo/vectorbt",
            license="NOASSERTION",
            py="project dependent",
            win="UNVERIFIED",
            compute="array prices",
            api="Python API",
            cpu="CPU; optional numba",
            conflict="isolated optional",
            repro="depends on data",
            cost="local CPU",
            value="vectorized research",
        ),
        dict(
            name="AI Hedge Fund",
            package="ai_hedge_fund",
            url="https://github.com/virattt/ai-hedge-fund",
            license="MIT",
            py="project pinned",
            win="UNVERIFIED",
            compute="LLM/data-provider keys",
            api="CLI/repository",
            cpu="CPU; network",
            conflict="isolated",
            repro="keys and prompts required",
            cost="model/provider quota",
            value="experimental multi-agent research",
        ),
        dict(
            name="FinRL-X",
            package="finrlx",
            url="https://github.com/AI4Finance-Foundation/FinRL-X",
            license="UNVERIFIED",
            py="UNVERIFIED",
            win="UNVERIFIED",
            compute="RL data/GPU",
            api="UNVERIFIED",
            cpu="GPU optional",
            conflict="not installed",
            repro="UNVERIFIED",
            cost="GPU/provider dependent",
            value="unverified; upstream endpoint unavailable",
        ),
        dict(
            name="FinRL",
            package="finrl",
            url="https://github.com/AI4Finance-Foundation/FinRL",
            license="MIT",
            py="project pinned",
            win="UNVERIFIED",
            compute="historical data and RL",
            api="Python notebooks/API",
            cpu="CPU/GPU optional",
            conflict="isolated",
            repro="seed/data/environment required",
            cost="local/GPU",
            value="experimental RL research",
        ),
        dict(
            name="Backtrader",
            package="backtrader",
            url="https://github.com/mementum/backtrader",
            license="GPL-3.0-only",
            py="legacy-compatible",
            win="SUPPORTED",
            compute="feed + strategy",
            api="Python API",
            cpu="CPU",
            conflict="GPL boundary",
            repro="feed/config required",
            cost="local",
            value="event backtesting; license boundary",
        ),
    )

    def __init__(self) -> None:
        self._records: dict[str, FrameworkRecord] = self._audit()

    @staticmethod
    def _version(package: str) -> str | None:
        try:
            return version(package)
        except PackageNotFoundError:
            return None

    def _audit(self) -> dict[str, FrameworkRecord]:
        result: dict[str, FrameworkRecord] = {}
        for spec in self._SPECS:
            installed = bool(importlib.util.find_spec(spec["package"]))
            # LEAN's command name is the authoritative startup prerequisite;
            # importing a similarly named Python package does not start LEAN.
            if spec["name"] == "QuantConnect LEAN":
                installed = shutil.which("lean") is not None or shutil.which("docker") is not None
            adapter = spec["name"] in {"QuantStats", "QuantConnect LEAN"}
            status = (
                "READY"
                if adapter and installed
                else "NOT_CONFIGURED"
                if adapter
                else "EXPERIMENTAL"
            )
            diagnostics: tuple[str, ...] = ()
            if spec["name"] == "FinRL-X":
                status, diagnostics = (
                    "BLOCKED",
                    ("official repository/API was unavailable during audit",),
                )
            elif spec["name"] == "Backtrader":
                status, diagnostics = (
                    "LICENSE_BLOCKED",
                    ("GPL-3.0; no adapter in the Apache-2.0 core",),
                )
            elif spec["name"] not in {"QuantStats", "QuantConnect LEAN"}:
                diagnostics = ("adapter not present; dependency is intentionally not installed",)
            elif not installed:
                diagnostics = ("optional dependency or executable is not installed",)
            result[spec["name"]] = FrameworkRecord(
                name=spec["name"],
                official_url=spec["url"],
                version=self._version(spec["package"]),
                license_spdx=spec["license"],
                python_compatibility=spec["py"],
                windows_compatible=spec["win"],
                cpu_gpu_requirements=spec["cpu"],
                dependency_conflicts=spec["conflict"],
                formal_interface=spec["api"],
                data_requirements=spec["compute"],
                reproducibility=spec["repro"],
                runtime_cost=spec["cost"],
                research_value=spec["value"],
                adapter_present=adapter,
                dependency_installed=installed,
                engine_started=False,
                computation_succeeded=False,
                validation_passed=False,
                status=status,
                diagnostics=diagnostics,
            )
        return result

    def records(self) -> list[FrameworkRecord]:
        return list(self._records.values())

    def record(
        self,
        name: str,
        *,
        engine_started: bool = False,
        computation_succeeded: bool = False,
        validation_passed: bool = False,
        diagnostics: tuple[str, ...] = (),
    ) -> FrameworkRecord:
        if name not in self._records:
            raise KeyError(name)
        previous = self._records[name]
        status = previous.status
        if validation_passed:
            status = "VALIDATED"
        elif computation_succeeded:
            status = "COMPUTED"
        elif engine_started:
            status = "STARTED"
        self._records[name] = replace(
            previous,
            engine_started=engine_started,
            computation_succeeded=computation_succeeded,
            validation_passed=validation_passed,
            status=status,
            diagnostics=previous.diagnostics + diagnostics,
        )
        return self._records[name]

    def as_dict(self) -> list[dict[str, object]]:
        return [asdict(item) for item in self.records()]
