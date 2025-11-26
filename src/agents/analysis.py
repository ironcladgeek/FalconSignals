"""Analysis agents for technical and fundamental evaluation."""

from typing import Any

from src.agents.base import AgentConfig, BaseAgent
from src.tools.analysis import TechnicalIndicatorTool
from src.tools.fetchers import PriceFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TechnicalAnalysisAgent(BaseAgent):
    """Agent for technical analysis of instruments."""

    def __init__(self, tools: list = None):
        """Initialize Technical Analysis agent.

        Args:
            tools: Optional list of tools
        """
        config = AgentConfig(
            role="Technical Analyst",
            goal="Analyze price patterns and technical indicators to identify entry/exit points and trends",
            backstory=(
                "You are a skilled technical analyst with expertise in chart patterns, "
                "moving averages, momentum indicators, and volume analysis. "
                "You use technical indicators to identify trend strength, reversals, and support/resistance levels. "
                "Your analysis helps traders make informed decisions based on price action."
            ),
        )
        default_tools = [PriceFetcherTool(), TechnicalIndicatorTool()]
        super().__init__(config, tools or default_tools)

    def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Execute technical analysis.

        Args:
            task: Task description
            context: Context with ticker and price data

        Returns:
            Technical analysis results with scores
        """
        try:
            context = context or {}
            ticker = context.get("ticker")

            if not ticker:
                return {
                    "status": "error",
                    "message": "No ticker provided",
                    "technical_score": 0,
                }

            logger.debug(f"Analyzing technical indicators for {ticker}")

            # Get price data
            price_fetcher = next(
                (t for t in self.tools if hasattr(t, "name") and t.name == "PriceFetcher"),
                None,
            )

            if not price_fetcher:
                return {
                    "status": "error",
                    "message": "Price fetcher unavailable",
                    "technical_score": 0,
                }

            price_data = price_fetcher.run(ticker, days_back=60)

            if "error" in price_data:
                return {
                    "status": "error",
                    "message": price_data["error"],
                    "technical_score": 0,
                }

            # Get technical indicators
            tech_tool = next(
                (t for t in self.tools if hasattr(t, "name") and t.name == "TechnicalIndicator"),
                None,
            )

            if not tech_tool:
                return {
                    "status": "error",
                    "message": "Technical indicator tool unavailable",
                    "technical_score": 0,
                }

            indicators = tech_tool.run(price_data.get("prices", []))

            if "error" in indicators:
                return {
                    "status": "error",
                    "message": indicators["error"],
                    "technical_score": 0,
                }

            # Calculate technical score (0-100)
            score = self._calculate_technical_score(indicators)

            result = {
                "status": "success",
                "ticker": ticker,
                "technical_score": score,
                "indicators": indicators,
                "trend": indicators.get("trend", "unknown"),
                "rsi": indicators.get("rsi"),
                "recommendation": self._score_to_recommendation(score),
            }

            logger.debug(f"Technical analysis for {ticker}: {score}/100")
            self.remember(f"{ticker}_technical_score", score)

            return result

        except Exception as e:
            logger.error(f"Error during technical analysis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "technical_score": 0,
            }

    @staticmethod
    def _calculate_technical_score(indicators: dict[str, Any]) -> float:
        """Calculate overall technical score.

        Args:
            indicators: Technical indicators

        Returns:
            Score from 0-100
        """
        score = 50  # Start at neutral

        # RSI contribution (0-20 points)
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            if rsi < 30:
                score += 15  # Oversold (bullish)
            elif rsi > 70:
                score -= 15  # Overbought (bearish)
            elif 40 <= rsi <= 60:
                score += 5  # Neutral momentum

        # MACD histogram contribution (0-15 points)
        if "macd" in indicators:
            hist = indicators["macd"].get("histogram", 0)
            if hist > 0:
                score += 10
            elif hist < 0:
                score -= 10

        # Volume contribution (0-10 points)
        if "volume_ratio" in indicators:
            vol_ratio = indicators["volume_ratio"]
            if vol_ratio > 1.2:
                score += 8

        # Trend contribution (0-20 points)
        if indicators.get("trend") == "bullish":
            score += 15
        elif indicators.get("trend") == "bearish":
            score -= 15

        # ATR volatility (0-10 points, lower is better for stable trends)
        if "atr" in indicators and "latest_price" in indicators:
            atr_pct = indicators["atr"] / indicators["latest_price"] * 100
            if atr_pct < 2:
                score += 5

        return max(0, min(100, score))

    @staticmethod
    def _score_to_recommendation(score: float) -> str:
        """Convert score to recommendation.

        Args:
            score: Technical score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 75:
            return "strong_buy"
        elif score >= 60:
            return "buy"
        elif score >= 40:
            return "hold"
        elif score >= 25:
            return "sell"
        else:
            return "strong_sell"


class FundamentalAnalysisAgent(BaseAgent):
    """Agent for fundamental analysis of companies."""

    def __init__(self, tools: list = None):
        """Initialize Fundamental Analysis agent.

        Args:
            tools: Optional list of tools
        """
        config = AgentConfig(
            role="Fundamental Analyst",
            goal="Evaluate financial health, growth prospects, and valuation metrics to assess investment quality",
            backstory=(
                "You are an experienced fundamental analyst with deep knowledge of financial statements, "
                "valuation metrics, and business fundamentals. "
                "You analyze earnings growth, profitability, debt levels, and valuations to identify "
                "companies with strong business models and reasonable prices."
            ),
        )
        super().__init__(config, tools or [])

    def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Execute fundamental analysis.

        Args:
            task: Task description
            context: Context with company data

        Returns:
            Fundamental analysis results with scores
        """
        try:
            context = context or {}
            ticker = context.get("ticker")

            if not ticker:
                return {
                    "status": "error",
                    "message": "No ticker provided",
                    "fundamental_score": 0,
                }

            logger.debug(f"Analyzing fundamentals for {ticker}")

            # This is a simplified implementation
            # In production, this would fetch real financial data
            score = self._calculate_fundamental_score(context)

            result = {
                "status": "success",
                "ticker": ticker,
                "fundamental_score": score,
                "metrics": context.get("metrics", {}),
                "recommendation": self._score_to_recommendation(score),
            }

            logger.debug(f"Fundamental analysis for {ticker}: {score}/100")
            self.remember(f"{ticker}_fundamental_score", score)

            return result

        except Exception as e:
            logger.error(f"Error during fundamental analysis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fundamental_score": 0,
            }

    @staticmethod
    def _calculate_fundamental_score(context: dict[str, Any]) -> float:
        """Calculate fundamental score.

        Args:
            context: Context with metrics

        Returns:
            Score from 0-100
        """
        # Placeholder implementation
        # In production, would analyze P/E, growth, margins, debt, etc.
        return 50

    @staticmethod
    def _score_to_recommendation(score: float) -> str:
        """Convert score to recommendation.

        Args:
            score: Fundamental score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 75:
            return "strong_buy"
        elif score >= 60:
            return "buy"
        elif score >= 40:
            return "hold"
        elif score >= 25:
            return "sell"
        else:
            return "strong_sell"
