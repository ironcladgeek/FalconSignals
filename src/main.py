"""NordInvest CLI interface."""

import json
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

import typer

from src.analysis import InvestmentSignal
from src.analysis.signal_creator import SignalCreator
from src.cache.manager import CacheManager
from src.config import load_config
from src.data.db import init_db
from src.data.historical import HistoricalDataFetcher
from src.data.portfolio import PortfolioState
from src.data.price_manager import PriceDataManager
from src.data.provider_manager import ProviderManager
from src.data.repository import (
    PerformanceRepository,
    RecommendationsRepository,
    RunSessionRepository,
)
from src.filtering import FilterOrchestrator
from src.filtering.strategies import list_strategies as get_strategies
from src.llm.integration import LLMAnalysisOrchestrator
from src.llm.token_tracker import TokenTracker
from src.MARKET_TICKERS import (
    get_tickers_for_analysis,
    get_tickers_for_markets,
    get_us_categories,
)
from src.pipeline import AnalysisPipeline
from src.utils.llm_check import get_fallback_warning_message, log_llm_status
from src.utils.logging import get_logger, setup_logging
from src.utils.resilience import RateLimiter
from src.utils.scheduler import RunLog
from src.website.generator import WebsiteGenerator

app = typer.Typer(
    name="nordinvest",
    help="AI-powered financial analysis and investment recommendation system",
    no_args_is_help=True,
)

logger = get_logger(__name__)


def _filter_tickers(
    tickers: list[str],
    strategy: str,
    config_obj,
    typer_instance,
    force_full_analysis: bool = False,
    historical_date=None,
    test_mode_config=None,
) -> tuple[list[str], dict]:
    """Filter tickers using specified strategy before analysis.

    Unified filtering path for both LLM and rule-based analysis modes.
    Implements DRY principle by having a single filtering logic.

    Args:
        tickers: List of tickers to filter
        strategy: Filtering strategy name ('anomaly', 'volume', 'all')
        config_obj: Configuration object
        typer_instance: Typer instance for output
        force_full_analysis: If True, use 'all' strategy regardless of specified strategy
        historical_date: Optional date for historical analysis
        test_mode_config: Optional test mode configuration

    Returns:
        Tuple of (filtered_tickers, filter_result)
        - filtered_tickers: List of tickers that passed the filter
        - filter_result: Full filter result dictionary with details

    Raises:
        RuntimeError: If filtering fails or no tickers pass filter (unless force_full_analysis)
    """
    try:
        # Override strategy if force_full_analysis is enabled
        if force_full_analysis:
            strategy = "all"
            typer_instance.echo(
                "  ⚠️  --force-full-analysis enabled: using 'all' strategy (no filtering)"
            )

        typer_instance.echo(f"🔍 Filtering tickers using '{strategy}' strategy...")

        # Get lookback days from config
        lookback_days = 730
        if hasattr(config_obj, "analysis") and hasattr(
            config_obj.analysis, "historical_data_lookback_days"
        ):
            lookback_days = config_obj.analysis.historical_data_lookback_days

        # Get strategy config if available (convert Pydantic model to dict)
        strategy_config = None
        if hasattr(config_obj, "filtering") and hasattr(config_obj.filtering, "strategies"):
            strategy_cfg = getattr(config_obj.filtering.strategies, strategy, None)
            if strategy_cfg:
                # Convert Pydantic model to dict for strategy initialization
                strategy_config = (
                    strategy_cfg.model_dump()
                    if hasattr(strategy_cfg, "model_dump")
                    else dict(strategy_cfg)
                )

        # Setup provider for price fetching
        provider_name = None
        fixture_path = None
        if test_mode_config and test_mode_config.enabled:
            provider_name = "fixture"
            fixture_path = test_mode_config.fixture_path
        else:
            provider_name = config_obj.data.primary_provider

        # Create orchestrator
        orchestrator = FilterOrchestrator(
            strategy=strategy,
            provider_name=provider_name,
            fixture_path=fixture_path,
            config=config_obj,
            strategy_config=strategy_config,
        )

        # Execute filtering
        filter_result = orchestrator.filter_tickers(
            tickers=tickers,
            historical_date=historical_date,
            lookback_days=lookback_days,
            show_progress=True,
        )

        if filter_result.get("status") != "success":
            error_msg = filter_result.get("message", "Unknown error")
            logger.error(f"Filtering failed: {error_msg}")
            raise RuntimeError(
                f"Filtering failed: {error_msg}\n"
                "Unable to proceed with analysis.\n"
                "Check logs for details."
            )

        filtered_tickers = filter_result.get("filtered_tickers", [])

        if not filtered_tickers and strategy != "all":
            logger.warning(f"No tickers passed '{strategy}' filter")
            if not force_full_analysis:
                raise RuntimeError(
                    f"No tickers passed the '{strategy}' filter.\n"
                    "To analyze all tickers anyway (higher cost), "
                    "use --force-full-analysis flag or --strategy all.\n"
                    f"Example: analyze --group us_mega_cap --strategy {strategy} --force-full-analysis"
                )

        total_scanned = filter_result.get("total_scanned", len(tickers))
        total_filtered = filter_result.get("total_filtered", len(filtered_tickers))

        if total_filtered < total_scanned:
            reduction_pct = 100 * (1 - total_filtered / total_scanned)
            typer_instance.echo(
                f"  ✓ Filtering complete: {total_filtered}/{total_scanned} tickers selected "
                f"({reduction_pct:.0f}% reduction)"
            )
        else:
            typer_instance.echo(f"  ✓ All {total_filtered} tickers selected")

        return filtered_tickers, filter_result

    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Error during filtering: {e}", exc_info=True)
        raise RuntimeError(
            f"Filtering error: {str(e)}\nUnable to proceed with analysis.\nCheck logs for details."
        )


