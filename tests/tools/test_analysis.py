"""Comprehensive tests for TechnicalIndicatorTool and SentimentAnalyzerTool."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.tools.analysis import SentimentAnalyzerTool, TechnicalIndicatorTool


class TestTechnicalIndicatorTool:
    """Test suite for TechnicalIndicatorTool class."""

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data for testing."""
        dates = pd.date_range("2024-01-01", periods=60, freq="D")
        prices = []
        for i, date in enumerate(dates):
            # Create simple uptrend data
            base_price = 100 + i * 0.5
            prices.append(
                {
                    "date": date,
                    "ticker": "AAPL",
                    "open": base_price - 0.5,
                    "high": base_price + 1.0,
                    "low": base_price - 1.0,
                    "close": base_price,
                    "high_price": base_price + 1.0,
                    "low_price": base_price - 1.0,
                    "close_price": base_price,
                    "volume": 1000000 + i * 10000,
                }
            )
        return prices

    @pytest.fixture
    def tool(self):
        """Create TechnicalIndicatorTool instance."""
        return TechnicalIndicatorTool()

    @pytest.fixture
    def tool_with_config(self):
        """Create TechnicalIndicatorTool with custom config."""
        from src.config.schemas import TechnicalIndicatorsConfig

        config = TechnicalIndicatorsConfig(
            enabled_indicators=["rsi", "macd", "sma"],
            rsi_period=14,
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
        )
        return TechnicalIndicatorTool(config=config)

    def test_initialization_default_config(self):
        """Test initialization with default configuration."""
        tool = TechnicalIndicatorTool()

        assert tool.name == "TechnicalIndicator"
        assert "technical indicators" in tool.description.lower()
        assert tool._analyzer is not None

    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration."""
        from src.config.schemas import IndicatorConfig, TechnicalIndicatorsConfig

        config = TechnicalIndicatorsConfig(
            indicators=[
                IndicatorConfig(name="rsi", params={"length": 21}, enabled=True),
                IndicatorConfig(
                    name="macd", params={"fast": 12, "slow": 26, "signal": 9}, enabled=True
                ),
            ]
        )
        tool = TechnicalIndicatorTool(config=config)

        assert tool._analyzer is not None
        assert len(tool._analyzer.config.indicators) == 2

    def test_initialization_with_global_config_fallback(self):
        """Test initialization falls back to global config when no config provided."""
        with patch("src.config.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.analysis.technical_indicators = MagicMock()
            mock_get_config.return_value = mock_config

            tool = TechnicalIndicatorTool()

            assert tool._analyzer is not None
            mock_get_config.assert_called_once()

    def test_run_with_valid_prices(self, tool, sample_prices):
        """Test run with valid price data."""
        result = tool.run(sample_prices)

        assert "error" not in result
        assert "symbol" in result
        assert result["symbol"] == "AAPL"
        assert "latest_price" in result
        assert "trend" in result
        assert "full_analysis" in result

    def test_run_with_empty_prices(self, tool):
        """Test run with empty price list."""
        result = tool.run([])

        assert "error" in result
        assert result["error"] == "No price data provided"

    def test_run_returns_rsi(self, tool, sample_prices):
        """Test that RSI is calculated and returned."""
        result = tool.run(sample_prices)

        if "rsi" in result:
            assert isinstance(result["rsi"], (int, float))
            assert 0 <= result["rsi"] <= 100

    def test_run_returns_macd(self, tool, sample_prices):
        """Test that MACD indicators are calculated and returned."""
        result = tool.run(sample_prices)

        # MACD may or may not be present depending on config
        if "macd" in result:
            assert isinstance(result["macd"], (int, float))
            assert "macd_signal" in result
            assert "macd_histogram" in result

    def test_run_returns_bollinger_bands(self, tool, sample_prices):
        """Test that Bollinger Bands are calculated and returned."""
        result = tool.run(sample_prices)

        if "bbands_upper" in result:
            assert isinstance(result["bbands_upper"], (int, float))
            assert "bbands_middle" in result
            assert "bbands_lower" in result
            # Upper should be > middle > lower
            assert result["bbands_upper"] >= result["bbands_middle"]
            assert result["bbands_middle"] >= result["bbands_lower"]

    def test_run_returns_moving_averages(self, tool, sample_prices):
        """Test that moving averages are calculated and returned."""
        result = tool.run(sample_prices)

        # Check for various moving averages
        ma_fields = ["sma_20", "sma_50", "ema_12", "ema_26", "wma_14"]
        found_mas = [field for field in ma_fields if field in result]

        # At least some moving averages should be present
        assert len(found_mas) > 0

    def test_run_returns_atr(self, tool, sample_prices):
        """Test that ATR is calculated and returned."""
        result = tool.run(sample_prices)

        if "atr" in result:
            assert isinstance(result["atr"], (int, float))
            assert result["atr"] >= 0

    def test_run_returns_adx(self, tool, sample_prices):
        """Test that ADX indicators are calculated and returned."""
        result = tool.run(sample_prices)

        if "adx" in result:
            assert isinstance(result["adx"], (int, float))
            assert 0 <= result["adx"] <= 100

    def test_run_returns_stochastic(self, tool, sample_prices):
        """Test that Stochastic indicators are calculated and returned."""
        result = tool.run(sample_prices)

        if "stoch_k" in result:
            assert isinstance(result["stoch_k"], (int, float))
            assert 0 <= result["stoch_k"] <= 100
            if "stoch_d" in result:
                assert 0 <= result["stoch_d"] <= 100

    def test_run_returns_ichimoku(self, tool, sample_prices):
        """Test that Ichimoku indicators are calculated and returned."""
        result = tool.run(sample_prices)

        ichimoku_fields = [
            "ichimoku_tenkan",
            "ichimoku_kijun",
            "ichimoku_senkou_a",
            "ichimoku_senkou_b",
            "ichimoku_chikou",
        ]
        found_ichimoku = [field for field in ichimoku_fields if field in result]

        # If Ichimoku is enabled, should have some components
        if len(found_ichimoku) > 0:
            assert all(isinstance(result[field], (int, float)) for field in found_ichimoku)

    def test_run_returns_trend_information(self, tool, sample_prices):
        """Test that trend information is included."""
        result = tool.run(sample_prices)

        assert "trend" in result
        assert result["trend"] in ["up", "down", "neutral", "sideways"]

        if "trend_signals" in result:
            assert isinstance(result["trend_signals"], list)

    def test_run_returns_volume_ratio(self, tool, sample_prices):
        """Test that volume ratio is calculated when available."""
        result = tool.run(sample_prices)

        if "volume_ratio" in result:
            assert isinstance(result["volume_ratio"], (int, float))
            assert result["volume_ratio"] >= 0

    def test_run_with_insufficient_data(self, tool):
        """Test run with insufficient price data."""
        # Only 5 days of data - not enough for most indicators
        short_prices = [
            {
                "date": datetime(2024, 1, i),
                "ticker": "AAPL",
                "close": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "volume": 1000000,
            }
            for i in range(1, 6)
        ]

        result = tool.run(short_prices)

        # Should not error out, but may have limited indicators
        assert "symbol" in result or "error" in result

    def test_run_with_missing_ticker(self, tool, sample_prices):
        """Test run with price data missing ticker field."""
        prices_no_ticker = [p.copy() for p in sample_prices]
        for p in prices_no_ticker:
            p.pop("ticker", None)

        result = tool.run(prices_no_ticker)

        assert "symbol" in result
        # Should default to "Unknown" when ticker is missing
        assert result["symbol"] == "Unknown"

    def test_run_with_exception_in_analyzer(self, tool, sample_prices):
        """Test run handles exceptions from analyzer gracefully."""
        tool._analyzer.calculate_indicators = MagicMock(side_effect=Exception("Calculation error"))

        result = tool.run(sample_prices)

        assert "error" in result
        assert "Calculation error" in result["error"]

    def test_run_with_error_from_analyzer(self, tool, sample_prices):
        """Test run handles error result from analyzer."""
        tool._analyzer.calculate_indicators = MagicMock(return_value={"error": "Invalid data"})

        result = tool.run(sample_prices)

        assert "error" in result
        assert result["error"] == "Invalid data"

    def test_get_summary_with_valid_prices(self, tool, sample_prices):
        """Test get_summary with valid price data."""
        summary = tool.get_summary(sample_prices)

        assert "error" not in summary
        # Summary should be simpler than full results
        assert isinstance(summary, dict)

    def test_get_summary_with_error(self, tool):
        """Test get_summary with empty prices."""
        summary = tool.get_summary([])

        assert "error" in summary

    def test_get_summary_calls_analyzer_summary(self, tool, sample_prices):
        """Test that get_summary uses analyzer's summary method."""
        with patch.object(
            tool._analyzer, "get_indicator_summary", return_value={"summary": "test"}
        ) as mock_summary:
            tool.get_summary(sample_prices)

            mock_summary.assert_called_once()

    def test_legacy_calculate_rsi(self):
        """Test legacy RSI calculation method."""
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 2)

        rsi = TechnicalIndicatorTool._calculate_rsi(prices, period=14)

        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_legacy_calculate_macd(self):
        """Test legacy MACD calculation method."""
        prices = pd.Series(range(100, 150))

        macd = TechnicalIndicatorTool._calculate_macd(prices)

        assert "line" in macd
        assert "signal" in macd
        assert "histogram" in macd
        assert all(isinstance(v, float) for v in macd.values())

    def test_legacy_calculate_atr(self):
        """Test legacy ATR calculation method."""
        df = pd.DataFrame(
            {
                "high_price": [101, 103, 102, 105, 104] * 5,
                "low_price": [99, 100, 98, 102, 100] * 5,
                "close_price": [100, 102, 101, 104, 103] * 5,
            }
        )

        atr = TechnicalIndicatorTool._calculate_atr(df, period=14)

        assert isinstance(atr, float)
        assert atr >= 0


