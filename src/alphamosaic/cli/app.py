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


@app.command()
def providers() -> None:
    """Installed provider capabilities and availability boundaries."""
    output(ApplicationService().providers())


@app.command()
def integrations() -> None:
    """List upstream and commercial integration status without making network calls."""
    output(ApplicationService().integrations())


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
) -> None:
    """Discover a live US pool or use an explicit list; save JSON/Markdown research."""
    if symbols is not None and universe_file is not None:
        raise typer.BadParameter("choose symbols or universe-file")
    service = ApplicationService()
    try:
        universe = (
            UniverseManager(service.provider).imported(universe_file) if universe_file else None
        )
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
def report() -> None:
    """Query the latest validated local report (no new request)."""
    output(ApplicationService().latest_report())


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Serve the six bounded read-only tools over local stdio."""
    from alphamosaic.mcp.server import create_server

    create_server().run(transport="stdio")


if __name__ == "__main__":
    app()
