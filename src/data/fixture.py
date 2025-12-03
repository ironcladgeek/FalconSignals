"""Fixture-based data provider for testing without API calls."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.data.models import (
    AnalystRating,
    FinancialStatement,
    InstrumentMetadata,
    NewsArticle,
    StockPrice,
)
from src.data.providers import DataProvider, DataProviderFactory
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FixtureDataProvider(DataProvider):
    """Data provider that reads from fixture files instead of APIs.

    Perfect for testing without API calls or costs.
    """

    def __init__(self, fixture_path: Path | str):
        """Initialize fixture provider.

        Args:
            fixture_path: Path to fixture directory containing JSON files

        Raises:
            FileNotFoundError: If fixture directory doesn't exist
        """
        super().__init__("fixture")
        self.fixture_path = Path(fixture_path)

        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Fixture directory not found: {fixture_path}")

        self._fixtures = {}
        self._load_all_fixtures()
        self.is_available = True

    def _load_all_fixtures(self) -> None:
        """Load all fixture files from directory."""
        # Look for price_data.json, fundamentals.json, news.json files
        self._fixtures = {
            "price_data": self._load_json_file("price_data.json"),
            "fundamentals": self._load_json_file("fundamentals.json"),
            "news": self._load_json_file("news.json"),
            "metadata": self._load_json_file("metadata.json"),
        }
        logger.debug(f"Loaded fixtures from {self.fixture_path}")

    def _load_json_file(self, filename: str) -> dict | list | None:
        """Load JSON file from fixture directory.

        Args:
            filename: Name of JSON file to load

        Returns:
            Parsed JSON data or None if file doesn't exist
        """
        file_path = self.fixture_path / filename
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {filename}: {e}")
            return None

    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[StockPrice]:
        """Get stock prices from fixture data.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (ignored for fixtures)
            end_date: End date (ignored for fixtures)

        Returns:
            List of StockPrice objects
        """
        prices_data = self._fixtures.get("price_data")
        if not prices_data:
            return []

        prices = []
        for price_dict in prices_data:
            if price_dict.get("ticker", "").upper() == ticker.upper():
                try:
                    price = StockPrice(**price_dict)
                    prices.append(price)
                except Exception as e:
                    logger.warning(f"Failed to parse price data: {e}")

        # Sort by date descending (most recent first)
        prices.sort(key=lambda p: p.date, reverse=True)
        return prices

    def get_latest_price(self, ticker: str) -> StockPrice:
        """Get latest stock price from fixture data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            RuntimeError: If no price data found
        """
        prices = self.get_stock_prices(ticker, datetime.min, datetime.max)

        if not prices:
            raise RuntimeError(f"No price data found for {ticker} in fixtures")

        return prices[0]  # Most recent first

    def get_financial_statements(
        self,
        ticker: str,
        statement_type: str = "income_statement",
        limit: int = 5,
    ) -> list[FinancialStatement]:
        """Financial statements are not supported in fixtures.

        Args:
            ticker: Stock ticker symbol
            statement_type: Type of statement
            limit: Number of periods

        Returns:
            Empty list (fixtures don't include detailed statements)
        """
        return []

    def get_news(
        self,
        ticker: str,
        limit: int = 10,
        as_of_date: datetime | None = None,
    ) -> list[NewsArticle]:
        """Get news articles from fixture data.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles
            as_of_date: Optional date for historical news (only fetch news before this date)

        Returns:
            List of NewsArticle objects
        """
        news_data = self._fixtures.get("news")
        if not news_data:
            return []

        articles = []
        for article_dict in news_data:
            if article_dict.get("ticker", "").upper() == ticker.upper():
                try:
                    article = NewsArticle(**article_dict)
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse news article: {e}")

        # Sort by date descending (most recent first)
        articles.sort(key=lambda a: a.published_date, reverse=True)
        return articles[:limit]

    def get_analyst_ratings(self, ticker: str) -> Optional[AnalystRating]:
        """Get analyst ratings from fundamentals data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AnalystRating object or None if not available
        """
        fundamentals = self._fixtures.get("fundamentals")
        if not fundamentals:
            return None

        if fundamentals.get("ticker", "").upper() != ticker.upper():
            return None

        # Extract rating info from fundamentals
        return AnalystRating(
            ticker=ticker,
            name=fundamentals.get("name", ticker),
            rating_date=datetime.now(),
            rating=fundamentals.get("analyst_rating", "hold"),
            price_target=fundamentals.get("price_target_12m"),
            num_analysts=fundamentals.get("num_analysts"),
            consensus=fundamentals.get("analyst_rating", "hold"),
        )

    def get_instrument_metadata(self, ticker: str) -> InstrumentMetadata:
        """Get instrument metadata.

        Args:
            ticker: Stock ticker symbol

        Returns:
            InstrumentMetadata object

        Raises:
            RuntimeError: If metadata not found
        """
        fundamentals = self._fixtures.get("fundamentals")
        if not fundamentals or fundamentals.get("ticker", "").upper() != ticker.upper():
            raise RuntimeError(f"No metadata found for {ticker} in fixtures")

        return InstrumentMetadata(
            ticker=ticker,
            name=fundamentals.get("name", ticker),
            market="us",
            instrument_type="stock",
            sector=fundamentals.get("sector", "Unknown"),
            industry=fundamentals.get("industry", "Unknown"),
            last_updated=datetime.now(),
        )

    def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker exists in fixtures.

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if ticker found in any fixture data
        """
        # Check in fundamentals
        fundamentals = self._fixtures.get("fundamentals")
        if fundamentals and fundamentals.get("ticker", "").upper() == ticker.upper():
            return True

        # Check in price data
        prices_data = self._fixtures.get("price_data")
        if prices_data:
            for price_dict in prices_data:
                if price_dict.get("ticker", "").upper() == ticker.upper():
                    return True

        # Check in news
        news_data = self._fixtures.get("news")
        if news_data:
            for news_dict in news_data:
                if news_dict.get("ticker", "").upper() == ticker.upper():
                    return True

        return False

    def get_fixture_metadata(self) -> dict:
        """Get metadata about the fixture.

        Returns:
            Dictionary containing fixture metadata
        """
        return self._fixtures.get("metadata", {})


# Register FixtureDataProvider with factory
DataProviderFactory.register("fixture", FixtureDataProvider)
