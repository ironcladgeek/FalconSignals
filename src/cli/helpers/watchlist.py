"""Watchlist helper functions for CLI commands."""

from datetime import date

from rich.console import Console
from rich.table import Table

from src.agents.llm import AITechnicalAnalysisAgent
from src.config.llm import initialize_llm_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


def run_watchlist_scan(
    ticker_list: list[str],
    config_obj,
    watchlist_repo,
    signal_repo,
    typer_instance,
) -> tuple[int, int]:
    """Run AI technical analysis on watchlist tickers.

    Args:
        ticker_list: List of ticker symbols to analyze
        config_obj: Configuration object
        watchlist_repo: Watchlist repository instance
        signal_repo: Watchlist signal repository instance
        typer_instance: Typer instance for output

    Returns:
        Tuple of (success_count, error_count)
    """
    # Initialize LLM client for AI analysis using centralized initialization
    llm_client = initialize_llm_client(config_obj.llm)

    # Initialize AI technical analysis agent in tactical mode for specific trading guidance
    agent = AITechnicalAnalysisAgent(
        llm_client=llm_client, config=config_obj, prompt_mode="tactical"
    )
    analysis_date = date.today()

    # Prepare context with lookback period and LLM client
    context = {
        "historical_data_lookback_days": config_obj.analysis.historical_data_lookback_days
        if hasattr(config_obj, "analysis")
        and hasattr(config_obj.analysis, "historical_data_lookback_days")
        else 730,
        "analysis_date": analysis_date,
        "llm_client": llm_client,
    }

    # Track results
    success_count = 0
    error_count = 0

    # Create results table
    table = Table(
        title=f"📊 Technical Analysis Results - {analysis_date}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Ticker", style="green", width=8)
    table.add_column("Score", justify="right", style="yellow", width=8)
    table.add_column("Action", style="magenta", width=10)
    table.add_column("Trend", style="cyan", width=10)
    table.add_column("RSI", justify="right", style="white", width=6)
    table.add_column("Status", style="blue", width=10)

    # Analyze each ticker
    for ticker_symbol in ticker_list:
        try:
            typer_instance.echo(f"  Analyzing {ticker_symbol}...", nl=False)

            # Update context with current ticker
            context["ticker"] = ticker_symbol

            # Execute technical analysis
            result = agent.execute("Analyze technical indicators", context)

            if result.get("status") == "error":
                typer_instance.echo(f" ❌ Error: {result.get('message', 'Unknown error')}")
                error_count += 1
                table.add_row(ticker_symbol, "-", "-", "-", "-", "❌ Error")
                continue

            # Extract results from AI agent (already includes confidence and action)
            score = result.get("technical_score", 0)
            confidence = result.get("confidence", 60.0)  # AI agent provides confidence
            action = result.get("action", "Wait")  # AI agent provides action directly
            rationale = result.get("rationale", "No rationale provided")
            trend = result.get("trend", "unknown")

            # Get current price from result or indicators
            current_price = result.get("current_price", 0)
            if not current_price:
                indicators = result.get("indicators", {})
                current_price = indicators.get("latest_price", 0)

            # Get RSI for display (from indicators if not in main result)
            rsi = result.get("rsi")
            if not rsi and "indicators" in result:
                indicators_dict = result.get("indicators", {})
                rsi = indicators_dict.get("rsi")

            # Extract tactical trading levels from AI analysis
            entry_price = result.get("entry_price")
            stop_loss = result.get("stop_loss")
            take_profit = result.get("take_profit")
            wait_for_price = result.get("wait_for_price")

            # Store signal in database with tactical levels
            success, message = signal_repo.store_signal(
                ticker_symbol=ticker_symbol,
                analysis_date=analysis_date,
                score=score,
                confidence=confidence,
                current_price=current_price,
                rationale=rationale,
                action=action,
                currency="USD",
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                wait_for_price=wait_for_price,
            )

            if success:
                typer_instance.echo(f" ✅ Score: {score:.0f}/100 | Action: {action}")
                success_count += 1

                # Add to table
                rsi_str = f"{rsi:.0f}" if rsi else "-"
                table.add_row(
                    ticker_symbol,
                    f"{score:.0f}",
                    action,
                    trend.capitalize(),
                    rsi_str,
                    "✅ Saved",
                )
            else:
                typer_instance.echo(f" ⚠️  Analysis complete but storage failed: {message}")
                error_count += 1
                rsi_str = f"{rsi:.0f}" if rsi else "-"
                table.add_row(
                    ticker_symbol,
                    f"{score:.0f}",
                    action,
                    trend.capitalize(),
                    rsi_str,
                    "⚠️  Warning",
                )

        except Exception as e:
            typer_instance.echo(f" ❌ Error: {e}")
            logger.error(f"Error analyzing {ticker_symbol}: {e}", exc_info=True)
            error_count += 1
            table.add_row(ticker_symbol, "-", "-", "-", "-", "❌ Error")

    # Display results table
    console = Console()
    console.print("\n")
    console.print(table)
    console.print(f"\n✅ Successfully analyzed: {success_count} ticker(s)", style="bold green")
    if error_count > 0:
        console.print(f"❌ Errors: {error_count} ticker(s)", style="bold red")
    console.print("\n")

    return success_count, error_count
