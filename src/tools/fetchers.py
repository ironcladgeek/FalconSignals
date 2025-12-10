"""Data fetching tools for agents."""

from datetime import date, datetime, timedelta
from typing import Any, Optional

import pandas as pd

from src.cache.manager import CacheManager
from src.config import get_config
from src.data.news_aggregator import NewsSourceConfig, UnifiedNewsAggregator
from src.data.price_manager import PriceDataManager
from src.data.provider_manager import ProviderManager
from src.data.providers import DataProviderFactory
from src.sentiment.analyzer import ConfigurableSentimentAnalyzer
from src.tools.base import BaseTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PriceFetcherTool(BaseTool):
    """Tool for fetching stock price data with unified CSV storage."""

    def __init__(
        self,
        cache_manager: CacheManager = None,
        provider_name: str = None,
        fixture_path: str = None,
        use_unified_storage: bool = True,
        config=None,
    ):
        """Initialize price fetcher.

        Args:
            cache_manager: Optional cache manager for caching prices
            provider_name: Data provider to use (default: yahoo_finance, or 'fixture' for test mode)
            fixture_path: Path to fixture directory (required if provider_name is 'fixture')
            use_unified_storage: Use unified CSV storage (PriceDataManager)
            config: Configuration object with analysis settings (for historical_data_lookback_days)
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
        self.use_unified_storage = use_unified_storage
        self.config = config

        # Initialize unified price manager
        self._price_manager: Optional[PriceDataManager] = None

        # Create provider with fixture path if needed
        if self.provider_name == "fixture" and fixture_path:
            self.provider = DataProviderFactory.create(
                self.provider_name, fixture_path=fixture_path
            )
        else:
            self.provider = DataProviderFactory.create(self.provider_name)

    @property
    def price_manager(self) -> PriceDataManager:
        """Get or create price manager."""
        if self._price_manager is None:
            self._price_manager = PriceDataManager()
        return self._price_manager

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
        days_back: int = None,
        period: str = None,
    ) -> dict[str, Any]:
        """Fetch price data for ticker using unified CSV storage.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (if None, uses days_back or period)
            end_date: End date (defaults to today or historical_date if set)
            days_back: Days back from end_date if start_date is None (defaults to config value or 730)
            period: Period string for yfinance (e.g., '60d' for 60 trading days). Overrides days_back.

        Returns:
            Dictionary with prices and metadata
        """
        try:
            # Use config value for days_back if not provided
            if days_back is None and period is None:
                if (
                    self.config
                    and hasattr(self.config, "analysis")
                    and hasattr(self.config.analysis, "historical_data_lookback_days")
                ):
                    days_back = self.config.analysis.historical_data_lookback_days
                    logger.debug(f"Using config historical_data_lookback_days: {days_back}")
                else:
                    days_back = 730
                    logger.debug(f"No config available, using default days_back: {days_back}")

            # Set date range - use historical_date if set for backtesting
            if end_date is None:
                if self.historical_date:
                    end_date = datetime.combine(self.historical_date, datetime.max.time())
                    logger.debug(f"Using historical end_date: {end_date.date()} for {ticker}")
                else:
                    end_date = datetime.now()

            if start_date is None and period is None:
                start_date = end_date - timedelta(days=days_back)

            # When using period, we don't need start/end dates at all
            if period:
                # Period-based fetching - yfinance handles everything
                start_d = None
                end_d = None
                logger.debug(f"Period-based request: period={period}, ignoring date range")
            else:
                # Date-based fetching
                start_d = start_date.date() if isinstance(start_date, datetime) else start_date
                end_d = end_date.date() if isinstance(end_date, datetime) else end_date

            # Use unified CSV storage if enabled
            if self.use_unified_storage:
                return self._fetch_with_unified_storage(ticker, start_d, end_d, days_back, period)
            else:
                return self._fetch_with_legacy_cache(ticker, start_date, end_date)

        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            return {
                "ticker": ticker,
                "prices": [],
                "count": 0,
                "error": str(e),
            }

    def _fetch_with_unified_storage(
        self,
        ticker: str,
        start_date: date | None,
        end_date: date | None,
        days_back: int = None,
        period: str = None,
    ) -> dict[str, Any]:
        """Fetch prices using unified CSV storage.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (what we need), None if using period
            end_date: End date (what we need), None if using period
            days_back: Number of days to fetch (used for period-based fetching)
            period: Period string for yfinance (e.g., '60d' for 60 trading days). Overrides dates.

        Returns:
            Dictionary with prices and metadata
        """
        pm = self.price_manager

        # Check what data we already have
        existing_start, existing_end = pm.get_data_range(ticker)

        needs_fetch = False
        fetch_start = None
        fetch_end = None
        fetched_successfully = False

        # If period is provided, check if existing cached data is sufficient
        if period:
            if existing_start is None or existing_end is None:
                # No cached data - need to fetch
                needs_fetch = True
                logger.debug(f"No existing data for {ticker}, fetching with period={period}")
            else:
                # Have cached data - check if we need to fetch more based on period
                # Extract number of days from period (e.g., "90d" -> 90)
                try:
                    requested_days = int(period.rstrip("d"))
                    # Count existing trading days
                    df_existing = pm.get_prices(ticker)
                    existing_trading_days = len(df_existing)

                    if existing_trading_days >= requested_days:
                        # We have enough data
                        logger.debug(
                            f"Cached data sufficient for {ticker}: have {existing_trading_days} trading days, "
                            f"need {requested_days} (period={period})"
                        )
                    else:
                        # Need to fetch more data
                        needs_fetch = True
                        logger.debug(
                            f"Cached data insufficient for {ticker}: have {existing_trading_days} trading days, "
                            f"need {requested_days} (period={period}), refetching"
                        )
                except (ValueError, AttributeError) as e:
                    # Can't parse period, fetch fresh
                    needs_fetch = True
                    logger.warning(f"Could not parse period '{period}': {e}, fetching fresh")
        elif existing_start is None or existing_end is None:
            # No data at all - use period-based fetch (more reliable than exact dates)
            needs_fetch = True
            period = f"{days_back}d" if days_back else "730d"
            fetch_start = None  # Will use period instead
            fetch_end = None
            logger.debug(f"No existing price data for {ticker}, fetching with period={period}")
        else:
            # We have some data - check if it covers our needed range
            # Adjust end_date if it's today and we already have yesterday's data
            # (market may not have closed yet or data may not be available)
            today = date.today()
            if end_date >= today and existing_end >= today - timedelta(days=1):
                # We need today's data, but we have yesterday's - that's recent enough
                # Don't try to fetch today until we know data is available
                logger.debug(
                    f"Adjusting end_date from {end_date} to {existing_end} (market may not have closed)"
                )
                end_date = existing_end

            if existing_start <= start_date and existing_end >= end_date:
                # We have all the data we need - no fetch required
                logger.debug(
                    f"Using cached {ticker} prices: have {existing_start} to {existing_end}, need {start_date} to {end_date}"
                )
            elif existing_end < end_date:
                # Need to fetch forward to update to end_date
                needs_fetch = True
                fetch_start = existing_end + timedelta(days=1)
                fetch_end = end_date
                logger.debug(f"Updating {ticker} prices forward: {fetch_start} -> {fetch_end}")
            elif existing_start > start_date:
                # Need to fetch backward to get earlier data
                needs_fetch = True
                fetch_start = start_date
                fetch_end = existing_start - timedelta(days=1)
                logger.debug(f"Backfilling {ticker} prices: {fetch_start} -> {fetch_end}")

        if needs_fetch:
            if fetch_start is None and fetch_end is None:
                # Period-based fetch (initial fetch with no existing data)
                if period is None:
                    period = f"{days_back}d" if days_back else "730d"
                logger.info(f"Fetching {ticker} prices with period={period}")
                prices = self.provider.get_stock_prices(ticker, period=period)
            else:
                # Date-range fetch (updating existing data)
                logger.info(f"Fetching {ticker} prices: {fetch_start} to {fetch_end}")
                prices = self.provider.get_stock_prices(
                    ticker,
                    datetime.combine(fetch_start, datetime.min.time()),
                    datetime.combine(fetch_end, datetime.max.time()),
                )

            if prices:
                # Store in unified CSV
                price_dicts = [p.model_dump() for p in prices]
                pm.store_prices(ticker, price_dicts, append=True)
                logger.info(f"Stored {len(prices)} prices for {ticker} in unified CSV")
                fetched_successfully = True
            else:
                logger.warning(
                    f"No new prices fetched for {ticker} in range {fetch_start} to {fetch_end}"
                )

        # Read from unified storage (this will use cached data if we already have the full range)
        # If start_date is None (period-based request), read all available data
        # Also read all data if we used days_back (to get full trading days, not calendar filtered)
        if start_date is None or (period and not needs_fetch):
            df = pm.get_prices(ticker)
            logger.debug(
                f"Reading all available prices for {ticker} (period-based or full cache request)"
            )
        else:
            df = pm.get_prices(ticker, start_date=start_date, end_date=end_date)

        if df.empty:
            # If we just fetched successfully but got no data in our range, get nearest available data
            # (the requested dates might be non-trading days)
            if fetched_successfully:
                logger.warning(
                    f"Fetch completed for {ticker} but no data in exact range {start_date} to {end_date}. "
                    "Using nearest available data..."
                )
                # Try to get any available data for this ticker
                df = pm.get_prices(ticker)
                if not df.empty:
                    logger.info(
                        f"Found {len(df)} prices for {ticker} from {df['date'].min().date()} to {df['date'].max().date()}"
                    )
                else:
                    return {
                        "ticker": ticker,
                        "prices": [],
                        "count": 0,
                        "error": f"No price data found for {ticker} after successful fetch",
                    }
            else:
                return {
                    "ticker": ticker,
                    "prices": [],
                    "count": 0,
                    "error": f"No price data found for {ticker}",
                }

        # Convert DataFrame to list of dicts with legacy column names for compatibility
        prices_list = []
        for _, row in df.iterrows():
            price_dict = {
                "close_price": row["close"],
                "open_price": row["open"],
                "high_price": row["high"],
                "low_price": row["low"],
                "volume": row["volume"],
                "date": row["date"],
            }
            # Include optional fields if present
            if "adj_close" in row and pd.notna(row["adj_close"]):
                price_dict["adjusted_close"] = row["adj_close"]
            if "currency" in row and pd.notna(row["currency"]):
                price_dict["currency"] = row["currency"]

            prices_list.append(price_dict)

        # Get latest price
        latest = pm.get_latest_price(ticker)
        latest_price = latest["close"] if latest else None

        # Get actual date range from data
        if not df.empty:
            actual_start = df["date"].min().date()
            actual_end = df["date"].max().date()
        else:
            actual_start = start_date
            actual_end = end_date

        return {
            "ticker": ticker,
            "prices": prices_list,
            "count": len(prices_list),
            "start_date": actual_start.isoformat() if actual_start else None,
            "end_date": actual_end.isoformat() if actual_end else None,
            "latest_price": latest_price,
            "storage": "unified_csv",
        }

    def _fetch_with_legacy_cache(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Fetch prices using legacy JSON cache (backward compatibility).

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with prices and metadata
        """
        # Check cache first
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
            "storage": "legacy_json",
        }
        self.cache_manager.set(cache_key, result, ttl_hours=24)

        return result

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

    def __init__(self, cache_manager: CacheManager = None, db_path: str = None):
        """Initialize financial data fetcher.

        Args:
            cache_manager: Optional cache manager for caching data
            db_path: Optional path to database for storing analyst ratings
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
            db_path=db_path,
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
            # Convert historical_date to datetime if needed
            as_of_date = None
            if self.historical_date:
                as_of_date = datetime.combine(self.historical_date, datetime.max.time())
                logger.info(f"Fetching fundamental data as of {self.historical_date} for {ticker}")

            # Create cache key with date (historical or current)
            if self.historical_date:
                cache_key = f"fundamental_enriched:{ticker}:{self.historical_date}"
            else:
                current_date = datetime.now().strftime("%Y-%m-%d")
                cache_key = f"fundamental_enriched:{ticker}:{current_date}"

            # Check cache first
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {ticker} fundamental data")
                return cached

            logger.debug(f"Fetching enriched fundamental data for {ticker}")

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

            # Note: News sentiment is handled by SentimentAgent and NewsFetcherTool
            # No need to duplicate it in fundamental data

            # Fetch analyst recommendations (Finnhub only) + store in database
            analyst_data = None
            try:
                if self.finnhub_provider.is_available:
                    # Get recommendation trends dict for immediate use (with historical date)
                    analyst_data = self.finnhub_provider.get_recommendation_trends(
                        ticker, as_of_date=as_of_date
                    )

                    # Also fetch as AnalystRating object and store in database
                    if analyst_data and self.provider_manager.repository:
                        try:
                            analyst_rating_obj = self.finnhub_provider.get_analyst_ratings(
                                ticker, as_of_date=as_of_date
                            )
                            if analyst_rating_obj:
                                stored = self.provider_manager.repository.store_ratings(
                                    analyst_rating_obj, data_source="finnhub"
                                )
                                logger.debug(
                                    f"Stored analyst ratings for {ticker} in database: {stored}"
                                )
                        except Exception as store_error:
                            logger.warning(
                                f"Could not store analyst ratings in database: {store_error}"
                            )
            except Exception as e:
                logger.warning(f"Could not fetch analyst data for {ticker}: {e}")

            # Fetch price context for momentum
            price_context = self._get_price_context(ticker)

            # Extract metrics from Alpha Vantage company_info (primary) with yfinance fallback
            metrics = self._extract_metrics_from_company_info(company_info)
            if not self._has_valid_metrics(metrics):
                logger.debug(
                    f"Alpha Vantage metrics incomplete for {ticker}, using yfinance fallback"
                )
                yfinance_metrics = self._get_yfinance_metrics(ticker)
                metrics = self._merge_metrics(metrics, yfinance_metrics)

            # Determine data availability
            available_sources = []
            if company_info:
                available_sources.append("company_overview")
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
                "earnings_estimates": earnings_estimates_with_source,
                "analyst_data": analyst_data_with_source,
                "price_context": price_context_with_source,
                "metrics": metrics_with_source,
                "data_availability": (
                    ", ".join(available_sources) if available_sources else "limited"
                ),
                "timestamp": datetime.now().isoformat(),
                "data_sources": (
                    "Alpha Vantage Premium (financial + earnings) + Finnhub (analysts) + "
                    "Yahoo Finance (prices)."
                ),
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

    def _extract_metrics_from_company_info(self, company_info: dict | None) -> dict[str, Any]:
        """Extract fundamental metrics from Alpha Vantage company info (OVERVIEW endpoint).

        Args:
            company_info: Dictionary from Alpha Vantage get_company_info()

        Returns:
            Dictionary with valuation, profitability, financial health, and growth metrics
        """
        if not company_info:
            return {}

        # Extract valuation metrics from Alpha Vantage OVERVIEW
        valuation = {}
        if company_info.get("trailing_pe"):
            valuation["trailing_pe"] = company_info["trailing_pe"]
        if company_info.get("forward_pe"):
            valuation["forward_pe"] = company_info["forward_pe"]
        if company_info.get("price_to_book"):
            valuation["price_to_book"] = company_info["price_to_book"]
        if company_info.get("price_to_sales"):
            valuation["price_to_sales"] = company_info["price_to_sales"]
        if company_info.get("peg_ratio"):
            valuation["peg_ratio"] = company_info["peg_ratio"]
        if company_info.get("ev_to_revenue"):
            valuation["enterprise_to_revenue"] = company_info["ev_to_revenue"]
        if company_info.get("ev_to_ebitda"):
            valuation["enterprise_to_ebitda"] = company_info["ev_to_ebitda"]
        if company_info.get("book_value"):
            valuation["book_value"] = company_info["book_value"]

        # Extract profitability metrics
        profitability = {}
        if company_info.get("profit_margin"):
            profitability["profit_margin"] = company_info["profit_margin"]
        if company_info.get("operating_margin"):
            profitability["operating_margin"] = company_info["operating_margin"]
        if company_info.get("return_on_equity"):
            profitability["return_on_equity"] = company_info["return_on_equity"]
        if company_info.get("return_on_assets"):
            profitability["return_on_assets"] = company_info["return_on_assets"]
        if company_info.get("eps"):
            profitability["trailing_eps"] = company_info["eps"]
        if company_info.get("diluted_eps_ttm"):
            profitability["diluted_eps_ttm"] = company_info["diluted_eps_ttm"]
        if company_info.get("revenue_ttm"):
            profitability["revenue_ttm"] = company_info["revenue_ttm"]
        if company_info.get("gross_profit_ttm"):
            profitability["gross_profit_ttm"] = company_info["gross_profit_ttm"]
        if company_info.get("ebitda"):
            profitability["ebitda"] = company_info["ebitda"]

        # Note: Alpha Vantage OVERVIEW doesn't include financial health metrics like
        # debt_to_equity, current_ratio, free_cashflow - these come from yfinance
        financial_health = {}

        # Extract growth metrics
        growth = {}
        if company_info.get("quarterly_earnings_growth_yoy"):
            growth["earnings_growth"] = company_info["quarterly_earnings_growth_yoy"]
            growth["earnings_quarterly_growth"] = company_info["quarterly_earnings_growth_yoy"]
        if company_info.get("quarterly_revenue_growth_yoy"):
            growth["revenue_growth"] = company_info["quarterly_revenue_growth_yoy"]

        return {
            "valuation": valuation,
            "profitability": profitability,
            "financial_health": financial_health,
            "growth": growth,
            "data_source": "Alpha Vantage",
        }

    def _has_valid_metrics(self, metrics: dict) -> bool:
        """Check if metrics dictionary has enough valid data.

        Args:
            metrics: Metrics dictionary

        Returns:
            True if metrics have at least 3 valid valuation fields
        """
        if not metrics:
            return False
        valuation = metrics.get("valuation", {})
        # Consider valid if we have at least P/E, P/B, and one other metric
        key_metrics = ["trailing_pe", "price_to_book", "peg_ratio", "ev_to_ebitda"]
        valid_count = sum(1 for k in key_metrics if valuation.get(k) is not None)
        return valid_count >= 2

    def _merge_metrics(self, primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        """Merge two metrics dictionaries, preferring primary values.

        Args:
            primary: Primary metrics (Alpha Vantage)
            fallback: Fallback metrics (yfinance)

        Returns:
            Merged metrics dictionary
        """
        if not fallback:
            return primary
        if not primary:
            return fallback

        merged = {}
        for category in ["valuation", "profitability", "financial_health", "growth"]:
            primary_cat = primary.get(category, {})
            fallback_cat = fallback.get(category, {})

            # Start with fallback, then override with primary (non-None values)
            merged_cat = dict(fallback_cat)
            for key, value in primary_cat.items():
                if value is not None:
                    merged_cat[key] = value

            if merged_cat:
                merged[category] = merged_cat

        # Use Alpha Vantage as primary data source if it contributed
        if primary.get("valuation") or primary.get("profitability"):
            merged["data_source"] = "Alpha Vantage (primary) + Yahoo Finance (fallback)"
        else:
            merged["data_source"] = "Yahoo Finance"

        return merged


class NewsFetcherTool(BaseTool):
    """Tool for fetching news articles with local FinBERT sentiment scoring."""

    def __init__(
        self,
        cache_manager: CacheManager = None,
        use_local_sentiment: bool = True,
    ):
        """Initialize news fetcher.

        Args:
            cache_manager: Optional cache manager for caching news
            use_local_sentiment: Use local FinBERT for sentiment scoring (more accurate)
        """
        super().__init__(
            name="NewsFetcher",
            description=(
                "Fetch recent news articles with local FinBERT sentiment analysis. "
                "Input: ticker symbol. "
                "Output: List of news articles with accurate sentiment scores."
            ),
        )
        self.cache_manager = cache_manager or CacheManager()
        self.use_local_sentiment = use_local_sentiment
        self.historical_date = None  # Track historical date for backtesting

        # Get news configuration from config
        config = get_config()
        news_config = config.data.news if hasattr(config.data, "news") else None

        # Initialize UnifiedNewsAggregator for combining news from multiple sources
        if news_config and news_config.use_unified_aggregator:
            # Convert config sources to NewsSourceConfig objects
            sources = [
                NewsSourceConfig(
                    name=source.name,
                    priority=source.priority,
                    enabled=source.enabled,
                    max_articles=source.max_articles,
                )
                for source in news_config.sources
            ]

            self.news_aggregator = UnifiedNewsAggregator(
                sources=sources,
                target_article_count=news_config.target_article_count,
                max_age_days=news_config.max_age_days,
                cache_manager=None,  # Disable internal caching; NewsFetcherTool handles it
            )
            logger.debug(
                f"Initialized UnifiedNewsAggregator with {len(sources)} sources, "
                f"target={news_config.target_article_count} articles"
            )
        else:
            # Fallback to default configuration if config not available
            self.news_aggregator = UnifiedNewsAggregator(
                sources=[
                    NewsSourceConfig(name="alpha_vantage", priority=1, max_articles=50),
                    NewsSourceConfig(name="finnhub", priority=2, max_articles=50),
                ],
                target_article_count=50,
                max_age_days=7,
                cache_manager=None,  # Disable internal caching; NewsFetcherTool handles it
            )
            logger.debug("Initialized UnifiedNewsAggregator with default configuration")

        # Lazy-load sentiment analyzer
        self._sentiment_analyzer = None

    @property
    def sentiment_analyzer(self):
        """Get or create sentiment analyzer (lazy initialization)."""
        if self._sentiment_analyzer is None:
            try:
                config = get_config()
                sentiment_config = config.data.sentiment if config.data.sentiment else None
                self._sentiment_analyzer = ConfigurableSentimentAnalyzer(sentiment_config)
            except Exception as e:
                logger.warning(f"Could not initialize sentiment analyzer: {e}")
                self._sentiment_analyzer = None
        return self._sentiment_analyzer

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

            # Convert historical_date to datetime if needed
            as_of_date = None
            if self.historical_date:
                as_of_date = datetime.combine(self.historical_date, datetime.max.time())
                logger.info(f"Fetching news as of {self.historical_date} for {ticker}")

            # Try to find existing cache with matching date range
            # Check for news cache files matching this ticker and date
            if self.historical_date:
                # Look for cache files with date range that includes our historical date
                # The cache manager doesn't support pattern matching, so we'll fetch and check
                # the date range after retrieval
                pass

            # Check for existing cached news data
            # First try simple key for current requests, then look for any recent news cache
            simple_cache_key = f"news_sentiment:{ticker}"
            news_prefix = f"news:{ticker}"  # Matches any TICKER_news*.json files

            cached = self.cache_manager.get(simple_cache_key)
            if cached and not self.historical_date:
                logger.debug(f"Cache hit for {ticker} news (simple key)")
                return cached

            # Try to find any existing news cache (news-finbert, news-sentiment, etc.)
            cached = self.cache_manager.find_latest_by_prefix(news_prefix)
            if cached and not self.historical_date:
                logger.debug(f"Cache hit for {ticker} news (pattern match)")
                return cached

            # Fetch news from multiple sources using UnifiedNewsAggregator
            logger.debug(f"Fetching news for {ticker} from multiple sources")
            articles = self.news_aggregator.fetch_news(
                ticker,
                lookback_days=None,  # Will use max_age_days from config
                as_of_date=as_of_date,
            )

            if not articles:
                return {
                    "ticker": ticker,
                    "articles": [],
                    "count": 0,
                    "sentiment_summary": None,
                    "scoring_method": "none",
                }

            # Apply local FinBERT sentiment scoring (more accurate than API sentiment)
            scoring_method = "api_provider"
            if self.use_local_sentiment and self.sentiment_analyzer:
                try:
                    logger.info(f"Applying FinBERT sentiment to {len(articles)} articles")
                    sentiment_result = self.sentiment_analyzer.analyze_sentiment(
                        articles, method="local"
                    )
                    scoring_method = sentiment_result.get("method", "local_finbert")
                    # Articles are updated in-place by the analyzer
                    logger.info(f"Sentiment scoring complete using {scoring_method}")
                except Exception as e:
                    logger.warning(f"Local sentiment scoring failed, using API scores: {e}")
                    scoring_method = "api_provider_fallback"

            # Calculate date range from articles for cache key
            cache_key = simple_cache_key  # Default
            article_dates = []
            for article in articles:
                pub_date_str = article.published_date
                if isinstance(pub_date_str, str):
                    # Extract date portion (YYYY-MM-DD)
                    date_part = (
                        pub_date_str.split()[0] if " " in pub_date_str else pub_date_str[:10]
                    )
                    article_dates.append(date_part)
                elif isinstance(pub_date_str, datetime):
                    article_dates.append(pub_date_str.strftime("%Y-%m-%d"))

            if article_dates:
                min_date = min(article_dates)
                max_date = max(article_dates)
                cache_key = f"news_finbert:{ticker}:{min_date}:{max_date}"
                logger.debug(f"News date range for {ticker}: {min_date} to {max_date}")

            # Calculate sentiment summary from (now FinBERT-scored) articles
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
                "scoring_method": scoring_method,
            }

            result = {
                "ticker": ticker,
                "articles": [a.model_dump() for a in articles],
                "count": len(articles),
                "sentiment_summary": sentiment_summary,
                "scoring_method": scoring_method,
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
