"""Comprehensive tests for PriceFetcherTool and NewsFetcherTool."""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.cache.manager import CacheManager
from src.data.models import NewsArticle, StockPrice
from src.tools.fetchers import NewsFetcherTool, PriceFetcherTool


class TestPriceFetcherTool:
    """Test suite for PriceFetcherTool class."""

    @pytest.fixture
    def mock_cache_manager(self):
        """Create a mock cache manager."""
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None  # Default to cache miss
        return cache

    @pytest.fixture
    def mock_provider(self):
        """Create a mock data provider."""
        provider = MagicMock()
        provider.get_stock_prices.return_value = []
        provider.get_latest_price.return_value = MagicMock(close_price=150.0)
        return provider

    @pytest.fixture
    def tool(self, mock_cache_manager, mock_provider):
        """Create PriceFetcherTool instance with mocks."""
        with patch("src.tools.fetchers.DataProviderFactory.create", return_value=mock_provider):
            tool = PriceFetcherTool(cache_manager=mock_cache_manager, use_unified_storage=False)
            return tool

    @pytest.fixture
    def tool_with_unified_storage(self, mock_cache_manager, mock_provider):
        """Create PriceFetcherTool with unified storage enabled."""
        with patch("src.tools.fetchers.DataProviderFactory.create", return_value=mock_provider):
            tool = PriceFetcherTool(cache_manager=mock_cache_manager, use_unified_storage=True)
            return tool

    def test_initialization_default_params(self, mock_cache_manager):
        """Test initialization with default parameters."""
        with patch("src.tools.fetchers.DataProviderFactory.create") as mock_factory:
            tool = PriceFetcherTool(cache_manager=mock_cache_manager)

            assert tool.name == "PriceFetcher"
            assert "stock price data" in tool.description.lower()
            assert tool.provider_name == "yahoo_finance"
            assert tool.use_unified_storage is True
            mock_factory.assert_called_once_with("yahoo_finance")

    def test_initialization_with_custom_provider(self, mock_cache_manager):
        """Test initialization with custom provider."""
        with patch("src.tools.fetchers.DataProviderFactory.create") as mock_factory:
            tool = PriceFetcherTool(cache_manager=mock_cache_manager, provider_name="alpha_vantage")

            assert tool.provider_name == "alpha_vantage"
            mock_factory.assert_called_once_with("alpha_vantage")

    def test_initialization_with_fixture_provider(self, mock_cache_manager):
        """Test initialization with fixture provider and path."""
        with patch("src.tools.fetchers.DataProviderFactory.create") as mock_factory:
            tool = PriceFetcherTool(
                cache_manager=mock_cache_manager,
                provider_name="fixture",
                fixture_path="/path/to/fixtures",
            )

            assert tool.provider_name == "fixture"
            mock_factory.assert_called_once_with("fixture", fixture_path="/path/to/fixtures")

    def test_set_historical_date(self, tool):
        """Test setting historical date for backtesting."""
        historical_date = date(2024, 6, 15)

        tool.set_historical_date(historical_date)

        assert tool.historical_date == historical_date

    def test_price_manager_lazy_initialization(self, tool_with_unified_storage):
        """Test that price manager is lazily initialized."""
        assert tool_with_unified_storage._price_manager is None

        # Access property triggers initialization
        pm = tool_with_unified_storage.price_manager

        assert pm is not None
        assert tool_with_unified_storage._price_manager is pm

    def test_run_with_legacy_cache_hit(self, tool, mock_cache_manager):
        """Test run with cache hit (legacy JSON cache)."""
        cached_data = {
            "ticker": "AAPL",
            "prices": [{"close_price": 150.0, "date": "2024-01-01"}],
            "count": 1,
            "period": "730d",
        }
        mock_cache_manager.get.return_value = cached_data

        result = tool.run("AAPL", days_back=730)

        assert result == cached_data
        mock_cache_manager.get.assert_called_once()

    def test_run_with_legacy_cache_miss(self, tool, mock_cache_manager, mock_provider):
        """Test run with cache miss (legacy JSON cache)."""
        # Create mock StockPrice objects
        price1 = MagicMock(spec=StockPrice)
        price1.close_price = 145.0
        price1.model_dump.return_value = {"close_price": 145.0, "date": "2024-01-01"}

        price2 = MagicMock(spec=StockPrice)
        price2.close_price = 150.0
        price2.model_dump.return_value = {"close_price": 150.0, "date": "2024-01-02"}

        mock_provider.get_stock_prices.return_value = [price1, price2]
        mock_cache_manager.get.return_value = None

        result = tool.run("AAPL", days_back=730)

        assert result["ticker"] == "AAPL"
        assert result["count"] == 2
        assert result["latest_price"] == 150.0
        assert result["storage"] == "legacy_json"
        mock_provider.get_stock_prices.assert_called_once()
        mock_cache_manager.set.assert_called_once()

    def test_run_with_period_parameter(self, tool, mock_provider):
        """Test run with explicit period parameter."""
        price = MagicMock(spec=StockPrice)
        price.close_price = 155.0
        price.model_dump.return_value = {"close_price": 155.0}
        mock_provider.get_stock_prices.return_value = [price]

        result = tool.run("AAPL", period="60d")

        assert result["ticker"] == "AAPL"
        assert result["period"] == "60d"
        mock_provider.get_stock_prices.assert_called_once_with("AAPL", period="60d")

    def test_run_with_date_range(self, tool, mock_provider):
        """Test run with explicit date range."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        price = MagicMock(spec=StockPrice)
        price.close_price = 160.0
        price.model_dump.return_value = {"close_price": 160.0}
        mock_provider.get_stock_prices.return_value = [price]

        result = tool.run("AAPL", start_date=start_date, end_date=end_date)

        assert result["ticker"] == "AAPL"
        mock_provider.get_stock_prices.assert_called_once()

    def test_run_with_historical_date(self, tool, mock_provider):
        """Test run with historical date set (backtesting)."""
        historical_date = date(2024, 6, 15)
        tool.set_historical_date(historical_date)

        price = MagicMock(spec=StockPrice)
        price.close_price = 140.0
        price.model_dump.return_value = {"close_price": 140.0}
        mock_provider.get_stock_prices.return_value = [price]

        result = tool.run("AAPL", days_back=30)

        assert result["ticker"] == "AAPL"
        # Should fetch prices ending at historical date, not today

    def test_run_with_no_prices_found(self, tool, mock_provider):
        """Test run when no prices are returned."""
        mock_provider.get_stock_prices.return_value = []

        result = tool.run("INVALID")

        assert result["ticker"] == "INVALID"
        assert result["count"] == 0
        assert "error" in result

    def test_run_with_exception(self, tool, mock_provider):
        """Test run with exception during fetch."""
        mock_provider.get_stock_prices.side_effect = Exception("API error")

        result = tool.run("ERROR_TICKER")

        assert result["ticker"] == "ERROR_TICKER"
        assert "error" in result
        assert "API error" in result["error"]

    def test_run_with_config_lookback_days(self, mock_cache_manager, mock_provider):
        """Test that config lookback days are used when days_back is None."""
        mock_config = MagicMock()
        mock_config.analysis.historical_data_lookback_days = 365

        with patch("src.tools.fetchers.DataProviderFactory.create", return_value=mock_provider):
            tool = PriceFetcherTool(
                cache_manager=mock_cache_manager, use_unified_storage=False, config=mock_config
            )

            price = MagicMock(spec=StockPrice)
            price.close_price = 150.0
            price.model_dump.return_value = {"close_price": 150.0}
            mock_provider.get_stock_prices.return_value = [price]

            tool.run("AAPL")

            # Should use config value (365d) instead of default (730d)
            mock_provider.get_stock_prices.assert_called_once()
            args, kwargs = mock_provider.get_stock_prices.call_args
            assert "period" in kwargs
            assert kwargs["period"] == "365d"

    def test_get_latest_with_cache_hit(self, tool, mock_cache_manager):
        """Test get_latest with cache hit."""
        cached_price = {
            "ticker": "AAPL",
            "price": {"close_price": 155.0},
            "timestamp": "2024-01-01T10:00:00",
        }
        mock_cache_manager.get.return_value = cached_price

        result = tool.get_latest("AAPL")

        assert result == cached_price
        mock_cache_manager.get.assert_called_once()

    def test_get_latest_with_cache_miss(self, tool, mock_cache_manager, mock_provider):
        """Test get_latest with cache miss."""
        price_obj = MagicMock()
        price_obj.model_dump.return_value = {"close_price": 160.0}
        mock_provider.get_latest_price.return_value = price_obj
        mock_cache_manager.get.return_value = None

        result = tool.get_latest("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["price"] == {"close_price": 160.0}
        assert "timestamp" in result
        mock_provider.get_latest_price.assert_called_once_with("AAPL")
        mock_cache_manager.set.assert_called_once()

    def test_get_latest_with_error(self, tool, mock_provider):
        """Test get_latest with error."""
        mock_provider.get_latest_price.side_effect = Exception("Connection failed")

        result = tool.get_latest("ERROR")

        assert result["ticker"] == "ERROR"
        assert "error" in result
        assert "Connection failed" in result["error"]

    @patch("src.tools.fetchers.PriceDataManager")
    def test_fetch_with_unified_storage_no_existing_data(
        self, mock_pm_class, tool_with_unified_storage, mock_provider
    ):
        """Test unified storage fetch with no existing data."""
        mock_pm = MagicMock()
        mock_pm.get_data_range.return_value = (None, None)
        mock_pm.get_prices.return_value = pd.DataFrame(
            {
                "date": [datetime(2024, 1, 1)],
                "close": [150.0],
                "open": [148.0],
                "high": [151.0],
                "low": [147.0],
                "volume": [1000000],
            }
        )
        mock_pm_class.return_value = mock_pm
        tool_with_unified_storage._price_manager = mock_pm

        # Mock provider to return prices
        price = MagicMock(spec=StockPrice)
        price.model_dump.return_value = {
            "date": datetime(2024, 1, 1),
            "close": 150.0,
            "open": 148.0,
            "high": 151.0,
            "low": 147.0,
            "volume": 1000000,
        }
        mock_provider.get_stock_prices.return_value = [price]

        result = tool_with_unified_storage.run("AAPL", days_back=30)

        assert result["ticker"] == "AAPL"
        assert result["storage"] == "unified_csv"
        assert result["count"] == 1
        mock_provider.get_stock_prices.assert_called_once()
        mock_pm.store_prices.assert_called_once()

    @patch("src.tools.fetchers.PriceDataManager")
    def test_fetch_with_unified_storage_existing_sufficient_data(
        self, mock_pm_class, tool_with_unified_storage, mock_provider
    ):
        """Test unified storage with sufficient existing data."""
        mock_pm = MagicMock()
        # Simulate having data from 2024-01-01 to 2024-12-31 (enough for days_back=30)
        mock_pm.get_data_range.return_value = (date(2024, 1, 1), date(2024, 12, 31))

        # Mock DataFrame with 100 trading days
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        mock_pm.get_prices.return_value = pd.DataFrame(
            {
                "date": dates,
                "close": [150.0] * 100,
                "open": [148.0] * 100,
                "high": [151.0] * 100,
                "low": [147.0] * 100,
                "volume": [1000000] * 100,
            }
        )
        mock_pm_class.return_value = mock_pm
        tool_with_unified_storage._price_manager = mock_pm

        result = tool_with_unified_storage.run("AAPL", days_back=30)

        assert result["ticker"] == "AAPL"
        assert result["count"] == 100
        # Should NOT fetch new data - existing is sufficient
        mock_provider.get_stock_prices.assert_not_called()

    @patch("src.tools.fetchers.PriceDataManager")
    def test_fetch_with_unified_storage_insufficient_data(
        self, mock_pm_class, tool_with_unified_storage, mock_provider
    ):
        """Test unified storage with insufficient existing data (needs fetch)."""
        mock_pm = MagicMock()
        # Simulate having only 10 trading days (need 30)
        mock_pm.get_data_range.return_value = (date(2024, 1, 1), date(2024, 1, 15))
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        existing_df = pd.DataFrame(
            {
                "date": dates,
                "close": [150.0] * 10,
                "open": [148.0] * 10,
                "high": [151.0] * 10,
                "low": [147.0] * 10,
                "volume": [1000000] * 10,
            }
        )
        mock_pm.get_prices.return_value = existing_df
        mock_pm_class.return_value = mock_pm
        tool_with_unified_storage._price_manager = mock_pm

        # Mock provider to return additional prices
        price = MagicMock(spec=StockPrice)
        price.model_dump.return_value = {
            "date": datetime(2024, 1, 20),
            "close": 155.0,
            "open": 153.0,
            "high": 156.0,
            "low": 152.0,
            "volume": 1200000,
        }
        mock_provider.get_stock_prices.return_value = [price]

        result = tool_with_unified_storage.run("AAPL", days_back=30)

        assert result["ticker"] == "AAPL"
        # Should fetch additional data since existing is insufficient
        mock_provider.get_stock_prices.assert_called_once()
        mock_pm.store_prices.assert_called_once()


class TestNewsFetcherTool:
    """Test suite for NewsFetcherTool class."""

    @pytest.fixture
    def mock_cache_manager(self):
        """Create a mock cache manager."""
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        cache.find_latest_by_prefix.return_value = None
        return cache

    @pytest.fixture
    def mock_aggregator(self):
        """Create a mock news aggregator."""
        aggregator = MagicMock()
        aggregator.fetch_news.return_value = []
        return aggregator

    @pytest.fixture
    def tool(self, mock_cache_manager):
        """Create NewsFetcherTool instance with mocks."""
        with patch("src.tools.fetchers.get_config") as mock_config:
            mock_config.return_value.data.news.use_unified_aggregator = False
            tool = NewsFetcherTool(cache_manager=mock_cache_manager, use_local_sentiment=False)
            return tool

    @pytest.fixture
    def sample_articles(self):
        """Create sample news articles."""
        return [
            NewsArticle(
                ticker="AAPL",
                title="Apple hits new high",
                summary="Strong earnings report",
                source="MarketWatch",
                published_date=datetime.now() - timedelta(days=1),
                url="https://example.com/news1",
                sentiment="positive",
                sentiment_score=0.8,
            ),
            NewsArticle(
                ticker="AAPL",
                title="Apple faces regulatory scrutiny",
                summary="EU investigation ongoing",
                source="Bloomberg",
                published_date=datetime.now() - timedelta(days=2),
                url="https://example.com/news2",
                sentiment="negative",
                sentiment_score=-0.6,
            ),
            NewsArticle(
                ticker="AAPL",
                title="Apple announces new product",
                summary="Product launch scheduled",
                source="TechCrunch",
                published_date=datetime.now() - timedelta(days=3),
                url="https://example.com/news3",
                sentiment="neutral",
                sentiment_score=0.0,
            ),
        ]

    def test_initialization_default_params(self, mock_cache_manager):
        """Test initialization with default parameters."""
        with patch("src.tools.fetchers.get_config") as mock_config:
            mock_config.return_value.data.news.use_unified_aggregator = False
            tool = NewsFetcherTool(cache_manager=mock_cache_manager)

            assert tool.name == "NewsFetcher"
            assert "news articles" in tool.description.lower()
            assert tool.use_local_sentiment is True

    def test_initialization_with_unified_aggregator(self, mock_cache_manager):
        """Test initialization with unified aggregator enabled."""
        with patch("src.tools.fetchers.get_config") as mock_config:
            # Mock news configuration
            mock_news_config = MagicMock()
            mock_news_config.use_unified_aggregator = True
            mock_news_config.target_article_count = 50
            mock_news_config.max_age_days = 7

            # Mock source configuration
            mock_source = MagicMock()
            mock_source.name = "alpha_vantage"
            mock_source.priority = 1
            mock_source.enabled = True
            mock_source.max_articles = 50
            mock_news_config.sources = [mock_source]

            mock_config.return_value.data.news = mock_news_config

            tool = NewsFetcherTool(cache_manager=mock_cache_manager)

            assert tool.news_aggregator is not None

    def test_set_historical_date(self, tool):
        """Test setting historical date for backtesting."""
        historical_date = date(2024, 6, 15)

        tool.set_historical_date(historical_date)

        assert tool.historical_date == historical_date

    def test_sentiment_analyzer_lazy_initialization(self, tool):
        """Test that sentiment analyzer is lazily initialized."""
        assert tool._sentiment_analyzer is None

        with patch("src.tools.fetchers.get_config"):
            with patch("src.tools.fetchers.ConfigurableSentimentAnalyzer"):
                # Access property triggers initialization
                _ = tool.sentiment_analyzer

                assert tool._sentiment_analyzer is not None

    def test_run_with_cache_hit(self, tool, mock_cache_manager):
        """Test run with cache hit."""
        cached_data = {
            "ticker": "AAPL",
            "articles": [],
            "count": 0,
            "sentiment_summary": None,
        }
        mock_cache_manager.get.return_value = cached_data

        result = tool.run("AAPL")

        assert result == cached_data
        mock_cache_manager.get.assert_called_once()

    def test_run_with_no_articles(self, tool, sample_articles):
        """Test run when no articles are returned."""
        tool.news_aggregator.fetch_news = MagicMock(return_value=[])

        result = tool.run("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["count"] == 0
        assert result["articles"] == []
        assert result["sentiment_summary"] is None

    def test_run_with_articles_no_local_sentiment(self, tool, sample_articles):
        """Test run with articles but local sentiment disabled."""
        tool.use_local_sentiment = False
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        result = tool.run("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["count"] == 3
        assert len(result["articles"]) == 3
        assert result["scoring_method"] == "api_provider"
        assert result["sentiment_summary"]["total"] == 3
        assert result["sentiment_summary"]["positive"] == 1
        assert result["sentiment_summary"]["negative"] == 1
        assert result["sentiment_summary"]["neutral"] == 1

    def test_run_with_articles_and_local_sentiment(self, tool, sample_articles):
        """Test run with articles and local FinBERT sentiment."""
        tool.use_local_sentiment = True
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        # Mock sentiment analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_sentiment.return_value = {
            "method": "local_finbert",
            "articles": sample_articles,
        }
        tool._sentiment_analyzer = mock_analyzer

        result = tool.run("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["count"] == 3
        assert result["scoring_method"] == "local_finbert"
        mock_analyzer.analyze_sentiment.assert_called_once()

    def test_run_with_local_sentiment_fallback(self, tool, sample_articles):
        """Test run with local sentiment failing and falling back to API."""
        tool.use_local_sentiment = True
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        # Mock sentiment analyzer that raises exception
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_sentiment.side_effect = Exception("FinBERT not available")
        tool._sentiment_analyzer = mock_analyzer

        result = tool.run("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["count"] == 3
        # Should fall back to API provider sentiment
        assert result["scoring_method"] == "api_provider_fallback"

    def test_run_with_historical_date(self, tool, sample_articles):
        """Test run with historical date set (backtesting)."""
        historical_date = date(2024, 6, 15)
        tool.set_historical_date(historical_date)
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        tool.run("AAPL")

        # Verify aggregator was called with historical date
        call_args = tool.news_aggregator.fetch_news.call_args
        assert call_args[1]["as_of_date"] is not None

    def test_run_with_custom_limit(self, tool, sample_articles):
        """Test run with custom article limit."""
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        with patch("src.tools.fetchers.get_config") as mock_config:
            mock_config.return_value.data.news.max_articles = 50
            result = tool.run("AAPL", limit=25)

            assert result["ticker"] == "AAPL"

    def test_run_with_exception(self, tool):
        """Test run with exception during fetch."""
        tool.news_aggregator.fetch_news = MagicMock(side_effect=Exception("API error"))

        result = tool.run("ERROR_TICKER")

        assert result["ticker"] == "ERROR_TICKER"
        assert "error" in result
        assert "API error" in result["error"]

    def test_sentiment_summary_calculation(self, tool, sample_articles):
        """Test sentiment summary calculation from articles."""
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        result = tool.run("AAPL")

        summary = result["sentiment_summary"]
        assert summary["total"] == 3
        assert summary["positive"] == 1
        assert summary["negative"] == 1
        assert summary["neutral"] == 1
        assert summary["positive_pct"] == pytest.approx(33.3, abs=0.1)
        assert summary["negative_pct"] == pytest.approx(33.3, abs=0.1)
        # Average: (0.8 + (-0.6) + 0.0) / 3 ≈ 0.067
        assert summary["avg_sentiment_score"] == pytest.approx(0.067, abs=0.01)
        assert summary["overall_sentiment"] == "neutral"

    def test_sentiment_summary_positive_overall(self, tool):
        """Test sentiment summary with positive overall sentiment."""
        positive_articles = [
            NewsArticle(
                ticker="AAPL",
                title="Great news",
                summary="Very positive",
                source="Test",
                published_date=datetime.now(),
                url="https://example.com",
                sentiment="positive",
                sentiment_score=0.9,
            ),
            NewsArticle(
                ticker="AAPL",
                title="Good news",
                summary="Positive",
                source="Test",
                published_date=datetime.now(),
                url="https://example.com",
                sentiment="positive",
                sentiment_score=0.7,
            ),
        ]
        tool.news_aggregator.fetch_news = MagicMock(return_value=positive_articles)

        result = tool.run("AAPL")

        summary = result["sentiment_summary"]
        assert summary["overall_sentiment"] == "positive"
        assert summary["avg_sentiment_score"] > 0.1

    def test_sentiment_summary_negative_overall(self, tool):
        """Test sentiment summary with negative overall sentiment."""
        negative_articles = [
            NewsArticle(
                ticker="AAPL",
                title="Bad news",
                summary="Very negative",
                source="Test",
                published_date=datetime.now(),
                url="https://example.com",
                sentiment="negative",
                sentiment_score=-0.9,
            ),
            NewsArticle(
                ticker="AAPL",
                title="Worse news",
                summary="Negative",
                source="Test",
                published_date=datetime.now(),
                url="https://example.com",
                sentiment="negative",
                sentiment_score=-0.7,
            ),
        ]
        tool.news_aggregator.fetch_news = MagicMock(return_value=negative_articles)

        result = tool.run("AAPL")

        summary = result["sentiment_summary"]
        assert summary["overall_sentiment"] == "negative"
        assert summary["avg_sentiment_score"] < -0.1

    def test_cache_key_with_date_range(self, tool, mock_cache_manager, sample_articles):
        """Test that cache key includes date range from articles."""
        tool.news_aggregator.fetch_news = MagicMock(return_value=sample_articles)

        tool.run("AAPL")

        # Verify cache.set was called with a key that includes date range
        mock_cache_manager.set.assert_called_once()
        cache_key = mock_cache_manager.set.call_args[0][0]
        assert "AAPL" in cache_key
        assert "news_finbert" in cache_key or "news_sentiment" in cache_key
