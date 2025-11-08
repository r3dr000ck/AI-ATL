# python/valuecell_trader/cli.py
"""
Command-line interface for ValueCell AI Trader
"""
import click
from pathlib import Path
import asyncio
import sys

from .app import ValueCellTrader
from .config.schema import create_default_config
from .main import run_backtest_from_config


@click.group()
def cli():
    """ValueCell AI Trader - Command Line Interface"""
    pass


@cli.command()
@click.option(
    "--output",
    "-o",
    type=Path,
    default=Path("config.yaml"),
    help="Output path for configuration file",
)
def init(output: Path):
    """Create a default configuration file"""
    click.echo(f"Creating default configuration at {output}")
    create_default_config(output)
    click.echo(f"✓ Configuration created successfully!")
    click.echo(f"\nEdit {output} to customize your trading strategy.")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=Path,
    default=Path("config.yaml"),
    help="Path to configuration file",
)
def run(config: Path):
    """Run the trader in real-time mode"""
    if not config.exists():
        click.echo(f"Error: Configuration file not found: {config}", err=True)
        click.echo("Create one with: valuecell-trader init", err=True)
        sys.exit(1)

    click.echo("Starting ValueCell AI Trader...")
    click.echo(f"Configuration: {config}")
    click.echo("")

    # Create and run trader
    trader = ValueCellTrader(config)

    try:
        asyncio.run(trader.start_realtime_mode())
    except KeyboardInterrupt:
        click.echo("\n\nShutting down...")
        trader.stop()


@cli.command()
@click.option(
    "--config",
    "-c",
    type=Path,
    default=Path("config.yaml"),
    help="Path to configuration file",
)
def backtest(config: Path):
    """Run a backtest simulation"""
    if not config.exists():
        click.echo(f"Error: Configuration file not found: {config}", err=True)
        sys.exit(1)

    click.echo("Starting backtest...")
    click.echo(f"Configuration: {config}")
    click.echo("")

    # Run backtest
    run_backtest_from_config(config)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=Path,
    default=Path("config.yaml"),
    help="Path to configuration file",
)
def serve(config: Path):
    """Start API server only (no trading loop)"""
    if not config.exists():
        click.echo(f"Error: Configuration file not found: {config}", err=True)
        sys.exit(1)

    click.echo("Starting API server...")
    click.echo("API documentation available at:")
    click.echo("  - http://localhost:8000/docs (main)")
    click.echo("  - http://localhost:8000/execution/docs")
    click.echo("  - http://localhost:8000/scoring/docs")
    click.echo("  - http://localhost:8000/monitor/docs")
    click.echo("")

    from .app import ValueCellTrader

    trader = ValueCellTrader(config)

    # Run only API server
    asyncio.run(trader._run_api_server())


if __name__ == "__main__":
    cli()

# python/valuecell_trader/__main__.py
"""
Make package executable: python -m valuecell_trader
"""
from .cli import cli

if __name__ == "__main__":
    cli()
