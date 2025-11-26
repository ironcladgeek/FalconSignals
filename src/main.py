"""NordInvest CLI interface."""

from pathlib import Path

import typer

from src.config import load_config
from src.utils.logging import get_logger, setup_logging

app = typer.Typer(
    name="nordinvest",
    help="AI-powered financial analysis and investment recommendation system",
    no_args_is_help=True,
)

logger = get_logger(__name__)


@app.command()
def run(
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: config/local.yaml or config/default.yaml)",
        exists=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Run analysis without executing trades or sending alerts",
    ),
) -> None:
    """Run daily financial analysis and generate signals.

    Fetches market data, analyzes instruments, and generates investment
    recommendations with confidence scores.
    """
    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        logger.info(f"Starting NordInvest analysis (dry_run={dry_run})")
        logger.info(f"Using config: {config}")
        logger.debug(f"Risk tolerance: {config_obj.risk.tolerance}")
        logger.debug(f"Capital: €{config_obj.capital.starting_capital_eur:,.2f}")

        # Phase 2+ implementation will add actual analysis here
        typer.echo("✓ Configuration loaded successfully")
        typer.echo(f"  Risk tolerance: {config_obj.risk.tolerance}")
        typer.echo(f"  Capital: €{config_obj.capital.starting_capital_eur:,.2f}")
        typer.echo(f"  Monthly deposit: €{config_obj.capital.monthly_deposit_eur:,.2f}")
        typer.echo(f"  Markets: {', '.join(config_obj.markets.included)}")

        if dry_run:
            typer.echo("  [DRY RUN MODE - No trades will be executed]")

        logger.info("Analysis run completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception(f"Unexpected error during analysis run: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def report(
    date: str = typer.Option(
        None,
        "--date",
        "-d",
        help="Generate report for specific date (YYYY-MM-DD format)",
    ),
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Generate report from cached data.

    Creates a report for a specific date using previously cached data,
    without fetching new data from APIs.
    """
    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        logger.info(f"Generating report for date: {date}")

        typer.echo(f"✓ Report configuration loaded")
        if date:
            typer.echo(f"  Date: {date}")
        typer.echo(f"  Format: {config_obj.output.report_format}")

        # Phase 4+ implementation will add actual report generation here
        logger.info("Report generation completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception(f"Unexpected error during report generation: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def config_init(
    output: Path = typer.Option(
        Path("config/local.yaml"),
        "--output",
        "-o",
        help="Output path for local configuration file",
    ),
) -> None:
    """Initialize local configuration from template.

    Creates a local.yaml file based on the default.yaml template
    that you can customize for your preferences.
    """
    try:
        project_root = Path(__file__).parent.parent
        default_config = project_root / "config" / "default.yaml"

        if not default_config.exists():
            typer.echo(f"❌ Default config not found: {default_config}", err=True)
            raise typer.Exit(code=1)

        # Read default config
        with open(default_config, "r") as f:
            default_content = f.read()

        # Create output directory
        output.parent.mkdir(parents=True, exist_ok=True)

        # Write local config
        with open(output, "w") as f:
            f.write(default_content)

        logger.info(f"Local configuration initialized: {output}")
        typer.echo(f"✓ Configuration template created: {output}")
        typer.echo("  Please edit this file with your preferences")

    except Exception as e:
        logger.exception(f"Error initializing configuration: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def validate_config(
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Validate configuration file.

    Loads and validates the configuration without running analysis,
    useful for checking configuration before deployment.
    """
    try:
        config_obj = load_config(config)

        typer.echo("✓ Configuration is valid")
        typer.echo(f"  Risk tolerance: {config_obj.risk.tolerance}")
        typer.echo(f"  Capital: €{config_obj.capital.starting_capital_eur:,.2f}")
        typer.echo(f"  Markets: {', '.join(config_obj.markets.included)}")
        typer.echo(f"  Instruments: {', '.join(config_obj.markets.included_instruments)}")
        typer.echo(f"  Buy threshold: {config_obj.analysis.buy_threshold}")
        typer.echo(f"  Cost limit: €{config_obj.deployment.cost_limit_eur_per_month:.2f}/month")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception(f"Unexpected error validating configuration: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.callback()
def version_callback(
    version: bool = typer.Option(None, "--version", "-v", help="Show version and exit"),
) -> None:
    """Show version information."""
    if version:
        typer.echo("NordInvest v0.1.0")
        raise typer.Exit()


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
