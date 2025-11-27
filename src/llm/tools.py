"""CrewAI tool adapters for analysis functions."""

from typing import Callable

from src.tools.analysis import TechnicalIndicatorTool
from src.tools.fetchers import NewsFetcherTool, PriceFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CrewAIToolAdapter:
    """Adapts existing tools for use with CrewAI agents."""

    def __init__(self):
        """Initialize tool adapters."""
        self.price_fetcher = PriceFetcherTool()
        self.technical_tool = TechnicalIndicatorTool()
        self.news_fetcher = NewsFetcherTool()

    def fetch_price_data(self, ticker: str, days_back: int = 60) -> str:
        """Fetch historical and current price data for an instrument.

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days of history to fetch

        Returns:
            JSON string with price data including OHLCV
        """
        try:
            result = self.price_fetcher.run(ticker, days_back=days_back)
            if "error" in result:
                return f"Error fetching price data: {result['error']}"
            return str(result)
        except Exception as e:
            logger.error(f"Error fetching price data for {ticker}: {e}")
            return f"Error: {str(e)}"

    def calculate_technical_indicators(self, price_data: str) -> str:
        """Calculate technical indicators from price data.

        Args:
            price_data: Price data as JSON string or dict

        Returns:
            JSON string with calculated indicators (SMA, RSI, MACD, ATR, etc.)
        """
        try:
            import json

            if isinstance(price_data, str):
                prices = json.loads(price_data)
            else:
                prices = price_data

            # Extract price list if wrapped
            if isinstance(prices, dict):
                prices = prices.get("prices", [])

            result = self.technical_tool.run(prices)
            if "error" in result:
                return f"Error calculating indicators: {result['error']}"
            return str(result)
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return f"Error: {str(e)}"

    def fetch_news(self, ticker: str, max_articles: int = 10, max_age_hours: int = 168) -> str:
        """Fetch recent news articles for an instrument.

        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to fetch
            max_age_hours: Maximum age of articles in hours

        Returns:
            JSON string with news articles and sentiment
        """
        try:
            result = self.news_fetcher.run(
                ticker, max_articles=max_articles, max_age_hours=max_age_hours
            )
            if "error" in result:
                return f"Error fetching news: {result['error']}"
            return str(result)
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return f"Error: {str(e)}"

    def get_crewai_tools(self) -> list[Callable]:
        """Get all tools as CrewAI-compatible tool list.

        Returns:
            List of tool functions
        """
        return [
            self.fetch_price_data,
            self.calculate_technical_indicators,
            self.fetch_news,
        ]
