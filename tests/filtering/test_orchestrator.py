"""Unit tests for the filtering orchestrator module."""

from unittest.mock import MagicMock, patch

import pytest

from src.filtering.orchestrator import FilterOrchestrator


class MockStrategy:
    """Mock filter strategy for testing."""

    name = "mock_strategy"

    def filter(self, ticker: str, prices: list) -> tuple[bool, list[str]]:
        """Mock filter that passes tickers starting with 'A'."""
        if ticker.startswith("A"):
            return True, ["Passed mock filter"]
        return False, ["Failed mock filter: doesn't start with A"]


class TestFilterOrchestrator:
    """Test suite for FilterOrchestrator class."""

    @pytest.fixture
    def mock_price_fetcher(self):
        """Create mock price fetcher."""
        fetcher = MagicMock()
        # Default to returning valid price data
        fetcher.run.return_value = {
            "prices": [
                {"close": 100},
                {"close": 101},
                {"close": 102},
                {"close": 103},
                {"close": 104},
                {"close": 105},
            ],
            "latest_price": 105,
        }
        return fetcher

    @pytest.fixture
    def mock_strategy(self):
        """Create mock strategy."""
        return MockStrategy()

    @pytest.fixture
    def orchestrator(self, mock_strategy, mock_price_fetcher):
        """Create orchestrator with mocks."""
        return FilterOrchestrator(
            strategy=mock_strategy,
            price_fetcher=mock_price_fetcher,
        )

    def test_initialization_with_strategy_instance(self, mock_strategy, mock_price_fetcher):
        """Test initialization with strategy instance."""
        orch = FilterOrchestrator(
            strategy=mock_strategy,
            price_fetcher=mock_price_fetcher,
        )

        assert orch.strategy == mock_strategy
        assert orch.price_fetcher == mock_price_fetcher

    @patch("src.filtering.orchestrator.get_strategy")
    def test_initialization_with_strategy_string(self, mock_get_strategy, mock_price_fetcher):
        """Test initialization with strategy name string."""
        mock_get_strategy.return_value = MockStrategy()

        orch = FilterOrchestrator(
            strategy="mock",
            price_fetcher=mock_price_fetcher,
        )

        mock_get_strategy.assert_called_once_with("mock", None)
        assert orch.strategy.name == "mock_strategy"

    def test_filter_tickers_basic(self, orchestrator, mock_price_fetcher):
        """Test basic ticker filtering."""
        tickers = ["AAPL", "MSFT"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["status"] == "success"
        assert "AAPL" in result["filtered_tickers"]
        assert "MSFT" not in result["filtered_tickers"]
        assert result["total_scanned"] == 2
        assert result["total_filtered"] == 1

    def test_filter_tickers_all_pass(self, orchestrator, mock_price_fetcher):
        """Test when all tickers pass filter."""
        tickers = ["AAPL", "AMZN", "AMD"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["status"] == "success"
        assert len(result["filtered_tickers"]) == 3

    def test_filter_tickers_all_fail(self, orchestrator, mock_price_fetcher):
        """Test when all tickers fail filter."""
        tickers = ["MSFT", "GOOGL", "META"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["status"] == "success"
        assert len(result["filtered_tickers"]) == 0

    def test_filter_tickers_handles_error(self, orchestrator, mock_price_fetcher):
        """Test handling of price fetcher error."""
        mock_price_fetcher.run.return_value = {"error": "API rate limit"}
        tickers = ["AAPL"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["status"] == "success"
        assert len(result["filtered_tickers"]) == 0
        assert "AAPL" in result["filter_details"]
        assert result["filter_details"]["AAPL"]["included"] is False
        assert "Data error" in result["filter_details"]["AAPL"]["reasons"][0]

    def test_filter_tickers_insufficient_data(self, orchestrator, mock_price_fetcher):
        """Test handling of insufficient price data."""
        mock_price_fetcher.run.return_value = {
            "prices": [{"close": 100}, {"close": 101}],  # Only 2 prices
            "latest_price": 101,
        }
        tickers = ["AAPL"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["status"] == "success"
        assert len(result["filtered_tickers"]) == 0
        assert "Insufficient price data" in result["filter_details"]["AAPL"]["reasons"]

    def test_filter_details_structure(self, orchestrator, mock_price_fetcher):
        """Test filter details structure."""
        tickers = ["AAPL", "MSFT"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        # Check AAPL (passes)
        assert result["filter_details"]["AAPL"]["included"] is True
        assert "Passed mock filter" in result["filter_details"]["AAPL"]["reasons"]
        assert result["filter_details"]["AAPL"]["latest_price"] == 105

        # Check MSFT (fails)
        assert result["filter_details"]["MSFT"]["included"] is False

    def test_filter_tickers_with_lookback_days(self, orchestrator, mock_price_fetcher):
        """Test lookback_days parameter is passed to fetcher."""
        tickers = ["AAPL"]

        orchestrator.filter_tickers(tickers, lookback_days=365, show_progress=False)

        mock_price_fetcher.run.assert_called_with("AAPL", days_back=365)

    def test_set_historical_date(self, orchestrator, mock_price_fetcher):
        """Test set_historical_date method."""
        from datetime import datetime

        mock_price_fetcher.set_historical_date = MagicMock()

        orchestrator.set_historical_date(datetime(2024, 1, 15))

        mock_price_fetcher.set_historical_date.assert_called_once()

    def test_filter_tickers_with_historical_date(self, orchestrator, mock_price_fetcher):
        """Test filtering with historical date."""
        from datetime import datetime

        mock_price_fetcher.set_historical_date = MagicMock()
        tickers = ["AAPL"]

        result = orchestrator.filter_tickers(
            tickers,
            historical_date=datetime(2024, 1, 15),
            show_progress=False,
        )

        mock_price_fetcher.set_historical_date.assert_called_once()
        assert result["status"] == "success"

    def test_filter_tickers_exception_handling(self, orchestrator, mock_price_fetcher):
        """Test exception handling during filtering."""
        mock_price_fetcher.run.side_effect = Exception("Unexpected error")
        tickers = ["AAPL"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["status"] == "error"
        assert "Unexpected error" in result["message"]
        assert result["filtered_tickers"] == []

    def test_strategy_name_in_result(self, orchestrator, mock_price_fetcher):
        """Test strategy name is included in result."""
        tickers = ["AAPL"]

        result = orchestrator.filter_tickers(tickers, show_progress=False)

        assert result["strategy"] == "mock_strategy"

    def test_empty_ticker_list(self, orchestrator, mock_price_fetcher):
        """Test filtering empty ticker list."""
        result = orchestrator.filter_tickers([], show_progress=False)

        assert result["status"] == "success"
        assert result["filtered_tickers"] == []
        assert result["total_scanned"] == 0
        assert result["total_filtered"] == 0
