"""Data fetching tools for agents."""

from datetime import datetime, timedelta
from typing import Any

from src.cache.manager import CacheManager
from src.data.models import StockPrice
from src.data.providers import DataProviderFactory
from src.tools.base import BaseTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PriceFetcherTool(BaseTool):
    """Tool for fetching stock price data."""

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize price fetcher.

        Args:
            cache_manager: Optional cache manager for caching prices
        """
        super().__init__(
            name="PriceFetcher",
            description=(
                "Retrieve historical and current stock price data. "
                "Input: ticker symbol and date range. "
                "Output: List of prices with OHLCV data."
            ),
        )
        self.cache_manager = cache_manager or CacheManager()
        self.provider = DataProviderFactory.create("yahoo_finance")

    def run(
        self,
        ticker: str,
        start_date: datetime = None,
        end_date: datetime = None,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """Fetch price data for ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (if None, uses days_back)
            end_date: End date (defaults to today)
            days_back: Days back from end_date if start_date is None

        Returns:
            Dictionary with prices and metadata
        """
        try:
            # Set date range
            if end_date is None:
                end_date = datetime.now()

            if start_date is None:
                start_date = end_date - timedelta(days=days_back)

            # Check cache first
            cache_key = f"prices:{ticker}:{start_date.date()}:{end_date.date()}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {ticker} prices")
                return cached

            # Fetch from provider
            logger.debug(f"Fetching prices for {ticker}")
            prices = self.provider.get_stock_prices(ticker, start_date, end_date)

            if not prices:
                return {
                    "ticker": ticker,
                    "prices": [],
                    "count": 0,
                    "error": f"No price data found for {ticker}",
                }

            # Cache results
            result = {
                "ticker": ticker,
                "prices": [p.model_dump() for p in prices],
                "count": len(prices),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "latest_price": prices[-1].close_price,
            }
            self.cache_manager.set(cache_key, result, ttl_hours=24)

            return result

        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            return {
                "ticker": ticker,
                "prices": [],
                "count": 0,
                "error": str(e),
            }

    def get_latest(self, ticker: str) -> dict[str, Any]:
        """Get latest price for ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest price data
        """
        try:
            cache_key = f"latest_price:{ticker}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                return cached

            price = self.provider.get_latest_price(ticker)
            result = {
                "ticker": ticker,
                "price": price.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }
            self.cache_manager.set(cache_key, result, ttl_hours=1)

            return result

        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}


class NewsFetcherTool(BaseTool):
    """Tool for fetching news articles."""

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize news fetcher.

        Args:
            cache_manager: Optional cache manager for caching news
        """
        super().__init__(
            name="NewsFetcher",
            description=(
                "Fetch and filter relevant news articles. "
                "Input: ticker symbol and optional time window. "
                "Output: List of news articles with metadata."
            ),
        )
        self.cache_manager = cache_manager or CacheManager()
        self.provider = DataProviderFactory.create("finnhub")

    def run(
        self,
        ticker: str,
        limit: int = 10,
        max_age_hours: int = 48,
    ) -> dict[str, Any]:
        """Fetch news for ticker.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles
            max_age_hours: Maximum age of articles

        Returns:
            Dictionary with articles and metadata
        """
        try:
            cache_key = f"news:{ticker}:{limit}:{max_age_hours}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {ticker} news")
                return cached

            if not self.provider.is_available:
                return {
                    "ticker": ticker,
                    "articles": [],
                    "count": 0,
                    "error": "Finnhub provider not available",
                }

            logger.debug(f"Fetching news for {ticker}")
            articles = self.provider.get_news(ticker, limit=limit, max_age_hours=max_age_hours)

            result = {
                "ticker": ticker,
                "articles": [a.model_dump() for a in articles],
                "count": len(articles),
                "timestamp": datetime.now().isoformat(),
            }
            self.cache_manager.set(cache_key, result, ttl_hours=4)

            return result

        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return {
                "ticker": ticker,
                "articles": [],
                "count": 0,
                "error": str(e),
            }
