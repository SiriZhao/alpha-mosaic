"""Consistent CLI over ApplicationService."""

import json
from pathlib import Path

import typer

from alphamosaic.core.contracts import Status
from alphamosaic.core.service import ApplicationService
from alphamosaic.providers.openbb import OpenBBDataProvider
from alphamosaic.screening.universe import UniverseManager

app = typer.Typer(no_args_is_help=True, help="AlphaMosaic: research only, no broker execution")
mcp_app = typer.Typer(no_args_is_help=True)
app.add_typer(mcp_app, name="mcp")


def output(value: object) -> None:
    typer.echo(json.dumps(value, indent=2, allow_nan=False, default=str))


@app.command()
def doctor() -> None:
    """Installation health, market calendar and permissions (no live network probe)."""
    output(ApplicationService().status())


@app.command("research-demo")
def research_demo(sessions: int = typer.Option(504, min=80, max=2000), seed: int = 42) -> None:
    """Register clearly labelled synthetic data without network access."""
    output(ApplicationService().research_demo(sessions, seed))


@app.command("experiment")
def run_experiment(config: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Run a bounded local experiment from a versioned JSON configuration."""
    result = ApplicationService().research_experiment(json.loads(config.read_text(encoding="utf-8")))
    output({k: result.get(k) for k in ("experiment_id", "status", "acceptance", "analysis", "error")})
    if result["status"] != "COMPLETED":
        raise typer.Exit(1)


@app.command("experiments")
def research_experiments() -> None:
    """List successful, interrupted and failed local experiments."""
    output(ApplicationService().research_experiments())


@app.command()
def providers() -> None:
    """Installed provider capabilities and availability boundaries."""
    output(ApplicationService().providers())


@app.command()
def integrations() -> None:
    """List upstream and commercial integration status without making network calls."""
    output(ApplicationService().integrations())


@app.command()
def frameworks() -> None:
    """Audit external framework maturity without installing optional dependencies."""
    output(ApplicationService().framework_matrix())


@app.command()
def research(
    symbols: str,
    profile: str = typer.Option("FAST", case_sensitive=False),
) -> None:
    """Run bounded multi-source research for up to five screened candidates."""
    try:
        result = ApplicationService().research([item.strip().upper() for item in symbols.split(",")], profile.upper())
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    output({"research_only": True, "broker_enabled": False, "profile": profile.upper(), "decisions": result})


@app.command()
def scan(
    universe_limit: int = typer.Option(30, min=1, max=100),
    top: int = typer.Option(10, min=1, max=10),
    symbols: str | None = None,
    universe_file: Path | None = typer.Option(None, exists=True, dir_okay=False),
    evaluate: bool = True,
    strata_json: str | None = None,
) -> None:
    """Discover a live US pool or use an explicit list; save JSON/Markdown research."""
    if sum(value is not None for value in (symbols, universe_file, strata_json)) > 1:
        raise typer.BadParameter("choose symbols or universe-file")
    service = ApplicationService()
    try:
        universe = (
            UniverseManager(service.provider).imported(universe_file) if universe_file else None
        )
        if strata_json:
            strata = json.loads(strata_json)
            if not isinstance(strata, dict) or any(not isinstance(values, list) or any(not isinstance(symbol, str) for symbol in values) for values in strata.values()):
                raise ValueError("strata-json must map style names to symbol arrays")
            universe = UniverseManager(service.provider).stratified(strata, universe_limit)
        report = service.scan(
            universe_limit,
            top,
            symbols.split(",") if symbols is not None else None,
            universe,
            evaluate=evaluate,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    output(
        {
            "report_directory": str(service.store.root / report.run_id),
            **report.model_dump(mode="json"),
        }
    )
    if report.status == Status.EMPTY:
        raise typer.Exit(2)


@app.command()
def opportunities(
    mode: str = typer.Option("FAST", case_sensitive=False),
    universe_limit: int = typer.Option(30, min=1, max=100),
    top: int = typer.Option(10, min=1, max=10),
    deep: int = typer.Option(3, min=1, max=3),
    pool: str = typer.Option("BROAD_LIQUIDITY"),
    symbols: str | None = None,
    resume: bool = typer.Option(False, help="Resume the same-day checkpoint when available"),
) -> None:
    """Run bounded universe discovery, ranking and optional top-three research."""
    try:
        result = ApplicationService().discover_opportunities(
            mode.upper(), universe_limit, top, deep, pool.upper(),
            [x.strip().upper() for x in symbols.split(",")] if symbols else None,
            resume,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    output(result)


@app.command()
def analyze(symbol: str, fundamentals: bool = False) -> None:
    """Get an evidence-labelled stock snapshot; optionally fetch financial statements."""
    service = ApplicationService()
    if fundamentals:
        service = ApplicationService(
            service.home, OpenBBDataProvider(service.home, fundamentals=True)
        )
    try:
        result = service.analyze(symbol)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    output(result)
    if result["status"] != "OK":
        raise typer.Exit(2)


@app.command()
def strategies() -> None:
    """List transparent research baselines and unconfigured engine status."""
    from alphamosaic.backtesting.strategies import StrategyRegistry
    from alphamosaic.integrations.lean import LeanAdapter

    output({"strategies": StrategyRegistry().list(), "lean": LeanAdapter().health()})


@app.command()
def backtest(symbols: str, strategy: str = "momentum", fee_bps: float = 10, slippage_bps: float = 5, out_of_sample: bool = True) -> None:
    """Run a sourced reconstructed-history replay; no alpha certification."""
    output(ApplicationService().run_backtest(symbols, strategy, out_of_sample, fee_bps, slippage_bps))


@app.command()
def forward_init(initial_cash: float = 100_000) -> None:
    """Initialize a separate empty paper record; idempotent, no fills."""
    output(ApplicationService().initialize_forward(initial_cash))


@app.command("forward-evaluate")
def forward_evaluate(signal_id: str) -> None:
    """Evaluate one frozen signal using newly fetched provider observations."""
    output(ApplicationService().evaluate_forward(signal_id))


@app.command()
def report(run_id: str | None = None, finalize: bool = False) -> None:
    """Query the latest validated local report (no new request)."""
    service = ApplicationService()
    if finalize:
        if run_id is None:
            raise typer.BadParameter("finalize requires explicit run-id")
        output({"report_directory": str(service.store.finalize(run_id))})
    else:
        result = service.store.get(run_id) if run_id else service.store.latest()
        output(result.model_dump(mode="json") if result else {"status": "NO_REPORT"})


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Serve the six bounded read-only tools over local stdio."""
    from alphamosaic.mcp.server import create_server

    create_server().run(transport="stdio")


if __name__ == "__main__":
    app()
