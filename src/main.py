"""NordInvest CLI interface."""

import time
from datetime import datetime
from pathlib import Path

import typer

from src.analysis import InvestmentSignal
from src.cache.manager import CacheManager
from src.config import load_config
from src.data.portfolio import PortfolioState
from src.llm.integration import LLMAnalysisOrchestrator
from src.llm.token_tracker import TokenTracker
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


def _run_llm_analysis(
    tickers: list[str],
    config_obj,
    typer_instance,
) -> tuple[list[InvestmentSignal], None]:
    """Run analysis using LLM-powered orchestrator.

    Args:
        tickers: List of tickers to analyze
        config_obj: Loaded configuration object
        typer_instance: Typer instance for output

    Returns:
        Tuple of (signals, portfolio_manager)
    """
    try:
        # Initialize LLM orchestrator with token tracking
        data_dir = Path("data")
        tracker = TokenTracker(
            config_obj.token_tracker,
            storage_dir=data_dir / "tracking",
        )

        orchestrator = LLMAnalysisOrchestrator(
            llm_config=config_obj.llm,
            token_tracker=tracker,
            enable_fallback=config_obj.llm.enable_fallback,
        )

        typer_instance.echo(f"  LLM Provider: {config_obj.llm.provider}")
        typer_instance.echo(f"  Model: {config_obj.llm.model}")
        typer_instance.echo(f"  Temperature: {config_obj.llm.temperature}")
        typer_instance.echo(f"  Token tracking: enabled")

        # Analyze each ticker with LLM
        signals = []
        with typer_instance.progressbar(
            tickers, label="Analyzing instruments", show_pos=True, show_percent=True
        ) as progress:
            for ticker in progress:
                try:
                    result = orchestrator.analyze_instrument(ticker)

                    # Extract signal from result if successful
                    if result.get("status") == "complete":
                        # Use the synthesis result if available
                        synthesis_result = result.get("results", {}).get("synthesis", {})
                        if synthesis_result.get("status") == "success":
                            signal_data = synthesis_result.get("result", {})
                            # Create InvestmentSignal from LLM result
                            signal = _create_signal_from_llm_result(ticker, signal_data)
                            if signal:
                                signals.append(signal)
                        else:
                            logger.warning(f"Synthesis failed for {ticker}, skipping")

                except Exception as e:
                    logger.error(f"Error analyzing {ticker} with LLM: {e}")
                    typer_instance.echo(f"  ⚠️  Error analyzing {ticker}: {e}")

        # Log token usage summary
        daily_stats = tracker.get_daily_stats()
        if daily_stats:
            typer_instance.echo(f"\n💰 Token Usage Summary:")
            typer_instance.echo(f"  Input tokens: {daily_stats.total_input_tokens:,}")
            typer_instance.echo(f"  Output tokens: {daily_stats.total_output_tokens:,}")
            typer_instance.echo(f"  Cost: €{daily_stats.total_cost_eur:.2f}")
            typer_instance.echo(f"  Requests: {daily_stats.requests}")

        return signals, None

    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}", exc_info=True)
        typer_instance.echo(f"❌ LLM Analysis Error: {e}", err=True)
        return [], None


def _create_signal_from_llm_result(
    ticker: str,
    llm_result: dict,
) -> InvestmentSignal | None:
    """Convert LLM analysis result to InvestmentSignal.

    Args:
        ticker: Stock ticker
        llm_result: LLM analysis result dict

    Returns:
        InvestmentSignal or None if conversion fails
    """
    try:
        # Parse LLM result (assumes JSON structure from prompt)
        if isinstance(llm_result, str):
            import json

            llm_result = json.loads(llm_result)

        # Extract key fields
        recommendation = llm_result.get("recommendation", "Hold").upper()
        if recommendation not in ["BUY", "HOLD", "AVOID"]:
            recommendation = "HOLD"

        combined_score = llm_result.get("combined_score", 50)
        confidence = llm_result.get("confidence", 50)
        thesis = llm_result.get("thesis", "")

        # Create signal
        signal = InvestmentSignal(
            ticker=ticker,
            name=ticker,  # Use ticker as name since we may not have company name
            market="Global",
            sector="Unknown",
            recommendation=recommendation,
            time_horizon="3M",
            expected_return={"min": 5, "max": 15},
            confidence=confidence,
            scores={
                "fundamental": llm_result.get("fundamental_score", 50),
                "technical": llm_result.get("technical_score", 50),
                "sentiment": llm_result.get("sentiment_score", 50),
            },
            key_reasons=llm_result.get("catalysts", []),
            risk_assessment={
                "level": "Medium",
                "volatility": "Normal",
                "flags": llm_result.get("risks", []),
            },
            allocation={"eur": 0, "percentage": 0},
        )

        return signal

    except Exception as e:
        logger.error(f"Error creating signal from LLM result: {e}")
        return None


