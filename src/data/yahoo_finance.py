"""Yahoo Finance data provider implementation."""

from datetime import datetime

import pandas as pd
import yfinance as yf

from src.data.models import InstrumentType, Market, StockPrice
from src.data.providers import DataProvider, DataProviderFactory
from src.utils.logging import get_logger

logger = get_logger(__name__)


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider implementation.

    Supports stock price data fetching using the yfinance library.
    Free tier, unlimited requests for most data.
    """

    def __init__(self):
        """Initialize Yahoo Finance provider."""
        super().__init__("yahoo_finance")
        self.is_available = True
        logger.debug("Yahoo Finance provider initialized")

    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime = None,
        end_date: datetime = None,
        period: str = None,
    ) -> list[StockPrice]:
        """Fetch historical stock price data from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data (ignored if period is set)
            end_date: End date for historical data (ignored if period is set)
            period: Period string like '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
                    or '100d' for 100 days. If set, overrides start_date/end_date.

        Returns:
            List of StockPrice objects sorted by date

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
        """
        try:
            if period:
                logger.debug(f"Fetching prices for {ticker} with period={period}")
                # Use period-based fetching (more reliable)
                stock = yf.Ticker(ticker)
                data = stock.history(period=period, auto_adjust=False)
            else:
                logger.debug(f"Fetching prices for {ticker} from {start_date} to {end_date}")
                # Fetch data using yfinance with date range
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=False,  # Keep original and adjusted close prices
                )

            if data.empty:
                raise ValueError(f"No data found for ticker: {ticker}")

            prices = []
            for index, row in data.iterrows():
                # Handle different column formats from yfinance
                # yf.Ticker().history() returns flat columns: Open, High, Low, Close, Volume, etc.
                # yf.download() can return MultiIndex columns: (PriceLevel, Ticker)
                def get_price_value(row, key):
                    """Extract scalar price value, handling both flat and MultiIndex columns."""
                    try:
                        # Try flat column first (from Ticker().history())
                        val = row[key]
                    except (KeyError, TypeError):
                        try:
                            # Try MultiIndex (from yf.download())
                            val = row[(key, ticker.upper())]
                        except (KeyError, TypeError):
                            return None
                    return float(val) if pd.notna(val) else None

                # Extract price values
                adjusted_close = get_price_value(row, "Adj Close")
                if adjusted_close is None:
                    adjusted_close = get_price_value(row, "Close")
                if adjusted_close is None:
                    logger.warning(f"No valid close price for {ticker} on {index}")
                    continue

                open_price = get_price_value(row, "Open")
                high_price = get_price_value(row, "High")
                low_price = get_price_value(row, "Low")
                close_price = get_price_value(row, "Close")
                volume = get_price_value(row, "Volume")

                if any(v is None for v in [open_price, high_price, low_price, close_price, volume]):
                    logger.warning(f"Missing price data for {ticker} on {index}")
                    continue

                market = self._infer_market(ticker)

                # Convert index to naive datetime (remove timezone info)
                if hasattr(index, "to_pydatetime"):
                    dt = index.to_pydatetime()
                    # Remove timezone if present
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)
                else:
                    dt = index

                price = StockPrice(
                    ticker=ticker.upper(),
                    name=self._get_ticker_name(ticker),
                    market=market,
                    instrument_type=InstrumentType.STOCK,
                    date=dt,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=int(volume),
                    adjusted_close=adjusted_close,
                    currency=self._get_currency_for_market(market),
                )
                prices.append(price)

            logger.debug(f"Retrieved {len(prices)} price records for {ticker}")
            return prices

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch prices for {ticker}: {e}")

    def get_latest_price(self, ticker: str) -> StockPrice:
        """Fetch latest stock price from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
        """
        try:
            logger.debug(f"Fetching latest price for {ticker}")

            # Fetch latest data
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")

            if hist.empty:
                raise ValueError(f"No data found for ticker: {ticker}")

            latest = hist.iloc[-1]
            market = self._infer_market(ticker)
            price = StockPrice(
                ticker=ticker.upper(),
                name=self._get_ticker_name(ticker),
                market=market,
                instrument_type=InstrumentType.STOCK,
                date=hist.index[-1].to_pydantic(),
                open_price=float(latest["Open"]),
                high_price=float(latest["High"]),
                low_price=float(latest["Low"]),
                close_price=float(latest["Close"]),
                volume=int(latest["Volume"]),
                adjusted_close=float(latest["Close"]),
                currency=self._get_currency_for_market(market),
            )

            logger.debug(f"Latest price for {ticker}: {price.close_price}")
            return price

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch latest price for {ticker}: {e}")

    @staticmethod
    def _get_ticker_name(ticker: str) -> str:
        """Get company name from ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company name or ticker if not found
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            return info.get("longName", ticker.upper())
        except Exception:
            return ticker.upper()

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

    @staticmethod
    def _get_currency_for_market(market: Market) -> str:
        """Get currency code for market.

        Args:
            market: Market classification

        Returns:
            Currency code (USD, EUR, etc.)
        """
        if market == Market.US:
            return "USD"
        elif market == Market.NORDIC or market == Market.EU:
            return "EUR"
        else:
            return "USD"  # Default fallback


# Register the provider
DataProviderFactory.register("yahoo_finance", YahooFinanceProvider)
