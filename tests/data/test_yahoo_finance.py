"""Tests for Yahoo Finance data provider."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data.models import StockPrice
from src.data.yahoo_finance import YahooFinanceProvider


class TestYahooFinanceProvider:
    """Test suite for YahooFinanceProvider."""

    @pytest.fixture
    def provider(self):
        """Create a YahooFinanceProvider instance."""
        return YahooFinanceProvider()

    @pytest.fixture
    def mock_ticker_data(self):
        """Create mock yfinance Ticker data."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "longName": "Apple Inc.",
            "longBusinessSummary": "Apple designs and manufactures consumer electronics.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "currency": "USD",
            "exchange": "NASDAQ",
            "marketCap": 3000000000000,
            "trailingPE": 30.5,
            "forwardPE": 28.0,
            "pegRatio": 2.5,
            "priceToBook": 45.0,
            "priceToSalesTrailing12Months": 7.5,
            "bookValue": 4.0,
            "trailingEps": 6.0,
            "revenuePerShare": 24.0,
            "profitMargins": 0.25,
            "operatingMargins": 0.30,
            "returnOnAssets": 0.20,
            "returnOnEquity": 0.50,
            "totalRevenue": 400000000000,
            "ebitda": 120000000000,
            "beta": 1.2,
            "sharesOutstanding": 16000000000,
        }
        return mock_ticker

    @pytest.fixture
    def mock_quarterly_financials(self):
        """Create mock quarterly financials DataFrame."""
        dates = [
            pd.Timestamp("2025-06-30"),
            pd.Timestamp("2025-03-31"),
            pd.Timestamp("2024-12-31"),
            pd.Timestamp("2024-09-30"),
        ]
        data = {
            dates[0]: {
                "Total Revenue": 95000000000,
                "Net Income": 25000000000,
                "Gross Profit": 45000000000,
                "Operating Income": 30000000000,
                "EBITDA": 35000000000,
            },
            dates[1]: {
                "Total Revenue": 90000000000,
                "Net Income": 23000000000,
                "Gross Profit": 42000000000,
                "Operating Income": 28000000000,
                "EBITDA": 32000000000,
            },
            dates[2]: {
                "Total Revenue": 120000000000,
                "Net Income": 33000000000,
                "Gross Profit": 55000000000,
                "Operating Income": 38000000000,
                "EBITDA": 42000000000,
            },
            dates[3]: {
                "Total Revenue": 85000000000,
                "Net Income": 21000000000,
                "Gross Profit": 40000000000,
                "Operating Income": 26000000000,
                "EBITDA": 30000000000,
            },
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_quarterly_balance_sheet(self):
        """Create mock quarterly balance sheet DataFrame."""
        dates = [
            pd.Timestamp("2025-06-30"),
            pd.Timestamp("2025-03-31"),
            pd.Timestamp("2024-12-31"),
            pd.Timestamp("2024-09-30"),
        ]
        data = {
            dates[0]: {
                "Total Equity Gross Minority Interest": 70000000000,
                "Ordinary Shares Number": 16000000000,
            },
            dates[1]: {
                "Total Equity Gross Minority Interest": 68000000000,
                "Ordinary Shares Number": 16000000000,
            },
            dates[2]: {
                "Total Equity Gross Minority Interest": 65000000000,
                "Ordinary Shares Number": 16000000000,
            },
            dates[3]: {
                "Total Equity Gross Minority Interest": 63000000000,
                "Ordinary Shares Number": 16000000000,
            },
        }
        return pd.DataFrame(data)

    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.name == "yahoo_finance"
        assert provider.is_available is True

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_stock_prices_success(self, mock_ticker_class, provider):
        """Test successful stock price fetching with period."""
        # Mock yfinance data
        mock_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0],
                "High": [152.0, 153.0],
                "Low": [149.0, 150.0],
                "Close": [151.0, 152.0],
                "Volume": [1000000, 1100000],
                "Adj Close": [151.0, 152.0],
            },
            index=pd.DatetimeIndex(["2025-01-01", "2025-01-02"]),
        )
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_data
        mock_ticker.info = {"longName": "Apple Inc.", "currency": "USD"}
        mock_ticker_class.return_value = mock_ticker

        prices = provider.get_stock_prices("AAPL", period="5d")

        assert len(prices) == 2
        assert isinstance(prices[0], StockPrice)
        assert prices[0].ticker == "AAPL"
        assert prices[0].close_price == 151.0
        assert prices[0].volume == 1000000

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_stock_prices_empty_data(self, mock_ticker_class, provider):
        """Test handling of empty stock price data."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(ValueError, match="No data found for ticker"):
            provider.get_stock_prices("INVALID", period="5d")

    @patch("src.data.yahoo_finance.yf.download")
    def test_get_stock_prices_with_date_range(self, mock_download, provider):
        """Test stock price fetching with start and end dates."""
        # Mock yfinance data
        mock_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0],
                "High": [152.0, 153.0],
                "Low": [149.0, 150.0],
                "Close": [151.0, 152.0],
                "Volume": [1000000, 1100000],
                "Adj Close": [151.0, 152.0],
            },
            index=pd.DatetimeIndex(["2025-01-01", "2025-01-02"]),
        )
        mock_download.return_value = mock_data

        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 3)
        prices = provider.get_stock_prices("AAPL", start_date=start_date, end_date=end_date)

        assert len(prices) == 2
        assert isinstance(prices[0], StockPrice)
        mock_download.assert_called_once()

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_latest_price_success(self, mock_ticker_class, provider):
        """Test successful latest price fetching."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [152.0],
                "Low": [149.0],
                "Close": [151.0],
                "Volume": [1000000],
                "Adj Close": [151.0],
            },
            index=pd.DatetimeIndex(["2025-01-01"]),
        )
        mock_ticker.info = {"longName": "Apple Inc.", "currency": "USD"}
        mock_ticker_class.return_value = mock_ticker

        price = provider.get_latest_price("AAPL")

        assert isinstance(price, StockPrice)
        assert price.ticker == "AAPL"
        assert price.close_price == 151.0

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_latest_price_no_data(self, mock_ticker_class, provider):
        """Test handling of no latest price data."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(ValueError, match="No data found for ticker"):
            provider.get_latest_price("INVALID")

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_success(
        self,
        mock_ticker_class,
        provider,
        mock_ticker_data,
        mock_quarterly_financials,
        mock_quarterly_balance_sheet,
    ):
        """Test successful historical company info fetching."""
        # Setup mocks
        mock_ticker = mock_ticker_data
        mock_ticker.quarterly_financials = mock_quarterly_financials
        mock_ticker.quarterly_balance_sheet = mock_quarterly_balance_sheet

        # Mock historical price data
        mock_hist_prices = pd.DataFrame(
            {
                "Close": [180.0],
            },
            index=[pd.Timestamp("2025-06-30")],
        )
        mock_ticker.history = MagicMock(return_value=mock_hist_prices)

        mock_ticker_class.return_value = mock_ticker

        # Test
        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        # Assertions
        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["sector"] == "TECHNOLOGY"
        assert result["industry"] == "CONSUMER ELECTRONICS"
        assert "revenue_ttm" in result
        assert "eps" in result
        assert "pe_ratio" in result
        assert "market_cap" in result
        assert result["data_source"].startswith("Yahoo Finance (Quarterly)")
        assert "historical_quarter_date" in result

        # Verify TTM calculations (sum of 4 quarters)
        expected_ttm_revenue = 95000000000 + 90000000000 + 120000000000 + 85000000000
        assert result["revenue_ttm"] == expected_ttm_revenue

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_no_yfinance_data(self, mock_ticker_class, provider):
        """Test handling of missing yfinance info."""
        mock_ticker = MagicMock()
        mock_ticker.info = None
        mock_ticker_class.return_value = mock_ticker

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("INVALID", as_of_date)

        assert result is None

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_no_quarterly_data(
        self, mock_ticker_class, provider, mock_ticker_data
    ):
        """Test fallback when no quarterly data available."""
        mock_ticker = mock_ticker_data
        mock_ticker.quarterly_financials = pd.DataFrame()  # Empty DataFrame
        mock_ticker.quarterly_balance_sheet = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        # Should fall back to current data
        assert result is not None
        assert result["data_source"] == "Yahoo Finance (Current)"

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_insufficient_quarters(
        self,
        mock_ticker_class,
        provider,
        mock_ticker_data,
    ):
        """Test handling of insufficient quarters for TTM calculation."""
        # Create quarterly data with only 2 quarters
        dates = [pd.Timestamp("2025-06-30"), pd.Timestamp("2025-03-31")]
        quarterly_financials = pd.DataFrame(
            {
                dates[0]: {
                    "Total Revenue": 95000000000,
                    "Net Income": 25000000000,
                },
                dates[1]: {
                    "Total Revenue": 90000000000,
                    "Net Income": 23000000000,
                },
            }
        )
        quarterly_balance_sheet = pd.DataFrame(
            {
                dates[0]: {
                    "Total Equity Gross Minority Interest": 70000000000,
                    "Ordinary Shares Number": 16000000000,
                },
            }
        )

        mock_ticker = mock_ticker_data
        mock_ticker.quarterly_financials = quarterly_financials
        mock_ticker.quarterly_balance_sheet = quarterly_balance_sheet

        # Mock historical price data
        mock_hist_prices = pd.DataFrame(
            {
                "Close": [180.0],
            },
            index=[pd.Timestamp("2025-06-30")],
        )
        mock_ticker.history = MagicMock(return_value=mock_hist_prices)

        mock_ticker_class.return_value = mock_ticker

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        # Should fall back to single quarter calculation
        assert result is not None
        assert result["revenue_ttm"] == 95000000000  # Single quarter

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_no_price_data(
        self,
        mock_ticker_class,
        provider,
        mock_ticker_data,
        mock_quarterly_financials,
        mock_quarterly_balance_sheet,
    ):
        """Test handling when historical price data is unavailable."""
        mock_ticker = mock_ticker_data
        mock_ticker.quarterly_financials = mock_quarterly_financials
        mock_ticker.quarterly_balance_sheet = mock_quarterly_balance_sheet

        # Mock empty historical price data (no price available)
        mock_hist_prices = pd.DataFrame()  # Empty DataFrame
        mock_ticker.history = MagicMock(return_value=mock_hist_prices)

        mock_ticker_class.return_value = mock_ticker

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        # Should still return data but without valuation ratios
        assert result is not None
        assert "pe_ratio" not in result
        assert "market_cap" not in result

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_exception(self, mock_ticker_class, provider):
        """Test exception handling in get_historical_company_info."""
        mock_ticker_class.side_effect = Exception("Network error")

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        assert result is None

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_company_info_from_current_data_success(self, mock_ticker_class, mock_ticker_data):
        """Test successful company info from current data."""
        mock_ticker_class.return_value = mock_ticker_data

        result = YahooFinanceProvider.get_company_info_from_current_data("AAPL")

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["market_cap"] == 3000000000000
        assert result["pe_ratio"] == 30.5
        assert result["data_source"] == "Yahoo Finance (Current)"

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_company_info_from_current_data_with_provided_info(
        self, mock_ticker_class, mock_ticker_data
    ):
        """Test company info with pre-provided info dict."""
        result = YahooFinanceProvider.get_company_info_from_current_data(
            "AAPL", info=mock_ticker_data.info
        )

        assert result is not None
        assert result["ticker"] == "AAPL"
        mock_ticker_class.assert_not_called()  # Should not fetch if info provided

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_company_info_from_current_data_empty_info(self, mock_ticker_class):
        """Test handling of empty info dict."""
        mock_ticker = MagicMock()
        mock_ticker.info = None
        mock_ticker_class.return_value = mock_ticker

        result = YahooFinanceProvider.get_company_info_from_current_data("AAPL")

        assert result is None

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_company_info_from_current_data_exception(self, mock_ticker_class):
        """Test exception handling in get_company_info_from_current_data."""
        mock_ticker_class.side_effect = Exception("Network error")

        result = YahooFinanceProvider.get_company_info_from_current_data("AAPL")

        assert result is None

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_alternative_equity_fields(
        self,
        mock_ticker_class,
        provider,
        mock_ticker_data,
        mock_quarterly_financials,
    ):
        """Test fallback equity field names in balance sheet."""
        # Create balance sheet with alternative field names
        dates = [pd.Timestamp("2025-06-30")]
        quarterly_balance_sheet = pd.DataFrame(
            {
                dates[0]: {
                    "Stockholders Equity": 70000000000,  # Alternative field
                    "Ordinary Shares Number": 16000000000,
                },
            }
        )

        mock_ticker = mock_ticker_data
        mock_ticker.quarterly_financials = mock_quarterly_financials
        mock_ticker.quarterly_balance_sheet = quarterly_balance_sheet

        # Mock historical price data
        mock_hist_prices = pd.DataFrame(
            {
                "Close": [180.0],
            },
            index=[pd.Timestamp("2025-06-30")],
        )
        mock_ticker.history = MagicMock(return_value=mock_hist_prices)

        mock_ticker_class.return_value = mock_ticker

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        assert result is not None
        assert "return_on_equity" in result

    @patch("src.data.yahoo_finance.yf.Ticker")
    def test_get_historical_company_info_alternative_net_income_field(
        self,
        mock_ticker_class,
        provider,
        mock_ticker_data,
        mock_quarterly_balance_sheet,
    ):
        """Test alternative net income field name."""
        # Create quarterly financials with alternative field name
        dates = [
            pd.Timestamp("2025-06-30"),
            pd.Timestamp("2025-03-31"),
            pd.Timestamp("2024-12-31"),
            pd.Timestamp("2024-09-30"),
        ]
        quarterly_financials = pd.DataFrame(
            {
                dates[0]: {
                    "Total Revenue": 95000000000,
                    "Net Income From Continuing Operation Net Minority Interest": 25000000000,
                },
                dates[1]: {
                    "Total Revenue": 90000000000,
                    "Net Income From Continuing Operation Net Minority Interest": 23000000000,
                },
                dates[2]: {
                    "Total Revenue": 120000000000,
                    "Net Income From Continuing Operation Net Minority Interest": 33000000000,
                },
                dates[3]: {
                    "Total Revenue": 85000000000,
                    "Net Income From Continuing Operation Net Minority Interest": 21000000000,
                },
            }
        )

        mock_ticker = mock_ticker_data
        mock_ticker.quarterly_financials = quarterly_financials
        mock_ticker.quarterly_balance_sheet = mock_quarterly_balance_sheet

        # Mock historical price data
        mock_hist_prices = pd.DataFrame(
            {
                "Close": [180.0],
            },
            index=[pd.Timestamp("2025-06-30")],
        )
        mock_ticker.history = MagicMock(return_value=mock_hist_prices)

        mock_ticker_class.return_value = mock_ticker

        as_of_date = datetime(2025, 9, 4)
        result = provider.get_historical_company_info("AAPL", as_of_date)

        assert result is not None
        assert "eps" in result
        assert result["eps"] > 0
