"""Sentiment analysis and signal synthesis agents."""

from typing import Any

from src.agents.base import AgentConfig, BaseAgent
from src.config import get_config
from src.tools.analysis import SentimentAnalyzerTool
from src.tools.fetchers import NewsFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SentimentAgent(BaseAgent):
    """Agent for analyzing news sentiment and market perception."""

    def __init__(self, tools: list = None):
        """Initialize Sentiment agent.

        Args:
            tools: Optional list of tools
        """
        config = AgentConfig(
            role="Sentiment Analyst",
            goal="Analyze news sentiment and market perception to understand investor sentiment and potential catalyst events",
            backstory=(
                "You are an expert sentiment analyst with strong skills in NLP and market psychology. "
                "You analyze news articles, earnings calls, and social media to gauge investor sentiment. "
                "You identify catalyst events and understand how news impacts market perception and prices."
            ),
        )
        default_tools = [NewsFetcherTool(), SentimentAnalyzerTool()]
        super().__init__(config, tools or default_tools)

    def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Execute sentiment analysis.

        Args:
            task: Task description
            context: Context with ticker

        Returns:
            Sentiment analysis results with scores
        """
        try:
            context = context or {}
            ticker = context.get("ticker")

            if not ticker:
                return {
                    "status": "error",
                    "message": "No ticker provided",
                    "sentiment_score": 0,
                }

            logger.debug(f"Analyzing sentiment for {ticker}")

            # Fetch news
            news_fetcher = next(
                (t for t in self.tools if hasattr(t, "name") and t.name == "NewsFetcher"),
                None,
            )

            if not news_fetcher:
                return {
                    "status": "error",
                    "message": "News fetcher unavailable",
                    "sentiment_score": 0,
                }

            # Set historical date if provided in context
            if "analysis_date" in context and hasattr(news_fetcher, "set_historical_date"):
                news_fetcher.set_historical_date(context["analysis_date"])
                logger.debug(
                    f"Set historical date {context['analysis_date']} for sentiment analysis"
                )

            news_data = news_fetcher.run(
                ticker,
                limit=get_config().data.news.max_articles,
            )

            if "error" in news_data or not news_data.get("articles"):
                return {
                    "status": "warning",
                    "message": "Limited news data available",
                    "sentiment_score": 50,  # Neutral
                }

            # Analyze sentiment with weighted scoring
            sentiment_tool = next(
                (t for t in self.tools if hasattr(t, "name") and t.name == "SentimentAnalyzer"),
                None,
            )

            if not sentiment_tool:
                return {
                    "status": "error",
                    "message": "Sentiment analyzer unavailable",
                    "sentiment_score": 0,
                }

            # Set analysis date for recency weighting
            analysis_date = context.get("analysis_date")
            if hasattr(sentiment_tool, "analysis_date"):
                sentiment_tool.analysis_date = analysis_date

            # Run weighted sentiment analysis
            sentiment = sentiment_tool.run(
                news_data.get("articles", []), reference_date=analysis_date
            )

            if "error" in sentiment:
                return {
                    "status": "error",
                    "message": sentiment["error"],
                    "sentiment_score": 0,
                }

            # Check if we have pre-calculated scores or need LLM analysis
            requires_llm = sentiment.get("requires_llm_analysis", False)

            if requires_llm:
                logger.info(
                    f"{ticker}: No pre-calculated sentiment scores available. "
                    "LLM analysis would be needed for deeper insights."
                )
                # Return neutral with note - LLM analysis can be added here later
                score = 50
            else:
                # Use weighted sentiment score from pre-calculated data
                weighted_score = sentiment.get("weighted_sentiment", 0.0)

                # Convert weighted sentiment (-1 to +1) to 0-100 score
                # -1 -> 0, 0 -> 50, +1 -> 100
                score = 50 + (weighted_score * 50)
                score = max(0, min(100, score))

                logger.info(
                    f"{ticker}: Using pre-calculated sentiment scores. "
                    f"Weighted score: {weighted_score:.3f} -> {score:.1f}/100"
                )

            result = {
                "status": "success",
                "ticker": ticker,
                "sentiment_score": score,
                "sentiment_metrics": sentiment,
                "direction": sentiment.get("sentiment_direction", "neutral"),
                "news_count": sentiment.get("count", 0),
                "positive_news": sentiment.get("positive", 0),
                "negative_news": sentiment.get("negative", 0),
                "neutral_news": sentiment.get("neutral", 0),
                "recommendation": self._score_to_recommendation(score),
            }

            logger.debug(f"Sentiment analysis for {ticker}: {score}/100")
            self.remember(f"{ticker}_sentiment_score", score)

            return result

        except Exception as e:
            logger.error(f"Error during sentiment analysis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "sentiment_score": 0,
            }

    @staticmethod
    def _score_to_recommendation(score: float) -> str:
        """Convert score to recommendation.

        Args:
            score: Sentiment score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 70:
            return "positive"
        elif score >= 55:
            return "moderately_positive"
        elif score >= 45:
            return "neutral"
        elif score >= 30:
            return "moderately_negative"
        else:
            return "negative"


