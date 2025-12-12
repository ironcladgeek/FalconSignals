"""Fundamental analysis calculations and scoring using free tier data.

NOTE: This implementation uses ONLY free tier API data:
- Analyst recommendations from Finnhub (free tier: /stock/recommendation-trend)
- Price data from Yahoo Finance (free tier)
- Fundamental metrics from yfinance (free tier)
- News sentiment analyzed by CrewAI agents/LLM (no premium API calls)

Premium endpoints like /stock/metric, /stock/financials, and /news-sentiment
are NOT used to maintain cost efficiency and free tier compatibility.
"""

from typing import Any

from src.analysis.metrics import FundamentalMetricsAnalyzer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FundamentalAnalyzer:
    """Calculates fundamental scores from free tier API data only.

    Scores based on:
    - Analyst recommendations (from /stock/recommendation-trend - FREE TIER)
    - Price momentum (from price data - FREE TIER)
    - News sentiment (analyzed by CrewAI agents/LLM, not from premium APIs)
    """

    @staticmethod
    def calculate_score(
        analyst_data: dict[str, Any] = None,
        price_context: dict[str, Any] = None,
        sentiment_score: float = None,
    ) -> dict[str, Any]:
        """Calculate fundamental score from free tier data sources.

        Args:
            analyst_data: Analyst recommendation trends from Finnhub
                         Expected keys: strong_buy, buy, hold, sell, strong_sell, total_analysts
            price_context: Price momentum context
                          Expected keys: change_percent, trend (bullish/bearish)
            sentiment_score: News sentiment score from CrewAI agent (0-100, optional)
                           If None, will default to neutral (50)

        Returns:
            Dictionary with component scores and overall fundamental score
        """
        analyst_score = FundamentalAnalyzer._score_analyst_consensus(analyst_data)
        momentum_score = FundamentalAnalyzer._score_momentum(price_context)

        # Use provided sentiment score or default to neutral
        if sentiment_score is None:
            sentiment_score = 50

        # Weight the components
        # Analyst: 50%, Momentum: 50%
        # (Sentiment handled separately by CrewAI News & Sentiment Agent)
        overall_score = analyst_score * 0.50 + momentum_score * 0.50

        return {
            "overall_score": max(0, min(100, overall_score)),
            "analyst_score": analyst_score,
            "momentum_score": momentum_score,
            "sentiment_score": sentiment_score,
            "components": {
                "analyst_consensus": {
                    "score": analyst_score,
                    "data": analyst_data or {},
                },
                "momentum": {
                    "score": momentum_score,
                    "data": price_context or {},
                },
                "sentiment": {
                    "score": sentiment_score,
                    "note": "Calculated by News & Sentiment Agent (CrewAI/LLM)",
                },
            },
        }

    @staticmethod
    def _score_analyst_consensus(analyst_data: dict[str, Any]) -> float:
        """Score based on analyst recommendation distribution.

        Args:
            analyst_data: Analyst recommendations with buy/hold/sell counts

        Returns:
            Score 0-100
        """
        if not analyst_data:
            return 50  # Neutral if no data

        strong_buy = analyst_data.get("strong_buy", 0)
        buy = analyst_data.get("buy", 0)
        hold = analyst_data.get("hold", 0)
        sell = analyst_data.get("sell", 0)
        strong_sell = analyst_data.get("strong_sell", 0)
        total = analyst_data.get("total_analysts", 0)

        if total == 0:
            return 50

        # Calculate weighted average score
        bullish = strong_buy * 100 + buy * 75
        neutral = hold * 50
        bearish = sell * 25 + strong_sell * 0

        score = (bullish + neutral + bearish) / total

        return max(0, min(100, score))

    @staticmethod
    def _score_momentum(price_context: dict[str, Any]) -> float:
        """Score based on price momentum and trend.

        Args:
            price_context: Price change percentage and trend direction

        Returns:
            Score 0-100
        """
        if not price_context:
            return 50  # Neutral if no data

        change_percent = price_context.get("change_percent", 0)
        trend = price_context.get("trend", "neutral")

        score = 50

        # Price change contribution (±30 points)
        if change_percent > 0.05:  # 5% gain
            score += 15
        elif change_percent > 0.02:  # 2% gain
            score += 8
        elif change_percent < -0.05:  # 5% loss
            score -= 15
        elif change_percent < -0.02:  # 2% loss
            score -= 8

        # Trend contribution (±15 points)
        if trend == "bullish":
            score += 15
        elif trend == "bearish":
            score -= 15

        return max(0, min(100, score))

    @staticmethod
    def calculate_enhanced_score(
        analyst_data: dict[str, Any] = None,
        price_context: dict[str, Any] = None,
        sentiment_score: float = None,
        metrics_data: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Calculate enhanced fundamental score with metrics.

        Combines analyst consensus, price momentum, and yfinance metrics
        for comprehensive fundamental analysis.

        Args:
            analyst_data: Analyst recommendation trends from Finnhub
            price_context: Price momentum context
            sentiment_score: News sentiment score from CrewAI agent (0-100, optional)
            metrics_data: yfinance metrics (valuation, profitability, etc.)

        Returns:
            Dictionary with component scores and overall enhanced score
        """
        # Calculate baseline score (analyst + momentum)
        baseline = FundamentalAnalyzer.calculate_score(analyst_data, price_context, sentiment_score)

        # Calculate metrics score if data available
        metrics_score_data = {}
        if metrics_data:
            metrics_score_data = FundamentalMetricsAnalyzer.calculate_metrics_score(metrics_data)
        else:
            # Default neutral metrics score if no data
            metrics_score_data = {
                "overall_score": 50,
                "valuation_score": 50,
                "profitability_score": 50,
                "financial_health_score": 50,
                "growth_score": 50,
            }

        # Combine scores
        # Baseline (analyst + momentum): 60%, Metrics: 40%
        combined_score = (
            baseline["overall_score"] * 0.60 + metrics_score_data["overall_score"] * 0.40
        )

        return {
            "overall_score": max(0, min(100, combined_score)),
            "baseline_score": baseline["overall_score"],
            "metrics_score": metrics_score_data["overall_score"],
            "analyst_score": baseline["analyst_score"],
            "momentum_score": baseline["momentum_score"],
            "sentiment_score": baseline["sentiment_score"],
            "valuation_score": metrics_score_data.get("valuation_score", 50),
            "profitability_score": metrics_score_data.get("profitability_score", 50),
            "financial_health_score": metrics_score_data.get("financial_health_score", 50),
            "growth_score": metrics_score_data.get("growth_score", 50),
            "baseline_components": baseline.get("components", {}),
            "metrics_components": metrics_score_data.get("components", {}),
        }

    @staticmethod
    def get_recommendation(score: float) -> str:
        """Convert score to investment recommendation.

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
