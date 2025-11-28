"""Finnhub data provider implementation."""

import os
from datetime import datetime, timedelta
from typing import Optional

import requests

from src.data.models import Market, NewsArticle, StockPrice
from src.data.providers import DataProvider, DataProviderFactory
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Finnhub API constants
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
DEFAULT_TIMEOUT = 30


class FinnhubProvider(DataProvider):
    """Finnhub data provider implementation.

    Supports news and sentiment data fetching using Finnhub API.
    Free tier: 60 calls/minute.
    Focus on news, company news, and news sentiment.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize Finnhub provider.

        Args:
            api_key: Finnhub API key. If None, uses FINNHUB_API_KEY env var
            timeout: Request timeout in seconds
        """
        super().__init__("finnhub")
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.timeout = timeout
        self.is_available = bool(self.api_key)

        if self.is_available:
            logger.debug("Finnhub provider initialized")
        else:
            logger.warning("Finnhub API key not found. Set FINNHUB_API_KEY env var.")

    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[StockPrice]:
        """Fetch historical stock prices.

        Note: Finnhub's free tier has limited price data access.
        This method raises NotImplementedError as price data should use a different provider.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of StockPrice objects

        Raises:
            NotImplementedError: Finnhub is optimized for news/sentiment, not price data
        """
        raise NotImplementedError(
            "Finnhub provider is optimized for news and sentiment data. "
            "Use YahooFinanceProvider or AlphaVantageProvider for price data."
        )

    def get_latest_price(self, ticker: str) -> StockPrice:
        """Fetch latest stock price.

        Note: Finnhub's free tier has limited price data access.
        This method raises NotImplementedError as price data should use a different provider.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            NotImplementedError: Finnhub is optimized for news/sentiment, not price data
        """
        raise NotImplementedError(
            "Finnhub provider is optimized for news and sentiment data. "
            "Use YahooFinanceProvider or AlphaVantageProvider for price data."
        )

    def get_news(
        self,
        ticker: str,
        limit: int = 50,
        max_age_hours: int = 168,
    ) -> list[NewsArticle]:
        """Fetch news articles from Finnhub.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles to return (default: 50)
            max_age_hours: Maximum age of articles in hours (default: 168 = 7 days)

        Returns:
            List of NewsArticle objects sorted by date descending

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Finnhub API key is not configured")

        try:
            logger.debug(f"Fetching news for {ticker} (limit={limit})")

            # Calculate date range based on max_age_hours
            to_date = datetime.now()
            from_date = to_date - timedelta(hours=max_age_hours)

            response = requests.get(
                f"{FINNHUB_BASE_URL}/company-news",
                params={
                    "symbol": ticker,
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                    "token": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                logger.warning(f"Unexpected response format for news: {data}")
                return []

            articles = []
            for item in data[:limit]:
                try:
                    # Convert Unix timestamp to datetime
                    published_date = datetime.fromtimestamp(item["datetime"])

                    article = NewsArticle(
                        ticker=ticker.upper(),
                        title=item.get("headline", "")[:200],
                        summary=item.get("summary", "")[:500],
                        source=item.get("source", "Finnhub"),
                        url=item.get("url", ""),
                        published_date=published_date,
                    )
                    articles.append(article)

                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed news item: {e}")
                    continue

            logger.debug(f"Retrieved {len(articles)} news articles for {ticker}")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch news for {ticker}: {e}")

    def get_company_info(self, ticker: str) -> Optional[dict]:
        """Fetch company basic information.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with company info or None if not available

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Finnhub API key is not configured")

        try:
            logger.debug(f"Fetching company info for {ticker}")

            response = requests.get(
                f"{FINNHUB_BASE_URL}/stock/profile2",
                params={
                    "symbol": ticker,
                    "token": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if not data:
                return None

            return {
                "ticker": data.get("ticker", ticker),
                "name": data.get("name", ""),
                "industry": data.get("finnhubIndustry", ""),
                "sector": data.get("sector", ""),
                "market_cap": data.get("marketCapitalization", 0),
                "website": data.get("weburl", ""),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch company info for {ticker}: {e}")

    def get_recommendation_trends(self, ticker: str) -> Optional[dict]:
        """Fetch analyst recommendation trends (FREE TIER endpoint).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with analyst ratings distribution or None if not available

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Finnhub API key is not configured")

        try:
            logger.debug(f"Fetching recommendation trends for {ticker}")

            response = requests.get(
                f"{FINNHUB_BASE_URL}/stock/recommendation",
                params={
                    "symbol": ticker,
                    "token": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Handle empty or invalid JSON responses
            try:
                data = response.json()
            except ValueError as json_err:
                logger.warning(
                    f"Invalid JSON response for {ticker} recommendation trends: {json_err}"
                )
                return None

            if not data or len(data) == 0:
                logger.debug(f"No recommendation trend data available for {ticker}")
                return None

            # Get most recent recommendation data
            latest = data[0]
            return {
                "ticker": ticker,
                "period": latest.get("period"),
                "strong_buy": latest.get("strongBuy", 0),
                "buy": latest.get("buy", 0),
                "hold": latest.get("hold", 0),
                "sell": latest.get("sell", 0),
                "strong_sell": latest.get("strongSell", 0),
                "total_analysts": latest.get("strongBuy", 0)
                + latest.get("buy", 0)
                + latest.get("hold", 0)
                + latest.get("sell", 0)
                + latest.get("strongSell", 0),
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error fetching recommendation trends for {ticker}: {e}")
            return None

    @staticmethod
    def _infer_market(ticker: str) -> Market:
        """Infer market from ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Market classification (nordic, eu, or us)
        """
        ticker_upper = ticker.upper()

        # Nordic markets
        nordic_suffixes = {".ST", ".HE", ".CO", ".CSE"}
        if any(ticker_upper.endswith(suffix) for suffix in nordic_suffixes):
            return Market.NORDIC

        # EU markets
        eu_suffixes = {".DE", ".PA", ".MI", ".MA", ".BR", ".AS", ".VI"}
        if any(ticker_upper.endswith(suffix) for suffix in eu_suffixes):
            return Market.EU

        # Default to US
        return Market.US


# Register the provider
DataProviderFactory.register("finnhub", FinnhubProvider)