class SignalSynthesisAgent(BaseAgent):
    """Agent for synthesizing multiple signals into final recommendations."""

    def __init__(self, tools: list = None):
        """Initialize Signal Synthesis agent.

        Args:
            tools: Optional list of tools
        """
        config = AgentConfig(
            role="Signal Synthesizer",
            goal="Combine technical, fundamental, and sentiment signals to generate high-confidence investment recommendations",
            backstory=(
                "You are a master strategist who synthesizes diverse data sources into actionable recommendations. "
                "You understand how technical, fundamental, and sentiment factors interact to drive prices. "
                "Your ability to weight different signals appropriately has generated exceptional returns."
            ),
        )
        super().__init__(config, tools or [])

    def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Synthesize signals into recommendation.

        Args:
            task: Task description
            context: Context with analysis results

        Returns:
            Final recommendation with confidence
        """
        try:
            context = context or {}
            ticker = context.get("ticker")

            if not ticker:
                return {
                    "status": "error",
                    "message": "No ticker provided",
                    "recommendation": "hold",
                    "confidence": 0,
                }

            logger.debug(f"Synthesizing signals for {ticker}")

            # Extract scores from context
            technical_score = context.get("technical_score", 50)
            fundamental_score = context.get("fundamental_score", 50)
            sentiment_score = context.get("sentiment_score", 50)

            # Weight the scores (configurable)
            weights = {
                "technical": 0.35,
                "fundamental": 0.35,
                "sentiment": 0.30,
            }

            # Calculate final score
            final_score = (
                technical_score * weights["technical"]
                + fundamental_score * weights["fundamental"]
                + sentiment_score * weights["sentiment"]
            )

            # Calculate confidence based on agreement
            scores = [technical_score, fundamental_score, sentiment_score]
            score_variance = max(scores) - min(scores)
            confidence = max(0, 100 - score_variance * 0.5)  # Lower variance = higher confidence

            # Generate recommendation
            recommendation = self._score_to_recommendation(final_score)

            result = {
                "status": "success",
                "ticker": ticker,
                "final_score": round(final_score, 2),
                "confidence": round(confidence, 2),
                "recommendation": recommendation,
                "component_scores": {
                    "technical": technical_score,
                    "fundamental": fundamental_score,
                    "sentiment": sentiment_score,
                },
                "weights": weights,
                "rationale": self._generate_rationale(
                    final_score, technical_score, fundamental_score, sentiment_score
                ),
            }

            logger.info(
                f"Signal synthesis for {ticker}: {recommendation} "
                f"({final_score:.0f}/100, confidence: {confidence:.0f}%)"
            )
            self.remember(f"{ticker}_signal", result)

            return result

        except Exception as e:
            logger.error(f"Error during signal synthesis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "recommendation": "hold",
                "confidence": 0,
            }

    @staticmethod
    def _score_to_recommendation(score: float) -> str:
        """Convert score to recommendation.

        Args:
            score: Final score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 75:
            return "buy"
        elif score >= 60:
            return "hold_bullish"
        elif score >= 40:
            return "hold"
        elif score >= 25:
            return "hold_bearish"
        else:
            return "sell"

    @staticmethod
    def _generate_rationale(
        final: float, technical: float, fundamental: float, sentiment: float
    ) -> str:
        """Generate explanation for recommendation.

        Args:
            final: Final score
            technical: Technical score
            fundamental: Fundamental score
            sentiment: Sentiment score

        Returns:
            Rationale string
        """
        strong_factors = []

        if technical > 70:
            strong_factors.append("strong technical momentum")
        elif technical < 30:
            strong_factors.append("weak technical setup")

        if fundamental > 70:
            strong_factors.append("solid fundamentals")
        elif fundamental < 30:
            strong_factors.append("concerns about fundamentals")

        if sentiment > 70:
            strong_factors.append("positive market sentiment")
        elif sentiment < 30:
            strong_factors.append("negative market sentiment")

        if strong_factors:
            return f"Based on {', '.join(strong_factors)}."
        else:
            return "Mixed signals from various factors."
