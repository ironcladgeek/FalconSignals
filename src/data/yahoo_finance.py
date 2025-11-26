"""Yahoo Finance data provider implementation."""

from datetime import datetime

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
        logger.info("Yahoo Finance provider initialized")

    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[StockPrice]:
        """Fetch historical stock price data from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of StockPrice objects sorted by date

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
        """
        try:
            logger.debug(f"Fetching prices for {ticker} from {start_date} to {end_date}")

            # Fetch data using yfinance
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
            )

            if data.empty:
                raise ValueError(f"No data found for ticker: {ticker}")

            prices = []
            for index, row in data.iterrows():
                price = StockPrice(
                    ticker=ticker.upper(),
                    name=self._get_ticker_name(ticker),
                    market=self._infer_market(ticker),
                    instrument_type=InstrumentType.STOCK,
                    date=index.to_pydantic(),
                    open_price=float(row["Open"]),
                    high_price=float(row["High"]),
                    low_price=float(row["Low"]),
                    close_price=float(row["Close"]),
                    volume=int(row["Volume"]),
                    adjusted_close=float(row["Adj Close"]),
                    currency="USD",
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
            price = StockPrice(
                ticker=ticker.upper(),
                name=self._get_ticker_name(ticker),
                market=self._infer_market(ticker),
                instrument_type=InstrumentType.STOCK,
                date=hist.index[-1].to_pydantic(),
                open_price=float(latest["Open"]),
                high_price=float(latest["High"]),
                low_price=float(latest["Low"]),
                close_price=float(latest["Close"]),
                volume=int(latest["Volume"]),
                adjusted_close=float(latest["Close"]),
                currency="USD",
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


# Register the provider
DataProviderFactory.register("yahoo_finance", YahooFinanceProvider)
