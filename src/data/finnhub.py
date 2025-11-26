"""Finnhub data provider implementation."""

import os
from datetime import datetime
from typing import Optional

import requests

from src.data.models import Market, NewsArticle
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
            logger.info("Finnhub provider initialized")
        else:
            logger.warning("Finnhub API key not found. Set FINNHUB_API_KEY env var.")

    def get_news(
        self,
        ticker: str,
        limit: int = 10,
        max_age_hours: int = 24,
    ) -> list[NewsArticle]:
        """Fetch news articles from Finnhub.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles to return
            max_age_hours: Maximum age of articles in hours

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

            response = requests.get(
                f"{FINNHUB_BASE_URL}/company-news",
                params={
                    "symbol": ticker,
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

    def get_news_sentiment(self, ticker: str) -> Optional[dict]:
        """Fetch news sentiment for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with sentiment metrics or None if not available

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Finnhub API key is not configured")

        try:
            logger.debug(f"Fetching news sentiment for {ticker}")

            response = requests.get(
                f"{FINNHUB_BASE_URL}/news-sentiment",
                params={
                    "symbol": ticker,
                    "token": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()

            sentiment = {
                "positive": data.get("sentiment", {}).get("positive", 0),
                "negative": data.get("sentiment", {}).get("negative", 0),
                "neutral": 1
                - data.get("sentiment", {}).get("positive", 0)
                - data.get("sentiment", {}).get("negative", 0),
            }

            logger.debug(f"Sentiment for {ticker}: {sentiment}")
            return sentiment

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sentiment for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch sentiment for {ticker}: {e}")

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
