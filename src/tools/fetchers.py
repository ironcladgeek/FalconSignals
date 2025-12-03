"""Data fetching tools for agents."""

from datetime import datetime, timedelta
from typing import Any

from src.cache.manager import CacheManager
from src.config import get_config
from src.data.provider_manager import ProviderManager
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
        self.historical_date = None  # Track historical date for backtesting

        # Create provider with fixture path if needed
        if self.provider_name == "fixture" and fixture_path:
            self.provider = DataProviderFactory.create(
                self.provider_name, fixture_path=fixture_path
            )
        else:
            self.provider = DataProviderFactory.create(self.provider_name)

    def set_historical_date(self, historical_date):
        """Set historical date for backtesting.

        Args:
            historical_date: date object for historical analysis
        """
        self.historical_date = historical_date
        logger.debug(f"Historical date set to {historical_date} for PriceFetcherTool")

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
            end_date: End date (defaults to today or historical_date if set)
            days_back: Days back from end_date if start_date is None

        Returns:
            Dictionary with prices and metadata
        """
        try:
            # Set date range - use historical_date if set for backtesting
            if end_date is None:
                if self.historical_date:
                    end_date = datetime.combine(self.historical_date, datetime.max.time())
                    logger.debug(f"Using historical end_date: {end_date.date()} for {ticker}")
                else:
                    end_date = datetime.now()

            if start_date is None:
                start_date = end_date - timedelta(days=days_back)

            # Check cache first
            # Use consistent cache key format: prices:<ticker>:<start_date>:<end_date>
            cache_key = (
                f"prices:{ticker}:{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"
            )
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
    """Tool for fetching fundamental data using Alpha Vantage Premium + specialized providers.

    Provider configuration:
    - Alpha Vantage Premium: news sentiment + company overview + fundamentals + earnings estimates
    - Yahoo Finance: price data
    - Finnhub: analyst recommendations only
    """

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize financial data fetcher.

        Args:
            cache_manager: Optional cache manager for caching data
        """
        super().__init__(
            name="FinancialDataFetcher",
            description=(
                "Fetch fundamental data using Alpha Vantage Premium with specialized providers. "
                "Input: ticker symbol. "
                "Output: Dictionary with company info, news sentiment, earnings estimates, analyst data, and metrics."
            ),
        )
        self.cache_manager = cache_manager or CacheManager()

        # Use ProviderManager with Alpha Vantage for financial data
        self.provider_manager = ProviderManager(
            primary_provider="alpha_vantage",
            backup_providers=["yahoo_finance", "finnhub"],
        )

        # Keep direct access to specialized providers
        self.alpha_vantage_provider = DataProviderFactory.create("alpha_vantage")
        self.finnhub_provider = DataProviderFactory.create("finnhub")
        self.price_provider = DataProviderFactory.create("yahoo_finance")
        self.historical_date = None  # Track historical date for backtesting

    def set_historical_date(self, historical_date):
        """Set historical date for backtesting.

        Args:
            historical_date: date object for historical analysis
        """
        self.historical_date = historical_date
        logger.debug(f"Historical date set to {historical_date} for FinancialDataFetcherTool")

    def run(self, ticker: str) -> dict[str, Any]:
        """Fetch fundamental data for ticker using Alpha Vantage (primary) + fallbacks.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with company info, news sentiment, analyst data, and metrics
        """
        try:
            # Check cache first
            cache_key = f"fundamental_enriched:{ticker}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {ticker} fundamental data")
                return cached

            logger.debug(f"Fetching enriched fundamental data for {ticker}")

            # Convert historical_date to datetime if needed
            as_of_date = None
            if self.historical_date:
                as_of_date = datetime.combine(self.historical_date, datetime.max.time())
                logger.info(f"Fetching fundamental data as of {self.historical_date} for {ticker}")

            # Fetch company overview (Alpha Vantage Premium)
            company_info = None
            try:
                company_info = self.provider_manager.get_company_info(ticker)
            except Exception as e:
                logger.warning(f"Could not fetch company info for {ticker}: {e}")

            # Fetch earnings estimates (Alpha Vantage Premium) with historical date
            earnings_estimates = None
            try:
                if self.alpha_vantage_provider.is_available:
                    earnings_estimates = self.alpha_vantage_provider.get_earnings_estimates(
                        ticker, as_of_date=as_of_date
                    )
            except Exception as e:
                logger.warning(f"Could not fetch earnings estimates for {ticker}: {e}")

            # Fetch news with sentiment (Alpha Vantage Premium) with historical date
            news_articles = []
            news_sentiment_summary = None
            try:
                # Fetch latest news articles - limit provides sufficient filtering
                news_articles = self.provider_manager.get_news(
                    ticker, limit=50, as_of_date=as_of_date
                )
                # Calculate sentiment summary from articles
                if news_articles:
                    positive = sum(1 for a in news_articles if a.sentiment == "positive")
                    negative = sum(1 for a in news_articles if a.sentiment == "negative")
                    neutral = sum(1 for a in news_articles if a.sentiment == "neutral")
                    total = len(news_articles)

                    avg_sentiment = sum(
                        a.sentiment_score for a in news_articles if a.sentiment_score is not None
                    ) / max(1, sum(1 for a in news_articles if a.sentiment_score is not None))

                    news_sentiment_summary = {
                        "total_articles": total,
                        "positive": positive,
                        "negative": negative,
                        "neutral": neutral,
                        "positive_pct": round(100 * positive / total, 1) if total > 0 else 0,
                        "negative_pct": round(100 * negative / total, 1) if total > 0 else 0,
                        "avg_sentiment_score": round(avg_sentiment, 3),
                        "overall_sentiment": (
                            "positive"
                            if avg_sentiment > 0.1
                            else "negative"
                            if avg_sentiment < -0.1
                            else "neutral"
                        ),
                    }
            except Exception as e:
                logger.warning(f"Could not fetch news for {ticker}: {e}")

            # Fetch analyst recommendations (Finnhub only)
            analyst_data = None
            try:
                if self.finnhub_provider.is_available:
                    analyst_data = self.finnhub_provider.get_recommendation_trends(ticker)
            except Exception as e:
                logger.warning(f"Could not fetch analyst data for {ticker}: {e}")

            # Fetch price context for momentum
            price_context = self._get_price_context(ticker)

            # Fetch yfinance metrics
            metrics = self._get_yfinance_metrics(ticker)

            # Determine data availability
            available_sources = []
            if company_info:
                available_sources.append("company_overview")
            if news_sentiment_summary:
                available_sources.append("news_sentiment")
            if earnings_estimates:
                available_sources.append("earnings_estimates")
            if analyst_data:
                available_sources.append("analyst_consensus")
            if price_context and price_context.get("change_percent") is not None:
                available_sources.append("price_momentum")
            if metrics and any(v for v in metrics.values() if v and isinstance(v, dict) and v):
                available_sources.append("yfinance_metrics")

            # Add data_source attribution to each section
            company_info_with_source = company_info or {}
            if company_info_with_source:
                company_info_with_source["data_source"] = "Alpha Vantage"

            news_sentiment_with_source = news_sentiment_summary or {}
            if news_sentiment_with_source:
                news_sentiment_with_source["data_source"] = "Alpha Vantage"

            earnings_estimates_with_source = earnings_estimates or {}
            if earnings_estimates_with_source:
                earnings_estimates_with_source["data_source"] = "Alpha Vantage"

            analyst_data_with_source = analyst_data or {}
            if analyst_data_with_source:
                analyst_data_with_source["data_source"] = "Finnhub"

            price_context_with_source = price_context or {}
            if price_context_with_source:
                price_context_with_source["data_source"] = "Yahoo Finance"

            metrics_with_source = metrics or {}
            if metrics_with_source:
                metrics_with_source["data_source"] = "Yahoo Finance"

            result = {
                "ticker": ticker,
                "company_info": company_info_with_source,
                "news_sentiment": news_sentiment_with_source,
                "earnings_estimates": earnings_estimates_with_source,
                "analyst_data": analyst_data_with_source,
                "price_context": price_context_with_source,
                "metrics": metrics_with_source,
                "data_availability": (
                    ", ".join(available_sources) if available_sources else "limited"
                ),
                "timestamp": datetime.now().isoformat(),
                "data_sources": "Alpha Vantage Premium (financial + earnings) + Finnhub (analysts) + Yahoo Finance (prices)",
            }

            # Cache enriched data (24 hour TTL)
            self.cache_manager.set(cache_key, result, ttl_hours=24)

            return result

        except Exception as e:
            logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            return {
                "ticker": ticker,
                "company_info": {},
                "news_sentiment": {},
                "earnings_estimates": {},
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
            # Get last 30 days of price data, respecting historical date if set
            end_date = datetime.now()
            if self.historical_date:
                end_date = datetime.combine(self.historical_date, datetime.max.time())
                logger.debug(f"Using historical end_date {end_date.date()} for price context")

            start_date = end_date - timedelta(days=30)

            prices = self.price_provider.get_stock_prices(
                ticker, start_date=start_date, end_date=end_date
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
    """Tool for fetching news articles with sentiment using Alpha Vantage primary."""

    def __init__(self, cache_manager: CacheManager = None):
        """Initialize news fetcher.

        Args:
            cache_manager: Optional cache manager for caching news
        """
        super().__init__(
            name="NewsFetcher",
            description=(
                "Fetch recent news articles with sentiment analysis using Alpha Vantage. "
                "Input: ticker symbol. "
                "Output: List of news articles with sentiment scores and topics."
            ),
        )
        self.cache_manager = cache_manager or CacheManager()

        # Use Alpha Vantage Premium for news sentiment
        self.provider_manager = ProviderManager(
            primary_provider="alpha_vantage",
            backup_providers=[],  # No backup for news - Alpha Vantage Premium only
        )
        self.historical_date = None  # Track historical date for backtesting

    def set_historical_date(self, historical_date):
        """Set historical date for backtesting.

        Args:
            historical_date: date object for historical analysis
        """
        self.historical_date = historical_date
        logger.debug(f"Historical date set to {historical_date} for NewsFetcherTool")

    def run(
        self,
        ticker: str,
        limit: int = None,
    ) -> dict[str, Any]:
        """Fetch news articles with sentiment for ticker.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles (if None, use config default)

        Returns:
            Dictionary with articles and sentiment summary
        """
        try:
            # Use config defaults if not specified
            if limit is None:
                limit = get_config().data.news.max_articles

            # Check cache first - use date-based key for consistent daily caching
            cache_key = f"news_sentiment:{ticker}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {ticker} news")
                return cached

            # Convert historical_date to datetime if needed
            as_of_date = None
            if self.historical_date:
                as_of_date = datetime.combine(self.historical_date, datetime.max.time())
                logger.info(f"Fetching news as of {self.historical_date} for {ticker}")

            # Fetch news using Alpha Vantage Premium
            logger.debug(f"Fetching news with sentiment for {ticker}")
            articles = self.provider_manager.get_news(ticker, limit, as_of_date=as_of_date)

            if not articles:
                return {
                    "ticker": ticker,
                    "articles": [],
                    "count": 0,
                    "sentiment_summary": None,
                }

            # Calculate sentiment summary
            positive = sum(1 for a in articles if a.sentiment == "positive")
            negative = sum(1 for a in articles if a.sentiment == "negative")
            neutral = sum(1 for a in articles if a.sentiment == "neutral")
            total = len(articles)

            sentiment_scores = [
                a.sentiment_score for a in articles if a.sentiment_score is not None
            ]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

            sentiment_summary = {
                "total": total,
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_pct": round(100 * positive / total, 1) if total > 0 else 0,
                "negative_pct": round(100 * negative / total, 1) if total > 0 else 0,
                "avg_sentiment_score": round(avg_sentiment, 3),
                "overall_sentiment": (
                    "positive"
                    if avg_sentiment > 0.1
                    else "negative"
                    if avg_sentiment < -0.1
                    else "neutral"
                ),
            }

            result = {
                "ticker": ticker,
                "articles": [a.model_dump() for a in articles],
                "count": len(articles),
                "sentiment_summary": sentiment_summary,
                "timestamp": datetime.now().isoformat(),
            }

            # Cache news for 4 hours
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
