"""End-to-end analysis pipeline orchestration."""

from datetime import datetime
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
    ):
        """Initialize analysis pipeline.

        Args:
            config: Configuration dictionary with analysis parameters
            cache_manager: Cache manager for data caching
            portfolio_manager: Optional portfolio state manager for position tracking
        """
        self.config = config
        self.cache_manager = cache_manager
        self.portfolio_manager = portfolio_manager

        # Initialize components
        self.crew = AnalysisCrew()
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
        llm_configured, provider = check_llm_configuration()
        if llm_configured:
            logger.info(f"Analysis pipeline initialized with {provider} LLM")
        else:
            logger.warning(
                "Analysis pipeline initialized in RULE-BASED MODE. "
                "Using technical indicators and quantitative analysis without LLM. "
                "Signals will be based on price patterns, indicators, and simple rules."
            )

        logger.info("Analysis pipeline initialized")

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

        logger.info(f"Starting analysis pipeline for {len(tickers)} instruments")

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
                signal = self._create_investment_signal(analysis, portfolio_context)
                if signal:
                    signals.append(signal)

            logger.info(f"Generated {len(signals)} investment signals")

            # Phase 3: Generate portfolio allocation
            logger.debug("Phase 3: Generating portfolio allocation")
            # (Allocation is generated on-demand in reports, not here)

            return signals, self.portfolio_manager

        except Exception as e:
            logger.error(f"Error in analysis pipeline: {e}", exc_info=True)
            return signals, self.portfolio_manager

    def generate_daily_report(
        self,
        signals: list[InvestmentSignal],
        market_overview: str = "",
        generate_allocation: bool = True,
        report_date: str | None = None,
    ) -> DailyReport:
        """Generate daily analysis report from signals.

        Args:
            signals: List of investment signals
            market_overview: Optional market overview text
            generate_allocation: Whether to generate allocation suggestions
            report_date: Report date (YYYY-MM-DD), uses today if not provided

        Returns:
            Daily report object
        """
        logger.info(f"Generating daily report with {len(signals)} signals")

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
            )

            logger.info(f"Report generated: {report.strong_signals_count} strong signals")
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

    def _create_investment_signal(
        self,
        analysis: dict[str, Any],
        portfolio_context: dict[str, Any],
    ) -> InvestmentSignal | None:
        """Convert analysis result to investment signal with risk assessment.

        Args:
            analysis: Analysis result from crew
            portfolio_context: Current portfolio state

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
                current_price=100.0,  # Placeholder
                currency="EUR",
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
                    f"Confidence: {confidence}%",
                    f"Technical: {technical_score}/100",
                    f"Fundamental: {fundamental_score}/100",
                    f"Sentiment: {sentiment_score}/100",
                ],
                risk=risk_assessment,
                generated_at=datetime.now(),
                analysis_date=datetime.now().strftime("%Y-%m-%d"),
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
