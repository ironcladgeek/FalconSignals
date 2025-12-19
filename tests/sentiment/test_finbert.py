"""Unit tests for the FinBERT sentiment module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.data.models import NewsArticle


def make_article(
    title: str,
    summary: str | None = None,
    sentiment: str | None = None,
    sentiment_score: float | None = None,
) -> NewsArticle:
    """Create a test NewsArticle."""
    return NewsArticle(
        ticker="AAPL",
        title=title,
        summary=summary,
        source="Test Source",
        published_date=datetime(2024, 1, 15),
        url="https://example.com/news",
        sentiment=sentiment,
        sentiment_score=sentiment_score,
    )


class TestSentimentScore:
    """Test suite for SentimentScore dataclass."""

    def test_sentiment_score_creation(self):
        """Test creating SentimentScore."""
        # Import here to avoid issues if transformers not installed
        from src.sentiment.finbert import SentimentScore

        score = SentimentScore(
            sentiment="positive",
            score=0.85,
            confidence=0.85,
        )

        assert score.sentiment == "positive"
        assert score.score == 0.85
        assert score.confidence == 0.85
        assert score.raw_probs is None

    def test_sentiment_score_with_raw_probs(self):
        """Test creating SentimentScore with raw probabilities."""
        from src.sentiment.finbert import SentimentScore

        raw_probs = {"positive": 0.7, "negative": 0.2, "neutral": 0.1}
        score = SentimentScore(
            sentiment="positive",
            score=0.7,
            confidence=0.7,
            raw_probs=raw_probs,
        )

        assert score.raw_probs == raw_probs


class TestFinBERTSentimentScorer:
    """Test suite for FinBERTSentimentScorer class."""

    @pytest.fixture
    def mock_pipeline(self):
        """Create mock pipeline."""
        mock = MagicMock()
        mock.return_value = [{"label": "positive", "score": 0.9}]
        return mock

    @pytest.fixture
    def scorer(self, mock_pipeline):
        """Create scorer with mocked pipeline."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            with patch("src.sentiment.finbert.pipeline", mock_pipeline):
                from src.sentiment.finbert import FinBERTSentimentScorer

                scorer = FinBERTSentimentScorer()
                # Pre-load to use mock
                scorer._pipeline = mock_pipeline
                scorer._loaded = True
                return scorer

    def test_is_available_when_transformers_installed(self):
        """Test is_available returns True when transformers is installed."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            from src.sentiment.finbert import FinBERTSentimentScorer

            assert FinBERTSentimentScorer.is_available() is True

    def test_is_available_when_transformers_not_installed(self):
        """Test is_available returns False when transformers not installed."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", False):
            from src.sentiment.finbert import FinBERTSentimentScorer

            assert FinBERTSentimentScorer.is_available() is False

    def test_initialization_without_transformers(self):
        """Test initialization raises ImportError without transformers."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", False):
            from src.sentiment.finbert import FinBERTSentimentScorer

            with pytest.raises(ImportError, match="transformers is required"):
                FinBERTSentimentScorer()

    def test_initialization_with_defaults(self, mock_pipeline):
        """Test initialization with default parameters."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            with patch("src.sentiment.finbert.pipeline", mock_pipeline):
                from src.sentiment.finbert import FinBERTSentimentScorer

                scorer = FinBERTSentimentScorer()

                assert scorer.model_name == "ProsusAI/finbert"
                assert scorer.batch_size == 32
                assert scorer.max_length == 512
                assert scorer.device is None

    def test_initialization_with_custom_params(self, mock_pipeline):
        """Test initialization with custom parameters."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            with patch("src.sentiment.finbert.pipeline", mock_pipeline):
                from src.sentiment.finbert import FinBERTSentimentScorer

                scorer = FinBERTSentimentScorer(
                    model_name="custom/model",
                    device="cuda",
                    batch_size=16,
                    max_length=256,
                )

                assert scorer.model_name == "custom/model"
                assert scorer.device == "cuda"
                assert scorer.batch_size == 16
                assert scorer.max_length == 256

    def test_score_text(self, scorer, mock_pipeline):
        """Test scoring a single text."""
        mock_pipeline.return_value = [{"label": "positive", "score": 0.9}]

        result = scorer.score_text("Great earnings report!")

        assert result.sentiment == "positive"
        assert result.score == 0.9
        assert result.confidence == 0.9

    def test_score_text_negative(self, scorer, mock_pipeline):
        """Test scoring negative text."""
        mock_pipeline.return_value = [{"label": "negative", "score": 0.85}]

        result = scorer.score_text("Stock price plummets after scandal")

        assert result.sentiment == "negative"
        assert result.score == 0.85

    def test_score_articles_empty_list(self, scorer):
        """Test scoring empty article list."""
        result = scorer.score_articles([])

        assert result == []

    def test_score_articles_with_summary(self, scorer, mock_pipeline):
        """Test scoring articles with summaries."""
        mock_pipeline.return_value = [
            {"label": "positive", "score": 0.8},
            {"label": "neutral", "score": 0.7},
        ]

        articles = [
            make_article("Good news", summary="Company posts strong earnings"),
            make_article("Mixed signals", summary="Some good, some bad"),
        ]

        results = scorer.score_articles(articles)

        assert len(results) == 2
        assert results[0].sentiment == "positive"
        assert results[1].sentiment == "neutral"

    def test_score_articles_without_summary(self, scorer, mock_pipeline):
        """Test scoring articles without summaries uses title."""
        mock_pipeline.return_value = [{"label": "positive", "score": 0.75}]

        articles = [make_article("Great Q4 Results!", summary=None)]

        results = scorer.score_articles(articles)

        assert len(results) == 1
        # Pipeline should be called with title only
        mock_pipeline.assert_called()

    def test_score_articles_include_title(self, scorer, mock_pipeline):
        """Test scoring with include_title option."""
        mock_pipeline.return_value = [{"label": "positive", "score": 0.8}]

        articles = [make_article("Headline", summary="Article body")]

        scorer.score_articles(articles, include_title=True)

        # Should have been called with combined title and summary
        mock_pipeline.assert_called()

    def test_score_articles_batching(self, scorer, mock_pipeline):
        """Test that articles are processed in batches."""
        scorer.batch_size = 2

        # Mock should return results matching the batch size
        # For 5 articles with batch_size=2: batch1=2, batch2=2, batch3=1
        def mock_side_effect(texts):
            return [{"label": "positive", "score": 0.8} for _ in texts]

        mock_pipeline.side_effect = mock_side_effect

        articles = [make_article(f"Article {i}", summary=f"Summary {i}") for i in range(5)]

        results = scorer.score_articles(articles)

        # Should have 5 results total
        assert len(results) == 5
        # Mock should be called 3 times (2+2+1 batches)
        assert mock_pipeline.call_count == 3

    def test_update_articles_with_scores_empty(self, scorer):
        """Test update_articles_with_scores with empty list."""
        result = scorer.update_articles_with_scores([])

        assert result == []

    def test_update_articles_with_scores(self, scorer, mock_pipeline):
        """Test updating articles with sentiment scores."""
        mock_pipeline.return_value = [
            {"label": "positive", "score": 0.85},
            {"label": "negative", "score": 0.7},
        ]

        articles = [
            make_article("Good news", summary="Great results"),
            make_article("Bad news", summary="Disappointing quarter"),
        ]

        updated = scorer.update_articles_with_scores(articles)

        assert updated[0].sentiment == "positive"
        assert updated[0].sentiment_score == 0.85
        assert updated[1].sentiment == "negative"
        assert updated[1].sentiment_score == 0.7

    def test_get_aggregate_sentiment_empty(self, scorer):
        """Test aggregate sentiment with no articles."""
        result = scorer.get_aggregate_sentiment([])

        assert result["total"] == 0
        assert result["overall_sentiment"] == "neutral"

    def test_get_aggregate_sentiment_positive(self, scorer, mock_pipeline):
        """Test aggregate sentiment for positive articles."""
        mock_pipeline.return_value = [
            {"label": "positive", "score": 0.9},
            {"label": "positive", "score": 0.8},
            {"label": "neutral", "score": 0.7},
        ]

        articles = [
            make_article("Good 1", summary="Great"),
            make_article("Good 2", summary="Excellent"),
            make_article("Neutral", summary="Normal"),
        ]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["total"] == 3
        assert result["positive"] == 2
        assert result["neutral"] == 1
        assert result["overall_sentiment"] == "positive"
        assert result["scoring_method"] == "finbert_local"

    def test_get_aggregate_sentiment_negative(self, scorer, mock_pipeline):
        """Test aggregate sentiment for negative articles."""
        mock_pipeline.return_value = [
            {"label": "negative", "score": 0.9},
            {"label": "negative", "score": 0.8},
        ]

        articles = [
            make_article("Bad 1", summary="Terrible"),
            make_article("Bad 2", summary="Awful"),
        ]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["negative"] == 2
        assert result["overall_sentiment"] == "negative"
        assert result["avg_score"] < 0

    def test_get_aggregate_sentiment_with_existing_scores(self, scorer):
        """Test aggregate sentiment using existing article scores."""
        articles = [
            make_article("Article 1", sentiment="positive", sentiment_score=0.7),
            make_article("Article 2", sentiment="negative", sentiment_score=0.7),
        ]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["total"] == 2
        assert result["positive"] == 1
        assert result["negative"] == 1
        # With equal positive and negative scores, weighted avg = 0.0, should be neutral
        assert result["overall_sentiment"] == "neutral"
        assert result["avg_score"] == 0.0

    def test_get_aggregate_sentiment_percentages(self, scorer, mock_pipeline):
        """Test percentage calculations in aggregate sentiment."""
        mock_pipeline.return_value = [
            {"label": "positive", "score": 0.9},
            {"label": "positive", "score": 0.8},
            {"label": "negative", "score": 0.7},
            {"label": "neutral", "score": 0.6},
        ]

        articles = [make_article(f"Article {i}") for i in range(4)]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["positive_pct"] == 50.0  # 2/4
        assert result["negative_pct"] == 25.0  # 1/4
        assert result["neutral_pct"] == 25.0  # 1/4

    def test_ensure_loaded_lazy_loading(self, mock_pipeline):
        """Test that pipeline is lazy-loaded."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            with patch("src.sentiment.finbert.pipeline", mock_pipeline):
                from src.sentiment.finbert import FinBERTSentimentScorer

                scorer = FinBERTSentimentScorer()

                # Pipeline should not be loaded yet
                assert scorer._loaded is False
                assert scorer._pipeline is None

                # Force loading
                scorer._ensure_loaded()

                assert scorer._loaded is True
                mock_pipeline.assert_called_once()

    def test_ensure_loaded_only_once(self, mock_pipeline):
        """Test that pipeline is only loaded once."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            with patch("src.sentiment.finbert.pipeline", mock_pipeline):
                from src.sentiment.finbert import FinBERTSentimentScorer

                scorer = FinBERTSentimentScorer()

                scorer._ensure_loaded()
                scorer._ensure_loaded()
                scorer._ensure_loaded()

                # Should only be called once
                mock_pipeline.assert_called_once()

    def test_ensure_loaded_with_specific_device(self, mock_pipeline):
        """Test _ensure_loaded when device is set to a specific value."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            with patch("src.sentiment.finbert.pipeline", mock_pipeline):
                from src.sentiment.finbert import FinBERTSentimentScorer

                scorer = FinBERTSentimentScorer(device="cuda")
                scorer._ensure_loaded()

                # Verify pipeline was called with cuda device
                mock_pipeline.assert_called_once()
                call_kwargs = mock_pipeline.call_args[1]
                assert call_kwargs["device"] == "cuda"

    def test_default_model_class_variable(self):
        """Test that DEFAULT_MODEL class variable is set correctly."""
        with patch("src.sentiment.finbert.TRANSFORMERS_AVAILABLE", True):
            from src.sentiment.finbert import FinBERTSentimentScorer

            assert FinBERTSentimentScorer.DEFAULT_MODEL == "ProsusAI/finbert"

    def test_get_aggregate_sentiment_strongly_negative(self, scorer, mock_pipeline):
        """Test aggregate sentiment with strongly negative articles."""
        mock_pipeline.return_value = [
            {"label": "negative", "score": 0.9},
            {"label": "negative", "score": 0.8},
            {"label": "negative", "score": 0.85},
        ]

        articles = [make_article(f"Bad news {i}") for i in range(3)]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["total"] == 3
        assert result["negative"] == 3
        assert result["negative_pct"] == 100.0
        assert result["overall_sentiment"] == "negative"
        assert result["avg_score"] < -0.05

    def test_get_aggregate_sentiment_all_neutral(self, scorer, mock_pipeline):
        """Test aggregate sentiment with all neutral articles."""
        mock_pipeline.return_value = [
            {"label": "neutral", "score": 0.7},
            {"label": "neutral", "score": 0.6},
        ]

        articles = [make_article(f"Neutral article {i}") for i in range(2)]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["total"] == 2
        assert result["neutral"] == 2
        assert result["neutral_pct"] == 100.0
        assert result["positive_pct"] == 0.0
        assert result["negative_pct"] == 0.0
        assert result["overall_sentiment"] == "neutral"
        assert result["avg_score"] == 0.0

    def test_score_articles_with_title_and_summary(self, scorer, mock_pipeline):
        """Test scoring articles with both title and summary, include_title=True."""
        mock_pipeline.return_value = [{"label": "positive", "score": 0.85}]

        article = make_article("Breaking News", summary="This is great news")
        scorer.score_articles([article], include_title=True)

        # Verify pipeline was called with combined text
        mock_pipeline.assert_called_once()
        called_text = mock_pipeline.call_args[0][0][0]
        assert "Breaking News" in called_text
        assert "This is great news" in called_text

    def test_get_aggregate_sentiment_boundary_positive(self, scorer):
        """Test aggregate sentiment at exact positive threshold boundary."""
        # Create articles with avg_score slightly > 0.05
        articles = [
            make_article("Article 1", sentiment="positive", sentiment_score=0.06),
        ]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["avg_score"] == 0.06
        assert result["overall_sentiment"] == "positive"

    def test_get_aggregate_sentiment_boundary_negative(self, scorer):
        """Test aggregate sentiment at exact negative threshold boundary."""
        # Create articles with avg_score slightly < -0.05
        articles = [
            make_article("Article 1", sentiment="negative", sentiment_score=0.06),
        ]

        result = scorer.get_aggregate_sentiment(articles)

        assert result["avg_score"] == -0.06
        assert result["overall_sentiment"] == "negative"