@app.command()
def analyze(
    market: str = typer.Option(
        None,
        "--market",
        "-m",
        help="Market to analyze: 'global', 'us', 'eu', 'nordic', or comma-separated (e.g., 'us,eu')",
    ),
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Comma-separated list of tickers to analyze (e.g., 'AAPL,MSFT,GOOGL')",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of instruments to analyze per market",
    ),
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
    use_llm: bool = typer.Option(
        False,
        "--llm",
        help="Use LLM-powered analysis (CrewAI with Claude/GPT) instead of rule-based",
    ),
) -> None:
    """Analyze markets and generate investment signals.

    Fetches market data, analyzes instruments, and generates investment
    recommendations with confidence scores.

    Examples:
        # Analyze all available markets
        analyze --market global

        # Analyze US market only
        analyze --market us

        # Analyze multiple markets with limit
        analyze --market us,eu --limit 50

        # Analyze specific tickers
        analyze --ticker AAPL,MSFT,GOOGL
    """
    start_time = time.time()
    run_log = None
    signals_count = 0

    # Validate that either market or ticker is provided
    if not market and not ticker:
        typer.echo(
            "❌ Error: Either --market or --ticker must be provided\n"
            "Examples:\n"
            "  analyze --market global\n"
            "  analyze --market us\n"
            "  analyze --market us,eu --limit 50\n"
            "  analyze --ticker AAPL,MSFT,GOOGL",
            err=True,
        )
        raise typer.Exit(code=1)

    if market and ticker:
        typer.echo("❌ Error: Cannot specify both --market and --ticker", err=True)
        raise typer.Exit(code=1)

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

        logger.debug(f"Starting NordInvest analysis (dry_run={dry_run})")
        logger.debug(f"Using config: {config}")
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

        # Determine which tickers to analyze
        if ticker:
            # Parse comma-separated tickers
            ticker_list = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"\n📊 Running analysis on {len(ticker_list)} specified instruments...")
            typer.echo(f"  Tickers: {', '.join(ticker_list)}")
        else:
            # Parse market specification
            if market.lower() == "global":
                markets = ["nordic", "eu", "us"]
                typer.echo("\n🌍 Running GLOBAL market analysis...")
            else:
                markets = [m.strip().lower() for m in market.split(",")]
                typer.echo(f"\n📊 Running analysis for market(s): {', '.join(markets).upper()}...")

            # Validate markets
            valid_markets = ["nordic", "eu", "us"]
            invalid_markets = [m for m in markets if m not in valid_markets]
            if invalid_markets:
                typer.echo(
                    f"❌ Error: Invalid market(s): {', '.join(invalid_markets)}\n"
                    f"Valid markets: {', '.join(valid_markets)}, global",
                    err=True,
                )
                raise typer.Exit(code=1)

            ticker_list = get_tickers_for_markets(markets, limit=limit)

            if limit:
                typer.echo(f"  Limit: {limit} instruments per market")
            typer.echo(f"  Total instruments to analyze: {len(ticker_list)}")

        # Run analysis (LLM or rule-based)
        if use_llm:
            typer.echo("\n🤖 Using LLM-powered analysis (CrewAI with intelligent agents)")
            signals, portfolio_manager = _run_llm_analysis(ticker_list, config_obj, typer)
        else:
            signals, portfolio_manager = pipeline.run_analysis(ticker_list)
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
            typer.echo("\n📈 Report Summary:")
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
                timestamp = datetime.now().strftime("%H-%M-%S")

                if output_format == "markdown":
                    report_path = reports_dir / f"report_{report.report_date}_{timestamp}.md"
                    report_content = pipeline.report_generator.to_markdown(report)
                    with open(report_path, "w") as f:
                        f.write(report_content)
                    typer.echo(f"  Report saved: {report_path}")
                else:
                    report_path = reports_dir / f"report_{report.report_date}_{timestamp}.json"
                    import json

                    with open(report_path, "w") as f:
                        json.dump(pipeline.report_generator.to_json(report), f, indent=2)
                    typer.echo(f"  Report saved: {report_path}")
        else:
            typer.echo("⚠️  No signals generated from analysis")

        duration = time.time() - start_time
        logger.debug(f"Analysis run completed successfully in {duration:.2f}s")
        typer.echo(f"\n✓ Analysis completed in {duration:.2f}s")

        # Log the run
        if run_log:
            run_log.log_run(
                success=True,
                duration_seconds=duration,
                signal_count=signals_count,
            )

    except FileNotFoundError as e:
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

        logger.debug(f"Generating report for date: {date}")

        typer.echo("✓ Report configuration loaded")
        if date:
            typer.echo(f"  Date: {date}")
        typer.echo(f"  Format: {config_obj.output.report_format}")

        # Phase 4+ implementation will add actual report generation here
        logger.debug("Report generation completed successfully")

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

        logger.debug(f"Local configuration initialized: {output}")
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
