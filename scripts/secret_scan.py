"""Small deterministic CI guard against accidentally committed credentials."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][^\"']{16,}[\"']"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)


def main() -> int:
    names = subprocess.check_output(["git", "ls-files", "-z"], text=False).decode().split("\0")
    findings: list[str] = []
    for name in filter(None, names):
        path = Path(name)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".sqlite", ".db"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                findings.append(f"{name}:{line_no}")
    if findings:
        print("Potential credentials found:\n" + "\n".join(findings))
        return 1
    print("No credential patterns found in tracked text files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
