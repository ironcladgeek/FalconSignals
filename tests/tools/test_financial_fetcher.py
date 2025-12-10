"""Tests for FinancialDataFetcherTool using Alpha Vantage Premium."""

from unittest.mock import MagicMock

import pytest

from src.tools.fetchers import FinancialDataFetcherTool


class TestFinancialDataFetcherTool:
    """Test FinancialDataFetcherTool class with Alpha Vantage Premium."""

    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = FinancialDataFetcherTool()

        assert tool.name == "FinancialDataFetcher"
        assert tool.description is not None
        # Updated to use Alpha Vantage Premium as primary provider
        assert (
            "alpha vantage" in tool.description.lower()
            or "fundamental data" in tool.description.lower()
        )

    def test_run_missing_ticker(self):
        """Test run without ticker - returns neutral data."""
        tool = FinancialDataFetcherTool()

        result = tool.run(None)

        # Tool returns neutral data gracefully when ticker is missing
        assert "price_context" in result
        assert "company_info" in result

    def test_run_provider_not_available(self):
        """Test run when provider is not available."""
        tool = FinancialDataFetcherTool()

        mock_provider = MagicMock()
        mock_provider.is_available = False

        result = tool.run("TEST_UNAVAIL")

        assert "company_info" in result

    def test_run_with_company_data(self):
        """Test successful fetch with company data."""
        tool = FinancialDataFetcherTool()

        mock_price = MagicMock()
        mock_price_obj = MagicMock()
        mock_price_obj.close_price = 100.0
        mock_price.get_stock_prices.return_value = [
            MagicMock(close_price=95.0),
            MagicMock(close_price=100.0),
        ]

        tool.price_provider = mock_price

        result = tool.run("TEST_TICKER")

        assert result["ticker"] == "TEST_TICKER"
        assert "company_info" in result
        assert "price_context" in result
        assert "error" not in result

    def test_run_with_partial_data(self):
        """Test run with partial data (price only)."""
        tool = FinancialDataFetcherTool()

        mock_price = MagicMock()
        mock_price.get_stock_prices.return_value = []

        tool.price_provider = mock_price

        result = tool.run("PARTIAL_DATA")

        assert result["ticker"] == "PARTIAL_DATA"
        assert "company_info" in result
        assert "error" not in result

    def test_run_with_error_handling(self):
        """Test error handling when API calls fail - returns partial data."""
        tool = FinancialDataFetcherTool()

        mock_price = MagicMock()
        mock_price.get_stock_prices.return_value = []

        tool.price_provider = mock_price

        result = tool.run("ERROR_TICKER")

        # Tool returns partial data gracefully even when API calls fail
        assert "company_info" in result
        assert "price_context" in result

    def test_price_context_calculation(self):
        """Test price context calculation from price data."""
        tool = FinancialDataFetcherTool()

        # Create mock price objects
        old_price = MagicMock()
        old_price.close_price = 95.0
        new_price = MagicMock()
        new_price.close_price = 105.0

        tool.price_provider = MagicMock()
        tool.price_provider.get_stock_prices.return_value = [old_price, new_price]

        price_context = tool._get_price_context("PRICE_TEST")

        assert price_context["change_percent"] == pytest.approx(0.1053, abs=0.001)
        assert price_context["trend"] == "bullish"
        assert price_context["latest_price"] == 105.0

    def test_price_context_empty_prices(self):
        """Test price context when no price data available."""
        tool = FinancialDataFetcherTool()

        tool.price_provider = MagicMock()
        tool.price_provider.get_stock_prices.return_value = []

        price_context = tool._get_price_context("NO_PRICES")

        assert price_context["change_percent"] == 0
        assert price_context["trend"] == "neutral"

    def test_analyst_data_fetching(self):
        """Test that analyst data is fetched from Finnhub."""
        from unittest.mock import patch

        from src.cache.manager import CacheManager

        # Create tool with a mock cache that always returns None (cache miss)
        tool = FinancialDataFetcherTool(cache_manager=CacheManager())

        # Mock cache.get to always return None (force fresh fetch)
        with patch.object(tool.cache_manager, "get", return_value=None):
            mock_finnhub = MagicMock()
            mock_finnhub.is_available = True
            mock_finnhub.get_recommendation_trends.return_value = {
                "strong_buy": 10,
                "buy": 5,
                "hold": 2,
                "sell": 1,
                "strong_sell": 0,
                "total_analysts": 18,
            }

            tool.finnhub_provider = mock_finnhub

            result = tool.run("ANALYST_TEST")

            # Verify analyst_data is in result structure
            assert "analyst_data" in result, (
                f"analyst_data not in result. Keys: {list(result.keys())}"
            )
            assert "earnings_estimates" in result, (
                f"earnings_estimates not in result. Keys: {list(result.keys())}"
            )
            assert "company_info" in result
            # Verify Finnhub was actually called
            assert mock_finnhub.get_recommendation_trends.called, "Finnhub provider was not called"

    def test_news_sentiment_not_in_fundamental(self):
        """Test that news sentiment is NOT in fundamental data (handled by SentimentAgent)."""
        tool = FinancialDataFetcherTool()

        mock_price = MagicMock()
        mock_price.get_stock_prices.return_value = [
            MagicMock(close_price=100.0),
            MagicMock(close_price=102.0),
        ]

        tool.price_provider = mock_price

        result = tool.run("NEWS_TEST")

        # Verify news_sentiment is NOT included (handled separately by SentimentAgent)
        # Fundamental data focuses on: company_info, analyst_data, price_context, metrics
        assert "price_context" in result
        assert "company_info" in result
        assert "analyst_data" in result

    def test_earnings_estimates_integration(self):
        """Test that earnings estimates are fetched from Alpha Vantage Premium."""
        tool = FinancialDataFetcherTool()

        result = tool.run("EARNINGS_TEST")

        # Verify earnings_estimates is in result structure
        assert "earnings_estimates" in result
        assert "company_info" in result
        assert "analyst_data" in result
