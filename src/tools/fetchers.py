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

    def __init__(
        self,
        cache_manager: CacheManager = None,
        provider_name: str = None,
        fixture_path: str = None,
    ):
        """Initialize price fetcher.

        Args:
            cache_manager: Optional cache manager for caching prices
            provider_name: Data provider to use (default: yahoo_finance, or 'fixture' for test mode)
            fixture_path: Path to fixture directory (required if provider_name is 'fixture')
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
        self.provider_name = provider_name or "yahoo_finance"
        self.fixture_path = fixture_path

        # Create provider with fixture path if needed
        if self.provider_name == "fixture" and fixture_path:
            self.provider = DataProviderFactory.create(
                self.provider_name, fixture_path=fixture_path
            )
        else:
            self.provider = DataProviderFactory.create(self.provider_name)

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

            # Fetch yfinance metrics
            metrics = self._get_yfinance_metrics(ticker)

            # Determine data availability
            available_sources = []
            if analyst_data:
                available_sources.append("analyst_consensus")
            if price_context and price_context.get("change_percent") is not None:
                available_sources.append("price_momentum")
            if metrics and any(v for v in metrics.values() if v and isinstance(v, dict) and v):
                available_sources.append("yfinance_metrics")

            # Note: Sentiment is calculated by CrewAI News & Sentiment Agent, not from premium APIs
            result = {
                "ticker": ticker,
                "analyst_data": analyst_data or {},
                "price_context": price_context or {},
                "metrics": metrics or {},
                "data_availability": (
                    ", ".join(available_sources) if available_sources else "limited"
                ),
                "timestamp": datetime.now().isoformat(),
            }

            # Cache even partial data (longer TTL for financial metrics)
            self.cache_manager.set(cache_key, result, ttl_hours=24)

            return result

        except Exception as e:
            logger.debug(f"Error fetching fundamental data for {ticker}: {e}")
            return {
                "ticker": ticker,
                "analyst_data": {},
                "price_context": {},
                "metrics": {},
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

    def _get_yfinance_metrics(self, ticker: str) -> dict[str, Any]:
        """Get fundamental metrics from yfinance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with valuation, profitability, financial health, and growth metrics
        """
        try:
            import yfinance as yf

            logger.debug(f"Fetching yfinance metrics for {ticker}")

            # Fetch ticker data
            tick = yf.Ticker(ticker)
            info = tick.info

            if not info:
                logger.debug(f"No yfinance data available for {ticker}")
                return {}

            # Extract valuation metrics
            valuation = {
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "peg_ratio": info.get("pegRatio"),
                "enterprise_value": info.get("enterpriseValue"),
                "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
            }

            # Extract profitability metrics
            profitability = {
                "gross_margin": info.get("grossMargins"),
                "operating_margin": info.get("operatingMargins"),
                "profit_margin": info.get("profitMargins"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "ebitda": info.get("ebitda"),
                "trailing_eps": info.get("trailingEps"),
                "forward_eps": info.get("forwardEps"),
            }

            # Extract financial health metrics
            financial_health = {
                "debt_to_equity": info.get("debtToEquity"),
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "free_cashflow": info.get("freeCashflow"),
                "operating_cashflow": info.get("operatingCashflow"),
            }

            # Extract growth metrics
            growth = {
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
            }

            # Filter out None values for cleaner output
            metrics = {
                "valuation": {k: v for k, v in valuation.items() if v is not None},
                "profitability": {k: v for k, v in profitability.items() if v is not None},
                "financial_health": {k: v for k, v in financial_health.items() if v is not None},
                "growth": {k: v for k, v in growth.items() if v is not None},
            }

            logger.debug(f"Retrieved yfinance metrics for {ticker}")
            return metrics

        except ImportError:
            logger.warning("yfinance not installed, skipping metrics")
            return {}
        except Exception as e:
            logger.debug(f"Error getting yfinance metrics for {ticker}: {e}")
            return {}


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
