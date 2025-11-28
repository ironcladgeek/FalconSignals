"""Data fetching tools for agents."""

from datetime import datetime, timedelta
from typing import Any

from src.cache.manager import CacheManager
from src.config import get_config
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
            logger.debug(f"Error fetching prices for {ticker}: {e}")
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


class FinancialDataFetcherTool(BaseTool):
    """Tool for fetching fundamental data using free tier endpoints only.

    Uses Finnhub free tier endpoints:
    - /stock/profile2 (company info)
    - /stock/recommendation (analyst ratings)
    - Yahoo Finance (price data)

    Note: News sentiment is analyzed by CrewAI News & Sentiment Agent (not from premium APIs)
    """

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize financial data fetcher.

        Args:
            cache_manager: Optional cache manager for caching data
        """
        super().__init__(
            name="FinancialDataFetcher",
            description=(
                "Fetch fundamental data using free tier APIs only. "
                "Input: ticker symbol. "
                "Output: Dictionary with analyst consensus, sentiment, and price context."
            ),
        )
        self.cache_manager = cache_manager or CacheManager()
        self.finnhub_provider = DataProviderFactory.create("finnhub")
        self.price_provider = DataProviderFactory.create("yahoo_finance")

    def run(self, ticker: str) -> dict[str, Any]:
        """Fetch fundamental data for ticker (free tier only).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with analyst data, sentiment, and price context
        """
        try:
            # Check cache first
            cache_key = f"fundamental_freetier:{ticker}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {ticker} fundamental data")
                return cached

            if not self.finnhub_provider.is_available:
                logger.warning(f"Finnhub provider not available for {ticker}")
                # Return neutral data instead of error
                return {
                    "ticker": ticker,
                    "analyst_data": {},
                    "price_context": self._get_price_context(ticker) or {},
                    "data_availability": "limited - Finnhub API not configured",
                    "timestamp": datetime.now().isoformat(),
                }

            logger.debug(f"Fetching fundamental data for {ticker} (free tier only)")

            # Fetch analyst recommendations (may return None if unavailable)
            analyst_data = None
            try:
                analyst_data = self.finnhub_provider.get_recommendation_trends(ticker)
            except Exception as e:
                logger.warning(f"Could not fetch analyst data for {ticker}: {e}")

            # Fetch price context for momentum
            price_context = self._get_price_context(ticker)

            # Determine data availability
            available_sources = []
            if analyst_data:
                available_sources.append("analyst_consensus")
            if price_context and price_context.get("change_percent") is not None:
                available_sources.append("price_momentum")

            # Note: Sentiment is calculated by CrewAI News & Sentiment Agent, not from premium APIs
            result = {
                "ticker": ticker,
                "analyst_data": analyst_data or {},
                "price_context": price_context or {},
                "data_availability": (
                    ", ".join(available_sources) if available_sources else "limited"
                ),
                "timestamp": datetime.now().isoformat(),
            }

            # Cache even partial data
            self.cache_manager.set(cache_key, result, ttl_hours=4)  # Shorter cache for sentiment

            return result

        except Exception as e:
            logger.debug(f"Error fetching fundamental data for {ticker}: {e}")
            return {
                "ticker": ticker,
                "analyst_data": {},
                "price_context": {},
                "error": str(e),
            }

    def _get_price_context(self, ticker: str) -> dict[str, Any]:
        """Get price momentum context from price data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with change_percent and trend
        """
        try:
            # Get last 30 days of price data
            prices = self.price_provider.get_stock_prices(
                ticker, start_date=datetime.now() - timedelta(days=30), end_date=datetime.now()
            )

            if len(prices) < 2:
                return {"change_percent": 0, "trend": "neutral"}

            # Calculate recent change
            earliest_price = prices[0].close_price
            latest_price = prices[-1].close_price
            change_percent = (
                (latest_price - earliest_price) / earliest_price if earliest_price > 0 else 0
            )

            # Determine trend (simple: positive = bullish, negative = bearish)
            trend = (
                "bullish" if change_percent > 0 else "bearish" if change_percent < 0 else "neutral"
            )

            return {
                "change_percent": change_percent,
                "trend": trend,
                "latest_price": latest_price,
                "period_days": 30,
            }

        except Exception as e:
            logger.debug(f"Error getting price context for {ticker}: {e}")
            return {"change_percent": 0, "trend": "neutral"}


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
        limit: int = None,
        max_age_hours: int = None,
    ) -> dict[str, Any]:
        """Fetch news for ticker.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles (default: from config)
            max_age_hours: Maximum age of articles in hours (default: from config)

        Returns:
            Dictionary with articles and metadata
        """
        try:
            # Use config defaults if not specified
            if limit is None:
                limit = get_config().data.news.max_articles
            if max_age_hours is None:
                max_age_hours = get_config().data.news.max_age_hours

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
