"""Explicit inventory of upstream and commercial research resources."""

from importlib.metadata import PackageNotFoundError, version

from alphamosaic.core.contracts import IntegrationRecord, IntegrationStatus, Status


def _installed(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


class IntegrationRegistry:
    def records(self) -> list[IntegrationRecord]:
        openbb = _installed("openbb-core")
        agents = _installed("tradingagents")
        danelfin_configured = bool(__import__("os").environ.get("DANELFIN_API_KEY"))
        return [
            IntegrationRecord(
                name="OpenBB",
                official_url="https://github.com/openbq-org/OpenBB",
                version=openbb or "2.0.1 (optional pin)",
                license="Apache-2.0 core; provider terms apply",
                interface="Python adapter / isolated worker",
                authentication="Provider-specific; Nasdaq public endpoint selected",
                runtime_cost="Network latency; no AlphaMosaic paid provisioning",
                data_limits="Website terms, quota and adjustment/PIT limits",
                capabilities=["US_UNIVERSE", "HISTORICAL_OHLCV", "PROFILE", "FUNDAMENTALS"],
                status=IntegrationStatus.ACTIVE if openbb else IntegrationStatus.READY_UNCONFIGURED,
                connection_status=Status.OK if openbb else Status.NOT_INSTALLED,
                test_status="LIVE_AAPL_ACCEPTED" if openbb else "NOT_RUN",
                diagnostics=["Provider health is separate from signal validity"],
            ),
            IntegrationRecord(
                name="TradingAgents",
                official_url="https://github.com/TauricResearch/TradingAgents",
                version=agents or "0.6.0 (optional pin)",
                license="Upstream repository license; review before redistribution",
                interface="Official Python API in isolated worker",
                authentication="LLM and data-provider keys via environment variables",
                runtime_cost="FAST/BALANCED/DEEP bounded model calls",
                data_limits="Provider quotas, model context and upstream source terms",
                capabilities=["FUNDAMENTAL", "TECHNICAL", "NEWS", "SENTIMENT", "DEBATE", "RISK"],
                status=IntegrationStatus.ACTIVE if agents else IntegrationStatus.READY_UNCONFIGURED,
                connection_status=Status.OK if agents else Status.NOT_CONFIGURED,
                test_status="NOT_RUN_NO_MODEL_AUTH" if not agents else "INSTALLATION_ONLY",
                diagnostics=["No order or ledger authority is exposed"],
            ),
            IntegrationRecord(
                name="Danelfin",
                official_url="https://mcp.danelfin.com/docs/en",
                version=None,
                license="Commercial service terms",
                interface="Official remote MCP over HTTP",
                authentication="DANELFIN_API_KEY environment variable",
                runtime_cost="Quota and subscription dependent",
                data_limits="Plan calls/rate limits; daily history since 2017 subject to API terms",
                capabilities=["AI_SCORE", "RANKING", "DAILY_HISTORY", "SUBSCORES", "FILTER"],
                status=IntegrationStatus.ACTIVE if danelfin_configured else IntegrationStatus.READY_UNCONFIGURED,
                connection_status=Status.OK if danelfin_configured else Status.NOT_CONFIGURED,
                test_status="NOT_RUN_NO_CREDENTIAL" if not danelfin_configured else "NOT_RUN",
                diagnostics=["Score is research evidence, never an unconditional return probability"],
            ),
            IntegrationRecord(
                name="AI Hedge Fund",
                official_url="https://github.com/virattt/ai-hedge-fund",
                version=None,
                license="Upstream repository terms; not connected",
                interface="Repository / CLI",
                authentication="Provider-specific",
                runtime_cost="Model and data-provider dependent",
                data_limits="No stable AlphaMosaic adapter verified",
                capabilities=["MULTI_AGENT_RESEARCH"],
                status=IntegrationStatus.EXPERIMENTAL,
                connection_status=Status.UNSUPPORTED,
                test_status="NOT_RUN",
                diagnostics=["Manual import only until a stable official API is verified"],
            ),
            IntegrationRecord(
                name="FINVIZ",
                official_url="https://finviz.com/",
                version=None,
                license="Commercial website terms",
                interface="No approved API connected",
                authentication="Commercial account if licensed",
                runtime_cost="Unknown",
                data_limits="No scraping; no redistribution assumed",
                capabilities=["SCREENING"],
                status=IntegrationStatus.LICENSE_BLOCKED,
                connection_status=Status.UNSUPPORTED,
                test_status="NOT_RUN",
                diagnostics=["Use legal file import when user supplies data"],
            ),
            IntegrationRecord(
                name="TradingView",
                official_url="https://www.tradingview.com/",
                version=None,
                license="Commercial service terms",
                interface="No approved API connected",
                authentication="Commercial account if licensed",
                runtime_cost="Unknown",
                data_limits="No scraping or redistribution assumed",
                capabilities=["CHARTS", "ALERTS"],
                status=IntegrationStatus.LICENSE_BLOCKED,
                connection_status=Status.UNSUPPORTED,
                test_status="NOT_RUN",
                diagnostics=["Manual export/import only"],
            ),
            IntegrationRecord(
                name="TIKR",
                official_url="https://www.tikr.com/",
                version=None,
                license="Commercial service terms",
                interface="No approved API connected",
                authentication="Commercial account if licensed",
                runtime_cost="Unknown",
                data_limits="No scraping or redistribution assumed",
                capabilities=["FUNDAMENTALS", "ESTIMATES"],
                status=IntegrationStatus.LICENSE_BLOCKED,
                connection_status=Status.UNSUPPORTED,
                test_status="NOT_RUN",
                diagnostics=["Manual export/import only"],
            ),
            IntegrationRecord(
                name="Seeking Alpha",
                official_url="https://seekingalpha.com/",
                version=None,
                license="Commercial service terms",
                interface="No approved API connected",
                authentication="Commercial account if licensed",
                runtime_cost="Unknown",
                data_limits="No scraping or redistribution assumed",
                capabilities=["NEWS", "ESTIMATES", "SENTIMENT"],
                status=IntegrationStatus.LICENSE_BLOCKED,
                connection_status=Status.UNSUPPORTED,
                test_status="NOT_RUN",
                diagnostics=["Manual export/import only"],
            ),
        ]
