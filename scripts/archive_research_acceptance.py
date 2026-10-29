"""Archive measured software/fixture evidence; exclude provider payloads and secrets."""

import hashlib
import json
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

from alphamosaic.experiments.runner import source_manifest


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "runtime"
    output = root / "docs/evidence/renaissance-20261024"
    output.mkdir(parents=True, exist_ok=False)
    suite = read(next((runtime / "renaissance-final").glob("suite-*.json")))
    before = read(next((runtime / "renaissance-demo").glob("suite-*.json")))
    after = read(next((runtime / "renaissance-profile-after").glob("suite-*.json")))
    equality = []
    for left, right in zip(before["cases"], after["cases"], strict=True):
        a = read(runtime / "renaissance-demo/experiments" / left["experiment_id"] / "experiment.json")
        b = read(runtime / "renaissance-profile-after/experiments" / right["experiment_id"] / "experiment.json")
        equality.append({"case": left["case"], "result_equal": a["result"] == b["result"], "analysis_equal": a["analysis"] == b["analysis"]})
    if not all(row["result_equal"] and row["analysis_equal"] for row in equality):
        raise AssertionError("profiling optimization changed research results")
    audit = read(runtime / "dependency-audit-final.json")
    if any(d.get("vulns") or d.get("skip_reason") for d in audit["dependencies"]):
        raise AssertionError("dependency audit findings require explicit disposition")
    xml = ET.parse(runtime / "pytest-final.xml").getroot()
    suites = list(xml.iter("testsuite"))
    tests = {name: sum(int(s.get(name, "0")) for s in suites) for name in ("tests", "failures", "errors", "skipped")}
    python = runtime / "clean-wheel-final/Scripts/python.exe"
    wheel = subprocess.run([str(python), str(root / "scripts/verify_wheel.py")], cwd=runtime / "wheel-working", capture_output=True, text=True, timeout=45, check=True)
    clean = json.loads(wheel.stdout)
    clean["package_path"] = str(Path(clean["package_path"]).relative_to(root))
    mcp = subprocess.run([str(python), str(root / "scripts/mcp_smoke.py"), "--home", "mcp-archive"], cwd=runtime / "wheel-working", capture_output=True, text=True, timeout=45, check=True)
    browser = read(runtime / "terminal-qa-release/browser-qa.json")
    if browser["status"] != "PASSED":
        raise AssertionError("browser acceptance failed")
    build = runtime / "delivery-build-final"
    tar = next(build.glob("*.tar.gz"))
    with tarfile.open(tar) as archive:
        names = archive.getnames()
    if any(set(Path(name).parts) & {"runtime", ".venv", "credentials", ".git"} for name in names):
        raise AssertionError("source distribution contains forbidden runtime/environment paths")
    files = {p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in build.iterdir() if p.suffix in {".whl", ".gz"}}
    evidence = {"scope": "SOFTWARE_AND_SYNTHETIC_FIXTURE_ONLY", "tests": tests, "financial_runtime_warnings": "TREATED_AS_ERRORS", "source_hash": source_manifest()["source_hash"], "fixture_suite": suite, "profile_before": before["performance"], "profile_after": after["performance"], "exact_result_comparison": equality, "clean_base_wheel": clean, "clean_wheel_mcp": json.loads(mcp.stdout), "dependency_audit": {"service": "OSV", "packages": len(audit["dependencies"]), "known_findings": 0, "skipped": 0}, "browser": browser, "build": files, "sdist_runtime_excluded": True, "real_data_acceptance": "BLOCKED_PIT_ACTION_ADJUSTMENT_UNIVERSE_DELISTING", "remote_chatgpt": "NOT_VERIFIED", "hosted_ci": "NOT_VERIFIED"}
    (output / "acceptance.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    for name in ("01-research-overview.png", "04-backtest-results.png", "09-mobile-reports.png"):
        shutil.copyfile(runtime / "terminal-qa-release" / name, output / name)
    case = suite["cases"][1]
    experiment = runtime / "renaissance-final/experiments" / case["experiment_id"]
    shutil.copyfile(experiment / "report.md", output / "sample-fixture-report.md")
    shutil.copyfile(runtime / "pytest-final.xml", output / "pytest.xml")
    shutil.copyfile(runtime / "dependency-audit-final.json", output / "dependency-audit.json")
    print(json.dumps({"status": "PASSED", "evidence": str(output.relative_to(root)), "tests": tests, "result_comparison": "EXACT", "source_hash": evidence["source_hash"]}))


if __name__ == "__main__":
    main()
