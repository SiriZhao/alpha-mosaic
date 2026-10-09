"""Local LEAN CLI boundary. Never calls cloud endpoints or purchases data."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4


class LeanAdapter:
    def health(self) -> dict[str, Any]:
        missing = [name for name in ("docker", "lean") if shutil.which(name) is None]
        if missing:
            return {
                "status": "BLOCKED",
                "engine": "QuantConnect LEAN local",
                "diagnostics": ["MISSING_" + name.upper() for name in missing],
                "verified_computation": False,
            }
        try:
            result = subprocess.run(
                [str(shutil.which("docker")), "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {
                "status": "BLOCKED",
                "diagnostics": ["DOCKER_DAEMON_UNAVAILABLE"],
                "verified_computation": False,
            }
        return {
            "status": "NOT_CONFIGURED" if result.returncode == 0 else "BLOCKED",
            "diagnostics": ["REVIEWED_LOCAL_PROJECT_AND_LICENSED_DATA_REQUIRED"],
            "verified_computation": False,
        }

    def run(
        self, project: Path, workspace: Path, output_root: Path, timeout: int = 300
    ) -> dict[str, Any]:
        """Execute an operator-reviewed local algorithm; not exposed as an MCP path tool."""
        health = self.health()
        if health["status"] == "BLOCKED":
            return health
        project, workspace = project.resolve(), workspace.resolve()
        if (
            not project.is_relative_to(workspace)
            or not (workspace / "lean.json").is_file()
            or not (project / "main.py").is_file()
        ):
            return {
                "status": "NOT_CONFIGURED",
                "diagnostics": ["REVIEWED_LOCAL_LEAN_PROJECT_REQUIRED"],
            }
        if not 10 <= timeout <= 3600:
            raise ValueError("timeout must be 10..3600 seconds")
        output = output_root.resolve() / uuid4().hex
        output.mkdir(parents=True, exist_ok=False)
        try:
            result = subprocess.run(
                [str(shutil.which("lean")), "backtest", str(project), "--output", str(output)],
                cwd=workspace,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "FAILED",
                "diagnostics": ["LEAN_DEADLINE_EXCEEDED"],
                "verified_computation": False,
            }
        except OSError:
            return {
                "status": "FAILED",
                "diagnostics": ["LEAN_PROCESS_UNAVAILABLE"],
                "verified_computation": False,
            }
        if result.returncode:
            return {
                "status": "FAILED",
                "exit_code": result.returncode,
                "diagnostics": ["LEAN_LOCAL_BACKTEST_FAILED"],
                "verified_computation": False,
            }
        for path in sorted(output.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if (
                isinstance(payload, dict)
                and isinstance(payload.get("Statistics"), dict)
                and payload["Statistics"]
            ):
                return {
                    "status": "READY",
                    "engine": "LEAN",
                    "statistics": payload["Statistics"],
                    "acceptance": "LOCAL_ENGINE_OUTPUT_REQUIRES_DATA_REVIEW",
                    "output_directory": str(output),
                    "verified_computation": True,
                    "broker_enabled": False,
                }
        return {
            "status": "FAILED",
            "diagnostics": ["LEAN_RESULT_CONTRACT_MISSING"],
            "verified_computation": False,
        }