class TestSentimentAnalyzerTool:
    """Test suite for SentimentAnalyzerTool class."""

    @pytest.fixture
    def sample_articles(self):
        """Create sample news articles with sentiment."""
        now = datetime.now()
        return [
            {
                "title": "Company reports strong earnings",
                "summary": "Revenue beats expectations",
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "importance": 90,
                "published_date": now - timedelta(days=1),
            },
            {
                "title": "Regulatory concerns emerge",
                "summary": "Investigation announced",
                "sentiment": "negative",
                "sentiment_score": 0.7,
                "importance": 80,
                "published_date": now - timedelta(days=2),
            },
            {
                "title": "New product launch scheduled",
                "summary": "Event planned for next month",
                "sentiment": "neutral",
                "sentiment_score": 0.1,
                "importance": 60,
                "published_date": now - timedelta(days=3),
            },
            {
                "title": "Stock price unchanged",
                "summary": "Trading sideways",
                "sentiment": "neutral",
                "sentiment_score": 0.05,
                "importance": 40,
                "published_date": now - timedelta(days=5),
            },
        ]

    @pytest.fixture
    def tool(self):
        """Create SentimentAnalyzerTool instance."""
        return SentimentAnalyzerTool()

    @pytest.fixture
    def tool_with_date(self):
        """Create SentimentAnalyzerTool with specific analysis date."""
        return SentimentAnalyzerTool(analysis_date=datetime(2024, 6, 15))

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        tool = SentimentAnalyzerTool()

        assert tool.name == "SentimentAnalyzer"
        assert "sentiment" in tool.description.lower()
        assert tool.analysis_date is None

    def test_initialization_with_date(self):
        """Test initialization with custom analysis date."""
        analysis_date = datetime(2024, 6, 15)
        tool = SentimentAnalyzerTool(analysis_date=analysis_date)

        assert tool.analysis_date == analysis_date

    def test_run_with_valid_articles(self, tool, sample_articles):
        """Test run with valid articles."""
        result = tool.run(sample_articles)

        assert "error" not in result
        assert result["count"] == 4
        assert result["positive"] == 1
        assert result["negative"] == 1
        assert result["neutral"] == 2
        assert "weighted_sentiment" in result
        assert "sentiment_direction" in result

    def test_run_with_empty_articles(self, tool):
        """Test run with empty article list."""
        result = tool.run([])

        assert result["count"] == 0
        assert result["positive"] == 0
        assert result["negative"] == 0
        assert result["neutral"] == 0
        assert result["avg_sentiment"] == 0.0
        assert result["weighted_sentiment"] == 0.0

    def test_run_calculates_percentages(self, tool, sample_articles):
        """Test that percentage calculations are correct."""
        result = tool.run(sample_articles)

        assert "positive_pct" in result
        assert "negative_pct" in result
        assert "neutral_pct" in result

        # Percentages should sum to 100
        total_pct = result["positive_pct"] + result["negative_pct"] + result["neutral_pct"]
        assert abs(total_pct - 100.0) < 0.1

        # 1 positive out of 4 = 25%
        assert result["positive_pct"] == 25.0
        assert result["negative_pct"] == 25.0
        assert result["neutral_pct"] == 50.0

    def test_run_calculates_weighted_sentiment(self, tool, sample_articles):
        """Test weighted sentiment calculation."""
        result = tool.run(sample_articles)

        assert "weighted_sentiment" in result
        assert isinstance(result["weighted_sentiment"], float)
        # Should be between -1 and 1
        assert -1.0 <= result["weighted_sentiment"] <= 1.0

    def test_run_determines_sentiment_direction(self, tool, sample_articles):
        """Test sentiment direction determination."""
        result = tool.run(sample_articles)

        assert "sentiment_direction" in result
        assert result["sentiment_direction"] in ["positive", "negative", "neutral"]

    def test_run_with_positive_sentiment(self, tool):
        """Test with predominantly positive articles."""
        positive_articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 0.9,
                "importance": 80,
                "published_date": datetime.now(),
            },
            {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "importance": 70,
                "published_date": datetime.now(),
            },
        ]

        result = tool.run(positive_articles)

        assert result["sentiment_direction"] == "positive"
        assert result["weighted_sentiment"] > 0.05

    def test_run_with_negative_sentiment(self, tool):
        """Test with predominantly negative articles."""
        negative_articles = [
            {
                "sentiment": "negative",
                "sentiment_score": 0.9,
                "importance": 80,
                "published_date": datetime.now(),
            },
            {
                "sentiment": "negative",
                "sentiment_score": 0.8,
                "importance": 70,
                "published_date": datetime.now(),
            },
        ]

        result = tool.run(negative_articles)

        assert result["sentiment_direction"] == "negative"
        assert result["weighted_sentiment"] < -0.05

    def test_run_with_neutral_sentiment(self, tool):
        """Test with neutral articles."""
        neutral_articles = [
            {
                "sentiment": "neutral",
                "sentiment_score": 0.1,
                "importance": 50,
                "published_date": datetime.now(),
            }
            for _ in range(3)
        ]

        result = tool.run(neutral_articles)

        assert result["sentiment_direction"] == "neutral"
        assert abs(result["weighted_sentiment"]) <= 0.05

    def test_run_with_no_sentiment_data(self, tool):
        """Test with articles lacking sentiment data."""
        articles_no_sentiment = [
            {"title": "News 1", "summary": "Content 1"},
            {"title": "News 2", "summary": "Content 2"},
        ]

        result = tool.run(articles_no_sentiment)

        assert result["count"] == 2
        assert result["has_precalculated_scores"] is False
        assert result["requires_llm_analysis"] is True
        assert "note" in result

    def test_run_with_mixed_sentiment_data(self, tool):
        """Test with mix of articles with and without sentiment."""
        mixed_articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "published_date": datetime.now(),
            },
            {"title": "No sentiment article"},  # Missing sentiment
        ]

        result = tool.run(mixed_articles)

        # Should process the article with sentiment
        assert result["count"] == 2
        assert result["positive"] == 1
        assert result["has_precalculated_scores"] is True

    def test_calculate_recency_weight_recent_article(self, tool):
        """Test recency weight for recent article."""
        published = datetime.now() - timedelta(days=1)
        reference = datetime.now()

        weight = tool._calculate_recency_weight(published, reference)

        # Very recent article should have high weight
        assert weight > 0.9
        assert weight <= 1.0

    def test_calculate_recency_weight_old_article(self, tool):
        """Test recency weight for old article."""
        published = datetime.now() - timedelta(days=90)
        reference = datetime.now()

        weight = tool._calculate_recency_weight(published, reference)

        # Old article should have lower weight
        assert 0.01 <= weight < 0.5

    def test_calculate_recency_weight_with_string_dates(self, tool):
        """Test recency weight with string date inputs."""
        published = "2024-01-01"
        reference = "2024-01-31"

        weight = tool._calculate_recency_weight(published, reference)

        # Should handle string dates
        assert 0.01 <= weight <= 1.0

    def test_calculate_recency_weight_with_none_reference(self, tool):
        """Test recency weight with None reference date."""
        published = datetime.now() - timedelta(days=5)

        weight = tool._calculate_recency_weight(published, None)

        # Should use current date as reference
        assert 0.01 <= weight <= 1.0

    def test_calculate_recency_weight_with_error(self, tool):
        """Test recency weight handles errors gracefully."""
        weight = tool._calculate_recency_weight("invalid", "dates")

        # Should return default weight of 1.0 on error
        assert weight == 1.0

    def test_calculate_recency_weight_exponential_decay(self, tool):
        """Test that recency weight follows exponential decay."""
        reference = datetime.now()

        # Calculate weights at different time points
        weight_1day = tool._calculate_recency_weight(reference - timedelta(days=1), reference)
        weight_30days = tool._calculate_recency_weight(reference - timedelta(days=30), reference)
        weight_60days = tool._calculate_recency_weight(reference - timedelta(days=60), reference)

        # Should decay exponentially
        assert weight_1day > weight_30days > weight_60days

        # 30-day half-life with e^(-age/half_life) means weight at 30 days = e^-1 ≈ 0.368
        assert 0.35 <= weight_30days <= 0.40

    def test_calculate_importance_weight_high(self, tool):
        """Test importance weight for high importance article."""
        weight = tool._calculate_importance_weight(100)

        # 100 importance should give maximum weight
        assert weight == 1.0

    def test_calculate_importance_weight_medium(self, tool):
        """Test importance weight for medium importance article."""
        weight = tool._calculate_importance_weight(50)

        # 50 importance should give mid-range weight
        assert 0.6 <= weight <= 0.7

    def test_calculate_importance_weight_low(self, tool):
        """Test importance weight for low importance article."""
        weight = tool._calculate_importance_weight(0)

        # 0 importance should give minimum weight
        assert weight == 0.3

    def test_calculate_importance_weight_none(self, tool):
        """Test importance weight when importance is None."""
        weight = tool._calculate_importance_weight(None)

        # None should give default weight
        assert weight == 0.7

    def test_run_with_custom_reference_date(self, tool):
        """Test run with custom reference date parameter."""
        reference_date = datetime(2024, 1, 15)
        articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "published_date": datetime(2024, 1, 10),
            }
        ]

        result = tool.run(articles, reference_date=reference_date)

        assert "weighted_sentiment" in result

    def test_run_uses_instance_analysis_date(self, tool_with_date):
        """Test that run uses instance analysis_date when no reference_date provided."""
        articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "published_date": datetime(2024, 6, 10),
            }
        ]

        result = tool_with_date.run(articles)

        # Should use instance's analysis_date for recency calculations
        assert "weighted_sentiment" in result

    def test_run_with_articles_without_importance(self, tool):
        """Test run with articles missing importance scores."""
        articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "published_date": datetime.now(),
                # No importance field
            }
        ]

        result = tool.run(articles)

        # Should handle missing importance gracefully
        assert "weighted_sentiment" in result

    def test_run_with_articles_without_published_date(self, tool):
        """Test run with articles missing published dates."""
        articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "importance": 80,
                # No published_date field
            }
        ]

        result = tool.run(articles)

        # Should handle missing date gracefully
        assert "weighted_sentiment" in result

    def test_run_includes_scored_count(self, tool, sample_articles):
        """Test that result includes count of scored articles."""
        result = tool.run(sample_articles)

        assert "scored_count" in result
        assert result["scored_count"] == 4

    def test_run_with_exception(self, tool):
        """Test run handles exceptions gracefully."""
        # Pass invalid data that will cause an error
        invalid_articles = [{"sentiment": None, "sentiment_score": "not_a_number"}]

        result = tool.run(invalid_articles)

        # Should catch exception and return error
        assert "error" in result or "count" in result

    def test_weighted_sentiment_combines_weights(self, tool):
        """Test that weighted sentiment combines recency and importance weights."""
        now = datetime.now()
        articles = [
            {
                "sentiment": "positive",
                "sentiment_score": 1.0,
                "importance": 100,  # High importance
                "published_date": now,  # Very recent
            },
            {
                "sentiment": "positive",
                "sentiment_score": 1.0,
                "importance": 30,  # Low importance
                "published_date": now - timedelta(days=90),  # Old
            },
        ]

        result = tool.run(articles)

        # First article should dominate due to high importance and recency
        assert result["weighted_sentiment"] > 0
        assert result["scored_count"] == 2

    def test_signed_score_calculation(self, tool):
        """Test that scores are correctly signed based on sentiment."""
        articles = [
            {"sentiment": "positive", "sentiment_score": 0.8, "published_date": datetime.now()},
            {"sentiment": "negative", "sentiment_score": 0.8, "published_date": datetime.now()},
            {"sentiment": "neutral", "sentiment_score": 0.5, "published_date": datetime.now()},
        ]

        result = tool.run(articles)

        # With equal scores but opposite sentiments, should balance out close to neutral
        assert abs(result["weighted_sentiment"]) < 0.5
        assert result["positive"] == 1
        assert result["negative"] == 1
        assert result["neutral"] == 1

    def test_precalculated_scores_flag(self, tool):
        """Test has_precalculated_scores flag is set correctly."""
        # Articles with precalculated scores
        with_scores = [
            {"sentiment": "positive", "sentiment_score": 0.8, "published_date": datetime.now()}
        ]

        result_with = tool.run(with_scores)
        assert result_with["has_precalculated_scores"] is True
        assert result_with["requires_llm_analysis"] is False

        # Articles without precalculated scores
        without_scores = [{"title": "Article without sentiment"}]

        result_without = tool.run(without_scores)
        assert result_without["has_precalculated_scores"] is False
        assert result_without["requires_llm_analysis"] is True
