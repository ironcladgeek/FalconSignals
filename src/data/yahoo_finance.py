"""Yahoo Finance data provider implementation."""

from datetime import datetime

import pandas as pd
import yfinance as yf

from src.data.models import InstrumentType, Market, StockPrice
from src.data.price_manager import PriceDataManager
from src.data.providers import DataProvider, DataProviderFactory
from src.utils.errors import RateLimitException
from src.utils.logging import get_logger
from src.utils.resilience import retry

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

    @retry(
        max_attempts=5,
        initial_delay=5.0,
        max_delay=120.0,
        exponential_base=2.5,
    )
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
            period: Period string like '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y',
                    '5y', '10y', 'ytd', 'max' or '100d' for 100 days.
                    If set, overrides start_date/end_date.

        Returns:
            List of StockPrice objects sorted by date

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
            RateLimitException: If rate limited by API
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

                    # Ensure we have a scalar value (handle Series case)
                    if isinstance(val, pd.Series):
                        val = val.iloc[0] if len(val) > 0 else None

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
            error_msg = str(e)
            # Detect rate limiting errors from yfinance
            if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                logger.warning(
                    f"Rate limited by Yahoo Finance for {ticker}, will retry with backoff"
                )
                raise RateLimitException(
                    f"Rate limited by Yahoo Finance: {error_msg}",
                    provider="yahoo_finance",
                ) from e
            logger.error(f"Error fetching prices for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch prices for {ticker}: {e}") from e

    @retry(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=60.0,
        exponential_base=2.5,
    )
    def get_latest_price(self, ticker: str) -> StockPrice:
        """Fetch latest stock price from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
            RateLimitException: If rate limited by API
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

            # Convert pandas Timestamp to naive datetime
            timestamp = hist.index[-1]
            if hasattr(timestamp, "to_pydatetime"):
                dt = timestamp.to_pydatetime()
                # Remove timezone if present
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
            else:
                dt = timestamp

            price = StockPrice(
                ticker=ticker.upper(),
                name=self._get_ticker_name(ticker),
                market=market,
                instrument_type=InstrumentType.STOCK,
                date=dt,
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
            error_msg = str(e)
            # Detect rate limiting errors from yfinance
            if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                logger.warning(
                    f"Rate limited by Yahoo Finance for {ticker}, will retry with backoff"
                )
                raise RateLimitException(
                    f"Rate limited by Yahoo Finance: {error_msg}",
                    provider="yahoo_finance",
                ) from e
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            raise RuntimeError(f"Failed to fetch latest price for {ticker}: {e}") from e

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

    def get_historical_company_info(self, ticker: str, as_of_date: datetime) -> dict | None:
        """Get historical company info from yfinance quarterly data.

        Uses yfinance quarterly financial statements to reconstruct company_info
        as it would have appeared at the specified historical date.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Historical date for analysis

        Returns:
            Dictionary with company info reconstructed from historical quarterly data,
            or None if data unavailable
        """
        try:
            logger.debug(f"Fetching historical company info for {ticker} as of {as_of_date.date()}")

            # Fetch ticker data
            tick = yf.Ticker(ticker)

            # Get current info for static fields (name, sector, industry, etc.)
            # These don't change historically
            info = tick.info
            if not info:
                logger.warning(f"No yfinance info available for {ticker}")
                return None

            # Get quarterly financials and balance sheet
            quarterly_financials = tick.quarterly_financials
            quarterly_balance_sheet = tick.quarterly_balance_sheet

            # Find the most recent quarter before or at as_of_date
            target_date = as_of_date.date()
            selected_quarter = None
            selected_quarter_date = None

            # Check quarterly_financials columns (these are dates)
            if not quarterly_financials.empty:
                for col in quarterly_financials.columns:
                    quarter_date = col.date()
                    if quarter_date <= target_date:
                        if selected_quarter_date is None or quarter_date > selected_quarter_date:
                            selected_quarter_date = quarter_date
                            selected_quarter = col

            if selected_quarter is None:
                logger.warning(f"No quarterly data available for {ticker} before {target_date}")
                # Fall back to current yfinance info
                return self.get_company_info_from_current_data(ticker, info)

            logger.info(
                f"Using quarterly data from {selected_quarter_date} for {ticker} "
                f"(analysis date: {target_date})"
            )

            # Extract metrics from the selected quarter
            company_info = {
                # Static fields (from current info)
                "ticker": ticker.upper(),
                "name": info.get("longName", ticker.upper()),
                "description": info.get("longBusinessSummary", ""),
                "sector": info.get("sector", "").upper(),
                "industry": info.get("industry", "").upper(),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", ""),
                # Dynamic fields will be populated from quarterly data below
            }

            # Extract financial metrics from quarterly statements
            # Balance sheet metrics
            total_equity = None  # Initialize to avoid unbound variable
            if (
                not quarterly_balance_sheet.empty
                and selected_quarter in quarterly_balance_sheet.columns
            ):
                bs = quarterly_balance_sheet[selected_quarter]

                # Total equity
                total_equity = bs.get("Total Equity Gross Minority Interest", None)
                if total_equity is None:
                    total_equity = bs.get("Stockholders Equity", None)
                if total_equity is None:
                    total_equity = bs.get("Common Stock Equity", None)

                # Shares outstanding
                shares_outstanding = bs.get("Ordinary Shares Number", None)
                if shares_outstanding is None:
                    shares_outstanding = bs.get("Share Issued", None)

                # Book value per share
                if total_equity and shares_outstanding:
                    book_value_per_share = float(total_equity) / float(shares_outstanding)
                    company_info["book_value"] = round(book_value_per_share, 2)
                    company_info["shares_outstanding"] = float(shares_outstanding)

            # Income statement metrics (TTM from last 4 quarters)
            # CRITICAL: Calculate TTM (Trailing Twelve Months) by summing last 4 quarters
            # This matches how Yahoo Finance calculates historical fundamentals
            if not quarterly_financials.empty and selected_quarter in quarterly_financials.columns:
                # Get the last 4 quarters ending on or before selected_quarter
                quarters_for_ttm = []
                for col in quarterly_financials.columns:
                    if col.date() <= selected_quarter.date():
                        quarters_for_ttm.append(col)
                        if len(quarters_for_ttm) == 4:
                            break

                if len(quarters_for_ttm) >= 4:
                    # Calculate TTM metrics by summing 4 quarters
                    ttm_revenue = 0
                    ttm_net_income = 0
                    ttm_gross_profit = 0
                    ttm_operating_income = 0
                    ttm_ebitda = 0

                    for qtr in quarters_for_ttm:
                        inc = quarterly_financials[qtr]
                        ttm_revenue += float(inc.get("Total Revenue", 0) or 0)

                        ni = inc.get("Net Income", None)
                        if ni is None:
                            ni = inc.get(
                                "Net Income From Continuing Operation Net Minority Interest",
                                None,
                            )
                        ttm_net_income += float(ni or 0)

                        ttm_gross_profit += float(inc.get("Gross Profit", 0) or 0)
                        ttm_operating_income += float(inc.get("Operating Income", 0) or 0)
                        ttm_ebitda += float(inc.get("EBITDA", 0) or 0)

                    # Store TTM values
                    company_info["revenue_ttm"] = ttm_revenue
                    company_info["gross_profit_ttm"] = ttm_gross_profit
                    company_info["ebitda"] = ttm_ebitda

                    # TTM EPS calculation
                    if "shares_outstanding" in company_info and company_info["shares_outstanding"]:
                        ttm_eps = ttm_net_income / company_info["shares_outstanding"]
                        company_info["eps"] = round(ttm_eps, 2)
                        company_info["diluted_eps_ttm"] = round(ttm_eps, 2)

                    # TTM Profit margins
                    if ttm_revenue > 0:
                        company_info["profit_margin"] = round(ttm_net_income / ttm_revenue, 3)
                        company_info["operating_margin"] = round(
                            ttm_operating_income / ttm_revenue, 3
                        )

                    # TTM ROE
                    if total_equity and total_equity > 0:
                        company_info["return_on_equity"] = round(
                            ttm_net_income / float(total_equity), 3
                        )

                    net_income = ttm_net_income  # For later use
                    total_revenue = ttm_revenue
                else:
                    logger.warning(
                        f"Not enough quarters for TTM calculation (need 4, have {len(quarters_for_ttm)})"
                    )
                    # Fall back to single quarter if less than 4 quarters available
                    inc = quarterly_financials[selected_quarter]
                    total_revenue = inc.get("Total Revenue", None)
                    if total_revenue:
                        company_info["revenue_ttm"] = float(total_revenue)

                    net_income = inc.get("Net Income", None)
                    if net_income is None:
                        net_income = inc.get(
                            "Net Income From Continuing Operation Net Minority Interest", None
                        )

                    if net_income and "shares_outstanding" in company_info:
                        eps = float(net_income) / company_info["shares_outstanding"]
                        company_info["eps"] = round(eps, 2)
                        company_info["diluted_eps_ttm"] = round(eps, 2)

            # Get price data for the selected quarter to calculate valuation ratios
            # CRITICAL: Use quarter-end price, not analysis date price
            # This matches how Yahoo Finance calculates historical P/E, P/B, etc.
            try:
                # Verify selected_quarter_date is not None (should be guaranteed by earlier check)
                assert selected_quarter_date is not None, "selected_quarter_date must be set"
                pm = PriceDataManager()
                # Use quarter-end date for price lookup, not analysis date
                quarter_end_date = selected_quarter_date
                price_at_date = pm.get_price_at_date(ticker, quarter_end_date)

                if price_at_date:
                    historical_price = price_at_date["close"]
                    logger.debug(
                        f"Found quarter-end price for {ticker} on {quarter_end_date}: ${historical_price}"
                    )

                    # Calculate valuation metrics using historical price
                    if "eps" in company_info and company_info["eps"]:
                        company_info["pe_ratio"] = round(historical_price / company_info["eps"], 2)
                        company_info["trailing_pe"] = company_info["pe_ratio"]

                    if "book_value" in company_info and company_info["book_value"]:
                        company_info["price_to_book"] = round(
                            historical_price / company_info["book_value"], 2
                        )

                    if (
                        "revenue_ttm" in company_info
                        and company_info["revenue_ttm"]
                        and "shares_outstanding" in company_info
                    ):
                        revenue_per_share = (
                            company_info["revenue_ttm"] / company_info["shares_outstanding"]
                        )
                        company_info["price_to_sales"] = round(
                            historical_price / revenue_per_share, 2
                        )
                        company_info["revenue_per_share_ttm"] = round(revenue_per_share, 2)

                    # Market cap at historical price
                    if "shares_outstanding" in company_info:
                        company_info["market_cap"] = (
                            historical_price * company_info["shares_outstanding"]
                        )
                else:
                    logger.warning(f"No quarter-end price found for {ticker} on {quarter_end_date}")
            except Exception as e:
                logger.warning(f"Could not fetch quarter-end price for {ticker}: {e}")

            # Add metadata
            company_info["data_source"] = f"Yahoo Finance (Quarterly) - Q{selected_quarter_date}"
            company_info["historical_quarter_date"] = str(selected_quarter_date)

            logger.debug(
                f"Built historical company info for {ticker} from quarter {selected_quarter_date}"
            )
            return company_info

        except Exception as e:
            logger.error(f"Error fetching historical company info for {ticker}: {e}")
            return None

    @staticmethod
    def get_company_info_from_current_data(ticker: str, info: dict | None = None) -> dict | None:
        """Build company_info dict from yfinance .info property (fallback).

        Args:
            ticker: Stock ticker symbol
            info: Optional yfinance Ticker.info dictionary (fetched if not provided)

        Returns:
            Dictionary with company info in Alpha Vantage format
        """
        try:
            if info is None:
                tick = yf.Ticker(ticker)
                info = tick.info

            if not info:
                return None

            return {
                "ticker": ticker.upper(),
                "name": info.get("longName", ticker.upper()),
                "description": info.get("longBusinessSummary", ""),
                "sector": info.get("sector", "").upper(),
                "industry": info.get("industry", "").upper(),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", ""),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "book_value": info.get("bookValue"),
                "eps": info.get("trailingEps"),
                "diluted_eps_ttm": info.get("trailingEps"),
                "revenue_per_share_ttm": info.get("revenuePerShare"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "return_on_assets": info.get("returnOnAssets"),
                "return_on_equity": info.get("returnOnEquity"),
                "revenue_ttm": info.get("totalRevenue"),
                "ebitda": info.get("ebitda"),
                "beta": info.get("beta"),
                "shares_outstanding": info.get("sharesOutstanding"),
                "data_source": "Yahoo Finance (Current)",
            }
        except Exception as e:
            logger.error(f"Error building company info from current data for {ticker}: {e}")
            return None


# Register the provider
DataProviderFactory.register("yahoo_finance", YahooFinanceProvider)
