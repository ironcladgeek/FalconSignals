"""Backtesting command for historical validation of recommendations."""

from datetime import datetime
from pathlib import Path

import typer
from rich.table import Table

from src.backtesting import BacktestConfig, BacktestEngine
from src.cache.manager import CacheManager
from src.cli.app import app
from src.config import load_config
from src.data.provider_manager import ProviderManager
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def backtest(
    start_date: str = typer.Option(
        ...,
        "--start-date",
        "-s",
        help="Start date of backtest period (YYYY-MM-DD)",
    ),
    end_date: str = typer.Option(
        ...,
        "--end-date",
        "-e",
        help="End date of backtest period (YYYY-MM-DD)",
    ),
    ticker: str = typer.Option(
        ...,
        "--ticker",
        "-t",
        help="Comma-separated list of ticker symbols to analyze",
    ),
    frequency: str = typer.Option(
        "weekly",
        "--frequency",
        "-f",
        help="Analysis frequency: daily, weekly, or monthly",
    ),
    mode: str = typer.Option(
        "rule_based",
        "--mode",
        "-m",
        help="Analysis mode: rule_based or llm",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show plan and cost estimate without executing",
    ),
    skip_confirmation: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt for expensive backtests",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Run backtest across historical date range.

    Generates recommendations for multiple dates to validate system quality.
    Supports both LLM and rule-based analysis modes.

    Examples:
        # Rule-based backtest (free)
        backtest --start-date 2024-01-01 --end-date 2024-12-31 \\
                 --ticker AAPL,MSFT --frequency weekly --mode rule_based

        # LLM backtest with cost estimate
        backtest --start-date 2024-06-01 --end-date 2024-09-01 \\
                 --ticker NVDA --frequency monthly --mode llm --dry-run

        # Daily backtest for single month
        backtest --start-date 2024-11-01 --end-date 2024-11-30 \\
                 --ticker AAPL --frequency daily --mode rule_based
    """
    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)
        logger.info("Starting backtest command")

        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            typer.echo(f"❌ Invalid date format: {e}", err=True)
            typer.echo("   Expected format: YYYY-MM-DD (e.g., 2024-01-15)")
            raise typer.Exit(code=1) from e

        if start > end:
            typer.echo("❌ Error: start_date must be before end_date", err=True)
            raise typer.Exit(code=1)

        # Parse tickers
        tickers = [t.strip().upper() for t in ticker.split(",")]

        # Validate frequency
        if frequency not in ["daily", "weekly", "monthly"]:
            typer.echo(
                f"❌ Invalid frequency: {frequency}. Must be daily, weekly, or monthly",
                err=True,
            )
            raise typer.Exit(code=1)

        # Validate mode
        if mode not in ["rule_based", "llm"]:
            typer.echo(
                f"❌ Invalid mode: {mode}. Must be rule_based or llm",
                err=True,
            )
            raise typer.Exit(code=1)

        # LLM mode requires API key
        if mode == "llm":
            from src.utils.llm_check import check_llm_configuration

            llm_available, llm_message = check_llm_configuration()
            if not llm_available:
                typer.echo(f"❌ LLM mode error: {llm_message}", err=True)
                typer.echo(
                    "   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable",
                    err=True,
                )
                raise typer.Exit(code=1)

        # Initialize database path
        db_path = None
        if config_obj.database.enabled:
            db_path = Path(config_obj.database.db_path)
        else:
            typer.echo("⚠️  Warning: Database is disabled. Results will not be stored.")
            typer.echo("   Enable database in config to store backtest results.\n")

        # Initialize components
        provider_manager = ProviderManager(
            primary_provider=config_obj.data.primary_provider,
            backup_providers=config_obj.data.backup_providers,
            db_path=db_path,
            historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
        )

        cache_manager = CacheManager(
            cache_dir=Path("data/cache"),
        )

        # Load backtesting config
        backtest_config = BacktestConfig()
        if config_obj.backtesting:
            # Convert dict to BacktestConfig
            backtest_config = BacktestConfig(**config_obj.backtesting)

        # Initialize engine
        engine = BacktestEngine(
            config=config_obj,
            backtest_config=backtest_config,
            provider_manager=provider_manager,
            cache_manager=cache_manager,
            db_path=db_path,
        )

        # Display plan
        typer.echo("\n" + "=" * 60)
        typer.echo("📊 BACKTEST PLAN")
        typer.echo("=" * 60)
        typer.echo(f"Date range: {start_date} to {end_date}")
        typer.echo(f"Frequency: {frequency}")
        typer.echo(f"Analysis mode: {mode}")
        typer.echo(f"Tickers: {', '.join(tickers)}")

        # Run dry-run to get estimate
        dry_result = engine.run(
            start_date=start,
            end_date=end,
            tickers=tickers,
            frequency=frequency,
            analysis_mode=mode,
            dry_run=True,
        )

        typer.echo(f"Analysis dates: {len(dry_result.analysis_dates)}")
        typer.echo(f"Total analyses: {dry_result.total_analyses}")

        if mode == "llm" and dry_result.estimated_cost:
            typer.echo(f"Estimated cost: €{dry_result.estimated_cost:.2f}")

            # Check against cost limit
            if (
                backtest_config.llm_cost_limit_per_backtest > 0
                and dry_result.estimated_cost > backtest_config.llm_cost_limit_per_backtest
            ):
                typer.echo(
                    f"\n❌ Error: Estimated cost (€{dry_result.estimated_cost:.2f}) "
                    f"exceeds limit (€{backtest_config.llm_cost_limit_per_backtest:.2f})"
                )
                typer.echo("   Reduce scope (fewer tickers, shorter date range, lower frequency)")
                typer.echo("   Or increase llm_cost_limit_per_backtest in config")
                raise typer.Exit(code=1)

        typer.echo("=" * 60)

        # If dry-run, exit here
        if dry_run:
            typer.echo("\n✅ Dry-run complete. No analysis performed.")
            typer.echo("   Remove --dry-run flag to execute backtest.")
            return

        # Require confirmation for expensive LLM backtests
        if (
            mode == "llm"
            and not skip_confirmation
            and backtest_config.require_confirmation
            and dry_result.estimated_cost
            and dry_result.estimated_cost > backtest_config.cost_confirmation_threshold
        ):
            typer.echo(
                f"\n⚠️  This backtest will cost approximately €{dry_result.estimated_cost:.2f}"
            )
            confirm = typer.confirm("Continue?")
            if not confirm:
                typer.echo("Backtest cancelled.")
                raise typer.Exit(code=0)

        # Execute backtest
        typer.echo("\n🚀 Starting backtest execution...")
        typer.echo(f"   This may take a while ({dry_result.total_analyses} analyses)\n")

        result = engine.run(
            start_date=start,
            end_date=end,
            tickers=tickers,
            frequency=frequency,
            analysis_mode=mode,
            dry_run=False,
        )

        # Display results
        typer.echo("\n" + "=" * 60)
        typer.echo("✅ BACKTEST COMPLETE")
        typer.echo("=" * 60)

        # Create summary table
        from rich.console import Console

        console = Console()

        summary_table = Table(title="Execution Summary", show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Analyses", str(result.total_analyses))
        summary_table.add_row("Successful", str(result.successful_analyses))
        summary_table.add_row("Failed", str(result.failed_analyses))
        summary_table.add_row("Recommendations Generated", str(result.recommendation_count))

        if result.duration_seconds:
            duration_min = result.duration_seconds / 60
            summary_table.add_row("Duration", f"{duration_min:.1f} minutes")

        if mode == "llm" and result.actual_cost:
            summary_table.add_row("Actual Cost", f"€{result.actual_cost:.2f}")
            if result.estimated_cost:
                diff = result.actual_cost - result.estimated_cost
                diff_pct = (diff / result.estimated_cost) * 100
                summary_table.add_row("Cost vs Estimate", f"{diff_pct:+.1f}%")

        console.print(summary_table)

        # Show run session IDs
        if result.run_session_ids:
            typer.echo(f"\n📝 Run Session IDs: {', '.join(map(str, result.run_session_ids))}")
            typer.echo("\n💡 Generate backtest report with:")
            if len(result.run_session_ids) == 1:
                typer.echo(
                    f"   uv run python -m src.main backtest-report "
                    f"--session-id {result.run_session_ids[0]}"
                )
            else:
                typer.echo(
                    f"   uv run python -m src.main backtest-report "
                    f"--start-date {start_date} --end-date {end_date}"
                )

        # Show errors if any
        if result.errors:
            typer.echo(f"\n⚠️  {len(result.errors)} errors occurred:")
            for i, error in enumerate(result.errors[:5], 1):  # Show first 5 errors
                typer.echo(
                    f"   {i}. {error.get('ticker', 'unknown')} "
                    f"on {error.get('date', 'unknown')}: {error.get('error', 'unknown')}"
                )
            if len(result.errors) > 5:
                typer.echo(f"   ... and {len(result.errors) - 5} more")

        typer.echo("\n" + "=" * 60)

        logger.info("Backtest command completed successfully")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error in backtest command: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
