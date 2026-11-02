"""Retain current measured software/fixture acceptance without rewriting prior evidence."""

import json
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import digest, source_manifest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "runtime"
    output = root / "docs/evidence/continuation-20261025"
    output.mkdir(parents=True, exist_ok=False)
    suite = json.loads(next((runtime / "extended-acceptance-20261025").glob("suite-*.json")).read_bytes())
    service = ApplicationService(runtime / "extended-acceptance-20261025")
    plan = service.research_plan_report(suite["plan_id"])
    if suite["status"] != "PASSED" or plan["status"] != "COMPLETED" or plan["trials_attempted"] != 6:
        raise AssertionError("extended fixture/workflow acceptance failed")
    if len(plan["critics"]) != 6 or plan["automatic_promotion"] is not False:
        raise AssertionError("missing independent checklist or unsupported promotion")
    source = source_manifest()
    for row in suite["cases"]:
        item = service.research_result(row["experiment_id"])
        if item["status"] != "COMPLETED" or item["reproducibility"]["source_hash"] != source["source_hash"]:
            raise AssertionError("fixture result was produced by a different source tree")
        if item["analysis"]["trade_analysis"]["reconciliation"]["status"] != "PASSED":
            raise AssertionError("unqualified FIFO accounting")
    xml = ET.parse(runtime / "pytest-continuation-final.xml").getroot()
    tests = {key: sum(int(node.get(key, "0")) for node in xml.iter("testsuite")) for key in ("tests", "failures", "errors", "skipped")}
    if tests["failures"] or tests["errors"] or tests["skipped"]:
        raise AssertionError("test acceptance is incomplete")
    build = runtime / "continuation-build-20261025"
    wheel = next(build.glob("*.whl"))
    with zipfile.ZipFile(wheel) as package:
        for name in package.namelist():
            if name.startswith("alphamosaic/") and name.endswith(".py"):
                if package.read(name) != (root / "src" / name).read_bytes():
                    raise AssertionError("wheel source differs from the tested source tree")
    with tarfile.open(next(build.glob("*.tar.gz"))) as package:
        if any(set(Path(name).parts) & {"runtime", ".venv", ".git"} for name in package.getnames()):
            raise AssertionError("source package contains local runtime/environment paths")
    working = runtime / "continuation-wheel-work"
    working.mkdir(exist_ok=True)
    python = runtime / "continuation-wheel-env/Scripts/python.exe"
    wheel_run = subprocess.run([str(python), str(root / "scripts/verify_wheel.py")], cwd=working, capture_output=True, text=True, timeout=120, check=True)
    installed = json.loads(wheel_run.stdout)
    installed["package_path"] = str(Path(installed["package_path"]).relative_to(root))
    mcp_run = subprocess.run([str(python), str(root / "scripts/mcp_smoke.py"), "--home", "mcp-home"], cwd=working, capture_output=True, text=True, timeout=60, check=True)
    browser = json.loads((runtime / "continuation-terminal-qa-20261025/browser-qa.json").read_bytes())
    if browser["status"] != "PASSED":
        raise AssertionError("browser navigation/render failed")
    evidence = {"captured_at_utc": datetime.now(UTC).isoformat(), "scope": "SOFTWARE_AND_FIXTURE_ONLY", "source_hash": source["source_hash"],
        "tests": tests, "runtime_warnings": "TREATED_AS_ERRORS", "fixture_suite": suite,
        "frozen_plan": {"plan_id": suite["plan_id"], "status": plan["status"], "attempts": plan["trials_attempted"], "critics": len(plan["critics"]), "automatic_promotion": False},
        "clean_base_wheel": installed, "clean_wheel_mcp": json.loads(mcp_run.stdout), "browser": browser,
        "artifacts": {p.name: {"bytes": p.stat().st_size, "sha256": digest(p.read_bytes())} for p in build.iterdir() if p.suffix in {".gz", ".whl"}},
        "package_python_matches_tested_source": True, "sdist_runtime_excluded": True,
        "real_data_acceptance": "BLOCKED_PIT_ACTION_ADJUSTMENT_UNIVERSE_DELISTING", "remote_chatgpt": "NOT_VERIFIED", "overall_goal": "ACTIVE_NOT_COMPLETE", "hosted_ci": "CHECK_CURRENT_BRANCH_COMMIT_SEPARATELY"}
    with (output / "acceptance.json").open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, indent=2)
    shutil.copyfile(runtime / "pytest-continuation-final.xml", output / "pytest.xml")
    for name in ("01-research-overview.png", "04-backtest-results.png", "07-ai-research.png", "09-mobile-reports.png"):
        shutil.copyfile(runtime / "continuation-terminal-qa-20261025" / name, output / name)
    sample = runtime / "extended-acceptance-20261025/experiments" / suite["cases"][3]["experiment_id"]
    shutil.copyfile(sample / "report.md", output / "sample-weekly-fixture-report.md")
    with (output / "plan-evidence.json").open("x", encoding="utf-8") as stream:
        json.dump(plan, stream, indent=2)
    print(json.dumps({"status": "PASSED", "tests": tests, "source_hash": source["source_hash"], "output": str(output.relative_to(root))}))


if __name__ == "__main__":
    main()
