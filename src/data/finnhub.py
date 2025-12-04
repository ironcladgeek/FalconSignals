"""Finnhub data provider implementation."""

import os
from datetime import datetime, timedelta
from typing import Optional

import requests

from src.data.models import AnalystRating, Market, NewsArticle, StockPrice
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
        as_of_date: datetime | None = None,
    ) -> list[NewsArticle]:
        """Fetch news articles from Finnhub.

        Supports historical news fetching for backtesting with strict date filtering
        to prevent look-ahead bias.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles to return (default: 50)
            as_of_date: Optional date for historical news (only fetch news before this date)

        Returns:
            List of NewsArticle objects sorted by date descending

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Finnhub API key is not configured")

        try:
            logger.debug(f"Fetching news for {ticker} (limit={limit}, as_of_date={as_of_date})")

            # Fetch news articles with historical support
            if as_of_date:
                # For historical analysis, fetch news up to the analysis date
                to_date = as_of_date
                from_date = to_date - timedelta(days=90)  # 90-day lookback for historical
                logger.debug(f"Fetching historical news from {from_date} to {to_date}")
            else:
                # For current analysis, fetch recent news (30 days)
                to_date = datetime.now()
                from_date = to_date - timedelta(days=30)

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

                    # CLIENT-SIDE FILTERING: For historical analysis, ensure no future articles
                    # This prevents look-ahead bias even if API parameter filtering is incomplete
                    if as_of_date and published_date.date() > as_of_date.date():
                        logger.debug(
                            f"Filtering out future article (pub: {published_date.date()}, "
                            f"analysis: {as_of_date.date()})"
                        )
                        continue

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

    def get_recommendation_trends(
        self, ticker: str, as_of_date: datetime | None = None
    ) -> Optional[dict]:
        """Fetch analyst recommendation trends (FREE TIER endpoint).

        Supports historical recommendation fetching for backtesting with strict date filtering
        to prevent look-ahead bias.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Optional date for historical recommendations (only fetch recommendations before this date)

        Returns:
            Dictionary with analyst ratings distribution or None if not available

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Finnhub API key is not configured")

        try:
            logger.debug(f"Fetching recommendation trends for {ticker} (as_of_date={as_of_date})")

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

            # For historical analysis: find most recent recommendation before as_of_date
            # For current analysis: use most recent recommendation (current behavior)
            if as_of_date:
                as_of_date_only = as_of_date.date() if hasattr(as_of_date, "date") else as_of_date
                logger.debug(
                    f"Filtering recommendation trends for historical date {as_of_date_only}"
                )

                # Find most recent recommendation with period <= as_of_date
                # Data is ordered newest to oldest, so find first match
                matching_trend = None
                for trend in data:
                    trend_period_str = trend.get("period", "")
                    try:
                        trend_date = datetime.strptime(trend_period_str, "%Y-%m-%d").date()
                        if trend_date <= as_of_date_only:
                            matching_trend = trend
                            # Found most recent match (data is newest-first), stop searching
                            break
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse period: {trend_period_str}")
                        continue

                if not matching_trend:
                    logger.debug(
                        f"No recommendation trends available for {ticker} before {as_of_date_only}"
                    )
                    return None

                latest = matching_trend
            else:
                # Current analysis: use most recent recommendation
                latest = data[0]  # First item is most recent (API returns newest-first)

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

    def get_analyst_ratings(
        self, ticker: str, as_of_date: datetime | None = None
    ) -> Optional[AnalystRating]:
        """Fetch analyst ratings for a stock.

        This wraps get_recommendation_trends() and converts to AnalystRating model.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Optional date for historical ratings

        Returns:
            AnalystRating object or None if not available
        """
        trends = self.get_recommendation_trends(ticker, as_of_date=as_of_date)
        if not trends:
            return None

        try:
            # Convert trends dict to AnalystRating model
            # Determine consensus rating based on distribution
            total = trends.get("total_analysts", 0)
            if total == 0:
                return None

            strong_buy_pct = trends.get("strong_buy", 0) / total
            buy_pct = trends.get("buy", 0) / total

            if strong_buy_pct >= 0.4:
                consensus = "strong_buy"
                rating = "buy"
            elif (strong_buy_pct + buy_pct) >= 0.5:
                consensus = "buy"
                rating = "buy"
            elif trends.get("hold", 0) / total >= 0.4:
                consensus = "hold"
                rating = "hold"
            elif trends.get("sell", 0) / total >= 0.3:
                consensus = "sell"
                rating = "sell"
            else:
                consensus = "hold"
                rating = "hold"

            # Parse period date
            period_str = trends.get("period", "")
            try:
                rating_date = datetime.strptime(period_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                rating_date = datetime.now()

            return AnalystRating(
                ticker=ticker,
                name=trends.get("name", ticker),
                rating_date=rating_date,
                rating=rating,
                price_target=None,  # Finnhub doesn't provide this in free tier
                num_analysts=total,
                consensus=consensus,
                # Include raw recommendation counts from Finnhub
                strong_buy=trends.get("strong_buy", 0),
                buy=trends.get("buy", 0),
                hold=trends.get("hold", 0),
                sell=trends.get("sell", 0),
                strong_sell=trends.get("strong_sell", 0),
            )
        except Exception as e:
            logger.warning(f"Error converting recommendation trends to AnalystRating: {e}")
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
