"""Runtime identity independent of data/software/investment acceptance."""

import hashlib
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from alphamosaic import __version__


def runtime_manifest() -> dict[str, object]:
    package = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(package.rglob("*.py")):
        digest.update(path.relative_to(package).as_posix().encode())
        digest.update(path.read_bytes())
    dependencies = {}
    for name in ("pydantic", "numpy", "pandas", "mcp", "openbb-core", "openbb-nasdaq", "quantstats", "exchange-calendars"):
        try:
            dependencies[name] = version(name)
        except PackageNotFoundError:
            dependencies[name] = "NOT_INSTALLED"
    git_sha = None
    if package.parent.name == "src":
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=package.parent.parent, capture_output=True, text=True, timeout=5, check=False)
        git_sha = result.stdout.strip() if result.returncode == 0 else None
    return {
        "package_version": __version__, "python": platform.python_version(),
        "interpreter": sys.executable, "package_path": str(package),
        "git_sha": git_sha, "source_sha256": digest.hexdigest(),
        "dependencies": dependencies,
    }
