"""Unified signal creation from analysis results.

This module provides a single SignalCreator class that creates InvestmentSignal
objects from UnifiedAnalysisResult, working identically for both LLM and rule-based modes.
"""

from datetime import date, datetime
from typing import Any, Optional

from src.analysis.metadata_extractor import extract_metadata_from_unified_result
from src.analysis.models import ComponentScores, InvestmentSignal, UnifiedAnalysisResult
from src.data.price_manager import PriceDataManager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SignalCreator:
    """Creates InvestmentSignal from unified analysis results.

    This class consolidates signal creation logic that was previously
    duplicated between LLM and rule-based modes, providing a single
    source of truth for both execution paths.
    """

    def __init__(
        self,
        cache_manager=None,
        provider_manager=None,
        risk_assessor=None,
        price_manager: Optional[PriceDataManager] = None,
    ):
        """Initialize signal creator.

        Args:
            cache_manager: Cache manager for price lookup (deprecated, use price_manager)
            provider_manager: Provider manager for price fetching (fallback)
            risk_assessor: Risk assessor for signal evaluation
            price_manager: PriceDataManager for unified CSV price storage
        """
        self.cache_manager = cache_manager
        self.provider_manager = provider_manager
        self.risk_assessor = risk_assessor
        self._price_manager = price_manager

    @property
    def price_manager(self) -> PriceDataManager:
        """Lazy-load PriceDataManager for unified CSV storage."""
        if self._price_manager is None:
            self._price_manager = PriceDataManager()
        return self._price_manager

    def create_signal(
        self,
        result: UnifiedAnalysisResult,
        portfolio_context: dict[str, Any] | None = None,
        analysis_date: date | None = None,
    ) -> InvestmentSignal | None:
        """Create investment signal from unified analysis result.

        This is the single function that creates signals for both LLM and
        rule-based modes, ensuring consistent behavior.

        Args:
            result: UnifiedAnalysisResult from either mode
            portfolio_context: Current portfolio state for risk assessment
            analysis_date: Date of analysis (for historical analysis)

        Returns:
            InvestmentSignal or None if creation failed
        """
        try:
            ticker = result.ticker
            logger.debug(f"Creating signal for {ticker} from {result.mode} mode analysis")

            # Fetch price (historical-aware)
            price_data = self._fetch_price(ticker, analysis_date)
            if not price_data:
                logger.error(
                    f"Cannot create signal for {ticker}: no valid price available "
                    f"for {analysis_date or 'current date'}"
                )
                return None

            current_price, currency = price_data

            # Extract metadata from unified result
            metadata = extract_metadata_from_unified_result(result)

            # Assess risks (use provided risk assessment or generate new one)
            risk_assessment = result.risk_assessment
            if not risk_assessment and self.risk_assessor and portfolio_context:
                risk_assessment = self._assess_risk(result, portfolio_context)

            # Create signal
            signal = InvestmentSignal(
                ticker=ticker,
                name=result.company_name or ticker,
                market=result.market or "unknown",
                sector=result.sector,
                current_price=current_price,
                currency=currency,
                scores=ComponentScores(
                    technical=result.technical.score,
                    fundamental=result.fundamental.score,
                    sentiment=result.sentiment.score,
                ),
                final_score=result.final_score,
                recommendation=result.recommendation,
                confidence=result.confidence,
                time_horizon=result.time_horizon,
                expected_return_min=result.expected_return_min,
                expected_return_max=result.expected_return_max,
                key_reasons=result.key_reasons,
                risk=risk_assessment,
                allocation=None,  # Will be calculated later by allocation module
                generated_at=datetime.now(),
                analysis_date=analysis_date.strftime("%Y-%m-%d")
                if analysis_date
                else datetime.now().strftime("%Y-%m-%d"),
                rationale=result.rationale,
                caveats=result.caveats,
                metadata=metadata,
            )

            logger.debug(
                f"Created signal for {ticker}: {signal.recommendation} "
                f"(score: {signal.final_score:.1f}, confidence: {signal.confidence:.1f})"
            )
            return signal

        except Exception as e:
            logger.error(f"Error creating signal for {result.ticker}: {e}", exc_info=True)
            return None

    def _fetch_price(
        self,
        ticker: str,
        analysis_date: date | None,
    ) -> tuple[float, str] | None:
        """Fetch price for ticker (historical-aware).

        This consolidates the price fetching logic that was duplicated in
        both old signal creation functions.

        Args:
            ticker: Stock ticker symbol
            analysis_date: Date of analysis (None for current)

        Returns:
            Tuple of (price, currency) or None if not found
        """
        is_historical = analysis_date and analysis_date < date.today()

        if is_historical:
            return self._fetch_historical_price(ticker, analysis_date)
        else:
            return self._fetch_current_price(ticker)

    def _fetch_historical_price(
        self,
        ticker: str,
        target_date: date,
    ) -> tuple[float, str] | None:
        """Fetch historical price for a specific date.

        Args:
            ticker: Stock ticker symbol
            target_date: Target date for price

        Returns:
            Tuple of (price, currency) or None if not found
        """
        logger.debug(
            f"Fetching historical price for {ticker} on {target_date} (analysis is in the past)"
        )

        # Try provider for historical data
        if not self.provider_manager:
            logger.warning(f"No provider_manager available for historical price fetch of {ticker}")
            return None

        try:
            # Fetch recent prices using period parameter (get 5 days to ensure we have target date)
            prices = self.provider_manager.get_stock_prices(ticker, period="5d")
            if not prices:
                logger.warning(f"No historical prices found for {ticker} around {target_date}")
                return None

            # Find exact date match
            for price in prices:
                price_date = price.date.date() if isinstance(price.date, datetime) else price.date
                if price_date == target_date:
                    logger.debug(
                        f"Found historical price for {ticker} on {target_date}: "
                        f"${price.close_price}"
                    )
                    return (float(price.close_price), price.currency)

            # If exact date not found, use most recent in range
            if prices:
                most_recent = prices[-1]
                logger.warning(
                    f"Exact price for {ticker} on {target_date} not found, "
                    f"using most recent in range: ${most_recent.close_price} "
                    f"from {most_recent.date}"
                )
                return (float(most_recent.close_price), most_recent.currency)

        except Exception as e:
            logger.error(f"Failed to fetch historical price for {ticker} on {target_date}: {e}")
            return None

        return None

    def _fetch_current_price(self, ticker: str) -> tuple[float, str] | None:
        """Fetch current/latest price for ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Tuple of (price, currency) or None if not found
        """
        logger.debug(f"Fetching current price for {ticker}")

        # Try unified CSV storage first (PriceDataManager)
        try:
            latest = self.price_manager.get_latest_price(ticker)
            if latest:
                price = float(latest["close"])
                currency = latest.get("currency", "USD")
                logger.debug(f"Got price for {ticker} from unified storage: ${price}")
                return (price, currency)
        except Exception as e:
            logger.debug(f"Unified storage lookup failed for {ticker}: {e}")

        # Try legacy cache (deprecated but kept for backward compatibility)
        if self.cache_manager:
            try:
                latest_price = self.cache_manager.get_latest_price(ticker)
                if latest_price and latest_price.close_price:
                    logger.debug(
                        f"Got price for {ticker} from legacy cache: ${latest_price.close_price}"
                    )
                    return (float(latest_price.close_price), latest_price.currency)
            except Exception as e:
                logger.debug(f"Legacy cache lookup failed for {ticker}: {e}")

        # Fallback to provider (fetch from API)
        if self.provider_manager:
            try:
                price_obj = self.provider_manager.get_latest_price(ticker)
                if price_obj and price_obj.close_price:
                    logger.debug(f"Got price for {ticker} from provider: ${price_obj.close_price}")
                    return (float(price_obj.close_price), price_obj.currency)
            except Exception as e:
                logger.warning(f"Provider lookup failed for {ticker}: {e}")

        logger.error(f"Could not fetch current price for {ticker} from any source")
        return None

    def _assess_risk(
        self,
        result: UnifiedAnalysisResult,
        portfolio_context: dict[str, Any],
    ):
        """Assess risk for the signal.

        Args:
            result: Unified analysis result
            portfolio_context: Current portfolio state

        Returns:
            RiskAssessment object
        """
        if not self.risk_assessor:
            logger.warning("No risk assessor available, skipping risk assessment")
            return None

        # Convert UnifiedAnalysisResult to format expected by risk assessor
        signal_dict = {
            "ticker": result.ticker,
            "final_score": result.final_score,
            "confidence": result.confidence,
            "scores": {
                "technical": result.technical.score,
                "fundamental": result.fundamental.score,
                "sentiment": result.sentiment.score,
            },
            "volatility_pct": 2.0,  # Placeholder - would come from technical data
            "estimated_daily_volume": 100000,  # Placeholder - would come from technical data
            "sector": result.sector or "Unknown",
        }

        try:
            return self.risk_assessor.assess_signal(signal_dict, portfolio_context)
        except Exception as e:
            logger.warning(f"Risk assessment failed for {result.ticker}: {e}")
            return None
