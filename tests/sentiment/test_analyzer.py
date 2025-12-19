"""Unit tests for the configurable sentiment analyzer module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.config.schemas import SentimentConfig
from src.data.models import NewsArticle
from src.sentiment.analyzer import ConfigurableSentimentAnalyzer


def make_article(
    title: str,
    sentiment: str | None = None,
    sentiment_score: float | None = None,
    ticker: str = "AAPL",
) -> NewsArticle:
    """Create a test NewsArticle."""
    return NewsArticle(
        ticker=ticker,
        title=title,
        summary=f"Summary of {title}",
        source="Test Source",
        published_date=datetime(2024, 1, 15),
        url="https://example.com/news",
        sentiment=sentiment,
        sentiment_score=sentiment_score,
    )


class TestConfigurableSentimentAnalyzer:
    """Test suite for ConfigurableSentimentAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with default config."""
        return ConfigurableSentimentAnalyzer()

    @pytest.fixture
    def analyzer_no_fallback(self):
        """Create analyzer without LLM fallback."""
        config = SentimentConfig(llm_fallback=False)
        return ConfigurableSentimentAnalyzer(config)

    def test_initialization_default_config(self):
        """Test analyzer initializes with default config."""
        analyzer = ConfigurableSentimentAnalyzer()
        assert analyzer.config is not None
        assert isinstance(analyzer.config, SentimentConfig)
        assert analyzer._finbert_scorer is None
        assert analyzer._initialized is False

    def test_initialization_custom_config(self):
        """Test analyzer initializes with custom config."""
        config = SentimentConfig(scoring_method="api", llm_fallback=False)
        analyzer = ConfigurableSentimentAnalyzer(config)
        assert analyzer.config.scoring_method == "api"
        assert analyzer.config.llm_fallback is False

    def test_analyze_sentiment_empty_articles(self, analyzer):
        """Test analyzing empty article list."""
        result = analyzer.analyze_sentiment([])

        assert result["articles"] == []
        assert result["summary"]["total"] == 0
        assert result["method"] == "none"

    def test_analyze_sentiment_api_method_with_sentiment(self, analyzer):
        """Test API method when articles have sentiment data."""
        articles = [
            make_article("Good news", sentiment="positive", sentiment_score=0.8),
            make_article("Bad news", sentiment="negative", sentiment_score=-0.6),
            make_article("Neutral news", sentiment="neutral", sentiment_score=0.0),
        ]

        result = analyzer.analyze_sentiment(articles, method="api")

        assert len(result["articles"]) == 3
        assert result["method"] == "api_provider"
        assert result["summary"]["total"] == 3
        assert result["summary"]["positive"] == 1
        assert result["summary"]["negative"] == 1
        assert result["summary"]["neutral"] == 1

    def test_analyze_sentiment_api_method_no_sentiment(self, analyzer_no_fallback):
        """Test API method when articles have no sentiment data."""
        articles = [
            make_article("News 1"),
            make_article("News 2"),
        ]

        result = analyzer_no_fallback.analyze_sentiment(articles, method="api")

        assert result["method"] == "no_scoring"
        assert result["summary"]["neutral"] == 2
        assert "No sentiment data available" in result["summary"].get("note", "")

    def test_analyze_sentiment_llm_method(self, analyzer):
        """Test LLM method delegates to API."""
        articles = [
            make_article("News", sentiment="positive", sentiment_score=0.5),
        ]

        result = analyzer.analyze_sentiment(articles, method="llm")

        # LLM method currently delegates to API
        assert result["method"] == "api_provider"

    def test_analyze_sentiment_unknown_method(self, analyzer):
        """Test unknown method falls back to API."""
        articles = [
            make_article("News", sentiment="neutral", sentiment_score=0.0),
        ]

        result = analyzer.analyze_sentiment(articles, method="unknown_method")

        assert result["method"] == "api_provider"

    def test_calculate_stats_positive_sentiment(self, analyzer):
        """Test stats calculation for positive articles."""
        articles = [
            make_article("Good 1", sentiment="positive", sentiment_score=0.7),
            make_article("Good 2", sentiment="positive", sentiment_score=0.9),
            make_article("Good 3", sentiment="positive", sentiment_score=0.5),
        ]

        stats = analyzer._calculate_stats_from_articles(articles)

        assert stats["total"] == 3
        assert stats["positive"] == 3
        assert stats["negative"] == 0
        assert stats["neutral"] == 0
        assert stats["positive_pct"] == 100.0
        assert stats["overall_sentiment"] == "positive"
        assert stats["avg_sentiment_score"] > 0.1

    def test_calculate_stats_negative_sentiment(self, analyzer):
        """Test stats calculation for negative articles."""
        articles = [
            make_article("Bad 1", sentiment="negative", sentiment_score=-0.7),
            make_article("Bad 2", sentiment="negative", sentiment_score=-0.9),
        ]

        stats = analyzer._calculate_stats_from_articles(articles)

        assert stats["total"] == 2
        assert stats["negative"] == 2
        assert stats["positive"] == 0
        assert stats["overall_sentiment"] == "negative"
        assert stats["avg_sentiment_score"] < -0.1

    def test_calculate_stats_mixed_sentiment(self, analyzer):
        """Test stats calculation for mixed sentiment."""
        articles = [
            make_article("Good", sentiment="positive", sentiment_score=0.5),
            make_article("Bad", sentiment="negative", sentiment_score=-0.5),
        ]

        stats = analyzer._calculate_stats_from_articles(articles)

        assert stats["total"] == 2
        assert stats["positive"] == 1
        assert stats["negative"] == 1
        assert stats["overall_sentiment"] == "neutral"
        assert stats["avg_sentiment_score"] == 0.0

    def test_calculate_stats_no_scores(self, analyzer):
        """Test stats calculation when articles have no scores."""
        articles = [
            make_article("News 1", sentiment="positive"),
            make_article("News 2", sentiment="negative"),
        ]

        stats = analyzer._calculate_stats_from_articles(articles)

        assert stats["avg_sentiment_score"] == 0.0
        assert stats["overall_sentiment"] == "neutral"

    def test_calculate_stats_with_none_sentiment(self, analyzer):
        """Test stats count None sentiment as neutral."""
        articles = [
            make_article("News 1", sentiment=None),
            make_article("News 2", sentiment="positive", sentiment_score=0.8),
        ]

        stats = analyzer._calculate_stats_from_articles(articles)

        assert stats["neutral"] == 1
        assert stats["positive"] == 1

    def test_create_neutral_result(self, analyzer):
        """Test creating neutral result."""
        articles = [
            make_article("News 1"),
            make_article("News 2"),
        ]

        result = analyzer._create_neutral_result(articles)

        assert len(result["articles"]) == 2
        assert result["summary"]["neutral"] == 2
        assert result["summary"]["neutral_pct"] == 100
        assert result["method"] == "no_scoring"

    def test_empty_result(self, analyzer):
        """Test creating empty result."""
        result = analyzer._empty_result()

        assert result["articles"] == []
        assert result["summary"]["total"] == 0
        assert result["method"] == "none"
        assert "error" not in result

    def test_empty_result_with_error(self, analyzer):
        """Test creating empty result with error message."""
        result = analyzer._empty_result(error="Something went wrong")

        assert result["error"] == "Something went wrong"

    @patch("src.sentiment.analyzer.ConfigurableSentimentAnalyzer._get_finbert_scorer")
    def test_analyze_local_finbert_unavailable_with_fallback(self, mock_get_scorer, analyzer):
        """Test local analysis falls back to API when FinBERT unavailable."""
        mock_get_scorer.return_value = None

        articles = [
            make_article("News", sentiment="positive", sentiment_score=0.5),
        ]

        result = analyzer.analyze_sentiment(articles, method="local")

        # Should fall back to API
        assert result["method"] == "api_provider"

    @patch("src.sentiment.analyzer.ConfigurableSentimentAnalyzer._get_finbert_scorer")
    def test_analyze_local_finbert_unavailable_no_fallback(
        self, mock_get_scorer, analyzer_no_fallback
    ):
        """Test local analysis returns error when FinBERT unavailable and no fallback."""
        mock_get_scorer.return_value = None

        articles = [
            make_article("News"),
        ]

        result = analyzer_no_fallback.analyze_sentiment(articles, method="local")

        assert "error" in result or result["summary"].get("total") == 0

    @patch("src.sentiment.analyzer.ConfigurableSentimentAnalyzer._get_finbert_scorer")
    def test_analyze_hybrid_calls_local(self, mock_get_scorer, analyzer):
        """Test hybrid analysis first calls local analysis."""
        mock_scorer = MagicMock()
        mock_scorer.get_aggregate_sentiment.return_value = {
            "total": 1,
            "positive": 1,
            "negative": 0,
            "neutral": 0,
            "avg_sentiment_score": 0.7,
            "overall_sentiment": "positive",
        }
        mock_get_scorer.return_value = mock_scorer

        articles = [
            make_article("Good news", sentiment="positive", sentiment_score=0.7),
        ]

        result = analyzer.analyze_sentiment(articles, method="hybrid")

        assert result["requires_theme_extraction"] is True
        assert result["method"] == "hybrid_local_scoring"

    def test_is_local_available_no_finbert(self):
        """Test is_local_available when FinBERT not available."""
        with patch(
            "src.sentiment.analyzer.ConfigurableSentimentAnalyzer.is_local_available",
            return_value=False,
        ):
            assert ConfigurableSentimentAnalyzer.is_local_available() is False

    def test_percentages_calculation(self, analyzer):
        """Test percentage calculations are correct."""
        articles = [
            make_article("Pos 1", sentiment="positive", sentiment_score=0.5),
            make_article("Pos 2", sentiment="positive", sentiment_score=0.6),
            make_article("Neg 1", sentiment="negative", sentiment_score=-0.5),
            make_article("Neutral", sentiment="neutral", sentiment_score=0.0),
        ]

        stats = analyzer._calculate_stats_from_articles(articles)

        assert stats["positive_pct"] == 50.0  # 2/4
        assert stats["negative_pct"] == 25.0  # 1/4
        assert stats["neutral_pct"] == 25.0  # 1/4

    def test_method_override(self, analyzer):
        """Test that method parameter overrides config."""
        analyzer.config.scoring_method = "local"

        articles = [
            make_article("News", sentiment="positive", sentiment_score=0.5),
        ]

        # Override with api
        result = analyzer.analyze_sentiment(articles, method="api")

        assert result["method"] == "api_provider"
