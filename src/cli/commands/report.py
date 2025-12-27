"""Report generation command for FalconSignals CLI."""

import json
from datetime import datetime
from pathlib import Path

import typer

from src.cache.manager import CacheManager
from src.cli.app import app
from src.config import load_config
from src.data.db import init_db
from src.data.portfolio import PortfolioState
from src.data.provider_manager import ProviderManager
from src.data.repository import RecommendationsRepository
from src.pipeline import AnalysisPipeline
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def report(
    session_id: int | None = typer.Option(
        None, "--session-id", help="Generate report from run session ID (integer)"
    ),
    date: str | None = typer.Option(
        None, "--date", help="Generate report for specific date (YYYY-MM-DD)"
    ),
    analysis_mode: str | None = typer.Option(
        None,
        "--analysis-mode",
        help="Filter by analysis mode: 'llm' or 'rule_based'",
    ),
    signal_type: str | None = typer.Option(
        None,
        "--signal-type",
        help=(
            "Filter by signal type: 'strong_buy', 'buy', 'hold_bullish', 'hold', 'hold_bearish', "
            "'sell', 'strong_sell'"
        ),
    ),
    confidence_threshold: float | None = typer.Option(
        None,
        "--confidence-threshold",
        help="Minimum confidence score (e.g., 70 means confidence > 70)",
    ),
    final_score_threshold: float | None = typer.Option(
        None,
        "--final-score-threshold",
        help="Minimum final score (e.g., 70 means final_score > 70)",
    ),
    output_format: str = typer.Option(
        "markdown", "--format", help="Output format: markdown or json"
    ),
    save_report: bool = typer.Option(
        True, "--save/--no-save", help="Save report to file (default: save)"
    ),
    config: str = typer.Option(
        "config/local.yaml",
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Generate report from stored database results.

    Load investment signals from the database and regenerate reports.
    You can specify either a run session ID or a date.

    Examples:
        # Generate report from a specific session
        report --session-id 123

        # Generate report for all signals from a specific date
        report --date 2025-12-04

        # Filter by analysis mode
        report --date 2025-12-04 --analysis-mode llm

        # Filter by signal type
        report --date 2025-12-04 --signal-type strong_buy

        # Filter by confidence threshold
        report --date 2025-12-04 --confidence-threshold 70

        # Combine multiple filters
        report --date 2025-12-04 --analysis-mode llm --confidence-threshold 80 --signal-type buy

        # Generate JSON report instead of markdown
        report --session-id 123 --format json
    """
    try:
        # Validate inputs
        if not session_id and not date:
            typer.echo("❌ Error: Must specify either --session-id or --date", err=True)
            typer.echo("Examples:", err=True)
            typer.echo("  report --session-id 02a27c22-a123-4378-8654-95c592a66e2f", err=True)
            typer.echo("  report --date 2025-12-04", err=True)
            raise typer.Exit(code=1)

        if session_id and date:
            typer.echo(
                "❌ Error: Cannot specify both --session-id and --date. Choose one.", err=True
            )
            raise typer.Exit(code=1)

        # Validate date format if provided
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError as e:
                typer.echo(f"❌ Error: Invalid date format '{date}'. Use YYYY-MM-DD", err=True)
                raise typer.Exit(code=1) from e

        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        # Check if database is enabled
        if not config_obj.database.enabled:
            typer.echo(
                "❌ Error: Database is not enabled in configuration.\n"
                "   Enable database in config file to use historical reports.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Initialize database
        init_db(config_obj.database.db_path)
        logger.debug(f"Database initialized at {config_obj.database.db_path}")

        typer.echo("📊 Generating report from database...")
        if session_id:
            typer.echo(f"  Session ID: {session_id}")
        else:
            typer.echo(f"  Date: {date}")

        # Display active filters
        filters_applied = []
        if analysis_mode:
            filters_applied.append(f"analysis_mode={analysis_mode}")
        if signal_type:
            filters_applied.append(f"signal_type={signal_type}")
        if confidence_threshold is not None:
            filters_applied.append(f"confidence>{confidence_threshold}")
        if final_score_threshold is not None:
            filters_applied.append(f"final_score>{final_score_threshold}")

        if filters_applied:
            typer.echo(f"  Filters: {', '.join(filters_applied)}")

        # Initialize components
        data_dir = Path("data")
        cache_manager = CacheManager(str(data_dir / "cache"))
        portfolio_manager = PortfolioState(data_dir / "portfolio_state.json")

        # Initialize provider manager for price lookups
        provider_manager = ProviderManager(
            primary_provider=config_obj.data.primary_provider,
            backup_providers=config_obj.data.backup_providers,
            db_path=config_obj.database.db_path if config_obj.database.enabled else None,
            historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
        )

        # Load filtered signals from database
        repo = RecommendationsRepository(config_obj.database.db_path)

        if session_id:
            signals = repo.get_recommendations_by_session(
                run_session_id=session_id,
                analysis_mode=analysis_mode,
                signal_type=signal_type,
                confidence_threshold=confidence_threshold,
                final_score_threshold=final_score_threshold,
            )
        else:
            signals = repo.get_recommendations_by_date(
                report_date=date,
                analysis_mode=analysis_mode,
                signal_type=signal_type,
                confidence_threshold=confidence_threshold,
                final_score_threshold=final_score_threshold,
            )

        if not signals:
            typer.echo("⚠️  No signals found matching the specified criteria")
            raise typer.Exit(code=0)

        typer.echo(f"  Loaded {len(signals)} signal(s) from database")

        pipeline = AnalysisPipeline(
            config_obj,
            cache_manager,
            portfolio_manager,
            llm_provider=config_obj.llm.provider,
            test_mode_config=None,
            db_path=config_obj.database.db_path,
            run_session_id=session_id,  # Pass session_id if provided
            provider_manager=provider_manager,
        )

        # Generate report from loaded signals
        report_obj = pipeline.generate_daily_report(
            signals=signals,  # Pass filtered signals
            generate_allocation=True,
            report_date=date if date else signals[0].analysis_date if signals else None,
            run_session_id=session_id,
        )

        # Display summary
        typer.echo("\n📈 Report Summary:")
        typer.echo(f"  Report date: {report_obj.report_date}")
        typer.echo(f"  Strong signals: {report_obj.strong_signals_count}")
        typer.echo(f"  Moderate signals: {report_obj.moderate_signals_count}")
        typer.echo(f"  Total analyzed: {report_obj.total_signals_generated}")

        if report_obj.allocation_suggestion:
            typer.echo(
                f"  Diversification score: {report_obj.allocation_suggestion.diversification_score}%"
            )
            typer.echo(
                f"  Recommended allocation: €{report_obj.allocation_suggestion.total_allocated:,.0f}"
            )

        # Save report if requested
        if save_report:
            reports_dir = data_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%H-%M-%S")

            if output_format == "markdown":
                report_path = reports_dir / f"report_{report_obj.report_date}_{timestamp}.md"
                report_content = pipeline.report_generator.to_markdown(report_obj)
                with open(report_path, "w") as f:
                    f.write(report_content)
                typer.echo(f"\n✓ Report saved: {report_path}")
            else:
                report_path = reports_dir / f"report_{report_obj.report_date}_{timestamp}.json"
                with open(report_path, "w") as f:
                    json.dump(pipeline.report_generator.to_json(report_obj), f, indent=2)
                typer.echo(f"\n✓ Report saved: {report_path}")
        else:
            typer.echo("\n✓ Report generated (not saved)")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        typer.echo(f"\n❌ Error generating report: {e}", err=True)
        raise typer.Exit(code=1) from e
