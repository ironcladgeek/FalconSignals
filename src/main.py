"""NordInvest CLI interface."""

import time
from pathlib import Path

import typer

from src.cache.manager import CacheManager
from src.config import load_config
from src.data.portfolio import PortfolioState
from src.MARKET_TICKERS import get_tickers_for_markets
from src.pipeline import AnalysisPipeline
from src.utils.llm_check import get_fallback_warning_message, log_llm_status
from src.utils.logging import get_logger, setup_logging
from src.utils.scheduler import RunLog

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
    output_format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Report format: markdown or json",
    ),
    save_report: bool = typer.Option(
        True,
        "--save-report/--no-save-report",
        help="Save report to disk",
    ),
) -> None:
    """Run daily financial analysis and generate signals.

    Fetches market data, analyzes instruments, and generates investment
    recommendations with confidence scores.
    """
    start_time = time.time()
    run_log = None
    signals_count = 0
    error_occurred = False

    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        # Check LLM configuration and warn if using fallback mode
        llm_configured = log_llm_status()

        # Initialize run log
        data_dir = Path("data")
        run_log = RunLog(data_dir / "runs.jsonl")

        logger.info(f"Starting NordInvest analysis (dry_run={dry_run})")
        logger.info(f"Using config: {config}")
        logger.debug(f"Risk tolerance: {config_obj.risk.tolerance}")
        logger.debug(f"Capital: €{config_obj.capital.starting_capital_eur:,.2f}")

        typer.echo("✓ Configuration loaded successfully")
        typer.echo(f"  Risk tolerance: {config_obj.risk.tolerance}")
        typer.echo(f"  Capital: €{config_obj.capital.starting_capital_eur:,.2f}")
        typer.echo(f"  Monthly deposit: €{config_obj.capital.monthly_deposit_eur:,.2f}")
        typer.echo(f"  Markets: {', '.join(config_obj.markets.included)}")

        if not llm_configured:
            typer.echo("\n" + get_fallback_warning_message())

        if dry_run:
            typer.echo("  [DRY RUN MODE - No trades will be executed]")

        # Initialize pipeline
        typer.echo("\n⏳ Initializing analysis pipeline...")
        cache_manager = CacheManager(str(data_dir / "cache"))
        portfolio_manager = PortfolioState(data_dir / "portfolio_state.json")

        pipeline_config = {
            "capital_starting": config_obj.capital.starting_capital_eur,
            "capital_monthly_deposit": config_obj.capital.monthly_deposit_eur,
            "max_position_size_pct": 10.0,
            "max_sector_concentration_pct": 20.0,
            "include_disclaimers": True,
        }

        pipeline = AnalysisPipeline(pipeline_config, cache_manager, portfolio_manager)

        # Run analysis on sample tickers (for demonstration)
        # tickers = ["AAPL", "MSFT", "GOOGL"][:2]  # Limit to 2 for testing
        tickers = get_tickers_for_markets(["us"], limit=50)
        typer.echo(f"\n📊 Running analysis on {len(tickers)} instruments...")

        signals, portfolio_manager = pipeline.run_analysis(tickers)
        signals_count = len(signals)

        if signals:
            typer.echo(f"✓ Analysis complete: {signals_count} signals generated")

            # Generate report
            typer.echo("\n📋 Generating report...")
            report = pipeline.generate_daily_report(
                signals,
                generate_allocation=True,
            )

            # Display summary
            typer.echo(f"\n📈 Report Summary:")
            typer.echo(f"  Strong signals: {report.strong_signals_count}")
            typer.echo(f"  Moderate signals: {report.moderate_signals_count}")
            typer.echo(f"  Total analyzed: {report.total_signals_generated}")

            if report.allocation_suggestion:
                typer.echo(
                    f"  Diversification score: {report.allocation_suggestion.diversification_score}%"
                )
                typer.echo(
                    f"  Recommended allocation: €{report.allocation_suggestion.total_allocated:,.0f}"
                )

            # Save report if requested
            if save_report:
                reports_dir = data_dir / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)

                if output_format == "markdown":
                    report_path = reports_dir / f"report_{report.report_date}.md"
                    report_content = pipeline.report_generator.to_markdown(report)
                    with open(report_path, "w") as f:
                        f.write(report_content)
                    typer.echo(f"  Report saved: {report_path}")
                else:
                    report_path = reports_dir / f"report_{report.report_date}.json"
                    import json

                    with open(report_path, "w") as f:
                        json.dump(pipeline.report_generator.to_json(report), f, indent=2)
                    typer.echo(f"  Report saved: {report_path}")
        else:
            typer.echo("⚠️  No signals generated from analysis")

        duration = time.time() - start_time
        logger.info(f"Analysis run completed successfully in {duration:.2f}s")
        typer.echo(f"\n✓ Analysis completed in {duration:.2f}s")

        # Log the run
        if run_log:
            run_log.log_run(
                success=True,
                duration_seconds=duration,
                signal_count=signals_count,
            )

    except FileNotFoundError as e:
        error_occurred = True
        logger.error(f"Configuration error: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        if run_log:
            duration = time.time() - start_time
            run_log.log_run(
                success=False,
                duration_seconds=duration,
                signal_count=signals_count,
                error_message=str(e),
            )
        raise typer.Exit(code=1)
    except ValueError as e:
        error_occurred = True
        logger.error(f"Configuration validation error: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        if run_log:
            duration = time.time() - start_time
            run_log.log_run(
                success=False,
                duration_seconds=duration,
                signal_count=signals_count,
                error_message=str(e),
            )
        raise typer.Exit(code=1)
    except Exception as e:
        error_occurred = True
        logger.exception(f"Unexpected error during analysis run: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        if run_log:
            duration = time.time() - start_time
            run_log.log_run(
                success=False,
                duration_seconds=duration,
                signal_count=signals_count,
                error_message=str(e),
            )
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
