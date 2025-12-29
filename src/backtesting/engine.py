"""Core backtesting orchestration engine.

This module provides the BacktestEngine class that orchestrates historical analysis
across date ranges by reusing existing analysis pipeline logic.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from src.backtesting.config import BacktestConfig, BacktestFrequency
from src.backtesting.models import BacktestResult
from src.cache.manager import CacheManager
from src.cli.helpers.analysis import run_llm_analysis
from src.config import Config
from src.data.historical import HistoricalDataFetcher
from src.data.provider_manager import ProviderManager
from src.data.repository import RecommendationsRepository, RunSessionRepository
from src.pipeline import AnalysisPipeline


class BacktestEngine:
    """Orchestrates historical analysis across date ranges.

    Reuses existing analysis pipeline logic (both LLM and rule-based) to generate
    recommendations for multiple dates, enabling validation of recommendation quality
    through historical analysis.

    Example:
        engine = BacktestEngine(config, backtest_config, provider_manager, cache_manager)
        result = engine.run(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            tickers=["AAPL", "MSFT"],
            frequency="weekly",
            analysis_mode="rule_based"
        )
    """

    def __init__(
        self,
        config: Config,
        backtest_config: BacktestConfig,
        provider_manager: ProviderManager,
        cache_manager: CacheManager,
        db_path: Path | None = None,
    ):
        """Initialize backtesting engine.

        Args:
            config: Application configuration.
            backtest_config: Backtesting-specific configuration.
            provider_manager: Data provider manager.
            cache_manager: Cache manager for data caching.
            db_path: Optional path to database (for storing results).
        """
        self.config = config
        self.backtest_config = backtest_config
        self.provider_manager = provider_manager
        self.cache_manager = cache_manager
        self.db_path = db_path

        # Initialize repositories if database enabled
        self.session_repo = None
        self.recommendations_repo = None
        if db_path:
            self.session_repo = RunSessionRepository(db_path)
            self.recommendations_repo = RecommendationsRepository(db_path)

    def run(
        self,
        start_date: date,
        end_date: date,
        tickers: list[str],
        frequency: str = "weekly",
        analysis_mode: str = "rule_based",
        dry_run: bool = False,
    ) -> BacktestResult:
        """Run backtest across date range.

        Args:
            start_date: Start date of backtest period.
            end_date: End date of backtest period.
            tickers: List of ticker symbols to analyze.
            frequency: Analysis frequency (daily, weekly, monthly).
            analysis_mode: Analysis mode (rule_based, llm).
            dry_run: If True, only estimate cost and plan without executing.

        Returns:
            BacktestResult with metadata and references to generated recommendations.

        Raises:
            ValueError: If invalid frequency or analysis mode.
        """
        logger.info(
            f"Starting backtest: {start_date} to {end_date}, "
            f"frequency={frequency}, mode={analysis_mode}"
        )

        # Validate inputs
        if frequency not in ["daily", "weekly", "monthly"]:
            raise ValueError(f"Invalid frequency: {frequency}. Must be daily, weekly, or monthly")

        if analysis_mode not in ["rule_based", "llm"]:
            raise ValueError(f"Invalid analysis_mode: {analysis_mode}. Must be rule_based or llm")

        # Generate analysis dates
        analysis_dates = self._generate_dates(start_date, end_date, frequency)
        total_analyses = len(analysis_dates) * len(tickers)

        logger.info(
            f"Generated {len(analysis_dates)} analysis dates for {len(tickers)} tickers "
            f"= {total_analyses} total analyses"
        )

        # Estimate cost for LLM mode
        estimated_cost = None
        if analysis_mode == "llm":
            estimated_cost = self._estimate_cost(total_analyses)
            logger.info(f"Estimated LLM cost: €{estimated_cost:.2f}")

            if dry_run:
                # Return early with estimated plan
                return BacktestResult(
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    analysis_mode=analysis_mode,
                    tickers=tickers,
                    analysis_dates=analysis_dates,
                    total_analyses=total_analyses,
                    successful_analyses=0,
                    failed_analyses=0,
                    estimated_cost=estimated_cost,
                )

        # Track execution
        started_at = datetime.now()
        run_session_ids: list[int] = []
        recommendation_count = 0
        successful_analyses = 0
        failed_analyses = 0
        errors: list[dict[str, Any]] = []

        # Run analyses for each date
        for analysis_date in analysis_dates:
            logger.info(f"Running analysis for date: {analysis_date}")

            # Run analysis for this date
            try:
                session_id, signals_count, date_errors = self._run_analysis_for_date(
                    analysis_date=analysis_date,
                    tickers=tickers,
                    analysis_mode=analysis_mode,
                )

                if session_id:
                    run_session_ids.append(session_id)
                    recommendation_count += signals_count
                    successful_analyses += signals_count
                    failed_analyses += len(tickers) - signals_count

                    # Track errors for this date
                    errors.extend(date_errors)

            except Exception as e:
                logger.error(f"Error running analysis for {analysis_date}: {e}", exc_info=True)
                failed_analyses += len(tickers)
                errors.append(
                    {
                        "date": str(analysis_date),
                        "ticker": "all",
                        "error": str(e),
                    }
                )

        # Calculate actual cost (for LLM mode)
        completed_at = datetime.now()
        duration_seconds = (completed_at - started_at).total_seconds()
        actual_cost = None
        if analysis_mode == "llm":
            # TODO: Get actual cost from token tracker
            # For now, use estimate as placeholder
            actual_cost = estimated_cost

        # Build result
        result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            analysis_mode=analysis_mode,
            tickers=tickers,
            analysis_dates=analysis_dates,
            total_analyses=total_analyses,
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            run_session_ids=run_session_ids,
            recommendation_count=recommendation_count,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            errors=errors,
        )

        logger.info(
            f"Backtest complete: {successful_analyses} successful, "
            f"{failed_analyses} failed, {len(errors)} errors"
        )

        return result

    def _generate_dates(self, start_date: date, end_date: date, frequency: str) -> list[date]:
        """Generate list of analysis dates based on frequency.

        Args:
            start_date: Start date of range.
            end_date: End date of range.
            frequency: Frequency (daily, weekly, monthly).

        Returns:
            List of dates for analysis.
        """
        dates: list[date] = []
        current = start_date

        if frequency == BacktestFrequency.DAILY.value:
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=1)

        elif frequency == BacktestFrequency.WEEKLY.value:
            while current <= end_date:
                dates.append(current)
                current += timedelta(weeks=1)

        elif frequency == BacktestFrequency.MONTHLY.value:
            while current <= end_date:
                dates.append(current)
                # Move to next month (handle month boundary)
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        return dates

    def _estimate_cost(self, total_analyses: int) -> float:
        """Estimate LLM cost for backtest.

        Args:
            total_analyses: Total number of analyses to run.

        Returns:
            Estimated cost in EUR.
        """
        # Average cost per ticker analysis (empirical from production)
        # This is a rough estimate: €0.50-0.80 per ticker
        avg_cost_per_ticker = 0.65

        estimated_cost = total_analyses * avg_cost_per_ticker

        logger.debug(
            f"Cost estimation: {total_analyses} analyses × €{avg_cost_per_ticker:.2f} "
            f"= €{estimated_cost:.2f}"
        )

        return estimated_cost

    def _run_analysis_for_date(
        self, analysis_date: date, tickers: list[str], analysis_mode: str
    ) -> tuple[int | None, int, list[dict[str, Any]]]:
        """Run analysis for a specific date.

        Reuses existing analysis pipeline logic (DRY principle).

        Args:
            analysis_date: Date for historical analysis.
            tickers: List of tickers to analyze.
            analysis_mode: Analysis mode (rule_based, llm).

        Returns:
            Tuple of (session_id, signals_count, errors).
        """
        errors: list[dict[str, Any]] = []
        session_id = None
        signals_count = 0

        try:
            # Create run session
            if self.session_repo:
                session_id = self.session_repo.create_session(
                    analysis_mode=analysis_mode,
                    analyzed_tickers_specified=tickers,
                    initial_tickers_count=len(tickers),
                    anomalies_count=0,  # Backtesting doesn't use filtering
                    force_full_analysis=True,  # Backtesting always analyzes all tickers
                )

            # Fetch historical context for all tickers
            historical_context_data = self._fetch_historical_context(analysis_date, tickers)

            # Run appropriate analysis mode
            if analysis_mode == "llm":
                signals, _ = self._run_llm_analysis_internal(
                    tickers=tickers,
                    historical_date=analysis_date,
                    run_session_id=session_id,
                )
            else:
                signals, _ = self._run_rule_based_analysis(
                    tickers=tickers,
                    historical_context_data=historical_context_data,
                    historical_date=analysis_date,
                    run_session_id=session_id,
                )

            signals_count = len(signals)

            # Update session status
            if self.session_repo and session_id:
                initial_count = len(tickers)
                failed_count = initial_count - signals_count

                status = "completed" if signals_count == initial_count else "partial"
                self.session_repo.complete_session(
                    session_id=session_id,
                    signals_generated=signals_count,
                    signals_failed=failed_count,
                    status=status,
                )

        except Exception as e:
            logger.error(f"Error in analysis for {analysis_date}: {e}", exc_info=True)
            errors.append(
                {
                    "date": str(analysis_date),
                    "ticker": "all",
                    "error": str(e),
                }
            )

        return session_id, signals_count, errors

    def _fetch_historical_context(self, analysis_date: date, tickers: list[str]) -> dict[str, Any]:
        """Fetch historical context for all tickers.

        Args:
            analysis_date: Date for which to fetch historical data.
            tickers: List of tickers.

        Returns:
            Dictionary mapping ticker to HistoricalContext.
        """
        historical_context_data = {}

        # Initialize historical data fetcher
        primary_provider = self.provider_manager.primary_provider
        historical_fetcher = HistoricalDataFetcher(
            primary_provider, cache_manager=self.cache_manager
        )

        # Fetch context for each ticker
        for ticker in tickers:
            try:
                context = historical_fetcher.fetch_as_of_date(
                    ticker, analysis_date, lookback_days=365
                )
                historical_context_data[ticker] = context
            except Exception as e:
                logger.warning(f"Error fetching historical data for {ticker}: {e}")
                historical_context_data[ticker] = None

        return historical_context_data

    def _run_llm_analysis_internal(
        self,
        tickers: list[str],
        historical_date: date,
        run_session_id: int | None,
    ) -> tuple[list, Any]:
        """Run LLM analysis (reuses existing helper).

        Args:
            tickers: List of tickers to analyze.
            historical_date: Date for historical analysis.
            run_session_id: Run session ID for tracking.

        Returns:
            Tuple of (signals, portfolio_manager).
        """

        # Use a minimal typer interface for logging
        class MinimalTyper:
            """Minimal typer interface for silent operation."""

            def echo(self, message: str, err: bool = False) -> None:
                """Log message instead of printing."""
                if err:
                    logger.error(message)
                else:
                    logger.debug(message)

        typer_instance = MinimalTyper()

        # Reuse existing LLM analysis helper (DRY principle)
        signals, portfolio_manager = run_llm_analysis(
            tickers=tickers,
            config_obj=self.config,
            typer_instance=typer_instance,
            debug_llm=False,
            is_filtered=True,  # Backtesting doesn't filter
            cache_manager=self.cache_manager,
            provider_manager=self.provider_manager,
            historical_date=historical_date,
            run_session_id=run_session_id,
            recommendations_repo=self.recommendations_repo,
        )

        return signals, portfolio_manager

    def _run_rule_based_analysis(
        self,
        tickers: list[str],
        historical_context_data: dict[str, Any],
        historical_date: date,
        run_session_id: int | None,
    ) -> tuple[list, Any]:
        """Run rule-based analysis (reuses existing pipeline).

        Args:
            tickers: List of tickers to analyze.
            historical_context_data: Historical context for each ticker.
            historical_date: Date for historical analysis.
            run_session_id: Run session ID for tracking.

        Returns:
            Tuple of (signals, portfolio_manager).
        """
        # Initialize pipeline (reuses existing logic - DRY principle)
        pipeline = AnalysisPipeline(
            config=self.config,
            cache_manager=self.cache_manager,
            portfolio_manager=None,
            db_path=str(self.db_path) if self.db_path else None,
        )

        # Set provider manager for historical price fetching
        pipeline.provider_manager = self.provider_manager

        # Set run session ID
        pipeline.run_session_id = run_session_id

        # Prepare analysis context
        analysis_context = {}
        if historical_context_data:
            analysis_context["historical_contexts"] = historical_context_data
            analysis_context["analysis_date"] = historical_date

        # Run analysis
        signals, portfolio_manager = pipeline.run_analysis(tickers, analysis_context)

        return signals, portfolio_manager
