"""Analysis command for FalconSignals CLI."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import typer

from src.cache.manager import CacheManager
from src.cli.app import app
from src.cli.helpers.analysis import run_llm_analysis
from src.cli.helpers.filtering import filter_tickers
from src.config import load_config
from src.data.db import init_db
from src.data.historical import HistoricalDataFetcher
from src.data.portfolio import PortfolioState
from src.data.provider_manager import ProviderManager
from src.data.repository import RecommendationsRepository, RunSessionRepository
from src.MARKET_TICKERS import (
    get_tickers_for_analysis,
    get_tickers_for_markets,
    get_us_categories,
)
from src.pipeline import AnalysisPipeline
from src.utils.llm_check import get_fallback_warning_message, log_llm_status
from src.utils.logging import get_logger, setup_logging
from src.utils.scheduler import RunLog

logger = get_logger(__name__)


@app.command()
def analyze(
    market: str = typer.Option(
        None,
        "--market",
        "-m",
        help="Market to analyze: 'global', 'us', 'eu', 'nordic', or comma-separated (e.g., 'us,eu')",
    ),
    group: str = typer.Option(
        None,
        "--group",
        "-g",
        help="Ticker group: sector categories ('us_mega_cap', 'us_tech_software', 'us_ai_ml') or portfolios ('us_portfolio_balanced_conservative', 'us_portfolio_dividend_growth'). Comma-separated for multiple. Use list-categories or list-portfolios to see all options",
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
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: config/local.yaml or config/default.yaml)",
        exists=True,
    ),
    date: str = typer.Option(
        None,
        "--date",
        "-d",
        help="Analyze as if it were a specific date in the past (YYYY-MM-DD format) for historical analysis",
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
    debug_llm: bool = typer.Option(
        False,
        "--debug-llm",
        help="Save LLM inputs and outputs to data/llm_debug/ for inspection (only works with --llm)",
    ),
    test: bool = typer.Option(
        False,
        "--test",
        help="Run true test mode with pre-cached fixture data (zero API/LLM cost, fast, reproducible)",
    ),
    fixture: str = typer.Option(
        "test_ticker_minimal",
        "--fixture",
        help="Name of fixture to use in test mode (in data/fixtures/)",
    ),
    force_full_analysis: bool = typer.Option(
        False,
        "--force-full-analysis",
        help="Analyze all tickers regardless of filter strategy (increases costs)",
    ),
    strategy: str = typer.Option(
        "anomaly",
        "--strategy",
        "-s",
        help=(
            "Filtering strategy: 'anomaly' (price/volume anomalies), "
            "'volume' (volume patterns), 'momentum' (sustained trends), "
            "'volatility' (high volatility), 'breakout' (support/resistance breaks), "
            "'gap' (price gaps), 'all' (no filtering). Use 'list-strategies' command for details."
        ),
    ),
) -> None:
    """Analyze markets and generate investment signals.

    Fetches market data, analyzes instruments, and generates investment
    recommendations with confidence scores.

    Examples:
        # Run quick test (rule-based)
        analyze --test

        # Run quick test (LLM mode)
        analyze --test --llm

        # Analyze with LLM debug mode (saves inputs/outputs)
        analyze --ticker INTU --llm --debug-llm

        # Analyze all available markets
        analyze --market global

        # Analyze US market only
        analyze --market us

        # Analyze multiple markets with limit
        analyze --market us,eu --limit 50

        # Analyze specific tickers
        analyze --ticker AAPL,MSFT,GOOGL

        # Historical date analysis (backtesting)
        analyze --ticker AAPL --date 2024-06-01
        analyze --ticker AAPL --date 2024-06-01 --llm

        # Analyze US groups (categories and portfolios)
        analyze --group us_tech_software
        analyze --group us_ai_ml,us_cybersecurity --limit 30
        analyze --group us_mega_cap
        analyze --group us_portfolio_balanced_conservative
        analyze --group us_portfolio_dividend_growth

        # Combine markets and groups
        analyze --market nordic --group us_tech_software
    """
    start_time = time.time()
    run_log = None
    signals_count = 0
    historical_date = None

    # Parse and validate historical date if provided
    if date:
        try:
            historical_date = datetime.strptime(date, "%Y-%m-%d").date()
            typer.echo(f"📅 Historical date analysis mode: {historical_date}")
        except ValueError as e:
            typer.echo(
                f"❌ Error: Invalid date format '{date}'. Use YYYY-MM-DD format (e.g., 2024-06-01)",
                err=True,
            )
            raise typer.Exit(code=1) from e

    # Handle test mode (true test mode with fixtures)
    if test:
        typer.echo("🧪 Running TRUE TEST MODE (offline, zero cost, reproducible)...")
        typer.echo(f"  Fixture: {fixture}")
        typer.echo("  Data source: Local fixture files (no API calls)")
        if use_llm:
            typer.echo("  LLM: MockLLMClient (zero cost)")
        else:
            typer.echo("  Mode: Rule-based analysis")
        # Don't save report in test mode unless explicitly requested
        if save_report:
            save_report = False
            typer.echo("  Report saving: disabled (test mode)")

    # Validate that either market, group, ticker, or test is provided
    if not market and not group and not ticker and not test:
        typer.echo(
            "❌ Error: Either --market, --group, --ticker, or --test must be provided\n"
            "Examples:\n"
            "  analyze --test              # True test mode (offline, zero cost)\n"
            "  analyze --test --llm        # True test with mock LLM\n"
            "  analyze --market global\n"
            "  analyze --market us\n"
            "  analyze --group us_tech_software\n"
            "  analyze --group us_ai_ml,us_cybersecurity --limit 30\n"
            "  analyze --group us_portfolio_balanced_conservative\n"
            "  analyze --market us,eu --limit 50\n"
            "  analyze --ticker AAPL,MSFT,GOOGL",
            err=True,
        )
        raise typer.Exit(code=1)

    if (market or group) and ticker:
        typer.echo("❌ Error: Cannot specify --ticker with --market or --group", err=True)
        raise typer.Exit(code=1)

    if test and (market or group or ticker):
        typer.echo(
            "❌ Error: Cannot use --test with --market, --group, or --ticker",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        # Initialize database if enabled
        run_session_id: int | None = None
        session_repo = None
        recommendations_repo = None
        if config_obj.database.enabled:
            init_db(config_obj.database.db_path)
            logger.debug(f"Database initialized at {config_obj.database.db_path}")

            # Initialize repositories for session management
            session_repo = RunSessionRepository(config_obj.database.db_path)
            recommendations_repo = RecommendationsRepository(config_obj.database.db_path)

        # Check LLM configuration and warn if using fallback mode
        llm_configured = log_llm_status(config_obj.llm.provider)

        # Initialize run log
        data_dir = Path("data")
        run_log = RunLog(data_dir / "runs.jsonl")

        logger.debug(f"Starting FalconSignals analysis (dry_run={dry_run})")
        logger.debug(f"Using config: {config}")
        logger.debug(f"Risk tolerance: {config_obj.risk.tolerance}")
        logger.debug(f"Capital: €{config_obj.capital.starting_capital_eur:,.2f}")

        typer.echo("✓ Configuration loaded successfully")
        typer.echo(f"  Risk tolerance: {config_obj.risk.tolerance}")
        typer.echo(f"  Capital: €{config_obj.capital.starting_capital_eur:,.2f}")
        typer.echo(f"  Monthly deposit: €{config_obj.capital.monthly_deposit_eur:,.2f}")
        typer.echo(f"  Markets: {', '.join(config_obj.markets.included)}")

        if not llm_configured:
            typer.echo(
                "\n" + get_fallback_warning_message(config_obj.llm.provider if use_llm else None)
            )

        if dry_run:
            typer.echo("  [DRY RUN MODE - No trades will be executed]")

        # Initialize pipeline
        typer.echo("\n⏳ Initializing analysis pipeline...")
        cache_manager = CacheManager(str(data_dir / "cache"))
        portfolio_manager = PortfolioState(data_dir / "portfolio_state.json")

        # Initialize provider manager for price lookups
        provider_manager = ProviderManager(
            primary_provider=config_obj.data.primary_provider,
            backup_providers=config_obj.data.backup_providers,
            db_path=config_obj.database.db_path if config_obj.database.enabled else None,
            historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
        )

        # Setup test mode if enabled
        if test:
            fixture_path = data_dir / "fixtures" / fixture
            config_obj.test_mode.enabled = True
            config_obj.test_mode.fixture_name = fixture
            config_obj.test_mode.fixture_path = str(fixture_path)
            config_obj.test_mode.use_mock_llm = use_llm
            logger.debug(f"Test mode enabled with fixture: {fixture}")

        pipeline = AnalysisPipeline(
            config_obj,
            cache_manager,
            portfolio_manager,
            llm_provider=config_obj.llm.provider,
            test_mode_config=config_obj.test_mode if test else None,
            db_path=config_obj.database.db_path if config_obj.database.enabled else None,
            run_session_id=run_session_id,
            provider_manager=provider_manager,
        )

        # Determine which tickers to analyze
        if test:
            # In test mode, load ticker from fixture metadata
            from src.data.fixture import FixtureDataProvider

            fixture_path = data_dir / "fixtures" / fixture
            if not fixture_path.exists():
                typer.echo(f"❌ Error: Fixture not found: {fixture_path}", err=True)
                raise typer.Exit(code=1)

            fixture_provider = FixtureDataProvider(fixture_path)
            metadata = fixture_provider.get_fixture_metadata()
            test_ticker = metadata.get("ticker", "AAPL")
            ticker_list = [test_ticker]
            typer.echo("\n📊 Running analysis on test fixture...")
            typer.echo(f"  Ticker: {test_ticker}")
        elif ticker:
            # Parse comma-separated tickers
            ticker_list = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"\n📊 Running analysis on {len(ticker_list)} specified instruments...")
            typer.echo(f"  Tickers: {', '.join(ticker_list)}")
        elif group:
            # Parse group specification
            groups = [g.strip().lower() for g in group.split(",")]
            typer.echo(f"\n📊 Running analysis for group(s): {', '.join(groups).upper()}...")

            # Validate groups
            available_groups = get_us_categories()
            invalid_groups = [g for g in groups if g not in available_groups]
            if invalid_groups:
                typer.echo(
                    f"❌ Error: Invalid group(s): {', '.join(invalid_groups)}",
                    err=True,
                )
                typer.echo("Available groups:", err=True)
                for group_name, count in sorted(available_groups.items()):
                    typer.echo(f"  {group_name}: {count} tickers", err=True)
                sys.exit(1)

            # Get tickers from groups, optionally combined with markets
            if market:
                markets = (
                    ["global"]
                    if market.lower() == "global"
                    else [m.strip().lower() for m in market.split(",")]
                )
                if market.lower() == "global":
                    markets = ["nordic", "eu"]
                ticker_list = get_tickers_for_analysis(
                    markets=markets, categories=groups, limit_per_category=limit
                )
                typer.echo(f"  Markets: {', '.join(markets).upper()}")
            else:
                ticker_list = get_tickers_for_analysis(categories=groups, limit_per_category=limit)

            if limit:
                typer.echo(f"  Limit: {limit} instruments per group")
            typer.echo(f"  Total instruments to analyze: {len(ticker_list)}")
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

        # Prepare analysis context metadata
        analyzed_group = None
        analyzed_market = None
        analyzed_tickers_specified = []
        tickers_with_anomalies = []
        force_full_analysis_used = False

        if ticker:
            analyzed_tickers_specified = [t.strip().upper() for t in ticker.split(",")]
        elif group:
            analyzed_group = group
        else:
            analyzed_market = market

        # Setup historical data fetcher if analyzing historical data
        historical_context_data = {}
        if historical_date:
            typer.echo("\n📅 Preparing historical data fetcher...")
            # Get the primary data provider
            provider_manager = ProviderManager(
                historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
            )
            primary_provider = provider_manager.primary_provider
            # Pass cache_manager to enable historical cache retrieval
            historical_fetcher = HistoricalDataFetcher(
                primary_provider, cache_manager=cache_manager
            )

            # Fetch historical context for each ticker
            typer.echo(f"  Fetching historical data as of {historical_date}...")
            for tick in ticker_list:
                try:
                    context = historical_fetcher.fetch_as_of_date(
                        tick, historical_date, lookback_days=365
                    )
                    historical_context_data[tick] = context
                except Exception as e:
                    typer.echo(f"  ⚠️  Error fetching historical data for {tick}: {e}")
                    historical_context_data[tick] = None

            if historical_context_data:
                typer.echo(
                    f"  ✓ Historical data fetched for {len(historical_context_data)} instruments"
                )

        # Create run session if database is enabled
        if session_repo:
            run_session_id = session_repo.create_session(
                analysis_mode="llm" if use_llm else "rule_based",
                analyzed_category=analyzed_group,
                analyzed_market=analyzed_market,
                analyzed_tickers_specified=(
                    analyzed_tickers_specified if analyzed_tickers_specified else None
                ),
                initial_tickers_count=len(ticker_list),
                anomalies_count=0,  # Will be updated after filtering
                force_full_analysis=force_full_analysis,
            )
            # Update pipeline with session ID
            pipeline.run_session_id = run_session_id
            logger.debug(f"Created run session: {run_session_id}")

        # Apply filtering strategy before analysis (unified for both LLM and rule-based)
        typer.echo(f"\n🔍 Stage 1: Filtering tickers (strategy: {strategy})")
        try:
            filtered_ticker_list, _ = filter_tickers(
                ticker_list,
                strategy,
                config_obj,
                typer,
                force_full_analysis,
                historical_date,
                config_obj.test_mode if test else None,
            )
            if filtered_ticker_list:
                typer.echo("  ✓ Tickers selected for analysis: " + ", ".join(filtered_ticker_list))

            # Track which tickers passed the filter
            tickers_with_anomalies = filtered_ticker_list
            force_full_analysis_used = force_full_analysis

        except RuntimeError as e:
            # Display error cleanly without traceback
            typer.echo(f"\n❌ Error: {str(e)}", err=True)
            sys.exit(1)

        # Remove tickers that already have recommendations for this date and analysis mode
        if recommendations_repo and not test:
            analysis_mode = "llm" if use_llm else "rule_based"
            check_date = historical_date if historical_date else datetime.now().date()

            typer.echo(
                f"\n🔍 Checking for existing recommendations (date: {check_date}, mode: {analysis_mode})..."
            )
            existing_tickers = recommendations_repo.get_existing_tickers_for_date(
                check_date, analysis_mode
            )

            if existing_tickers:
                # Filter out tickers that already have recommendations
                original_count = len(filtered_ticker_list)
                filtered_ticker_list = [
                    t for t in filtered_ticker_list if t not in existing_tickers
                ]
                removed_count = original_count - len(filtered_ticker_list)

                if removed_count > 0:
                    typer.echo(
                        f"  ℹ️  Skipping {removed_count} ticker(s) with existing recommendations: "
                        f"{', '.join(sorted(existing_tickers & set(filtered_ticker_list[:original_count])))}"
                    )
                    typer.echo(f"  ✓ {len(filtered_ticker_list)} new ticker(s) to analyze")

                if not filtered_ticker_list:
                    typer.echo(
                        "\n✓ All tickers already have recommendations for this date and mode."
                    )
                    typer.echo("  No new analysis needed.")
                    return
            else:
                typer.echo("  ✓ No existing recommendations found. Proceeding with all tickers.")

        # Run analysis (LLM or rule-based)
        if use_llm:
            typer.echo("\n🤖 Stage 2: Deep LLM-powered analysis")
            typer.echo(f"   LLM Provider: {config_obj.llm.provider}")
            typer.echo(f"   Model: {config_obj.llm.model}")

            signals, portfolio_manager = run_llm_analysis(
                filtered_ticker_list,
                config_obj,
                typer,
                debug_llm,
                is_filtered=True,
                cache_manager=cache_manager,
                provider_manager=provider_manager,
                historical_date=historical_date,
                run_session_id=run_session_id,
                recommendations_repo=recommendations_repo,
            )
            analysis_mode = "llm"
        else:
            typer.echo("\n📊 Stage 2: Rule-based analysis")
            typer.echo("   Using technical indicators & fundamental metrics")
            # Pass historical context if available
            analysis_context = {}
            if historical_context_data:
                analysis_context["historical_contexts"] = historical_context_data
                analysis_context["analysis_date"] = historical_date
            signals, portfolio_manager = pipeline.run_analysis(
                filtered_ticker_list, analysis_context
            )
            analysis_mode = "rule_based"
        signals_count = len(signals)

        # Complete run session if database is enabled
        if session_repo and run_session_id:
            # Calculate failed count (initial tickers - generated signals)
            initial_count = len(ticker_list)
            failed_count = initial_count - signals_count

            # Determine status
            if signals_count == initial_count:
                status = "completed"
            elif signals_count > 0:
                status = "partial"
            else:
                status = "failed"

            session_repo.complete_session(
                session_id=run_session_id,
                signals_generated=signals_count,
                signals_failed=failed_count,
                status=status,
            )
            logger.debug(f"Completed run session: {run_session_id} (status: {status})")

        if signals:
            typer.echo(f"✓ Analysis complete: {signals_count} signals generated")

            # Generate report
            typer.echo("\n📋 Generating report...")
            # Use historical date for report if provided
            report_date = historical_date.strftime("%Y-%m-%d") if historical_date else None
            report = pipeline.generate_daily_report(
                signals,
                generate_allocation=True,
                report_date=report_date,
                analysis_mode=analysis_mode,
                analyzed_category=analyzed_group,
                analyzed_market=analyzed_market,
                analyzed_tickers_specified=analyzed_tickers_specified,
                initial_tickers=ticker_list,
                tickers_with_anomalies=tickers_with_anomalies,
                force_full_analysis_used=force_full_analysis_used,
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
        raise typer.Exit(code=1) from e
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
        raise typer.Exit(code=1) from e
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
        raise typer.Exit(code=1) from e
