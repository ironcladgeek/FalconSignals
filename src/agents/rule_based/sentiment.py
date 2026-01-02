"""Sentiment analysis module for rule-based analysis."""

from typing import Any

from src.agents.base import AgentConfig, BaseAgent
from src.config import get_config
from src.tools.analysis import SentimentAnalyzerTool
from src.tools.fetchers import NewsFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SentimentAnalysisModule(BaseAgent):
    """Module for analyzing news sentiment and market perception (rule-based)."""

    def __init__(self, tools: list | None = None):
        """Initialize Sentiment analysis module.

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

    def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
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

                logger.debug(
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
