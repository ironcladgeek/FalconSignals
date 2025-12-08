"""Alpha Vantage data provider implementation."""

import os
import time
from datetime import datetime
from typing import Optional

import requests

from src.data.models import InstrumentType, Market, NewsArticle, StockPrice
from src.data.providers import DataProvider, DataProviderFactory
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Alpha Vantage API constants
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_TIMEOUT = 30


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage data provider implementation.

    Supports stock price data, news sentiment, and company overview using Alpha Vantage API.
    Free tier: 25 requests/day, 500 requests/day with free API key.
    Provides enriched news sentiment data with topic relevance and sentiment scores.
    Primary data source for news and sentiment analysis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = DEFAULT_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize Alpha Vantage provider.

        Args:
            api_key: Alpha Vantage API key. If None, uses ALPHA_VANTAGE_API_KEY env var
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor for retries
            timeout: Request timeout in seconds
        """
        super().__init__("alpha_vantage")
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.is_available = bool(self.api_key)

        if self.is_available:
            logger.debug("Alpha Vantage provider initialized")
        else:
            logger.warning("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY env var.")

    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[StockPrice]:
        """Fetch historical stock price data from Alpha Vantage.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of StockPrice objects sorted by date

        Raises:
            ValueError: If ticker is invalid or API key is missing
            RuntimeError: If API call fails after retries
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is not configured")

        try:
            logger.debug(f"Fetching prices for {ticker} from {start_date} to {end_date}")

            # Alpha Vantage only provides day-level data
            data = self._api_call(
                {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": ticker,
                    "outputsize": "full",
                }
            )

            if "Error Message" in data:
                raise ValueError(f"Invalid ticker: {ticker}")

            if "Time Series (Daily)" not in data:
                raise RuntimeError(f"Unexpected API response format for {ticker}")

            prices = []
            time_series = data["Time Series (Daily)"]

            for date_str, values in time_series.items():
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")

                    # Filter by date range
                    if not (start_date <= date <= end_date):
                        continue

                    price = StockPrice(
                        ticker=ticker.upper(),
                        name=ticker.upper(),
                        market=self._infer_market(ticker),
                        instrument_type=InstrumentType.STOCK,
                        date=date,
                        open_price=float(values["1. open"]),
                        high_price=float(values["2. high"]),
                        low_price=float(values["3. low"]),
                        close_price=float(values["4. close"]),
                        volume=int(values["5. volume"]),
                        currency="USD",
                    )
                    prices.append(price)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed data for {date_str}: {e}")
                    continue

            # Sort by date ascending
            prices.sort(key=lambda p: p.date)

            logger.debug(f"Retrieved {len(prices)} price records for {ticker}")
            return prices

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch prices for {ticker}: {e}")

    def get_latest_price(self, ticker: str) -> StockPrice:
        """Fetch latest stock price from Alpha Vantage.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            ValueError: If ticker is invalid or API key is missing
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is not configured")

        try:
            logger.debug(f"Fetching latest price for {ticker}")

            data = self._api_call(
                {
                    "function": "GLOBAL_QUOTE",
                    "symbol": ticker,
                }
            )

            if "Error Message" in data:
                raise ValueError(f"Invalid ticker: {ticker}")

            if "Global Quote" not in data or not data["Global Quote"]:
                raise RuntimeError(f"No data available for {ticker}")

            quote = data["Global Quote"]

            price = StockPrice(
                ticker=ticker.upper(),
                name=ticker.upper(),
                market=self._infer_market(ticker),
                instrument_type=InstrumentType.STOCK,
                date=datetime.now(),
                open_price=float(quote.get("02. open", 0)),
                high_price=float(quote.get("03. high", 0)),
                low_price=float(quote.get("04. low", 0)),
                close_price=float(quote.get("05. price", 0)),
                volume=int(quote.get("06. volume", 0)),
                currency="USD",
            )

            logger.debug(f"Latest price for {ticker}: {price.close_price}")
            return price

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch latest price for {ticker}: {e}")

    def _api_call(self, params: dict) -> dict:
        """Make API call with retry logic and exponential backoff.

        Args:
            params: Query parameters

        Returns:
            API response as dictionary

        Raises:
            RuntimeError: If all retries fail
        """
        params["apikey"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"API call (attempt {attempt + 1}/{self.max_retries})")

                response = requests.get(
                    ALPHA_VANTAGE_BASE_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()

                # Check for rate limit messages
                if "Note" in data and "call frequency" in data["Note"].lower():
                    raise RuntimeError("Alpha Vantage API rate limit exceeded")

                return data

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor**attempt
                    logger.debug(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError("API call failed after retries (timeout)")

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor**attempt
                    logger.debug(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"API call failed after retries: {e}")

    def get_news(
        self,
        ticker: str,
        limit: int = 50,
        as_of_date: datetime | None = None,
    ) -> list[NewsArticle]:
        """Fetch news articles with sentiment analysis from Alpha Vantage.

        Uses the NEWS_SENTIMENT endpoint which provides:
        - Article title, summary, URL, publication time
        - Overall sentiment score and label
        - Ticker-specific sentiment scores and relevance
        - Topics with relevance scores

        Supports historical news fetching for backtesting with strict date filtering
        to prevent look-ahead bias.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles to return (default: 50)
            as_of_date: Optional date for historical news (only fetch news before this date)

        Returns:
            List of NewsArticle objects with sentiment data, sorted by date descending

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is not configured")

        try:
            logger.debug(
                f"Fetching news sentiment for {ticker} (limit={limit}, as_of_date={as_of_date})"
            )

            # Build NEWS_SENTIMENT API params with optional historical date filtering
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "limit": limit * 2,  # Request more to account for filtering by date
                "sort": "LATEST",  # Get newest first
            }

            # Add time range for historical analysis (prevent look-ahead bias)
            # Alpha Vantage requires BOTH time_from and time_to for filtering to work
            if as_of_date:
                # Set time_to to the historical date (end of analysis date)
                # Format: YYYYMMDDTHHMM (example: 20250902T2359 for Sept 2, 2025 at 11:59 PM)
                time_to = as_of_date.strftime("%Y%m%dT2359")

                # Set time_from to 365 days before as_of_date to get sufficient history
                # This ensures we get news from the past year leading up to the analysis date
                from datetime import timedelta

                time_from_date = as_of_date - timedelta(days=365)
                time_from = time_from_date.strftime("%Y%m%dT0000")

                params["time_from"] = time_from
                params["time_to"] = time_to
                logger.debug(f"Filtering news from {time_from_date.date()} to {as_of_date.date()}")

            logger.debug(f"Alpha Vantage NEWS_SENTIMENT params: {params}")
            data = self._api_call(params)

            if "Error Message" in data:
                raise ValueError(f"Invalid ticker or API error: {ticker}")

            if "feed" not in data:
                logger.warning(f"No news data available for {ticker}")
                return []

            articles = []
            for item in data["feed"]:
                try:
                    # Parse publication time (format: YYYYMMDDTHHMMSS)
                    time_str = item.get("time_published", "")
                    if len(time_str) >= 8:
                        # Parse date part (YYYYMMDD)
                        published_date = datetime.strptime(time_str[:8], "%Y%m%d")
                        # Try to parse time part if available
                        if len(time_str) >= 15 and "T" in time_str:
                            try:
                                time_part = time_str.split("T")[1][:6]
                                hour = int(time_part[:2])
                                minute = int(time_part[2:4])
                                second = int(time_part[4:6])
                                published_date = published_date.replace(
                                    hour=hour, minute=minute, second=second
                                )
                            except (ValueError, IndexError):
                                pass  # Use date only
                    else:
                        published_date = datetime.now()

                    # CLIENT-SIDE FILTERING: For historical analysis, ensure no future articles
                    # This prevents look-ahead bias even if API parameter filtering is incomplete
                    if as_of_date and published_date.date() > as_of_date.date():
                        logger.debug(
                            f"Filtering out future article (pub: {published_date.date()}, "
                            f"analysis: {as_of_date.date()})"
                        )
                        continue

                    # Extract ticker-specific sentiment
                    ticker_sentiment_score = None
                    ticker_sentiment_label = None
                    ticker_relevance = 0.0

                    ticker_sentiments = item.get("ticker_sentiment", [])
                    for ts in ticker_sentiments:
                        if ts.get("ticker", "").upper() == ticker.upper():
                            ticker_sentiment_score = float(ts.get("ticker_sentiment_score", 0))
                            ticker_sentiment_label = ts.get("ticker_sentiment_label", "Neutral")
                            ticker_relevance = float(ts.get("relevance_score", 0))
                            break

                    # Use overall sentiment if ticker-specific not found
                    if ticker_sentiment_score is None:
                        ticker_sentiment_score = float(item.get("overall_sentiment_score", 0))
                        ticker_sentiment_label = item.get("overall_sentiment_label", "Neutral")

                    # Map sentiment label to our format
                    sentiment_map = {
                        "Bearish": "negative",
                        "Somewhat-Bearish": "negative",
                        "Neutral": "neutral",
                        "Somewhat-Bullish": "positive",
                        "Bullish": "positive",
                    }
                    sentiment = sentiment_map.get(ticker_sentiment_label, "neutral")

                    # Calculate importance based on relevance and sentiment strength
                    importance = min(100, int(ticker_relevance * 100))

                    article = NewsArticle(
                        ticker=ticker.upper(),
                        title=item.get("title", "")[:200],
                        summary=item.get("summary", "")[:500],
                        source=item.get("source", "Alpha Vantage"),
                        url=item.get("url", ""),
                        published_date=published_date,
                        sentiment=sentiment,
                        sentiment_score=ticker_sentiment_score,
                        importance=importance,
                    )
                    articles.append(article)

                    # Stop if we have enough articles
                    if len(articles) >= limit:
                        break

                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Skipping malformed news item: {e}")
                    continue

            # Sort by date descending (most recent first)
            articles.sort(key=lambda a: a.published_date, reverse=True)

            logger.debug(f"Retrieved {len(articles)} news articles with sentiment for {ticker}")
            return articles

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch news for {ticker}: {e}")

    def get_company_info(self, ticker: str) -> Optional[dict]:
        """Fetch company overview and fundamental data.

        Uses the OVERVIEW endpoint to get:
        - Company name, description, sector, industry
        - Market capitalization, PE ratio, dividend yield
        - 52-week high/low, beta, analyst target price

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with company information or None if not available

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is not configured")

        try:
            logger.debug(f"Fetching company overview for {ticker}")

            data = self._api_call({"function": "OVERVIEW", "symbol": ticker})

            if "Error Message" in data:
                raise ValueError(f"Invalid ticker: {ticker}")

            # Check if we got valid data
            if not data or "Symbol" not in data:
                logger.warning(f"No company data available for {ticker}")
                return None

            # Extract comprehensive fundamental data from OVERVIEW
            return {
                # Basic info
                "ticker": data.get("Symbol", ticker),
                "name": data.get("Name", ""),
                "description": data.get("Description", ""),
                "sector": data.get("Sector", ""),
                "industry": data.get("Industry", ""),
                "currency": data.get("Currency", "USD"),
                "exchange": data.get("Exchange", ""),
                # Valuation metrics
                "market_cap": self._safe_float(data.get("MarketCapitalization")),
                "pe_ratio": self._safe_float(data.get("PERatio")),
                "trailing_pe": self._safe_float(data.get("TrailingPE")),
                "forward_pe": self._safe_float(data.get("ForwardPE")),
                "peg_ratio": self._safe_float(data.get("PEGRatio")),
                "price_to_book": self._safe_float(data.get("PriceToBookRatio")),
                "price_to_sales": self._safe_float(data.get("PriceToSalesRatioTTM")),
                "ev_to_revenue": self._safe_float(data.get("EVToRevenue")),
                "ev_to_ebitda": self._safe_float(data.get("EVToEBITDA")),
                "book_value": self._safe_float(data.get("BookValue")),
                # Profitability metrics
                "eps": self._safe_float(data.get("EPS")),
                "diluted_eps_ttm": self._safe_float(data.get("DilutedEPSTTM")),
                "revenue_per_share_ttm": self._safe_float(data.get("RevenuePerShareTTM")),
                "profit_margin": self._safe_float(data.get("ProfitMargin")),
                "operating_margin": self._safe_float(data.get("OperatingMarginTTM")),
                "return_on_assets": self._safe_float(data.get("ReturnOnAssetsTTM")),
                "return_on_equity": self._safe_float(data.get("ReturnOnEquityTTM")),
                "revenue_ttm": self._safe_float(data.get("RevenueTTM")),
                "gross_profit_ttm": self._safe_float(data.get("GrossProfitTTM")),
                "ebitda": self._safe_float(data.get("EBITDA")),
                # Growth metrics
                "quarterly_earnings_growth_yoy": self._safe_float(
                    data.get("QuarterlyEarningsGrowthYOY")
                ),
                "quarterly_revenue_growth_yoy": self._safe_float(
                    data.get("QuarterlyRevenueGrowthYOY")
                ),
                # Dividend info
                "dividend_per_share": self._safe_float(data.get("DividendPerShare")),
                "dividend_yield": self._safe_float(data.get("DividendYield")),
                # Analyst info
                "analyst_target_price": self._safe_float(data.get("AnalystTargetPrice")),
                "analyst_rating_strong_buy": self._safe_int(data.get("AnalystRatingStrongBuy")),
                "analyst_rating_buy": self._safe_int(data.get("AnalystRatingBuy")),
                "analyst_rating_hold": self._safe_int(data.get("AnalystRatingHold")),
                "analyst_rating_sell": self._safe_int(data.get("AnalystRatingSell")),
                "analyst_rating_strong_sell": self._safe_int(data.get("AnalystRatingStrongSell")),
                # Risk/Volatility
                "beta": self._safe_float(data.get("Beta"), default=1.0),
                "52_week_high": self._safe_float(data.get("52WeekHigh")),
                "52_week_low": self._safe_float(data.get("52WeekLow")),
                "50_day_moving_average": self._safe_float(data.get("50DayMovingAverage")),
                "200_day_moving_average": self._safe_float(data.get("200DayMovingAverage")),
                # Shares info
                "shares_outstanding": self._safe_float(data.get("SharesOutstanding")),
                "shares_float": self._safe_float(data.get("SharesFloat")),
                "percent_insiders": self._safe_float(data.get("PercentInsiders")),
                "percent_institutions": self._safe_float(data.get("PercentInstitutions")),
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch company info for {ticker}: {e}")

    def get_earnings_estimates(
        self, ticker: str, as_of_date: Optional[datetime] = None
    ) -> Optional[dict]:
        """Fetch earnings estimates from Alpha Vantage.

        Uses the EARNINGS_ESTIMATES endpoint to get:
        - EPS estimates (average, high, low) for next quarter and year
        - Revenue estimates
        - Analyst count and estimate revisions

        For historical analysis (as_of_date in the past):
        Earnings estimates are forward-looking data without explicit historical snapshots.
        Returns None with warning to prevent look-ahead bias.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Optional historical date for snapshot. If None, fetches current estimates.
                       For dates in the past, returns None to prevent future data leakage.

        Returns:
            Dictionary with earnings estimates or None if not available (including historical dates)

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is not configured")

        # For historical analysis, we'll use Alpha Vantage's historical estimate data
        # The API provides snapshots: _7_days_ago, _30_days_ago, _60_days_ago, _90_days_ago
        # These fields allow us to determine what estimates existed on historical dates
        historical_mode = as_of_date and as_of_date.date() < datetime.now().date()
        if historical_mode:
            logger.debug(
                f"Earnings estimates requested for historical date {as_of_date.date()}. "
                f"Will use historical estimate snapshots from API response."
            )

        try:
            logger.debug(f"Fetching earnings estimates for {ticker}")

            data = self._api_call({"function": "EARNINGS_ESTIMATES", "symbol": ticker})

            if "Error Message" in data:
                raise ValueError(f"Invalid ticker: {ticker}")

            # Check if we got valid data
            if not data or "estimates" not in data or not data["estimates"]:
                logger.warning(f"No earnings estimates available for {ticker}")
                return None

            estimates = data["estimates"]

            # Get next quarter and next year estimates
            # For historical analysis, select estimates where estimate date > analysis date
            # For current analysis (as_of_date=None), select immediate next quarter and year
            as_of_date_only = (
                as_of_date.date() if as_of_date else None
            )  # Convert to date for comparison

            next_quarter = None
            next_year = None

            for estimate in estimates:
                estimate_date_str = estimate.get("date", "")
                horizon = estimate.get("horizon", "").lower()

                # Parse estimate date (format: YYYY-MM-DD)
                try:
                    estimate_date = datetime.strptime(estimate_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    continue

                # For current analysis: use standard "next" pattern
                if not as_of_date_only:
                    if "next" in horizon and "quarter" in horizon and not next_quarter:
                        next_quarter = estimate
                    elif "next" in horizon and "year" in horizon and not next_year:
                        next_year = estimate
                # For historical analysis: select estimates AFTER the analysis date
                else:
                    if (
                        "historical" in horizon
                        and "quarter" in horizon
                        and estimate_date > as_of_date_only
                        and not next_quarter
                    ):
                        next_quarter = estimate
                    elif (
                        "historical" in horizon
                        and "year" in horizon
                        and estimate_date > as_of_date_only
                        and not next_year
                    ):
                        next_year = estimate

            result = {
                "ticker": data.get("symbol", ticker),
                "next_quarter": (
                    self._parse_earnings_estimate(next_quarter) if next_quarter else None
                ),
                "next_year": (self._parse_earnings_estimate(next_year) if next_year else None),
            }

            logger.debug(f"Retrieved earnings estimates for {ticker}")
            return result

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching earnings estimates for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch earnings estimates for {ticker}: {e}")

    @staticmethod
    def _parse_earnings_estimate(estimate: dict) -> dict:
        """Parse earnings estimate data.

        Args:
            estimate: Raw estimate data from API

        Returns:
            Parsed estimate dictionary
        """
        return {
            "date": estimate.get("date"),
            "horizon": estimate.get("horizon"),
            "eps_estimate_avg": AlphaVantageProvider._safe_float(
                estimate.get("eps_estimate_average")
            ),
            "eps_estimate_high": AlphaVantageProvider._safe_float(
                estimate.get("eps_estimate_high")
            ),
            "eps_estimate_low": AlphaVantageProvider._safe_float(estimate.get("eps_estimate_low")),
            "eps_analyst_count": AlphaVantageProvider._safe_float(
                estimate.get("eps_estimate_analyst_count")
            ),
            "revenue_estimate_avg": AlphaVantageProvider._safe_float(
                estimate.get("revenue_estimate_average")
            ),
            "revenue_estimate_high": AlphaVantageProvider._safe_float(
                estimate.get("revenue_estimate_high")
            ),
            "revenue_estimate_low": AlphaVantageProvider._safe_float(
                estimate.get("revenue_estimate_low")
            ),
            "revenue_analyst_count": AlphaVantageProvider._safe_float(
                estimate.get("revenue_estimate_analyst_count")
            ),
        }

    @staticmethod
    def _safe_float(value: str | None, default: float | None = None) -> float | None:
        """Safely convert string to float, handling None and 'None' strings.

        Args:
            value: String value to convert
            default: Default value if conversion fails

        Returns:
            Float value or default
        """
        if value is None or value == "" or value == "None" or value == "-":
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_int(value: str | None, default: int | None = None) -> int | None:
        """Safely convert string to int, handling None and 'None' strings.

        Args:
            value: String value to convert
            default: Default value if conversion fails

        Returns:
            Int value or default
        """
        if value is None or value == "" or value == "None" or value == "-":
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

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
DataProviderFactory.register("alpha_vantage", AlphaVantageProvider)
DataProviderFactory.register("alpha_vantage", AlphaVantageProvider)
