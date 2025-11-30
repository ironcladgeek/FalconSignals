"""NordInvest CLI interface."""

import time
from datetime import datetime
from pathlib import Path

import typer

from src.analysis import InvestmentSignal
from src.analysis.models import ComponentScores, RiskAssessment
from src.cache.manager import CacheManager
from src.config import load_config
from src.data.portfolio import PortfolioState
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
    debug_llm: bool = False,
) -> tuple[list[InvestmentSignal], None]:
    """Run analysis using LLM-powered orchestrator.

    Args:
        tickers: List of tickers to analyze
        config_obj: Loaded configuration object
        typer_instance: Typer instance for output
        debug_llm: Enable LLM debug mode (save inputs/outputs)

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
        )

        typer_instance.echo(f"  LLM Provider: {config_obj.llm.provider}")
        typer_instance.echo(f"  Model: {config_obj.llm.model}")
        typer_instance.echo(f"  Temperature: {config_obj.llm.temperature}")
        typer_instance.echo("  Token tracking: enabled")

        # Analyze each ticker with LLM
        signals = []
        with typer_instance.progressbar(
            tickers, label="Analyzing instruments", show_pos=True, show_percent=True
        ) as progress:
            for ticker in progress:
                try:
                    # Create a sub-progress callback for agent tasks
                    task_names = [
                        "market_scan",
                        "technical_analysis",
                        "fundamental_analysis",
                        "sentiment_analysis",
                    ]
                    current_task = [0]  # Use list to allow mutation in nested function

                    def agent_progress_callback(current, total, task_name):
                        """Update progress display for agent tasks."""
                        if current > current_task[0]:
                            current_task[0] = current
                            # Show which agent is working
                            agent_name = task_name.replace("_", " ").title()
                            typer_instance.echo(f"  → {agent_name} ({current}/{total})", nl=False)
                            typer_instance.echo("\r", nl=False)  # Carriage return to overwrite

                    result = orchestrator.analyze_instrument(
                        ticker, progress_callback=agent_progress_callback
                    )

                    # Extract signal from result if successful
                    if result.get("status") == "complete":
                        # Use the synthesis result if available
                        synthesis_result = result.get("results", {}).get("synthesis", {})
                        if synthesis_result.get("status") == "success":
                            signal_data = synthesis_result.get("result", {})

                            # Handle CrewOutput object - extract the raw output
                            if hasattr(signal_data, "raw"):
                                signal_text = signal_data.raw
                            elif hasattr(signal_data, "result"):
                                signal_text = signal_data.result
                            else:
                                signal_text = str(signal_data)

                            # Create InvestmentSignal from LLM result
                            signal = _create_signal_from_llm_result(ticker, signal_text)
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


def _create_signal_from_llm_result(
    ticker: str,
    llm_result: dict | str,
) -> InvestmentSignal | None:
    """Convert LLM analysis result to InvestmentSignal.

    Args:
        ticker: Stock ticker
        llm_result: LLM analysis result (dict or JSON string)

    Returns:
        InvestmentSignal or None if conversion fails
    """
    try:
        # Parse LLM result if it's a string
        if isinstance(llm_result, str):
            import json
            import re

            # Clean up common formatting issues
            llm_result = llm_result.strip()

            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", llm_result, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group(1))
            else:
                # Try to find JSON object in the text (looking for balanced braces)
                # Find the first { and last }
                first_brace = llm_result.find("{")
                last_brace = llm_result.rfind("}")

                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_str = llm_result[first_brace : last_brace + 1]
                    try:
                        llm_result = json.loads(json_str)
                        logger.debug("Successfully extracted JSON from LLM response")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Could not parse extracted JSON: {e}")
                        logger.debug(f"Attempted to parse: {json_str[:500]}")
                        return None
                else:
                    logger.warning("No JSON object found in LLM result")
                    logger.debug(f"Response preview: {llm_result[:200]}")
                    return None

        # Map recommendation to enum values
        recommendation = llm_result.get("recommendation", "hold").lower()
        recommendation_map = {
            "strong_buy": "strong_buy",
            "buy": "buy",
            "hold_bullish": "hold_bullish",
            "hold": "hold",
            "hold_bearish": "hold_bearish",
            "sell": "sell",
            "strong_sell": "strong_sell",
        }
        recommendation = recommendation_map.get(recommendation, "hold")

        # Parse risk assessment with proper defaults
        risk_data = llm_result.get("risk", {})
        risk_level = risk_data.get("level", "medium").lower()
        # Map 'moderate' to 'medium' for compatibility
        if risk_level == "moderate":
            risk_level = "medium"

        risk_assessment = RiskAssessment(
            level=risk_level,
            volatility=risk_data.get("volatility", "normal"),
            volatility_pct=risk_data.get("volatility_pct", 2.0),
            liquidity=risk_data.get("liquidity", "normal"),
            concentration_risk=risk_data.get("concentration_risk", False),
            sector_risk=risk_data.get("sector_risk"),
            flags=risk_data.get("flags", risk_data.get("factors", [])),
        )

        # Create signal with proper schema
        from datetime import datetime

        signal = InvestmentSignal(
            ticker=ticker,
            name=llm_result.get("name", ticker),
            market=llm_result.get("market", "Global"),
            sector=llm_result.get("sector"),
            current_price=llm_result.get("current_price", 0.0),
            currency=llm_result.get("currency", "USD"),
            scores=ComponentScores(
                **llm_result.get(
                    "scores",
                    {
                        "technical": 50,
                        "fundamental": 50,
                        "sentiment": 50,
                    },
                )
            ),
            final_score=llm_result.get("final_score", 50.0),
            recommendation=recommendation,
            confidence=llm_result.get("confidence", 50.0),
            time_horizon=llm_result.get("time_horizon", "3M"),
            expected_return_min=llm_result.get("expected_return_min", 0.0),
            expected_return_max=llm_result.get("expected_return_max", 10.0),
            key_reasons=llm_result.get("key_reasons", []),
            risk=risk_assessment,
            allocation=None,  # Will be calculated later
            generated_at=datetime.now(),
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            rationale=llm_result.get("rationale"),
            caveats=llm_result.get("caveats", []),
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
    category: str = typer.Option(
        None,
        "--category",
        help="US ticker category: 'mega_cap', 'tech_software', 'ai_ml', 'cybersecurity', etc. Comma-separated for multiple (e.g., 'tech_software,ai_ml'). Use list-categories to see all options",
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
    debug_llm: bool = typer.Option(
        False,
        "--debug-llm",
        help="Save LLM inputs and outputs to data/llm_debug/ for inspection (only works with --llm)",
    ),
    test: bool = typer.Option(
        False,
        "--test",
        help="Run minimal test case with a single ticker (AAPL) to verify system functionality",
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

        # Analyze US categories
        analyze --category tech_software
        analyze --category ai_ml,cybersecurity --limit 30
        analyze --category mega_cap

        # Combine markets and categories
        analyze --market nordic --category tech_software
    """
    start_time = time.time()
    run_log = None
    signals_count = 0

    # Handle test mode
    if test:
        ticker = "AAPL"  # Use a single, well-known ticker for testing
        typer.echo("🧪 Running minimal test case...")
        typer.echo(f"  Test ticker: {ticker}")
        typer.echo(f"  Mode: {'LLM-powered' if use_llm else 'Rule-based'}")
        # Don't save report in test mode unless explicitly requested
        if save_report:
            save_report = False
            typer.echo("  Report saving: disabled (test mode)")

    # Validate that either market, category, ticker, or test is provided
    if not market and not category and not ticker and not test:
        typer.echo(
            "❌ Error: Either --market, --category, --ticker, or --test must be provided\n"
            "Examples:\n"
            "  analyze --test              # Quick test\n"
            "  analyze --test --llm        # Quick test with LLM\n"
            "  analyze --market global\n"
            "  analyze --market us\n"
            "  analyze --category tech_software\n"
            "  analyze --category ai_ml,cybersecurity --limit 30\n"
            "  analyze --market us,eu --limit 50\n"
            "  analyze --ticker AAPL,MSFT,GOOGL",
            err=True,
        )
        raise typer.Exit(code=1)

    if (market or category) and ticker:
        typer.echo("❌ Error: Cannot specify --ticker with --market or --category", err=True)
        raise typer.Exit(code=1)

    if test and (market or category or (ticker and not ticker == "AAPL")):
        typer.echo("❌ Error: Cannot use --test with --market, --category, or --ticker", err=True)
        raise typer.Exit(code=1)

    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

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

        pipeline_config = {
            "capital_starting": config_obj.capital.starting_capital_eur,
            "capital_monthly_deposit": config_obj.capital.monthly_deposit_eur,
            "max_position_size_pct": 10.0,
            "max_sector_concentration_pct": 20.0,
            "include_disclaimers": True,
        }

        pipeline = AnalysisPipeline(
            pipeline_config, cache_manager, portfolio_manager, llm_provider=config_obj.llm.provider
        )

        # Determine which tickers to analyze
        if ticker:
            # Parse comma-separated tickers
            ticker_list = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"\n📊 Running analysis on {len(ticker_list)} specified instruments...")
            typer.echo(f"  Tickers: {', '.join(ticker_list)}")
        elif category:
            # Parse category specification
            categories = [c.strip().lower() for c in category.split(",")]
            typer.echo(
                f"\n📊 Running analysis for category(ies): {', '.join(categories).upper()}..."
            )

            # Validate categories
            available_categories = get_us_categories()
            invalid_categories = [c for c in categories if c not in available_categories]
            if invalid_categories:
                typer.echo(
                    f"❌ Error: Invalid category(ies): {', '.join(invalid_categories)}",
                    err=True,
                )
                typer.echo("Available categories:", err=True)
                for cat_name, count in sorted(available_categories.items()):
                    typer.echo(f"  {cat_name}: {count} tickers", err=True)
                raise typer.Exit(code=1)

            # Get tickers from categories, optionally combined with markets
            if market:
                markets = (
                    ["global"]
                    if market.lower() == "global"
                    else [m.strip().lower() for m in market.split(",")]
                )
                if market.lower() == "global":
                    markets = ["nordic", "eu"]
                ticker_list = get_tickers_for_analysis(
                    markets=markets, categories=categories, limit_per_category=limit
                )
                typer.echo(f"  Markets: {', '.join(markets).upper()}")
            else:
                ticker_list = get_tickers_for_analysis(
                    categories=categories, limit_per_category=limit
                )

            if limit:
                typer.echo(f"  Limit: {limit} instruments per category")
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

        # Run analysis (LLM or rule-based)
        if use_llm:
            typer.echo("\n🤖 Using LLM-powered analysis (CrewAI with intelligent agents)")
            signals, portfolio_manager = _run_llm_analysis(
                ticker_list, config_obj, typer, debug_llm
            )
            analysis_mode = "llm"
        else:
            typer.echo(
                "\n📊 Using rule-based analysis (technical indicators & fundamental metrics)"
            )
            signals, portfolio_manager = pipeline.run_analysis(ticker_list)
            analysis_mode = "rule_based"
        signals_count = len(signals)

        if signals:
            typer.echo(f"✓ Analysis complete: {signals_count} signals generated")

            # Generate report
            typer.echo("\n📋 Generating report...")
            report = pipeline.generate_daily_report(
                signals,
                generate_allocation=True,
                analysis_mode=analysis_mode,
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
def list_categories() -> None:
    """List all available US ticker categories.

    Shows all category names with the number of tickers in each.
    Use these category names with the `analyze --category` option.
    """
    categories = get_us_categories()

    typer.echo("\n🇺🇸 Available US Ticker Categories:\n")

    # Group by type for better readability
    groups = {
        "Market Cap": ["mega_cap", "large_cap", "mid_cap", "small_cap"],
        "Technology": [
            "tech",
            "tech_software",
            "tech_semiconductors",
            "tech_hardware",
            "tech_internet",
        ],
        "Healthcare": ["healthcare", "healthcare_pharma", "healthcare_devices"],
        "Financials": [
            "financials",
            "financials_banks",
            "financials_fintech",
            "financials_asset_mgmt",
        ],
        "Consumer": ["consumer", "consumer_retail", "consumer_food_bev", "consumer_restaurants"],
        "Other Sectors": [
            "industrials",
            "energy",
            "clean_energy",
            "utilities",
            "real_estate",
            "materials",
            "communication",
            "transportation",
        ],
        "Themes": [
            "ai_ml",
            "cybersecurity",
            "cloud_computing",
            "space_defense",
            "ev_autonomous",
            "biotech_genomics",
            "quantum_computing",
        ],
        "ETFs": [
            "etfs",
            "etfs_broad_market",
            "etfs_sector",
            "etfs_fixed_income",
            "etfs_international",
            "etfs_thematic",
            "etfs_dividend",
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
    typer.echo("  analyze --category tech_software")
    typer.echo("  analyze --category ai_ml,cybersecurity --limit 30")
    typer.echo("  analyze --market nordic --category tech_software")
    typer.echo()


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
