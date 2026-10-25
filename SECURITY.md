# Research-only security boundary

Bounded research workers execute a fixed module from a trusted package directory; the writable research home is never the child module-search working directory. The environment passes only required OS/runtime settings and an explicit trusted package path, not market/model credentials. Native OS leases coordinate new experiment entrypoints across processes. Existing path redirection through symlinks/junctions is rejected before opening plan databases, leases or request/response artifacts. Windows junction regression uses only isolated repository test directories and may require permission to construct the test fixture in a sandbox.

These local checks and hash chains are for a single-user research environment, not multi-tenant authentication or proof against a hostile filesystem writer racing all checks. Interrupted records do not establish liveness and are never automatically rerun. Worker timeouts, process-exit failures, missing responses and audit inconsistencies remain explicit outcomes. No tests weaken financial assertions to accept these failures.

No live orders, broker connectors, account credentials, portfolio synchronization or real-money execution tools. MCP accepts typed research parameters and identifiers; it offers no arbitrary shell, arbitrary file reader, credential accessor or unreviewed source-code execution. Optional LEAN is an operator-only local backtest boundary. Never connect it to a live brokerage.

AlphaMosaic is independent of Meridian Alpha and must not read its credentials or alter its files. Provider workers use isolated local runtime configuration. Optional LLM/commercial authorization is operator-managed; missing credentials remain NOT_CONFIGURED. No paid provisioning is automatic.

Local terminal binds to127.0.0.1 and is not an authenticated multi-user product. Do not expose it publicly. Existing remote MCP requires bearer authentication and operator-managed HTTPS; local protocol tests do not certify an internet deployment. Danelfin lifecycle cancellation releases owned resources and preserves external cancellation; regression tests treat leaked-coroutine RuntimeWarnings as errors.

Identifiers and artifact paths are bounded; replay revalidates all input schemas. Dataset snapshots are immutable, quarantine cannot replay, experiment hashes/required files detect corruption, and interrupted/failed work remains visible. These hashes provide local integrity checks, not tamperproof external notarization.

Keep runtime/market data, .env, credentials and private financial records ignored. The existing GitHub repository is public; visibility has not been changed. Scan tracked and nonignored files with `python scripts/secret_scan.py`, then staged blobs with `--staged`. This lightweight regex scanner is a defense layer, not proof that no secret exists. Review explicit staged paths and diffs before publishing.

Dependency review on2026-10-24 found OSV advisories for certifi2026.7.22 and Pillow12.3.0. Lock/minimum requirements were updated to certifi>=2026.10.19 and Pillow>=13 where image-bearing extras are used. Original findings and final audit status are recorded in delivery evidence; no vulnerability ignore list is added. [certifi upstream advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2), [Pillow security](https://github.com/python-pillow/Pillow/security).

Report vulnerabilities privately to the repository maintainer through an available private security channel; do not paste credentials, account data or exploit payloads into public issues. No security contact endpoint is invented here.
