# Architecture

AlphaMosaic is a modular monolith with one authoritative `ApplicationService`. The CLI and
MCP server call that service; they do not implement separate decision logic. Domain contracts
in `core` are Pydantic models and contain provenance, timestamps, data-quality labels and
point-in-time checks.

`providers` implements the `DataProvider` protocol. The OpenBB V5 adapter starts a bounded
worker process and exchanges JSON over stdin/stdout. The worker owns OpenBB configuration in a
repository-local runtime directory and never reads ambient credentials. `screening`, `factors`,
`portfolio`, `backtesting` and `evaluation` contain deterministic research logic. `reporting`
stores unique, schema-validated JSON and Markdown run bundles.

No module can create broker orders. MCP exposes a unified read-only tool surface (plus legacy
aliases) over stdio and opt-in Streamable HTTP. The HTTP app keeps MCP's session-manager lifespan,
requires a bearer token, limits request size and rate, rejects insecure non-local traffic, adds
safe cache headers and optionally writes redacted audit records. It has no arbitrary file, shell,
credential or order surface. AI-generated commentary is not accepted as a market observation.

The portable agent package under `plugins/alphamosaic` contains four skills that call these tools;
the packaged URL remains a deployment placeholder until a real HTTPS ChatGPT connection is tested.
