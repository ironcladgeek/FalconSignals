"""Configurable sentiment analyzer with multiple scoring modes.

Supports local FinBERT, LLM-based, API provider-based, and hybrid sentiment scoring.
"""

from typing import Any, Optional

from src.config.schemas import SentimentConfig
from src.data.models import NewsArticle
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigurableSentimentAnalyzer:
    """Configurable sentiment analyzer supporting multiple scoring methods.

    Scoring methods:
    - 'local': Use FinBERT model locally (zero cost, fast)
    - 'llm': Use LLM for sentiment analysis (more context-aware, costly)
    - 'api': Use provider-supplied sentiment scores (e.g., Alpha Vantage)
    - 'hybrid': Local scoring + LLM theme extraction
    """

    def __init__(self, config: Optional[SentimentConfig] = None):
        """Initialize configurable sentiment analyzer.

        Args:
            config: Sentiment configuration. Uses defaults if not provided.
        """
        if config is None:
            config = SentimentConfig()
        self.config = config

        # Lazy-load scorers
        self._finbert_scorer = None
        self._initialized = False

    def _get_finbert_scorer(self):
        """Get or create FinBERT scorer (lazy initialization)."""
        if self._finbert_scorer is not None:
            return self._finbert_scorer

        try:
            from src.sentiment.finbert import FinBERTSentimentScorer

            if not FinBERTSentimentScorer.is_available():
                logger.warning("FinBERT not available (transformers/torch not installed)")
                return None

            model_config = self.config.local_model
            device = model_config.device if model_config.device != "auto" else None

            self._finbert_scorer = FinBERTSentimentScorer(
                model_name=model_config.name,
                device=device,
                batch_size=model_config.batch_size,
                max_length=model_config.max_length,
            )
            return self._finbert_scorer
        except ImportError:
            logger.warning("FinBERT scorer not available")
            return None
        except Exception as e:
            logger.error(f"Error initializing FinBERT scorer: {e}")
            return None

    def analyze_sentiment(
        self,
        articles: list[NewsArticle],
        method: Optional[str] = None,
    ) -> dict[str, Any]:
        """Analyze sentiment for a list of articles.

        Args:
            articles: List of news articles
            method: Override scoring method (if None, uses config)

        Returns:
            Dictionary with sentiment metrics and scored articles
        """
        if not articles:
            return self._empty_result()

        method = method or self.config.scoring_method

        if method == "local":
            return self._analyze_local(articles)
        elif method == "llm":
            return self._analyze_llm(articles)
        elif method == "api":
            return self._analyze_api(articles)
        elif method == "hybrid":
            return self._analyze_hybrid(articles)
        else:
            logger.warning(f"Unknown scoring method: {method}, falling back to api")
            return self._analyze_api(articles)

    def _analyze_local(self, articles: list[NewsArticle]) -> dict[str, Any]:
        """Analyze sentiment using local FinBERT model.

        Args:
            articles: List of news articles

        Returns:
            Sentiment analysis result
        """
        scorer = self._get_finbert_scorer()

        if scorer is None:
            if self.config.llm_fallback:
                logger.info("FinBERT not available, falling back to API scoring")
                return self._analyze_api(articles)
            return self._empty_result(error="FinBERT not available")

        try:
            # Update articles with local scores
            scorer.update_articles_with_scores(articles)

            # Get aggregate stats
            stats = scorer.get_aggregate_sentiment(articles)

            return {
                "articles": [a.model_dump() for a in articles],
                "summary": stats,
                "method": "local_finbert",
            }

        except Exception as e:
            logger.error(f"Local sentiment analysis failed: {e}")
            if self.config.llm_fallback:
                logger.info("Falling back to API scoring")
                return self._analyze_api(articles)
            return self._empty_result(error=str(e))

    def _analyze_llm(self, articles: list[NewsArticle]) -> dict[str, Any]:
        """Analyze sentiment using LLM.

        This is a placeholder - actual LLM integration would go through
        the existing CrewAI agent infrastructure.

        Args:
            articles: List of news articles

        Returns:
            Sentiment analysis result
        """
        # For now, fall back to API since LLM analysis is handled by agents
        logger.info("LLM sentiment analysis delegated to agent infrastructure")
        return self._analyze_api(articles)

    def _analyze_api(self, articles: list[NewsArticle]) -> dict[str, Any]:
        """Use provider-supplied sentiment scores (if available).

        Args:
            articles: List of news articles with potential sentiment data

        Returns:
            Sentiment analysis result
        """
        # Check if articles already have sentiment from providers
        has_sentiment = any(a.sentiment is not None for a in articles)

        if not has_sentiment:
            # No sentiment data - return neutral or try local
            if self.config.llm_fallback:
                scorer = self._get_finbert_scorer()
                if scorer:
                    return self._analyze_local(articles)

            # No scoring available
            return self._create_neutral_result(articles)

        # Calculate stats from existing sentiment
        stats = self._calculate_stats_from_articles(articles)

        return {
            "articles": [a.model_dump() for a in articles],
            "summary": stats,
            "method": "api_provider",
        }

    def _analyze_hybrid(self, articles: list[NewsArticle]) -> dict[str, Any]:
        """Hybrid analysis: local scoring + API/LLM theme extraction.

        Args:
            articles: List of news articles

        Returns:
            Sentiment analysis result with both local scores and themes
        """
        # First, get local sentiment scores
        local_result = self._analyze_local(articles)

        if "error" in local_result.get("summary", {}):
            return local_result

        # Theme extraction would be done by the LLM agent separately
        # Here we just mark it for LLM processing
        local_result["requires_theme_extraction"] = True
        local_result["method"] = "hybrid_local_scoring"

        return local_result

    def _calculate_stats_from_articles(
        self,
        articles: list[NewsArticle],
    ) -> dict[str, Any]:
        """Calculate sentiment statistics from articles.

        Args:
            articles: List of articles with sentiment data

        Returns:
            Statistics dictionary
        """
        positive = sum(1 for a in articles if a.sentiment == "positive")
        negative = sum(1 for a in articles if a.sentiment == "negative")
        neutral = sum(1 for a in articles if a.sentiment == "neutral" or a.sentiment is None)
        total = len(articles)

        # Calculate average score
        scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Determine overall sentiment
        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_pct": round(100 * positive / total, 1) if total > 0 else 0,
            "negative_pct": round(100 * negative / total, 1) if total > 0 else 0,
            "neutral_pct": round(100 * neutral / total, 1) if total > 0 else 0,
            "avg_sentiment_score": round(avg_score, 3),
            "overall_sentiment": overall,
        }

    def _create_neutral_result(self, articles: list[NewsArticle]) -> dict[str, Any]:
        """Create a neutral result when no sentiment data is available.

        Args:
            articles: List of articles

        Returns:
            Neutral sentiment result
        """
        total = len(articles)
        return {
            "articles": [a.model_dump() for a in articles],
            "summary": {
                "total": total,
                "positive": 0,
                "negative": 0,
                "neutral": total,
                "positive_pct": 0,
                "negative_pct": 0,
                "neutral_pct": 100,
                "avg_sentiment_score": 0.0,
                "overall_sentiment": "neutral",
                "note": "No sentiment data available from provider",
            },
            "method": "no_scoring",
        }

    def _empty_result(self, error: Optional[str] = None) -> dict[str, Any]:
        """Create an empty result.

        Args:
            error: Optional error message

        Returns:
            Empty result dictionary
        """
        result = {
            "articles": [],
            "summary": {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_sentiment_score": 0.0,
                "overall_sentiment": "neutral",
            },
            "method": "none",
        }
        if error:
            result["error"] = error
        return result

    @classmethod
    def is_local_available(cls) -> bool:
        """Check if local FinBERT scoring is available.

        Returns:
            True if transformers and torch are installed
        """
        try:
            from src.sentiment.finbert import FinBERTSentimentScorer

            return FinBERTSentimentScorer.is_available()
        except ImportError:
            return False
