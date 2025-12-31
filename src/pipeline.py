"""End-to-end analysis pipeline orchestration."""

from datetime import date, datetime
from typing import Any

from src.analysis import (
    AllocationEngine,
    DailyReport,
    InvestmentSignal,
    ReportGenerator,
    RiskAssessor,
)
from src.analysis.normalizer import AnalysisResultNormalizer
from src.analysis.signal_creator import SignalCreator
from src.cache.manager import CacheManager
from src.config.schemas import Config
from src.data.portfolio import PortfolioState
from src.data.provider_manager import ProviderManager
from src.orchestration import UnifiedAnalysisOrchestrator
from src.utils.llm_check import check_llm_configuration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisPipeline:
    """End-to-end analysis pipeline from data to reports."""

    def __init__(
        self,
        config: Config,
        cache_manager: CacheManager,
        portfolio_manager: PortfolioState | None = None,
        llm_provider: str | None = None,
        test_mode_config: Any | None = None,
        db_path: str | None = None,
        run_session_id: int | None = None,
        provider_manager: ProviderManager | None = None,
    ):
        """Initialize analysis pipeline.

        Args:
            config: Configuration object with all settings
            cache_manager: Cache manager for data caching
            portfolio_manager: Optional portfolio state manager for position tracking
            llm_provider: Optional LLM provider to check configuration for
            test_mode_config: Optional test mode configuration for fixtures/mock LLM
            db_path: Optional path to database for storing analyst ratings and recommendations
            run_session_id: Optional integer ID linking signals to a specific analysis run session
            provider_manager: Optional provider manager for fetching current prices
        """
        self.config = config
        self.cache_manager = cache_manager
        self.portfolio_manager = portfolio_manager
        self.test_mode_config = test_mode_config
        self.run_session_id = run_session_id
        self.provider_manager = provider_manager

        # Initialize database repositories if db_path provided
        self.recommendations_repo = None
        if db_path:
            from src.data.repository import RecommendationsRepository

            self.recommendations_repo = RecommendationsRepository(db_path)

        # Initialize components (rule-based mode by default)
        self.crew = UnifiedAnalysisOrchestrator(
            llm_mode=False,  # Rule-based mode by default in pipeline
            llm_provider=llm_provider,
            test_mode_config=test_mode_config,
            db_path=db_path,
            config=config,
        )
        self.risk_assessor = RiskAssessor(
            volatility_threshold_high=3.0,
            volatility_threshold_very_high=5.0,
        )
        self.allocation_engine = AllocationEngine(
            total_capital=config.capital.starting_capital_eur,
            monthly_deposit=config.capital.monthly_deposit_eur,
            max_position_size_pct=config.risk.max_position_size_percent,
            max_sector_concentration_pct=config.risk.max_sector_concentration_percent,
        )
        self.report_generator = ReportGenerator(include_disclaimers=True)

        # Check and log LLM configuration status
        llm_configured, provider = check_llm_configuration(llm_provider)
        if llm_configured:
            logger.debug(f"Analysis pipeline initialized with {provider} LLM")
        else:
            logger.warning(
                "Analysis pipeline initialized in RULE-BASED MODE. "
                "Using technical indicators and quantitative analysis without LLM. "
                "Signals will be based on price patterns, indicators, and simple rules."
            )

        logger.debug("Analysis pipeline initialized")

    def run_analysis(
        self,
        tickers: list[str],
        context: dict[str, Any] | None = None,
        llm_mode: bool = False,
        debug_llm: bool = False,
        progress_callback: Any = None,
    ) -> tuple[list[InvestmentSignal], PortfolioState | None]:
        """Execute full analysis pipeline for given tickers.

        Args:
            tickers: List of tickers to analyze
            context: Optional additional context
            llm_mode: If True, use LLM-powered analysis; if False, use rule-based
            debug_llm: Enable LLM debug mode (save inputs/outputs)
            progress_callback: Optional callback function(message: str) for progress updates

        Returns:
            Tuple of (signals, updated portfolio state)
        """
        context = context or {}
        context["tickers"] = tickers
        # Add configured lookback period to context for agents
        if hasattr(self.config, "analysis") and hasattr(
            self.config.analysis, "historical_data_lookback_days"
        ):
            context["historical_data_lookback_days"] = (
                self.config.analysis.historical_data_lookback_days
            )

        # Extract analysis_date from context for historical analysis support
        analysis_date = context.get("analysis_date") if context else None

        mode_label = "LLM-powered" if llm_mode else "rule-based"
        logger.debug(f"Starting {mode_label} analysis pipeline for {len(tickers)} instruments")

        signals = []

        try:
            # Create orchestrator based on mode
            if llm_mode:
                # LLM mode: Create fresh orchestrator with LLM components
                from pathlib import Path

                from src.llm.token_tracker import TokenTracker

                # Initialize token tracker
                data_dir = Path("data")
                tracker = TokenTracker(
                    self.config.token_tracker,
                    storage_dir=data_dir / "tracking",
                )

                # Setup debug directory if requested
                debug_dir = None
                if debug_llm:
                    debug_dir = data_dir / "llm_debug" / datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"LLM debug mode enabled: {debug_dir}")

                orchestrator = UnifiedAnalysisOrchestrator(
                    llm_mode=True,
                    llm_config=self.config.llm,
                    token_tracker=tracker,
                    enable_fallback=self.config.llm.enable_fallback,
                    debug_dir=debug_dir,
                    progress_callback=progress_callback,
                    db_path=self.config.database.db_path if self.config.database.enabled else None,
                    config=self.config,
                )

                # Set historical date on tools if provided
                if analysis_date:
                    logger.debug(f"Setting historical date {analysis_date} on LLM tools")
                    if hasattr(orchestrator, "tool_adapter"):
                        if hasattr(orchestrator.tool_adapter, "price_fetcher"):
                            orchestrator.tool_adapter.price_fetcher.set_historical_date(
                                analysis_date
                            )
                        if hasattr(orchestrator.tool_adapter, "fundamental_fetcher"):
                            orchestrator.tool_adapter.fundamental_fetcher.set_historical_date(
                                analysis_date
                            )
                        if hasattr(orchestrator.tool_adapter, "news_fetcher"):
                            orchestrator.tool_adapter.news_fetcher.set_historical_date(
                                analysis_date
                            )

                # Analyze instruments with LLM
                analysis_results = []
                for ticker in tickers:
                    try:
                        unified_result = orchestrator.analyze_instrument(ticker)
                        if unified_result:
                            analysis_results.append(unified_result)
                    except Exception as e:
                        logger.error(f"Error analyzing {ticker} with LLM: {e}")

                # Log token usage if available
                if hasattr(orchestrator, "token_tracker") and orchestrator.token_tracker:
                    daily_stats = orchestrator.token_tracker.get_daily_stats()
                    if daily_stats:
                        logger.debug(
                            f"Token usage: {daily_stats.total_input_tokens:,} input, "
                            f"{daily_stats.total_output_tokens:,} output, "
                            f"€{daily_stats.total_cost_eur:.2f}"
                        )

                analysis_mode = "llm"
                llm_model = self.config.llm.model
            else:
                # Rule-based mode: Use existing orchestrator
                logger.debug("Phase 1: Running rule-based crew analysis")
                analysis_result = self.crew.analyze_instruments(tickers, context)

                if analysis_result.get("status") != "success":
                    logger.error(f"Crew analysis failed: {analysis_result.get('message')}")
                    return signals, self.portfolio_manager

                # Normalize rule-based results to UnifiedAnalysisResult
                raw_results = analysis_result.get("analysis_results", [])
                analysis_results = []
                for analysis in raw_results:
                    try:
                        unified_result = AnalysisResultNormalizer.normalize_rule_based_result(
                            analysis
                        )
                        analysis_results.append(unified_result)
                    except Exception as e:
                        ticker = analysis.get("ticker", "UNKNOWN")
                        logger.warning(f"Failed to normalize analysis for {ticker}: {e}")

                analysis_mode = "rule_based"
                llm_model = None

            # Phase 2: Create signals from unified results
            logger.debug("Phase 2: Creating signals from analysis results")
            portfolio_context = self.portfolio_manager.to_dict() if self.portfolio_manager else {}

            # Initialize SignalCreator for unified signal creation
            signal_creator = SignalCreator(
                cache_manager=self.cache_manager,
                provider_manager=self.provider_manager,
                risk_assessor=self.risk_assessor,
            )

            for unified_result in analysis_results:
                try:
                    # Create signal using SignalCreator (unified for both modes)
                    signal = signal_creator.create_signal(
                        result=unified_result,
                        portfolio_context=portfolio_context,
                        analysis_date=analysis_date,
                    )

                    if signal:
                        signals.append(signal)

                        # Store signal to database if enabled
                        if self.recommendations_repo and self.run_session_id:
                            try:
                                self.recommendations_repo.store_recommendation(
                                    signal=signal,
                                    run_session_id=self.run_session_id,
                                    analysis_mode=analysis_mode,
                                    llm_model=llm_model,
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to store recommendation for {signal.ticker} to database: {e}"
                                )
                                # Continue execution - DB failures don't halt pipeline
                except Exception as e:
                    ticker = (
                        unified_result.ticker if hasattr(unified_result, "ticker") else "UNKNOWN"
                    )
                    logger.error(f"Error creating signal for {ticker}: {e}")

            logger.debug(f"Generated {len(signals)} investment signals")

            # Phase 3: Generate portfolio allocation
            logger.debug("Phase 3: Generating portfolio allocation")
            # (Allocation is generated on-demand in reports, not here)

            return signals, self.portfolio_manager

        except Exception as e:
            logger.error(f"Error in analysis pipeline: {e}", exc_info=True)
            return signals, self.portfolio_manager

    def generate_daily_report(
        self,
        signals: list[InvestmentSignal] | None = None,
        market_overview: str = "",
        generate_allocation: bool = True,
        report_date: str | None = None,
        analysis_mode: str = "rule_based",
        analyzed_category: str | None = None,
        analyzed_market: str | None = None,
        analyzed_tickers_specified: list[str] | None = None,
        initial_tickers: list[str] | None = None,
        tickers_with_anomalies: list[str] | None = None,
        force_full_analysis_used: bool = False,
        run_session_id: int | None = None,
    ) -> DailyReport:
        """Generate daily analysis report from signals or database.

        Priority: in-memory signals > run_session_id > report_date

        Args:
            signals: List of investment signals (optional - loads from DB if not provided)
            market_overview: Optional market overview text
            generate_allocation: Whether to generate allocation suggestions
            report_date: Report date (YYYY-MM-DD), uses today if not provided (also used to load from DB)
            analysis_mode: Analysis mode used ("llm" or "rule_based")
            analyzed_category: Category analyzed (e.g., us_tech_software)
            analyzed_market: Market analyzed (e.g., us, nordic, eu, global)
            analyzed_tickers_specified: Specific tickers analyzed (if --ticker was used)
            initial_tickers: Complete list of initial tickers before filtering
            tickers_with_anomalies: Tickers with anomalies from Stage 1 market scan (LLM mode)
            force_full_analysis_used: Whether --force-full-analysis flag was provided
            run_session_id: Load signals from this run session (if signals not provided)

        Returns:
            Daily report object
        """
        # Load signals from database if not provided in-memory
        data_source = "in-memory"
        if signals is None:
            if not self.recommendations_repo:
                raise ValueError(
                    "Database not enabled but no signals provided. "
                    "Either provide signals or enable database in config."
                )

            if run_session_id:
                logger.debug(f"Loading signals from run session: {run_session_id}")
                signals = self.recommendations_repo.get_recommendations_by_session(run_session_id)
                data_source = f"database (session: {run_session_id})"
            elif report_date:
                logger.debug(f"Loading signals for date: {report_date}")
                signals = self.recommendations_repo.get_recommendations_by_date(report_date)
                data_source = f"database (date: {report_date})"
            else:
                raise ValueError(
                    "Must provide signals, run_session_id, or report_date for report generation"
                )

            if not signals:
                logger.warning("No signals found in database for specified criteria")
                signals = []  # Empty list for report generation

        logger.debug(f"Generating daily report with {len(signals)} signals from {data_source}")

        try:
            # Generate allocation if requested
            allocation_suggestion = None
            if generate_allocation and signals:
                signal_dicts = [self._signal_to_dict(s) for s in signals]
                # Convert positions to dict format expected by allocation engine
                existing_positions = (
                    self.portfolio_manager.to_dict()["positions"]
                    if self.portfolio_manager
                    else None
                )
                allocation_suggestion = self.allocation_engine.allocate_signals(
                    signal_dicts,
                    existing_positions,
                )
                allocation_suggestion.generated_at = datetime.now()

            # Generate report
            report = self.report_generator.generate_daily_report(
                signals=signals,
                market_overview=market_overview,
                allocation_suggestion=allocation_suggestion,
                report_date=report_date,
                analysis_mode=analysis_mode,
                analyzed_category=analyzed_category,
                analyzed_market=analyzed_market,
                analyzed_tickers_specified=analyzed_tickers_specified,
                initial_tickers=initial_tickers,
                tickers_with_anomalies=tickers_with_anomalies,
                force_full_analysis_used=force_full_analysis_used,
            )

            logger.debug(f"Report generated: {report.strong_signals_count} strong signals")
            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            # Return minimal report on error
            return DailyReport(
                report_date=report_date or datetime.now().strftime("%Y-%m-%d"),
                report_time=datetime.now(),
                market_overview="Report generation failed",
                market_indices={},
                strong_signals=[],
                portfolio_alerts=[],
                key_news=[],
                watchlist_additions=[],
                watchlist_removals=[],
                total_signals_generated=len(signals),
                strong_signals_count=0,
                moderate_signals_count=0,
                disclaimers=self.report_generator.STANDARD_DISCLAIMERS,
                data_sources=self.report_generator.DATA_SOURCES,
            )

    @staticmethod
    def _get_analysis_date(context: dict[str, Any] | None) -> str:
        """Get analysis date from context, handling both date objects and strings.

        Args:
            context: Optional context dictionary

        Returns:
            Analysis date as string in YYYY-MM-DD format
        """
        if not context:
            logger.debug("No context provided, using current date")
            return datetime.now().strftime("%Y-%m-%d")

        analysis_date = context.get("analysis_date")
        if not analysis_date:
            logger.debug(
                f"No analysis_date in context (keys: {list(context.keys())}), using current date"
            )
            return datetime.now().strftime("%Y-%m-%d")

        # Handle date object
        if isinstance(analysis_date, date):
            result = analysis_date.strftime("%Y-%m-%d")
            logger.debug(f"Using analysis_date from context (date object): {result}")
            return result

        # Handle datetime object
        if isinstance(analysis_date, datetime):
            result = analysis_date.strftime("%Y-%m-%d")
            logger.debug(f"Using analysis_date from context (datetime object): {result}")
            return result

        # Already a string
        logger.debug(f"Using analysis_date from context (string): {analysis_date}")
        return str(analysis_date)

    @staticmethod
    def _signal_to_dict(signal: InvestmentSignal) -> dict[str, Any]:
        """Convert InvestmentSignal to dictionary for allocation engine.

        Args:
            signal: Investment signal object

        Returns:
            Dictionary representation
        """
        return {
            "ticker": signal.ticker,
            "name": signal.name,
            "market": signal.market,
            "sector": signal.sector,
            "current_price": signal.current_price,
            "confidence": signal.confidence,
            "final_score": signal.final_score,
            "recommendation": signal.recommendation.value,
            "expected_return_min": signal.expected_return_min,
            "expected_return_max": signal.expected_return_max,
        }
