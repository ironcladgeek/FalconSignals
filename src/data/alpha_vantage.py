"""Alpha Vantage data provider implementation."""

import os
import time
from datetime import datetime
from typing import Optional

import requests

from src.data.models import InstrumentType, Market, StockPrice
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

    Supports stock price data fetching using Alpha Vantage API.
    Free tier: 25 requests/day with 5-minute delay between requests.
    Backup data source.
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
