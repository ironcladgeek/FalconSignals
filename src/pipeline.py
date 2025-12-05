"""End-to-end analysis pipeline orchestration."""

from datetime import date, datetime
from typing import Any

from src.agents import AnalysisCrew
from src.analysis import (
    AllocationEngine,
    DailyReport,
    InvestmentSignal,
    ReportGenerator,
    RiskAssessor,
)
from src.cache.manager import CacheManager
from src.data.portfolio import PortfolioState
from src.data.provider_manager import ProviderManager
from src.utils.llm_check import check_llm_configuration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisPipeline:
    """End-to-end analysis pipeline from data to reports."""

    def __init__(
        self,
        config: dict[str, Any],
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
            config: Configuration dictionary with analysis parameters
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

        # Initialize components
        self.crew = AnalysisCrew(
            llm_provider=llm_provider, test_mode_config=test_mode_config, db_path=db_path
        )
        self.risk_assessor = RiskAssessor(
            volatility_threshold_high=config.get("risk_volatility_high", 3.0),
            volatility_threshold_very_high=config.get("risk_volatility_very_high", 5.0),
        )
        self.allocation_engine = AllocationEngine(
            total_capital=config.get("capital_starting", 2000),
            monthly_deposit=config.get("capital_monthly_deposit", 500),
            max_position_size_pct=config.get("max_position_size_pct", 10),
            max_sector_concentration_pct=config.get("max_sector_concentration_pct", 20),
        )
        self.report_generator = ReportGenerator(
            include_disclaimers=config.get("include_disclaimers", True)
        )

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
    ) -> tuple[list[InvestmentSignal], PortfolioState | None]:
        """Execute full analysis pipeline for given tickers.

        Args:
            tickers: List of tickers to analyze
            context: Optional additional context

        Returns:
            Tuple of (signals, updated portfolio state)
        """
        context = context or {}
        context["tickers"] = tickers

        logger.debug(f"Starting analysis pipeline for {len(tickers)} instruments")

        signals = []

        try:
            # Phase 1: Execute crew analysis
            logger.debug("Phase 1: Running crew analysis")
            scan_result = self.crew.scan_and_analyze(tickers, context)

            if scan_result.get("status") != "success":
                logger.error(f"Crew analysis failed: {scan_result.get('message')}")
                return signals, self.portfolio_manager

            analysis_results = scan_result.get("analysis_results", [])

            # Phase 2: Convert to signals with risk assessment
            logger.debug("Phase 2: Assessing risks and creating signals")
            portfolio_context = self.portfolio_manager.to_dict() if self.portfolio_manager else {}

            for analysis in analysis_results:
                signal = self._create_investment_signal(analysis, portfolio_context, context)
                if signal:
                    signals.append(signal)

                    # Store signal to database if enabled
                    if self.recommendations_repo and self.run_session_id:
                        try:
                            self.recommendations_repo.store_recommendation(
                                signal=signal,
                                run_session_id=self.run_session_id,
                                analysis_mode="rule_based",
                                llm_model=None,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to store recommendation for {signal.ticker} to database: {e}"
                            )
                            # Continue execution - DB failures don't halt pipeline

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
                logger.warning(f"No signals found in database for specified criteria")
                signals = []  # Empty list for report generation

        logger.debug(f"Generating daily report with {len(signals)} signals from {data_source}")

        try:
            # Generate allocation if requested
            allocation_suggestion = None
            if generate_allocation and signals:
                signal_dicts = [self._signal_to_dict(s) for s in signals]
                allocation_suggestion = self.allocation_engine.allocate_signals(
                    signal_dicts,
                    self.portfolio_manager.positions if self.portfolio_manager else None,
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

    def _create_investment_signal(
        self,
        analysis: dict[str, Any],
        portfolio_context: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> InvestmentSignal | None:
        """Convert analysis result to investment signal with risk assessment.

        Args:
            analysis: Analysis result from crew
            portfolio_context: Current portfolio state
            context: Optional context with analysis_date for backtesting

        Returns:
            Investment signal or None if creation failed
        """
        try:
            ticker = analysis.get("ticker", "UNKNOWN")
            final_score = analysis.get("final_score", 50)
            confidence = analysis.get("confidence", 50)
            recommendation = analysis.get("final_recommendation", "hold")

            # Extract component scores
            analysis_data = analysis.get("analysis", {})
            technical_score = analysis_data.get("technical", {}).get("technical_score", 50)
            fundamental_score = analysis_data.get("fundamental", {}).get("fundamental_score", 50)
            sentiment_score = analysis_data.get("sentiment", {}).get("sentiment_score", 50)

            # Get analysis date to determine if we need historical or current price
            analysis_date_str = self._get_analysis_date(context)
            analysis_date = datetime.strptime(analysis_date_str, "%Y-%m-%d").date()
            is_historical = analysis_date < date.today()

            # Fetch actual current price and currency from cache or provider
            current_price = None
            currency = "USD"

            if is_historical:
                # For historical analysis, fetch price as of analysis_date
                logger.debug(
                    f"Historical analysis for {ticker} on {analysis_date}, "
                    f"fetching price as of that date"
                )

                # Try cache first (historical data might be cached)
                try:
                    # Cache might have historical prices - look for price data around that date
                    latest_price = self.cache_manager.get_latest_price(ticker)
                    if latest_price:
                        # This is current price from cache, not historical
                        # We'll need to fetch historical from provider
                        logger.debug(
                            f"Cache has current price, but we need historical for {analysis_date}"
                        )
                except Exception as e:
                    logger.debug(f"Cache lookup failed for {ticker}: {e}")

                # Fetch historical price from provider
                if current_price is None and self.provider_manager:
                    try:
                        # Fetch prices for a small window around analysis_date
                        from datetime import timedelta

                        start_date = datetime.combine(analysis_date, datetime.min.time())
                        end_date = datetime.combine(
                            analysis_date + timedelta(days=1), datetime.min.time()
                        )

                        prices = self.provider_manager.get_stock_prices(
                            ticker, start_date, end_date
                        )
                        if prices:
                            # Get the price closest to analysis_date
                            for price in prices:
                                if price.date == analysis_date:
                                    current_price = price.close_price
                                    currency = price.currency
                                    logger.debug(
                                        f"Got historical price for {ticker} on {analysis_date}: "
                                        f"${current_price}"
                                    )
                                    break
                            # If exact date not found, use the closest one
                            if current_price is None and prices:
                                current_price = prices[0].close_price
                                currency = prices[0].currency
                                logger.warning(
                                    f"Exact price for {ticker} on {analysis_date} not found, "
                                    f"using closest: ${current_price}"
                                )
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch historical price for {ticker} on {analysis_date}: {e}"
                        )
            else:
                # For current analysis, use latest price
                logger.debug(f"Current analysis for {ticker}, fetching latest price")

                # Try cache first
                try:
                    latest_price = self.cache_manager.get_latest_price(ticker)
                    if latest_price:
                        current_price = latest_price.close_price
                        currency = latest_price.currency
                        logger.debug(f"Got price for {ticker} from cache: ${current_price}")
                except Exception as e:
                    logger.debug(f"Cache lookup failed for {ticker}: {e}")

                # If cache didn't have it, try provider
                if current_price is None and self.provider_manager:
                    try:
                        price_obj = self.provider_manager.get_latest_price(ticker)
                        if price_obj:
                            current_price = price_obj.close_price
                            currency = price_obj.currency
                            logger.debug(f"Got price for {ticker} from provider: ${current_price}")
                    except Exception as e:
                        logger.warning(f"Provider lookup failed for {ticker}: {e}")

            # If we still don't have a price, we cannot create a valid signal
            if current_price is None or current_price <= 0:
                logger.error(
                    f"Cannot create signal for {ticker}: no valid current price available "
                    f"for {analysis_date}. Ensure price data is cached or provider_manager is configured."
                )
                return None

            current_price = float(current_price)

            # Assess risks
            signal_dict = {
                "ticker": ticker,
                "final_score": final_score,
                "confidence": confidence,
                "scores": {
                    "technical": technical_score,
                    "fundamental": fundamental_score,
                    "sentiment": sentiment_score,
                },
                "volatility_pct": 2.0,  # Placeholder
                "estimated_daily_volume": 100000,  # Placeholder
                "sector": "Unknown",  # Would come from metadata
            }

            risk_assessment = self.risk_assessor.assess_signal(signal_dict, portfolio_context)

            # Calculate expected returns (placeholder)
            expected_return_min = (final_score - 50) * 0.2  # -10% to +10%
            expected_return_max = expected_return_min + 10

            # Create signal
            signal = InvestmentSignal(
                ticker=ticker,
                name=analysis.get("ticker", "Unknown"),
                market="unknown",
                sector=None,
                current_price=current_price,
                currency=currency,
                scores=analysis_data.get("synthesis", {}).get("component_scores")
                or {
                    "technical": technical_score,
                    "fundamental": fundamental_score,
                    "sentiment": sentiment_score,
                },
                final_score=final_score,
                recommendation=recommendation,
                confidence=confidence,
                time_horizon="3M",
                expected_return_min=expected_return_min,
                expected_return_max=expected_return_max,
                key_reasons=[
                    analysis.get("final_recommendation", "hold").upper(),
                    f"Confidence: {confidence:.2f}%",
                    f"Technical: {technical_score:.2f}/100",
                    f"Fundamental: {fundamental_score:.2f}/100",
                    f"Sentiment: {sentiment_score:.2f}/100",
                ],
                risk=risk_assessment,
                generated_at=datetime.now(),
                analysis_date=self._get_analysis_date(context),
            )

            logger.debug(f"Created signal for {ticker}: {recommendation} ({confidence}%)")
            return signal

        except Exception as e:
            logger.error(f"Error creating signal from analysis: {e}")
            return None

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
