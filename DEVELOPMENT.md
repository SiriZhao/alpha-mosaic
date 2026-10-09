# Development

Requires Python 3.12 and `uv`. Install locked dependencies with `uv sync --all-extras`.

Useful checks:

```powershell
uv run ruff check .
uv run pyright
uv run pytest -q
uv run python -m build --wheel --sdist
uv run alphamosaic doctor
uv run alphamosaic providers
```

Network acceptance is explicit and should be run against a writable `ALPHAMOSAIC_HOME`:
`uv run alphamosaic scan --universe-limit 10 --top 10`. Provider errors are returned as
structured statuses; fixtures are never substituted for network failures.

Before a commit, inspect `git diff --check`, stage reviewed paths explicitly, scan staged files
for credentials and runtime data, and verify the repository root and remote owner. Never reset,
clean, force-push, or overwrite unknown files.
