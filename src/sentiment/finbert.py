"""Local FinBERT sentiment scoring for financial text.

Provides zero-cost sentiment analysis using the ProsusAI/finbert model,
with optional LLM fallback for theme extraction.
"""

from dataclasses import dataclass
from typing import Any, Optional

from src.data.models import NewsArticle
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import transformers
try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.info("transformers not installed, FinBERT scoring not available")


@dataclass
class SentimentScore:
    """Sentiment score for a single article."""

    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float  # Confidence score (0.0 to 1.0)
    confidence: float  # Same as score (kept for compatibility)
    raw_probs: Optional[dict[str, float]] = None  # Optional raw probabilities


class FinBERTSentimentScorer:
    """Local FinBERT-based sentiment scorer for financial text.

    Uses the ProsusAI/finbert model via transformers pipeline API,
    providing accurate sentiment analysis for financial text.
    """

    # Default model for financial sentiment
    DEFAULT_MODEL = "ProsusAI/finbert"

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 512,
    ):
        """Initialize FinBERT sentiment scorer.

        Args:
            model_name: Hugging Face model name. Defaults to ProsusAI/finbert.
            device: Device to use ('cpu', 'cuda', 'mps', or device number). Auto-detected if None.
            batch_size: Batch size for processing multiple texts.
            max_length: Maximum token length for texts.
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers is required for FinBERT. Install with: pip install transformers torch"
            )

        self.model_name = model_name or self.DEFAULT_MODEL
        self.batch_size = batch_size
        self.max_length = max_length
        self.device = device  # None = auto-detect, or specific device

        logger.debug(
            f"Initializing FinBERT scorer with model={self.model_name}, device={device or 'auto'}"
        )

        # Lazy-load pipeline
        self._pipeline = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazy-load the pipeline."""
        if self._loaded:
            return

        logger.debug(f"Loading FinBERT model: {self.model_name}")

        # Create pipeline with device auto-detection
        device_arg = self.device if self.device is not None else -1  # -1 = CPU, >=0 = GPU
        self._pipeline = pipeline(
            "text-classification",
            model=self.model_name,
            device=device_arg,
            truncation=True,
            max_length=self.max_length,
        )

        self._loaded = True
        logger.debug("FinBERT pipeline loaded successfully")

    def score_text(self, text: str) -> SentimentScore:
        """Score sentiment for a single text.

        Args:
            text: Text to analyze

        Returns:
            SentimentScore with sentiment label and confidence score
        """
        self._ensure_loaded()

        # Get prediction from pipeline
        result = self._pipeline(text)[0]

        # Extract label and score
        sentiment = result["label"]
        score = result["score"]

        return SentimentScore(
            sentiment=sentiment,
            score=score,
            confidence=score,  # Same as score
            raw_probs=None,  # Pipeline doesn't return all probabilities by default
        )

    def score_articles(
        self,
        articles: list[NewsArticle],
        include_title: bool = False,
    ) -> list[SentimentScore]:
        """Score sentiment for multiple articles.

        Args:
            articles: List of news articles to analyze
            include_title: If True, prepend title to summary for analysis

        Returns:
            List of SentimentScore objects (same order as input)
        """
        if not articles:
            return []

        self._ensure_loaded()

        # Prepare texts
        texts = []
        for article in articles:
            if article.summary:
                text = f"{article.title}. {article.summary}" if include_title else article.summary
            else:
                text = article.title
            texts.append(text)

        # Process in batches
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            batch_results = self._score_batch(batch_texts)
            results.extend(batch_results)

        return results

    def _score_batch(self, texts: list[str]) -> list[SentimentScore]:
        """Score a batch of texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of SentimentScore objects
        """
        # Get predictions from pipeline (returns list of dicts)
        pipeline_results = self._pipeline(texts)

        # Convert to SentimentScore objects
        results = []
        for result in pipeline_results:
            sentiment = result["label"]
            score = result["score"]

            results.append(
                SentimentScore(
                    sentiment=sentiment,
                    score=score,
                    confidence=score,
                    raw_probs=None,
                )
            )

        return results

    def update_articles_with_scores(
        self,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        """Update articles with local sentiment scores.

        Modifies articles in-place with sentiment and sentiment_score fields.

        Args:
            articles: List of news articles

        Returns:
            Same articles with updated sentiment fields
        """
        if not articles:
            return articles

        scores = self.score_articles(articles)

        for article, score in zip(articles, scores, strict=False):
            article.sentiment = score.sentiment
            article.sentiment_score = score.score

        logger.debug(f"Updated {len(articles)} articles with FinBERT sentiment scores")
        return articles

    def get_aggregate_sentiment(
        self,
        articles: list[NewsArticle],
    ) -> dict[str, Any]:
        """Get aggregate sentiment statistics for articles.

        Args:
            articles: List of news articles (with or without existing sentiment)

        Returns:
            Dictionary with aggregate sentiment metrics
        """
        # Score articles if they don't have sentiment
        needs_scoring = any(a.sentiment is None for a in articles)
        if needs_scoring:
            scores = self.score_articles(articles)
        else:
            # Use existing sentiment
            scores = [
                SentimentScore(
                    sentiment=a.sentiment or "neutral",
                    score=a.sentiment_score or 0.0,
                    confidence=0.8,  # Assume moderate confidence for pre-scored
                )
                for a in articles
            ]

        if not scores:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_score": 0.0,
                "avg_confidence": 0.0,
                "overall_sentiment": "neutral",
            }

        # Calculate statistics
        positive = sum(1 for s in scores if s.sentiment == "positive")
        negative = sum(1 for s in scores if s.sentiment == "negative")
        neutral = sum(1 for s in scores if s.sentiment == "neutral")
        total = len(scores)

        # Calculate weighted average score (-1 to +1)
        # Positive sentiment: +score, Negative: -score, Neutral: 0
        weighted_scores = []
        for s in scores:
            if s.sentiment == "positive":
                weighted_scores.append(s.score)
            elif s.sentiment == "negative":
                weighted_scores.append(-s.score)
            else:  # neutral
                weighted_scores.append(0.0)

        avg_score = sum(weighted_scores) / total if total > 0 else 0.0
        avg_confidence = sum(s.confidence for s in scores) / total if total > 0 else 0.0

        # Determine overall sentiment based on weighted average
        if avg_score > 0.05:
            overall = "positive"
        elif avg_score < -0.05:
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
            "avg_score": round(avg_score, 3),
            "avg_confidence": round(avg_confidence, 3),
            "overall_sentiment": overall,
            "scoring_method": "finbert_local",
        }

    @classmethod
    def is_available(cls) -> bool:
        """Check if FinBERT scoring is available.

        Returns:
            True if transformers and torch are installed
        """
        return TRANSFORMERS_AVAILABLE
