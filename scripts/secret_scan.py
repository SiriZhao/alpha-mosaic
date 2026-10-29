"""Small deterministic CI guard against accidentally committed credentials."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][^\"']{16,}[\"']"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)


def main(staged: bool = False) -> int:
    command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"] if staged else ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    names = subprocess.check_output(command, text=False).decode().split("\0")
    findings: list[str] = []
    for name in filter(None, names):
        path = Path(name)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".sqlite", ".db"}:
            continue
        try:
            text = subprocess.check_output(["git", "show", ":" + name]).decode("utf-8") if staged else path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                findings.append(f"{name}:{line_no}")
    if findings:
        print("Potential credentials found:\n" + "\n".join(findings))
        return 1
    print("No credential patterns found in " + ("staged blobs" if staged else "tracked and nonignored text files"))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true")
    raise SystemExit(main(parser.parse_args().staged))