def _run_llm_analysis(
    tickers: list[str],
    config_obj,
    typer_instance,
    debug_llm: bool = False,
    is_filtered: bool = False,
    cache_manager=None,
    provider_manager=None,
    historical_date=None,
    run_session_id: int | None = None,
    recommendations_repo=None,
) -> tuple[list[InvestmentSignal], None]:
    """Run analysis using LLM-powered orchestrator.

    Args:
        tickers: List of tickers to analyze (pre-filtered if is_filtered=True)
        config_obj: Loaded configuration object
        typer_instance: Typer instance for output
        debug_llm: Enable LLM debug mode (save inputs/outputs)
        is_filtered: Whether tickers have been pre-filtered by market scan
        cache_manager: Cache manager instance
        historical_date: Optional date for historical analysis
        run_session_id: Optional UUID linking signals to analysis run session
        recommendations_repo: Optional repository for storing recommendations

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

        # Setup debug directory if requested
        debug_dir = None
        if debug_llm:
            debug_dir = data_dir / "llm_debug" / datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_dir.mkdir(parents=True, exist_ok=True)
            typer_instance.echo("  LLM debug mode: enabled")
            typer_instance.echo(f"  Debug outputs: {debug_dir}")

        # Create progress callback for synthesis stage
        def progress_callback(message: str):
            """Display progress messages."""
            typer_instance.echo(message)

        orchestrator = LLMAnalysisOrchestrator(
            llm_config=config_obj.llm,
            token_tracker=tracker,
            enable_fallback=config_obj.llm.enable_fallback,
            debug_dir=debug_dir,
            progress_callback=progress_callback,
            db_path=config_obj.database.db_path if config_obj.database.enabled else None,
            config=config_obj,
        )

        # Set historical date on all tools if provided
        if historical_date:
            typer_instance.echo(f"  Setting historical date {historical_date} on analysis tools...")
            # Access the tool adapter's tool instances
            if hasattr(orchestrator, "tool_adapter"):
                if hasattr(orchestrator.tool_adapter, "price_fetcher"):
                    orchestrator.tool_adapter.price_fetcher.set_historical_date(historical_date)
                if hasattr(orchestrator.tool_adapter, "fundamental_fetcher"):
                    orchestrator.tool_adapter.fundamental_fetcher.set_historical_date(
                        historical_date
                    )
                if hasattr(orchestrator.tool_adapter, "news_fetcher"):
                    orchestrator.tool_adapter.news_fetcher.set_historical_date(historical_date)

        typer_instance.echo(f"  LLM Provider: {config_obj.llm.provider}")
        typer_instance.echo(f"  Model: {config_obj.llm.model}")
        typer_instance.echo(f"  Temperature: {config_obj.llm.temperature}")
        typer_instance.echo("  Token tracking: enabled")

        # Analyze each ticker with LLM
        signals = []
        stage_label = "Stage 2: Deep LLM analysis" if is_filtered else "Analyzing instruments"
        with typer_instance.progressbar(
            tickers, label=stage_label, show_pos=True, show_percent=True
        ) as progress:
            for ticker in progress:
                try:
                    current_task = [0]  # Use list to allow mutation in nested function

                    def agent_progress_callback(current, total, task_name):
                        """Update progress display for agent tasks."""
                        if current > current_task[0]:
                            current_task[0] = current
                            # Show which agent is working
                            agent_name = task_name.replace("_", " ").title()
                            typer_instance.echo(f"  → {agent_name} ({current}/{total})", nl=False)
                            typer_instance.echo("\r", nl=False)  # Carriage return to overwrite

                    # Analyze instrument - returns UnifiedAnalysisResult or None
                    unified_result = orchestrator.analyze_instrument(
                        ticker, progress_callback=agent_progress_callback
                    )

                    # Create signal from unified result using SignalCreator
                    if unified_result:
                        # Initialize SignalCreator with required dependencies
                        signal_creator = SignalCreator(
                            cache_manager=cache_manager,
                            provider_manager=provider_manager,
                            risk_assessor=None,  # Risk assessment already in unified_result
                        )

                        # Create signal from unified analysis result
                        signal = signal_creator.create_signal(
                            result=unified_result,
                            portfolio_context={},
                            analysis_date=historical_date,
                        )

                        if signal:
                            signals.append(signal)

                            # Store signal to database if enabled
                            if recommendations_repo and run_session_id:
                                try:
                                    recommendations_repo.store_recommendation(
                                        signal=signal,
                                        run_session_id=run_session_id,
                                        analysis_mode="llm",
                                        llm_model=config_obj.llm.model,
                                    )
                                except Exception as e:
                                    logger.warning(
                                        f"Failed to store recommendation for {ticker} to database: {e}"
                                    )
                                    # Continue execution - DB failures don't halt pipeline
                    else:
                        logger.warning(f"Analysis failed for {ticker}, skipping")

                except Exception as e:
                    logger.error(f"Error analyzing {ticker} with LLM: {e}")
                    typer_instance.echo(f"  ⚠️  Error analyzing {ticker}: {e}")

        # Log token usage summary
        daily_stats = tracker.get_daily_stats()
        if daily_stats:
            typer_instance.echo("\n💰 Token Usage Summary:")
            typer_instance.echo(f"  Input tokens: {daily_stats.total_input_tokens:,}")
            typer_instance.echo(f"  Output tokens: {daily_stats.total_output_tokens:,}")
            typer_instance.echo(f"  Cost: €{daily_stats.total_cost_eur:.2f}")
            typer_instance.echo(f"  Requests: {daily_stats.requests}")

        return signals, None

    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}", exc_info=True)
        typer_instance.echo(f"❌ LLM Analysis Error: {e}", err=True)
        return [], None


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
    config: Path = typer.Option(
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
                analyzed_tickers_specified=analyzed_tickers_specified
                if analyzed_tickers_specified
                else None,
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
            filtered_ticker_list, _ = _filter_tickers(
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

        # Run analysis (LLM or rule-based)
        if use_llm:
            typer.echo("\n🤖 Stage 2: Deep LLM-powered analysis")
            typer.echo(f"   LLM Provider: {config_obj.llm.provider}")
            typer.echo(f"   Model: {config_obj.llm.model}")

            signals, portfolio_manager = _run_llm_analysis(
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
    session_id: int | None = typer.Option(
        None, "--session-id", help="Generate report from run session ID (integer)"
    ),
    date: str | None = typer.Option(
        None, "--date", help="Generate report for specific date (YYYY-MM-DD)"
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
        report --session-id 02a27c22-a123-4378-8654-95c592a66e2f

        # Generate report for all signals from a specific date
        report --date 2025-12-04

        # Generate JSON report instead of markdown
        report --session-id abc123 --format json
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

        # Generate report from database
        report_obj = pipeline.generate_daily_report(
            signals=None,  # Load from database
            generate_allocation=True,
            report_date=date,
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


@app.command()
def publish(
    session_id: int | None = typer.Option(
        None, "--session-id", help="Publish report from run session ID"
    ),
    date: str | None = typer.Option(
        None, "--date", help="Publish report for specific date (YYYY-MM-DD)"
    ),
    ticker: str | None = typer.Option(
        None, "--ticker", help="Publish only for specific ticker symbol"
    ),
    build_only: bool = typer.Option(
        False, "--build-only", help="Only build site, don't deploy to GitHub Pages"
    ),
    no_build: bool = typer.Option(
        False, "--no-build", help="Skip MkDocs build step (for testing content generation)"
    ),
    config: str = typer.Option(
        "config/local.yaml",
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Publish analysis results to static website.

    Generate website content from database signals and optionally build/deploy
    to GitHub Pages. Similar to report command but outputs to website format.

    Examples:

        # Publish from specific session and deploy
        publish --session-id 123

        # Publish all signals from a date
        publish --date 2025-12-10

        # Publish only one ticker
        publish --ticker NVDA --date 2025-12-10

        # Generate content without building site
        publish --session-id 123 --no-build

        # Build site but don't deploy to GitHub Pages
        publish --session-id 123 --build-only
    """
    try:
        # Validate inputs
        if not session_id and not date and not ticker:
            typer.echo("❌ Error: Must specify --session-id, --date, or --ticker", err=True)
            typer.echo("Examples:", err=True)
            typer.echo("  publish --session-id 123", err=True)
            typer.echo("  publish --date 2025-12-10", err=True)
            typer.echo("  publish --ticker NVDA --date 2025-12-10", err=True)
            raise typer.Exit(code=1)

        # Validate date format if provided
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                typer.echo(f"❌ Error: Invalid date format '{date}'. Use YYYY-MM-DD", err=True)
                raise typer.Exit(code=1)

        # Load configuration
        config_obj = load_config(config)
        setup_logging(config_obj.logging)

        # Check if database is enabled
        if not config_obj.database.enabled:
            typer.echo(
                "❌ Error: Database is not enabled in configuration.\n"
                "   Enable database in config file to use website publishing.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Initialize database
        init_db(config_obj.database.db_path)
        logger.debug(f"Database initialized at {config_obj.database.db_path}")

        typer.echo("🌐 Publishing to website...")
        if session_id:
            typer.echo(f"  Session ID: {session_id}")
        if date:
            typer.echo(f"  Date: {date}")
        if ticker:
            typer.echo(f"  Ticker: {ticker}")

        # Initialize generator
        website_dir = Path("website/docs")
        generator = WebsiteGenerator(
            config=config_obj,
            db_path=config_obj.database.db_path,
            output_dir=str(website_dir),
        )

        # Load signals from database
        repo = RecommendationsRepository(config_obj.database.db_path)

        if ticker:
            # Load signals for specific ticker
            signals_data = repo.get_recommendations_by_ticker(ticker)
            if not signals_data:
                typer.echo(f"❌ No signals found for ticker: {ticker}", err=True)
                raise typer.Exit(code=1)

            # Generate ticker page
            typer.echo(f"  Generating page for {ticker}...")
            ticker_path = generator.generate_ticker_page(ticker)
            typer.echo(f"  ✓ Created: {ticker_path}")

        elif session_id or date:
            # Load signals by session or date
            if session_id:
                signals = repo.get_recommendations_by_session(session_id)
            else:
                signals = repo.get_recommendations_by_date(date)

            if not signals:
                typer.echo(
                    f"❌ No signals found for {'session ' + str(session_id) if session_id else 'date ' + date}",
                    err=True,
                )
                raise typer.Exit(code=1)

            # Convert to InvestmentSignal objects
            signal_objects = []
            for sig in signals:
                try:
                    signal_obj = InvestmentSignal.model_validate(sig)
                    signal_objects.append(signal_obj)
                except Exception as e:
                    logger.warning(f"Failed to load signal {sig.get('ticker', 'unknown')}: {e}")
                    continue

            if not signal_objects:
                typer.echo("❌ No valid signals could be loaded", err=True)
                raise typer.Exit(code=1)

            # Generate report page
            report_date_str = date if date else signal_objects[0].analysis_date
            typer.echo(f"  Generating report page for {report_date_str}...")

            metadata = {
                "session_id": session_id,
                "total_signals": len(signal_objects),
            }

            report_path = generator.generate_report_page(
                signals=signal_objects,
                report_date=report_date_str,
                metadata=metadata,
            )
            typer.echo(f"  ✓ Created: {report_path}")

            # Generate ticker pages for all tickers in the report
            typer.echo("  Generating ticker pages...")
            unique_tickers = list(set(s.ticker for s in signal_objects))
            for t in unique_tickers:
                try:
                    ticker_path = generator.generate_ticker_page(t)
                    typer.echo(f"    ✓ {t}: {ticker_path}")
                except Exception as e:
                    logger.warning(f"Failed to generate page for {t}: {e}")
                    typer.echo(f"    ⚠️  {t}: {e}")

        # Generate tag pages
        typer.echo("  Generating tag pages...")
        try:
            tag_pages = generator.generate_tag_pages()
            typer.echo(f"  ✓ Generated {len(tag_pages)} tag pages")
        except Exception as e:
            logger.warning(f"Failed to generate tag pages: {e}")
            typer.echo(f"  ⚠️  Tag generation failed: {e}")

        # Generate index page
        typer.echo("  Generating index page...")
        index_path = generator.generate_index_page()
        typer.echo(f"  ✓ Created: {index_path}")

        # Update navigation
        typer.echo("  Updating navigation...")
        generator.update_navigation()
        typer.echo("  ✓ Navigation updated")

        typer.echo(f"\n✓ Content generated successfully in {website_dir}")

        # Build site with MkDocs if requested
        if not no_build:
            typer.echo("\n🔨 Building site with MkDocs...")

            website_root = Path("website")
            result = subprocess.run(
                ["mkdocs", "build", "--clean"],
                cwd=str(website_root),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                typer.echo(f"❌ MkDocs build failed:\n{result.stderr}", err=True)
                raise typer.Exit(code=1)

            typer.echo("✓ Site built successfully")

            # Deploy to GitHub Pages if not build-only
            if not build_only:
                typer.echo("\n🚀 Deploying to GitHub Pages...")
                result = subprocess.run(
                    ["mkdocs", "gh-deploy", "--force"],
                    cwd=str(website_root),
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    typer.echo(f"❌ Deployment failed:\n{result.stderr}", err=True)
                    raise typer.Exit(code=1)

                typer.echo("✓ Deployed to GitHub Pages")
                typer.echo("\n🌐 Your site should be available at:")
                typer.echo("   https://ironcladgeek.github.io/NordInvest/")
            else:
                typer.echo("\n✓ Build complete (deployment skipped)")
        else:
            typer.echo("\n✓ Content generation complete (build skipped)")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error publishing website: {e}", exc_info=True)
        typer.echo(f"\n❌ Error publishing website: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def list_categories() -> None:
    """List all available US ticker categories.

    Shows all category names with the number of tickers in each.
    Use these category names with the `analyze --group` option.
    """
    categories = get_us_categories()

    typer.echo("\n🇺🇸 Available US Ticker Categories:\n")

    # Group by type for better readability
    groups = {
        "Market Cap": ["us_mega_cap", "us_large_cap", "us_mid_cap", "us_small_cap"],
        "Technology": [
            "us_tech",
            "us_tech_software",
            "us_tech_semiconductors",
            "us_tech_hardware",
            "us_tech_internet",
        ],
        "Healthcare": ["us_healthcare", "us_healthcare_pharma", "us_healthcare_devices"],
        "Financials": [
            "us_financials",
            "us_financials_banks",
            "us_financials_fintech",
            "us_financials_asset_mgmt",
        ],
        "Consumer": [
            "us_consumer",
            "us_consumer_retail",
            "us_consumer_food_bev",
            "us_consumer_restaurants",
        ],
        "Other Sectors": [
            "us_industrials",
            "us_energy",
            "us_clean_energy",
            "us_utilities",
            "us_real_estate",
            "us_materials",
            "us_communication",
            "us_transportation",
        ],
        "Themes": [
            "us_ai_ml",
            "us_cybersecurity",
            "us_cloud_computing",
            "us_space_defense",
            "us_ev_autonomous",
            "us_biotech_genomics",
            "us_quantum_computing",
        ],
        "ETFs": [
            "us_etfs",
            "us_etfs_broad_market",
            "us_etfs_sector",
            "us_etfs_fixed_income",
            "us_etfs_international",
            "us_etfs_thematic",
            "us_etfs_dividend",
        ],
    }

    for group_name, cat_list in groups.items():
        typer.echo(f"📌 {group_name}:")
        for cat in cat_list:
            if cat in categories:
                count = categories[cat]
                typer.echo(f"  • {cat}: {count} tickers")
        typer.echo()

    # Usage examples
    typer.echo("💡 Usage Examples:")
    typer.echo("  analyze --group us_tech_software")
    typer.echo("  analyze --group us_ai_ml,us_cybersecurity --limit 30")
    typer.echo("  analyze --market nordic --group us_tech_software")
    typer.echo()


@app.command()
def list_portfolios() -> None:
    """List all available diversified portfolio categories.

    Shows all pre-built portfolio categories with the number of tickers in each.
    Use these portfolio names with the `analyze --group` option.
    """
    categories = get_us_categories()

    # Filter for portfolio categories only
    portfolio_categories = {k: v for k, v in categories.items() if k.startswith("us_portfolio_")}

    typer.echo("\n💼 Available Diversified Portfolio Categories:\n")

    # Group by portfolio type for better readability
    groups = {
        "Balanced Portfolios": [
            "us_portfolio_balanced_conservative",
            "us_portfolio_balanced_moderate",
            "us_portfolio_balanced_aggressive",
        ],
        "Income Portfolios": [
            "us_portfolio_dividend_aristocrats",
            "us_portfolio_high_yield",
            "us_portfolio_dividend_growth",
        ],
        "Growth Portfolios": [
            "us_portfolio_tech_growth",
            "us_portfolio_next_gen_tech",
            "us_portfolio_disruptive",
        ],
        "Value Portfolios": [
            "us_portfolio_deep_value",
            "us_portfolio_garp",
            "us_portfolio_quality_value",
        ],
        "Economic Cycle": [
            "us_portfolio_expansion",
            "us_portfolio_contraction",
            "us_portfolio_inflation_hedge",
        ],
        "Thematic": [
            "us_portfolio_aging_population",
            "us_portfolio_millennial",
            "us_portfolio_infrastructure",
            "us_portfolio_reshoring",
            "us_portfolio_water",
        ],
        "International": [
            "us_portfolio_global_leaders",
            "us_portfolio_emerging_markets",
        ],
        "Risk Parity": [
            "us_portfolio_all_weather",
            "us_portfolio_permanent",
            "us_portfolio_golden_butterfly",
        ],
    }

    for group_name, portfolio_list in groups.items():
        typer.echo(f"📌 {group_name}:")
        for portfolio in portfolio_list:
            if portfolio in portfolio_categories:
                count = portfolio_categories[portfolio]
                typer.echo(f"  • {portfolio}: {count} tickers")
        typer.echo()

    # Summary
    total_portfolios = len(portfolio_categories)
    total_tickers = sum(portfolio_categories.values())
    typer.echo("📊 Summary:")
    typer.echo(f"  Total portfolios: {total_portfolios}")
    typer.echo(f"  Total tickers across all portfolios: {total_tickers}")
    typer.echo()

    # Usage examples
    typer.echo("💡 Usage Examples:")
    typer.echo("  analyze --group us_portfolio_balanced_conservative")
    typer.echo("  analyze --group us_portfolio_dividend_growth")
    typer.echo("  analyze --group us_portfolio_tech_growth --llm")
    typer.echo("  analyze --group us_portfolio_all_weather")
    typer.echo()


@app.command()
def download_prices(
    market: str = typer.Option(
        None,
        "--market",
        "-m",
        help="Market to download: 'global', 'us', 'eu', 'nordic', or comma-separated (e.g., 'us,eu')",
    ),
    group: str = typer.Option(
        None,
        "--group",
        "-g",
        help="Ticker group: sector categories or portfolios. Comma-separated for multiple.",
    ),
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Comma-separated list of tickers to download (e.g., 'AAPL,MSFT,GOOGL')",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of instruments to download per market",
    ),
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: config/local.yaml or config/default.yaml)",
        exists=True,
    ),
    force_refresh: bool = typer.Option(
        False,
        "--force-refresh",
        help="Force re-download of all data (ignores existing cache)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be downloaded without actually downloading",
    ),
) -> None:
    """Download historical price data for tickers and store as CSV files.

    Fetches historical price data from configured providers and stores it
    in the cache directory as CSV files (one per ticker). Uses the lookback
    period defined in config (historical_data_lookback_days).

    Examples:
        # Download prices for specific tickers
        download-prices --ticker AAPL,MSFT,GOOGL

        # Download prices for a market
        download-prices --market us --limit 50

        # Download prices for a group
        download-prices --group us_tech_software

        # Download all markets with force refresh
        download-prices --market global --force-refresh

        # Dry run to see what would be downloaded
        download-prices --market nordic --dry-run
    """
    # Validate inputs
    if not market and not group and not ticker:
        typer.echo(
            "❌ Error: Either --market, --group, or --ticker must be provided\n"
            "Examples:\n"
            "  download-prices --market us\n"
            "  download-prices --group us_tech_software\n"
            "  download-prices --ticker AAPL,MSFT,GOOGL",
            err=True,
        )
        raise typer.Exit(code=1)

    if (market or group) and ticker:
        typer.echo("❌ Error: Cannot specify --ticker with --market or --group", err=True)
        raise typer.Exit(code=1)

    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        typer.echo("📥 Historical Price Data Downloader")
        typer.echo(f"  Provider: {config_obj.data.primary_provider}")
        typer.echo(f"  Lookback period: {config_obj.analysis.historical_data_lookback_days} days")

        # Determine tickers to download
        if ticker:
            tickers = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"  Mode: Specific tickers ({len(tickers)} specified)")
        elif group:
            groups = [g.strip() for g in group.split(",")]
            typer.echo(f"  Mode: Group analysis ({', '.join(groups)})")
            tickers = get_tickers_for_analysis(
                markets=None, categories=groups, limit_per_category=limit
            )
        else:
            markets_list = [m.strip().lower() for m in market.split(",")]
            typer.echo(f"  Mode: Market analysis ({', '.join(markets_list)})")
            tickers = get_tickers_for_markets(markets_list, limit=limit)

        typer.echo(f"  Tickers to process: {len(tickers)}")

        if dry_run:
            typer.echo("\n🔍 DRY RUN MODE - No data will be downloaded")
            typer.echo(f"\nTickers that would be processed ({len(tickers)}):")
            for i, t in enumerate(tickers[:20], 1):
                typer.echo(f"  {i}. {t}")
            if len(tickers) > 20:
                typer.echo(f"  ... and {len(tickers) - 20} more")
            return

        # Initialize components
        data_dir = Path("data")
        price_manager = PriceDataManager(prices_dir=data_dir / "cache" / "prices")
        provider_manager = ProviderManager(
            primary_provider=config_obj.data.primary_provider,
            backup_providers=config_obj.data.backup_providers,
            db_path=config_obj.database.db_path if config_obj.database.enabled else None,
            historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
        )

        # Initialize rate limiter (conservative: 5 requests per second)
        rate_limiter = RateLimiter(rate=5, period=1.0)

        # Use period parameter for fetching
        period = f"{config_obj.analysis.historical_data_lookback_days}d"
        typer.echo(f"  Period: {period}")
        if force_refresh:
            typer.echo("  Force refresh: enabled (will re-download all data)")
        typer.echo()

        # Download prices
        success_count = 0
        skipped_count = 0
        error_count = 0

        with typer.progressbar(
            tickers, label="Downloading prices", show_pos=True, show_percent=True
        ) as progress:
            for ticker in progress:
                try:
                    # Check if we need to download
                    if not force_refresh and price_manager.has_data(ticker):
                        # Check if data is relatively current (within last 2 days)
                        _, existing_end = price_manager.get_data_range(ticker)
                        if existing_end and (datetime.now().date() - existing_end).days <= 2:
                            logger.debug(f"Skipping {ticker} - data is current")
                            skipped_count += 1
                            continue

                    # Wait for rate limiter
                    rate_limiter.wait_if_needed(tokens=1)

                    # Fetch prices using provider manager with period parameter
                    prices = provider_manager.get_stock_prices(ticker, period=period)

                    if prices:
                        # Store to CSV
                        stored = price_manager.store_prices(
                            ticker,
                            [p.model_dump() for p in prices],
                            append=not force_refresh,
                        )
                        if stored > 0:
                            success_count += 1
                            logger.debug(f"Downloaded {len(prices)} prices for {ticker}")
                    else:
                        logger.warning(f"No price data received for {ticker}")
                        error_count += 1

                except KeyboardInterrupt:
                    typer.echo("\n\n⚠️  Download interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Error downloading {ticker}: {e}")
                    error_count += 1
                    # Small delay on error to avoid hammering the API
                    time.sleep(0.5)

        # Summary
        typer.echo("\n✅ Download Summary:")
        typer.echo(f"  Successfully downloaded: {success_count}")
        typer.echo(f"  Skipped (already current): {skipped_count}")
        typer.echo(f"  Errors: {error_count}")
        typer.echo(f"  Total processed: {success_count + skipped_count + error_count}")

        # Show storage location
        typer.echo(f"\n💾 Data stored in: {price_manager.prices_dir}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception(f"Unexpected error during download: {e}")
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
    config: Path = typer.Option(
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
            config_obj.database.db_path if config_obj.database.enabled else "data/nordinvest.db"
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
    config: Path = typer.Option(
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
            config_obj.database.db_path if config_obj.database.enabled else "data/nordinvest.db"
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
        raise typer.Exit(code=1)


@app.command()
def list_strategies() -> None:
    """List all available filtering strategies with descriptions.

    Shows:
    - Strategy name (to use with --strategy flag)
    - Description of what the strategy detects
    - Suitable use cases

    Example:
        nordinvest list-strategies
    """

    typer.echo("\n📊 Available Filtering Strategies\n")
    typer.echo("=" * 80)

    strategies = get_strategies()

    for name, description in strategies:
        typer.echo(f"\n🔹 {name.upper()}")
        typer.echo(f"   {description}")

    typer.echo(f"\n{'=' * 80}")
    typer.echo(f"\nTotal strategies: {len(strategies)}")
    typer.echo("\nUsage: nordinvest analyze --strategy <strategy_name>")
    typer.echo("Example: nordinvest analyze --group us_tech_software --strategy momentum\n")


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
