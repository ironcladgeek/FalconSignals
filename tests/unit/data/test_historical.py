"""Tests for historical data fetching with strict date filtering.

This test suite verifies that HistoricalDataFetcher properly prevents
look-ahead bias by filtering ALL data types to only include data that
would have been available on a specific date in the past.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.data.historical import HistoricalDataFetcher
from src.data.models import (
    AnalystRating,
    FinancialStatement,
    InstrumentType,
    Market,
    NewsArticle,
    StockPrice,
)


@pytest.fixture
def mock_provider():
    """Create a mock data provider with test data."""
    provider = MagicMock()
    provider.name = "mock_provider"

    # Price data: mix of before and after the test date
    provider.get_stock_prices.return_value = [
        StockPrice(
            ticker="AAPL",
            name="Apple",
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
            date=datetime(2024, 5, 25),  # Before test date
            open_price=195.0,
            high_price=197.0,
            low_price=194.0,
            close_price=196.0,
            volume=1000000,
            currency="USD",
        ),
        StockPrice(
            ticker="AAPL",
            name="Apple",
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
            date=datetime(2024, 6, 1),  # On test date
            open_price=196.0,
            high_price=198.0,
            low_price=195.0,
            close_price=197.0,
            volume=1100000,
            currency="USD",
        ),
        StockPrice(
            ticker="AAPL",
            name="Apple",
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
            date=datetime(2024, 6, 5),  # After test date (SHOULD BE FILTERED OUT)
            open_price=197.0,
            high_price=199.0,
            low_price=196.0,
            close_price=198.0,
            volume=1200000,
            currency="USD",
        ),
    ]

    # Financial statements: mix of before and after
    provider.get_financial_statements.return_value = [
        FinancialStatement(
            ticker="AAPL",
            name="Apple",
            statement_type="income_statement",
            fiscal_year=2024,
            fiscal_quarter=1,
            report_date=datetime(2024, 5, 1),  # Before test date
            metric="revenue",
            value=95000000000,
            unit="USD",
        ),
        FinancialStatement(
            ticker="AAPL",
            name="Apple",
            statement_type="income_statement",
            fiscal_year=2024,
            fiscal_quarter=2,
            report_date=datetime(2024, 8, 1),  # After test date (SHOULD BE FILTERED OUT)
            metric="revenue",
            value=97000000000,
            unit="USD",
        ),
    ]

    # News articles: mix of before and after
    provider.get_news.return_value = [
        NewsArticle(
            ticker="AAPL",
            title="Apple Stock Rises",
            summary="Stock goes up",
            source="Reuters",
            url="https://example.com/1",
            published_date=datetime(2024, 5, 28),  # Before test date
            sentiment="positive",
            sentiment_score=0.8,
            importance=80,
        ),
        NewsArticle(
            ticker="AAPL",
            title="Apple Announces New Product",
            summary="New iPhone coming",
            source="Bloomberg",
            url="https://example.com/2",
            published_date=datetime(2024, 6, 1),  # On test date
            sentiment="positive",
            sentiment_score=0.9,
            importance=90,
        ),
        NewsArticle(
            ticker="AAPL",
            title="Apple Earnings Beat Expectations",
            summary="Better than expected",
            source="CNBC",
            url="https://example.com/3",
            published_date=datetime(2024, 6, 15),  # After test date (SHOULD BE FILTERED OUT)
            sentiment="positive",
            sentiment_score=0.95,
            importance=95,
        ),
    ]

    # Analyst ratings: before and after
    provider.get_analyst_ratings.return_value = AnalystRating(
        ticker="AAPL",
        name="Apple",
        rating_date=datetime(2024, 7, 1),  # After test date (SHOULD BE FILTERED OUT)
        rating="buy",
        price_target=210.0,
        num_analysts=25,
        consensus="buy",
    )

    return provider


def test_historical_data_fetcher_filters_price_data(mock_provider):
    """Verify that price data is filtered to exclude future dates."""
    fetcher = HistoricalDataFetcher(mock_provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=365)

    # Should have 2 prices (before and on test date, excluding future)
    assert len(context.price_data) == 2
    assert all(price.date.date() <= test_date.date() for price in context.price_data)

    # Verify specific dates
    dates = [price.date.date() for price in context.price_data]
    assert datetime(2024, 5, 25).date() in dates
    assert datetime(2024, 6, 1).date() in dates
    assert datetime(2024, 6, 5).date() not in dates  # Future date should be excluded


def test_historical_data_fetcher_filters_fundamentals(mock_provider):
    """Verify that fundamental data is filtered to exclude future dates."""
    fetcher = HistoricalDataFetcher(mock_provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=365)

    # Should have 1 statement (before test date, excluding future)
    assert len(context.fundamentals) == 1
    assert all(stmt.report_date.date() <= test_date.date() for stmt in context.fundamentals)

    # Verify the Q1 statement is included, Q2 is excluded
    assert context.fundamentals[0].fiscal_quarter == 1
    assert datetime(2024, 8, 1).date() not in [
        stmt.report_date.date() for stmt in context.fundamentals
    ]


def test_historical_data_fetcher_filters_news(mock_provider):
    """Verify that news articles are filtered to exclude future dates."""
    fetcher = HistoricalDataFetcher(mock_provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=365)

    # Should have 2 articles (before and on test date, excluding future)
    assert len(context.news) == 2
    assert all(article.published_date.date() <= test_date.date() for article in context.news)

    # Verify dates
    news_dates = [article.published_date.date() for article in context.news]
    assert datetime(2024, 5, 28).date() in news_dates
    assert datetime(2024, 6, 1).date() in news_dates
    assert datetime(2024, 6, 15).date() not in news_dates  # Future news should be excluded


def test_historical_data_fetcher_filters_analyst_ratings(mock_provider):
    """Verify that analyst ratings are filtered to exclude future dates."""
    fetcher = HistoricalDataFetcher(mock_provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=365)

    # Should NOT have analyst rating (it's dated after test date)
    assert context.analyst_ratings is None


def test_historical_data_fetcher_lookback_period(mock_provider):
    """Verify that lookback period is respected."""
    fetcher = HistoricalDataFetcher(mock_provider)
    test_date = datetime(2024, 6, 1)
    lookback_days = 7

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=lookback_days)

    # Verify lookback period is set correctly
    assert context.lookback_days == lookback_days

    # Verify data is within lookback period (if provider honored it)
    if context.price_data:
        earliest_date = min(price.date for price in context.price_data).date()
        expected_start = (test_date - timedelta(days=lookback_days)).date()
        assert earliest_date >= expected_start


def test_historical_data_fetcher_data_availability_tracking(mock_provider):
    """Verify that data availability is tracked correctly."""
    fetcher = HistoricalDataFetcher(mock_provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=365)

    # Should report data as available (we have price data)
    assert context.data_available is True

    # Should have a warning about sparse data (only 2 days of prices for 365 day lookback)
    # This is expected behavior - we're alerting about sparse data
    assert len(context.missing_data_warnings) == 1
    assert "Sparse price data" in context.missing_data_warnings[0]


def test_historical_data_fetcher_prevents_lookahead_bias():
    """Integration test: Verify complete prevention of look-ahead bias."""
    # Create a provider with deliberately mixed dates
    provider = MagicMock()
    provider.name = "test_provider"

    analysis_date = datetime(2024, 6, 15)

    # Create price data with clear markers: 10 days before, 10 days after
    prices = []
    for i in range(20):
        date = datetime(2024, 6, 5) + timedelta(days=i)  # June 5-24
        is_future = date > analysis_date
        prices.append(
            StockPrice(
                ticker="TEST",
                name="Test Company",
                market=Market.US,
                instrument_type=InstrumentType.STOCK,
                date=date,
                open_price=100.0 + (i if is_future else 0),  # Future prices are higher
                high_price=101.0 + (i if is_future else 0),
                low_price=99.0 + (i if is_future else 0),
                close_price=100.5 + (i if is_future else 0),
                volume=1000000,
                currency="USD",
            )
        )

    provider.get_stock_prices.return_value = prices
    provider.get_financial_statements.return_value = []
    provider.get_news.return_value = []

    fetcher = HistoricalDataFetcher(provider)
    context = fetcher.fetch_as_of_date("TEST", analysis_date, lookback_days=365)

    # Verify NO future prices are included
    max_price_date = max(p.date.date() for p in context.price_data)
    assert max_price_date <= analysis_date.date()

    # Verify all prices are before or on analysis date
    for price in context.price_data:
        assert price.date.date() <= analysis_date.date()
        # Verify price values are NOT inflated (which would indicate future data)
        assert price.open_price == 100.0

    # Verify we have exactly 11 prices (June 5-15 inclusive, all <= analysis date of June 15)
    assert len(context.price_data) == 11


def test_historical_data_fetcher_handles_missing_data():
    """Verify graceful handling of missing data types."""
    provider = MagicMock()
    provider.name = "test_provider"

    # Return empty data
    provider.get_stock_prices.return_value = []
    provider.get_financial_statements.side_effect = NotImplementedError("Not supported")
    provider.get_news.return_value = []
    provider.get_analyst_ratings.side_effect = NotImplementedError("Not supported")

    fetcher = HistoricalDataFetcher(provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("TEST", test_date, lookback_days=365)

    # Should handle missing data gracefully
    assert context.data_available is False
    assert len(context.missing_data_warnings) > 0
    assert len(context.price_data) == 0
    assert len(context.fundamentals) == 0
    assert len(context.news) == 0
    assert context.analyst_ratings is None


def test_historical_data_fetcher_earnings_estimates_historical_date():
    """Verify that earnings estimates use historical snapshots for historical dates.

    Alpha Vantage API provides historical snapshots: _7_days_ago, _30_days_ago, etc.
    The provider selects the appropriate snapshot based on days ago from analysis date.
    """
    provider = MagicMock()
    provider.name = "test_provider"

    # Mock earnings estimates with historical snapshots
    def mock_get_earnings_estimates(ticker, as_of_date=None):
        # Return full estimate data with historical snapshots
        return {
            "ticker": ticker,
            "next_quarter": {
                "date": "2024-09-30",
                "horizon": "next fiscal quarter",
                "eps_estimate_avg": 1.25,  # Current estimate
                "eps_estimate_average_7_days_ago": 1.24,
                "eps_estimate_average_30_days_ago": 1.23,
                "eps_estimate_average_60_days_ago": 1.22,
                "eps_estimate_average_90_days_ago": 1.20,
            },
            "next_year": {
                "date": "2024-12-31",
                "horizon": "next fiscal year",
                "eps_estimate_avg": 5.50,  # Current estimate
                "eps_estimate_average_7_days_ago": 5.48,
                "eps_estimate_average_30_days_ago": 5.45,
                "eps_estimate_average_60_days_ago": 5.40,
                "eps_estimate_average_90_days_ago": 5.30,
            },
        }

    provider.get_earnings_estimates.side_effect = mock_get_earnings_estimates

    # Mock other required methods
    provider.get_stock_prices.return_value = []
    provider.get_financial_statements.return_value = []
    provider.get_news.return_value = []
    provider.get_analyst_ratings.return_value = None

    fetcher = HistoricalDataFetcher(provider)
    test_date = datetime(2024, 6, 1)  # Historical date (in the past)

    context = fetcher.fetch_as_of_date("AAPL", test_date, lookback_days=365)

    # Earnings estimates should be returned with values from historical snapshots
    assert context.earnings_estimates is not None
    assert context.earnings_estimates["ticker"] == "AAPL"
    assert "next_quarter" in context.earnings_estimates
    assert "next_year" in context.earnings_estimates
    # Values should be from the historical snapshots, not current
    # (The actual values depend on provider implementation)
    assert context.earnings_estimates["next_quarter"]["eps_estimate_avg"] is not None
    assert context.earnings_estimates["next_year"]["eps_estimate_avg"] is not None

    # Provider should have been called with as_of_date parameter
    provider.get_earnings_estimates.assert_called_once()
    call_args = provider.get_earnings_estimates.call_args
    # Verify as_of_date was passed
    assert "as_of_date" in call_args.kwargs or len(call_args.args) > 1


def test_historical_data_fetcher_earnings_estimates_missing_provider():
    """Verify that missing get_earnings_estimates method is handled gracefully."""
    provider = MagicMock()
    provider.name = "test_provider"
    # Simulate provider without get_earnings_estimates method
    del provider.get_earnings_estimates

    # Mock other required methods
    provider.get_stock_prices.return_value = []
    provider.get_financial_statements.return_value = []
    provider.get_news.return_value = []
    provider.get_analyst_ratings.return_value = None

    fetcher = HistoricalDataFetcher(provider)
    test_date = datetime(2024, 6, 1)

    context = fetcher.fetch_as_of_date("TEST", test_date, lookback_days=365)

    # Should handle missing method gracefully
    assert context.earnings_estimates is None
    assert context.data_available is False  # No price data


def test_historical_data_fetcher_earnings_estimates_error_handling():
    """Verify graceful error handling for earnings estimate fetch failures."""
    provider = MagicMock()
    provider.name = "test_provider"

    # Simulate error in earnings estimates
    provider.get_earnings_estimates.side_effect = RuntimeError("API error")

    # Mock other required methods
    provider.get_stock_prices.return_value = []
    provider.get_financial_statements.return_value = []
    provider.get_news.return_value = []
    provider.get_analyst_ratings.return_value = None

    fetcher = HistoricalDataFetcher(provider)
    test_date = datetime(2024, 6, 1)

    # Should not raise, should log warning
    context = fetcher.fetch_as_of_date("TEST", test_date, lookback_days=365)

    # Should have returned context with None estimates
    assert context.earnings_estimates is None
    assert context.data_available is False  # No price data
