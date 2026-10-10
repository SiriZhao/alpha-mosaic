# Final acceptance (2026-10-10)

## Scope

This acceptance covers the local AlphaMosaic MCP server, portable agent package, security
boundaries and paper-only research workflows. It does not claim a public deployment, a ChatGPT
remote connection, broker access or demonstrated investment alpha.

## Verified locally

- Python 3.12.14 `.venv` imports the source package and runs the test suite.
- `pytest -q --basetemp .pytest-local-temp`: 10 passed (the repository currently contains ten tests).
- `ruff check .`: passed after the final remote-server changes.
- `pyright`: 0 errors, 0 warnings.
- `python -m build --wheel --sdist`: previously passed for the current package; repeat before a release.
- The stdio MCP server exposes the unified read-only tools and backward-compatible aliases.
- Streamable HTTP MCP handshake and tool transport succeed locally with bearer authentication;
  the MCP session manager lifespan is retained by using the MCP app as the root ASGI app.
- The remote app rejects short tokens, missing bearer credentials, oversized declared bodies and
  insecure non-local requests. It adds `no-store` and `nosniff` headers and can write redacted
  request metadata to `ALPHAMOSAIC_AUDIT_LOG`.
- `scripts/validate_plugin.py` validates four skills and confirms that each references a real
  MCP tool. The packaged URL remains a deployment placeholder and is therefore `NOT_VERIFIED`.
- OpenBB/Nasdaq live AAPL evidence, deterministic factor scanning, multi-source research and
  explicit `NOT_CONFIGURED` TradingAgents/Danelfin outcomes are recorded in `CURRENT_STATE.md`.
- A live explicit scan request reached Nasdaq/OpenBB and returned `REAL_DATA`; the current run
  qualified zero candidates because the provider data was stale at the cutoff, so no candidate was
  padded. AAPL historical momentum replay completed with fees/slippage and QQQM comparison;
  SPY was rejected for a malformed volume field. These are diagnostics, not alpha claims.

## Not verified or blocked

- ChatGPT remote end-to-end: `NOT_VERIFIED`; no public HTTPS endpoint was deployed and no manual
  ChatGPT connection was performed.
- GitHub Actions: `NOT_VERIFIED`; this checkout has no configured remote and `gh auth status`
  reports an invalid SiriZhao token. No push is claimed.
- QuantConnect LEAN: `BLOCKED` because Docker/LEAN CLI and licensed data were not provisioned.
- TradingAgents and Danelfin: `NOT_CONFIGURED` without optional package/model credentials and
  `DANELFIN_API_KEY`; no mock success is used.
- Forward signal history and forward performance: `NOT_CONFIGURED` until reviewed observations are
  initialized. Historical backtests remain historical statistics, not live returns.

## Safety boundary

The application remains research-only with `broker_enabled=false`. MCP has no arbitrary file,
shell, credential or order tools. Values remain sourced or null, model commentary is labelled as
inference, and heuristic rankings are not return probabilities.

## Release gate

Before publishing a remote plugin, replace the placeholder URL with an operator-managed HTTPS
deployment, perform a real ChatGPT tool call, record the evidence and only then change the remote
status to `VERIFIED`.
