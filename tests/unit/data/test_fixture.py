"""Tests for FixtureDataProvider and test mode functionality."""

import json
from datetime import datetime

import pytest

from src.data.fixture import FixtureDataProvider
from src.data.models import NewsArticle, StockPrice


@pytest.fixture
def fixture_path(tmp_path):
    """Create a temporary fixture directory with test data."""
    fixture_dir = tmp_path / "test_fixture"
    fixture_dir.mkdir()

    # Create price data
    price_data = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "us",
            "instrument_type": "stock",
            "date": "2024-10-25T00:00:00",
            "open_price": 228.50,
            "high_price": 230.25,
            "low_price": 227.75,
            "close_price": 229.10,
            "volume": 45325600,
            "adjusted_close": 229.10,
            "currency": "USD",
        },
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "us",
            "instrument_type": "stock",
            "date": "2024-10-24T00:00:00",
            "open_price": 227.80,
            "high_price": 229.75,
            "low_price": 227.50,
            "close_price": 228.85,
            "volume": 42156200,
            "adjusted_close": 228.85,
            "currency": "USD",
        },
    ]

    with open(fixture_dir / "price_data.json", "w") as f:
        json.dump(price_data, f)

    # Create fundamentals data
    fundamentals = {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "market_cap_usd": 3150000000000,
        "trailing_pe": 29.5,
        "roe_percent": 119.5,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "analyst_rating": "buy",
        "num_analysts": 45,
        "price_target_12m": 238.50,
    }

    with open(fixture_dir / "fundamentals.json", "w") as f:
        json.dump(fundamentals, f)

    # Create news data
    news_data = [
        {
            "ticker": "AAPL",
            "title": "Apple Q4 2024 Earnings Beat Expectations",
            "summary": "Strong earnings report",
            "source": "Reuters",
            "url": "https://example.com/news1",
            "published_date": "2024-10-25T14:30:00",
            "sentiment": "positive",
            "sentiment_score": 0.78,
            "importance": 95,
        }
    ]

    with open(fixture_dir / "news.json", "w") as f:
        json.dump(news_data, f)

    # Create metadata
    metadata = {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "description": "Test fixture for AAPL",
    }

    with open(fixture_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    return fixture_dir


class TestFixtureDataProvider:
    """Test suite for FixtureDataProvider."""

    def test_initialization(self, fixture_path):
        """Test provider initialization with valid fixture path."""
        provider = FixtureDataProvider(fixture_path)
        assert provider.name == "fixture"
        assert provider.is_available is True

    def test_initialization_with_missing_path(self):
        """Test provider initialization fails with missing path."""
        with pytest.raises(FileNotFoundError):
            FixtureDataProvider("/nonexistent/path")

    def test_get_stock_prices(self, fixture_path):
        """Test getting stock prices from fixture."""
        provider = FixtureDataProvider(fixture_path)
        prices = provider.get_stock_prices("AAPL", datetime.min, datetime.max)

        assert len(prices) == 2
        assert all(isinstance(p, StockPrice) for p in prices)
        assert prices[0].close_price == 229.10  # Most recent first
        assert prices[1].close_price == 228.85

    def test_get_latest_price(self, fixture_path):
        """Test getting latest price from fixture."""
        provider = FixtureDataProvider(fixture_path)
        latest = provider.get_latest_price("AAPL")

        assert isinstance(latest, StockPrice)
        assert latest.close_price == 229.10
        assert latest.ticker == "AAPL"

    def test_get_latest_price_missing_ticker(self, fixture_path):
        """Test getting latest price for missing ticker raises error."""
        provider = FixtureDataProvider(fixture_path)
        with pytest.raises(RuntimeError):
            provider.get_latest_price("NONEXISTENT")

    def test_get_news(self, fixture_path):
        """Test getting news articles from fixture."""
        provider = FixtureDataProvider(fixture_path)
        articles = provider.get_news("AAPL", limit=10)

        assert len(articles) == 1
        assert all(isinstance(a, NewsArticle) for a in articles)
        assert articles[0].title == "Apple Q4 2024 Earnings Beat Expectations"
        assert articles[0].sentiment == "positive"

    def test_get_analyst_ratings(self, fixture_path):
        """Test getting analyst ratings from fixture."""
        provider = FixtureDataProvider(fixture_path)
        rating = provider.get_analyst_ratings("AAPL")

        assert rating is not None
        assert rating.ticker == "AAPL"
        assert rating.rating == "buy"
        assert rating.num_analysts == 45

    def test_get_instrument_metadata(self, fixture_path):
        """Test getting instrument metadata from fixture."""
        provider = FixtureDataProvider(fixture_path)
        metadata = provider.get_instrument_metadata("AAPL")

        assert metadata.ticker == "AAPL"
        assert metadata.name == "Apple Inc."
        assert metadata.sector == "Technology"
        assert metadata.industry == "Consumer Electronics"

    def test_validate_ticker_existing(self, fixture_path):
        """Test ticker validation for existing ticker."""
        provider = FixtureDataProvider(fixture_path)
        assert provider.validate_ticker("AAPL") is True

    def test_validate_ticker_missing(self, fixture_path):
        """Test ticker validation for missing ticker."""
        provider = FixtureDataProvider(fixture_path)
        assert provider.validate_ticker("NONEXISTENT") is False

    def test_get_fixture_metadata(self, fixture_path):
        """Test getting fixture metadata."""
        provider = FixtureDataProvider(fixture_path)
        metadata = provider.get_fixture_metadata()

        assert metadata["ticker"] == "AAPL"
        assert metadata["name"] == "Apple Inc."
        assert metadata["description"] == "Test fixture for AAPL"

    def test_case_insensitive_ticker(self, fixture_path):
        """Test that ticker matching is case-insensitive."""
        provider = FixtureDataProvider(fixture_path)
        prices_upper = provider.get_stock_prices("AAPL", datetime.min, datetime.max)
        prices_lower = provider.get_stock_prices("aapl", datetime.min, datetime.max)
        prices_mixed = provider.get_stock_prices("AaPl", datetime.min, datetime.max)

        assert len(prices_upper) == len(prices_lower) == len(prices_mixed) == 2

    def test_news_limit(self, fixture_path):
        """Test that news limit parameter works."""
        provider = FixtureDataProvider(fixture_path)
        articles_all = provider.get_news("AAPL", limit=100)
        articles_limited = provider.get_news("AAPL", limit=0)

        assert len(articles_all) == 1
        assert len(articles_limited) == 0

    def test_financial_statements_unsupported(self, fixture_path):
        """Test that financial statements return empty list."""
        provider = FixtureDataProvider(fixture_path)
        statements = provider.get_financial_statements("AAPL")

        assert statements == []
