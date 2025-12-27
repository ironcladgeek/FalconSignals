"""Analysis helper functions for CLI commands."""

from datetime import datetime
from pathlib import Path

from src.analysis import InvestmentSignal
from src.analysis.signal_creator import SignalCreator
from src.llm.integration import LLMAnalysisOrchestrator
from src.llm.token_tracker import TokenTracker
from src.utils.logging import get_logger

logger = get_logger(__name__)


def run_llm_analysis(
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
        provider_manager: Provider manager instance
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

                    def agent_progress_callback(
                        current, total, task_name, task_tracker=current_task
                    ):
                        """Update progress display for agent tasks."""
                        if current > task_tracker[0]:
                            task_tracker[0] = current
                            # Show which agent is working
                            agent_name = task_name.replace("_", " ").title()
                            # Use regular newline instead of carriage return to avoid stdout pollution
                            typer_instance.echo(f"  → {agent_name} ({current}/{total})")

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
