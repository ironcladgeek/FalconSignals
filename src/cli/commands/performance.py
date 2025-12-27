"""Performance tracking and reporting commands."""

from datetime import date
from pathlib import Path

import typer

from src.cli.app import app
from src.config import load_config
from src.data.provider_manager import ProviderManager
from src.data.repository import PerformanceRepository
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def track_performance(
    max_age_days: int = typer.Option(
        180,
        "--max-age",
        "-m",
        help="Maximum age of recommendations to track (in days)",
    ),
    signal_types: str = typer.Option(
        "buy,strong_buy",
        "--signals",
        "-s",
        help="Comma-separated list of signal types to track",
    ),
    benchmark: str = typer.Option(
        "SPY",
        "--benchmark",
        "-b",
        help="Benchmark ticker symbol for comparison",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Track performance of active recommendations.

    Fetches current prices for all active recommendations and stores
    them for performance analysis. This should be run daily to maintain
    accurate performance tracking.

    Examples:
        track-performance
        track-performance --max-age 90
        track-performance --signals buy,strong_buy,hold
        track-performance --benchmark QQQ
    """
    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)
        logger.info("Starting performance tracking")

        db_path = Path(
            config_obj.database.db_path if config_obj.database.enabled else "data/falconsignals.db"
        )

        # Initialize repositories
        perf_repo = PerformanceRepository(db_path)
        provider_manager = ProviderManager(
            primary_provider=config_obj.data.primary_provider,
            backup_providers=config_obj.data.backup_providers,
            db_path=db_path,
            historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
        )

        # Parse signal types
        signal_list = [s.strip() for s in signal_types.split(",")]

        # Get active recommendations
        typer.echo("\n📊 Fetching active recommendations...")
        recommendations = perf_repo.get_active_recommendations(
            max_age_days=max_age_days, signal_types=signal_list
        )

        if not recommendations:
            typer.echo("  No active recommendations found to track")
            return

        typer.echo(f"  Found {len(recommendations)} active recommendations")

        # Track prices
        tracked_count = 0
        failed_count = 0
        today = date.today()

        typer.echo(f"\n⏳ Tracking prices (benchmark: {benchmark})...")

        for rec in recommendations:
            try:
                # Get ticker symbol
                ticker_symbol = rec.ticker_obj.symbol if rec.ticker_obj else None
                if not ticker_symbol:
                    logger.warning(f"Skipping recommendation {rec.id}: no ticker symbol")
                    failed_count += 1
                    continue

                # Fetch current price
                price_obj = provider_manager.get_latest_price(ticker_symbol)
                if not price_obj:
                    logger.warning(f"No price data for {ticker_symbol}")
                    failed_count += 1
                    continue

                current_price = price_obj.close_price

                # Fetch benchmark price
                benchmark_price = None
                benchmark_obj = provider_manager.get_latest_price(benchmark)
                if benchmark_obj:
                    benchmark_price = benchmark_obj.close_price

                # Track the price
                success = perf_repo.track_price(
                    recommendation_id=rec.id,
                    tracking_date=today,
                    price=current_price,
                    benchmark_price=benchmark_price,
                    benchmark_ticker=benchmark,
                )

                if success:
                    tracked_count += 1
                    logger.debug(f"Tracked {ticker_symbol}: ${current_price:.2f}")
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error tracking recommendation {rec.id}: {e}")
                failed_count += 1

        # Summary
        typer.echo("\n✅ Performance tracking complete:")
        typer.echo(f"  Tracked: {tracked_count} recommendations")
        if failed_count > 0:
            typer.echo(f"  Failed: {failed_count} recommendations")

        logger.info(
            f"Performance tracking complete: {tracked_count} tracked, {failed_count} failed"
        )

    except Exception as e:
        logger.error(f"Error in performance tracking: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def performance_report(
    period: int = typer.Option(
        30,
        "--period",
        "-p",
        help="Tracking period in days (7, 30, 90, 180)",
    ),
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Filter by ticker symbol",
    ),
    signal_type: str = typer.Option(
        None,
        "--signal",
        "-s",
        help="Filter by signal type (buy, strong_buy, etc.)",
    ),
    analysis_mode: str = typer.Option(
        None,
        "--mode",
        "-m",
        help="Filter by analysis mode (rule_based, llm)",
    ),
    update_summary: bool = typer.Option(
        True,
        "--update/--no-update",
        help="Update performance summary before generating report",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text or json",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Generate performance report for recommendations.

    Shows aggregated performance metrics including returns, win rate,
    alpha vs benchmark, and confidence calibration.

    Examples:
        performance-report
        performance-report --period 90
        performance-report --ticker AAPL
        performance-report --signal buy --mode llm
        performance-report --format json
    """
    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)
        logger.info("Generating performance report")

        db_path = Path(
            config_obj.database.db_path if config_obj.database.enabled else "data/falconsignals.db"
        )

        # Initialize repository
        perf_repo = PerformanceRepository(db_path)

        # Update performance summary if requested
        if update_summary:
            typer.echo("\n⏳ Updating performance summary...")
            success = perf_repo.update_performance_summary(
                ticker_id=None,  # Will be resolved from ticker symbol
                signal_type=signal_type,
                analysis_mode=analysis_mode,
                period_days=period,
            )
            if not success:
                typer.echo("  ⚠️  Warning: Failed to update performance summary")

        # Generate report
        typer.echo(f"\n📊 Generating performance report (period: {period} days)...")
        report = perf_repo.get_performance_report(
            ticker_symbol=ticker,
            signal_type=signal_type,
            analysis_mode=analysis_mode,
            period_days=period,
        )

        if not report or "message" in report:
            typer.echo(f"\n  {report.get('message', 'No performance data available')}")
            return

        # Display report
        if format == "json":
            import json

            typer.echo("\n" + json.dumps(report, indent=2))
        else:
            # Text format
            typer.echo("\n" + "=" * 60)
            typer.echo("📈 PERFORMANCE REPORT")
            typer.echo("=" * 60)

            typer.echo(f"\n📅 Period: {period} days")
            if ticker:
                typer.echo(f"🎯 Ticker: {ticker}")
            if signal_type:
                typer.echo(f"📊 Signal Type: {signal_type}")
            if analysis_mode:
                typer.echo(f"🤖 Analysis Mode: {analysis_mode}")

            typer.echo(f"\n📦 Total Recommendations: {report.get('total_recommendations', 0)}")

            typer.echo("\n💰 Returns:")
            avg_return = report.get("avg_return")
            if avg_return is not None:
                typer.echo(f"  Average Return: {avg_return:+.2f}%")
            median_return = report.get("median_return")
            if median_return is not None:
                typer.echo(f"  Median Return: {median_return:+.2f}%")

            win_rate = report.get("win_rate")
            if win_rate is not None:
                typer.echo(f"\n🎯 Win Rate: {win_rate:.1f}%")

            avg_alpha = report.get("avg_alpha")
            if avg_alpha is not None:
                typer.echo(f"\n📊 Alpha (vs SPY): {avg_alpha:+.2f}%")

            sharpe_ratio = report.get("sharpe_ratio")
            if sharpe_ratio is not None:
                typer.echo(f"\n⚖️  Sharpe Ratio: {sharpe_ratio:.2f}")

            max_drawdown = report.get("max_drawdown")
            if max_drawdown is not None:
                typer.echo(f"📉 Max Drawdown: {max_drawdown:.2f}%")

            avg_confidence = report.get("avg_confidence")
            calibration_error = report.get("calibration_error")
            if avg_confidence is not None and calibration_error is not None:
                typer.echo("\n🎲 Confidence Calibration:")
                typer.echo(f"  Average Confidence: {avg_confidence:.1f}%")
                typer.echo(f"  Calibration Error: {calibration_error:.1f}%")

            typer.echo("\n" + "=" * 60)

        logger.info("Performance report generated successfully")

    except Exception as e:
        logger.error(f"Error generating performance report: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
