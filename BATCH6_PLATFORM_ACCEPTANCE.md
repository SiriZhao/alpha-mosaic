# Batch 6 platform acceptance

This document records the delivery-layer acceptance boundary for `codex/next-platform-delivery`.
The branch is based on `origin/codex/batch5-alpha-validation` and keeps research and paper
evaluation read-only. No broker, order, credential, arbitrary shell, or arbitrary file tool is
exposed.

## Implemented

- MCP multi-symbol entry points now normalize, deduplicate, and reject malformed or over-sized
  requests with machine-readable `INVALID_INPUT` diagnostics. Portfolio and comparison limits are
  1..5 and 2..10 respectively.
- JSON reports use a versioned `schema_version: 1.0` envelope while `ReportStore.latest()` remains
  compatible with pre-envelope bundles. Markdown reports state objective, cutoff, provenance,
  missing-data policy, provider status, evidence limitations, and reproducibility identifiers.
- Plugin metadata version is explicitly aligned with `pyproject.toml` (`0.1.0`). The GitHub
  workflow retains least-privilege read permissions and uploads build/test diagnostics on failure.

## Verification

| Check | Result |
|---|---|
| Python bytecode compilation | PASS (`python -m compileall -q src scripts tests`) |
| Secret scan | PASS (`python scripts/secret_scan.py`) |
| Diff whitespace | PASS (`git diff --check`) |
| Full uv quality gate | NOT_RUN: `uv` is unavailable in this environment |
| Pytest / Ruff / Pyright / build / clean wheel | NOT_VERIFIED locally; CI workflow remains authoritative |
| ChatGPT remote MCP call | NOT_VERIFIED; no public deployment or personal account configured |

## Reproducible commands

```powershell
uv sync --locked --all-extras --dev
uv run ruff check .
uv run pyright
uv run pytest -q
uv build
uv run python scripts/secret_scan.py
```

Live provider tests remain explicit opt-in (`pytest -m live`) and are excluded from the offline
quality gate. Remote deployment still requires an operator-managed HTTPS reverse proxy, bearer
secret, rate-limit/session settings, and a verified ChatGPT MCP call; none is claimed here.
