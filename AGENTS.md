# AlphaMosaic engineering rules

## Architecture and permissions
- AlphaMosaic is independent. Never read runtime credentials from or modify Meridian Alpha.
- One authoritative ApplicationService orchestrates CLI and MCP. Adapters implement protocols;
  domain code must not import OpenBB, QuantStats, CLI, or MCP internals.
- Research and paper evaluation only. No broker order routes, credentials tools, arbitrary shell,
  arbitrary file reads, or real account connectors. AI comments never become market observations.
- Optional integrations may run in isolated processes; stdio must contain only MCP protocol traffic.

## Evidence and data
- Financial values are sourced or null. Never invent missing values or replace network errors
  with fixtures. Mark REAL/HISTORICAL/DELAYED/FIXTURE/MODEL_INFERENCE/MISSING explicitly.
- Use aware UTC timestamps and enforce known_at <= research cutoff. Revised historical data
  is not certified point-in-time data. Document survivorship and corporate action limitations.
- Check security identity, exchange, currency, adjustment policy, stale/duplicate/malformed data.
- Record provider health separately from investment signal validity. Heuristic ranking is not
  a return probability. No demonstrated alpha without independently qualified evidence.
- Provider software license does not grant redistribution rights to provider data.

## Quality and acceptance
- Python 3.12, uv lock, src-layout. Run ruff, pyright, pytest, wheel/sdist build, CLI and MCP smoke,
  and clean wheel installation. Test failure paths and PIT/risk boundaries meaningfully.
- Real-data acceptance and fixture acceptance are separate. Network tests are explicit opt-in.
- Narrow fixes, no silent fallback, no destructive overwrites. Reports use unique run directories.
- Update CURRENT_STATE and NEXT_STEPS with measured results and exact blockers before delivery.

## Git
- Verify repository root and remote identity. Stage explicit reviewed paths. Diff-check and scan
  staged files for secrets and runtime data. Commit only self-contained tested changes.
- No reset/clean/force-push/history rewrite, no paid provisioning, no unknown-file replacement.
- GitHub creation must be private as requested. Only push when authentication and ownership
  are verified; verify remote HEAD after success. Invalid authentication is an explicit blocker.
