"""Tests for LLM tools module."""

import json
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.config.schemas import IndicatorConfig, TechnicalIndicatorsConfig
from src.llm.tools import CrewAIToolAdapter, json_serial, tool_with_timeout


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock()
    config.analysis.historical_data_lookback_days = 90
    # Use real TechnicalIndicatorsConfig instead of Mock to avoid iteration issues
    config.analysis.technical_indicators = TechnicalIndicatorsConfig(
        indicators=[
            IndicatorConfig(name="rsi", params={"length": 14}, enabled=True),
            IndicatorConfig(name="sma", params={"length": 20}, enabled=True),
        ],
        min_periods_required=50,
        use_pandas_ta=True,
    )
    return config


@pytest.fixture
def tool_adapter(mock_config):
    """Create tool adapter instance."""
    return CrewAIToolAdapter(config=mock_config)


@pytest.fixture
def tool_adapter_no_config():
    """Create tool adapter without config."""
    return CrewAIToolAdapter(config=None)


class TestJsonSerial:
    """Test json_serial function."""

    def test_serializes_datetime(self):
        """Test datetime serialization."""
        dt = datetime(2025, 12, 19, 10, 30, 0)
        result = json_serial(dt)
        assert result == "2025-12-19T10:30:00"

    def test_serializes_date(self):
        """Test date serialization."""
        from datetime import date

        d = date(2025, 12, 19)
        result = json_serial(d)
        assert result == "2025-12-19"

    def test_raises_on_unsupported_type(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="Type .* not serializable"):
            json_serial({"key": "value"})


class TestToolWithTimeout:
    """Test tool_with_timeout decorator."""

    def test_normal_execution(self):
        """Test decorator with normal function execution."""

        @tool_with_timeout(timeout_seconds=5)
        def normal_func():
            return "success"

        result = normal_func()
        assert result == "success"

    def test_timeout_warning(self):
        """Test decorator logs warning on slow execution."""

        @tool_with_timeout(timeout_seconds=1)
        def slow_func():
            time.sleep(1.5)
            return "completed"

        with patch("src.llm.tools.logger") as mock_logger:
            result = slow_func()
            assert result == "completed"
            mock_logger.warning.assert_called_once()
            assert "exceeded" in mock_logger.warning.call_args[0][0]

    def test_exception_handling(self):
        """Test decorator handles exceptions gracefully."""

        @tool_with_timeout(timeout_seconds=5)
        def error_func():
            raise ValueError("Test error")

        result = error_func()
        result_dict = json.loads(result)
        assert "error" in result_dict
        assert result_dict["error"] == "Test error"
        assert result_dict["error_type"] == "ValueError"

    def test_timeout_error_handling(self):
        """Test decorator handles TimeoutError."""

        @tool_with_timeout(timeout_seconds=1)
        def timeout_func():
            raise TimeoutError("Operation timed out")

        result = timeout_func()
        result_dict = json.loads(result)
        assert "error" in result_dict
        assert "timed out" in result_dict["error"]


class TestCrewAIToolAdapterInit:
    """Test CrewAIToolAdapter initialization."""

    def test_init_with_config(self, mock_config):
        """Test initialization with config."""
        adapter = CrewAIToolAdapter(config=mock_config)
        assert adapter.config == mock_config
        assert adapter.price_fetcher is not None
        assert adapter.technical_tool is not None
        assert adapter.news_fetcher is not None
        assert adapter.fundamental_fetcher is not None
        assert adapter._data_cache == {}
        assert len(adapter._tools) == 4

    def test_init_without_config(self):
        """Test initialization without config."""
        adapter = CrewAIToolAdapter(config=None)
        assert adapter.config is None
        assert adapter.price_fetcher is not None
        assert adapter.technical_tool is not None
        assert len(adapter._tools) == 4

    def test_init_with_db_path(self, mock_config):
        """Test initialization with db_path."""
        adapter = CrewAIToolAdapter(db_path="/tmp/test.db", config=mock_config)
        assert adapter.fundamental_fetcher is not None


class TestCrewAIToolAdapterTools:
    """Test CrewAIToolAdapter tool methods."""

    def test_get_crewai_tools(self, tool_adapter):
        """Test getting CrewAI tools list."""
        tools = tool_adapter.get_crewai_tools()
        assert len(tools) == 4
        # CrewAI tools have a .run() method
        assert all(hasattr(t, "run") for t in tools)

    def test_tools_have_metadata(self, tool_adapter):
        """Test that tools have proper metadata."""
        tools = tool_adapter.get_crewai_tools()
        # CrewAI tools should have name and description
        for tool_func in tools:
            assert hasattr(tool_func, "name") or hasattr(tool_func, "__name__")


class TestFetchPriceDataTool:
    """Test fetch_price_data tool."""

    def test_fetch_price_data_success(self, tool_adapter):
        """Test successful price data fetch."""
        # Mock price fetcher
        mock_result = {
            "ticker": "AAPL",
            "count": 100,
            "start_date": "2025-09-01",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
            "prices": [{"date": "2025-12-19", "close": 150.25}],
        }
        tool_adapter.price_fetcher.run = Mock(return_value=mock_result)

        # Get the tool
        tools = tool_adapter.get_crewai_tools()
        fetch_price_tool = tools[0]

        # Execute tool - CrewAI tools have a .run() method
        result = fetch_price_tool.run("AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert result_dict["count"] == 100
        assert result_dict["latest_price"] == 150.25
        assert "cache_key" in result_dict
        assert "prices_AAPL" == result_dict["cache_key"]

    def test_fetch_price_data_error(self, tool_adapter):
        """Test price data fetch with error."""
        # Mock price fetcher with error
        tool_adapter.price_fetcher.run = Mock(return_value={"error": "API unavailable"})

        tools = tool_adapter.get_crewai_tools()
        fetch_price_tool = tools[0]

        result = fetch_price_tool.run("AAPL")
        result_dict = json.loads(result)

        assert "error" in result_dict
        assert result_dict["error"] == "API unavailable"

    def test_fetch_price_data_exception(self, tool_adapter):
        """Test price data fetch with exception."""
        # Mock price fetcher to raise exception
        tool_adapter.price_fetcher.run = Mock(side_effect=ValueError("Network error"))

        tools = tool_adapter.get_crewai_tools()
        fetch_price_tool = tools[0]

        result = fetch_price_tool.run("AAPL")
        result_dict = json.loads(result)

        assert "error" in result_dict
        assert "Network error" in result_dict["error"]

    def test_fetch_price_data_caching(self, tool_adapter):
        """Test that price data is cached."""
        mock_prices = [{"date": "2025-12-19", "close": 150.25}]
        mock_result = {
            "ticker": "AAPL",
            "count": 1,
            "prices": mock_prices,
            "start_date": "2025-12-19",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
        }
        tool_adapter.price_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        fetch_price_tool = tools[0]

        fetch_price_tool.run("AAPL")

        # Check cache
        assert "prices_AAPL" in tool_adapter._data_cache
        assert tool_adapter._data_cache["prices_AAPL"] == mock_prices

    def test_fetch_price_data_uses_config_lookback(self, tool_adapter):
        """Test that fetch uses config lookback period."""
        mock_result = {
            "ticker": "AAPL",
            "count": 90,
            "prices": [],
            "start_date": "2025-09-20",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
        }
        tool_adapter.price_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        fetch_price_tool = tools[0]

        fetch_price_tool.run("AAPL")

        # Verify config lookback was used
        tool_adapter.price_fetcher.run.assert_called_with("AAPL", days_back=90)

    def test_fetch_price_data_no_config_uses_default(self, tool_adapter_no_config):
        """Test that fetch uses default lookback when no config."""
        mock_result = {
            "ticker": "AAPL",
            "count": 730,
            "prices": [],
            "start_date": "2023-12-19",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
        }
        tool_adapter_no_config.price_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter_no_config.get_crewai_tools()
        fetch_price_tool = tools[0]

        fetch_price_tool.run("AAPL")

        # Verify default lookback was used
        tool_adapter_no_config.price_fetcher.run.assert_called_with("AAPL", days_back=730)


class TestCalculateTechnicalIndicatorsTool:
    """Test calculate_technical_indicators tool."""

    def test_calculate_technical_indicators_success(self, tool_adapter):
        """Test successful technical indicators calculation."""
        # Pre-populate cache
        mock_prices = [{"date": "2025-12-19", "close": 150.25}] * 50
        tool_adapter._data_cache["prices_AAPL"] = mock_prices

        # Mock technical tool
        mock_result = {
            "indicators": {"RSI": 65.5, "MACD": 1.2},
            "signals": {"trend": "bullish"},
        }
        tool_adapter.technical_tool.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        tech_tool = tools[1]

        result = tech_tool.run("AAPL")
        result_dict = json.loads(result)

        assert "indicators" in result_dict
        assert "analysis_type" in result_dict
        assert result_dict["analysis_type"] == "rule_based_calculations"

    def test_calculate_technical_indicators_auto_fetch(self, tool_adapter):
        """Test auto-fetch when price data not cached."""
        # Mock price fetcher
        mock_prices = [{"date": "2025-12-19", "close": 150.25}] * 50
        mock_price_result = {
            "ticker": "AAPL",
            "count": 50,
            "prices": mock_prices,
            "start_date": "2025-09-20",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
        }
        tool_adapter.price_fetcher.run = Mock(return_value=mock_price_result)

        # Mock technical tool
        mock_tech_result = {"indicators": {"RSI": 65.5}}
        tool_adapter.technical_tool.run = Mock(return_value=mock_tech_result)

        tools = tool_adapter.get_crewai_tools()
        tech_tool = tools[1]

        tech_tool.run("AAPL")

        # Verify price fetch was called
        tool_adapter.price_fetcher.run.assert_called_once()
        # Verify cache was populated
        assert "prices_AAPL" in tool_adapter._data_cache

    def test_calculate_technical_indicators_insufficient_data_refetch(self, tool_adapter):
        """Test refetch when insufficient data error."""
        # Pre-populate cache with insufficient data
        mock_prices_short = [{"date": "2025-12-19", "close": 150.25}] * 10
        tool_adapter._data_cache["prices_AAPL"] = mock_prices_short

        # Mock technical tool to return insufficient data error first, then success
        tool_adapter.technical_tool.run = Mock(
            side_effect=[
                {"error": "Insufficient data for technical analysis"},
                {"indicators": {"RSI": 65.5}},
            ]
        )

        # Mock refetch
        mock_prices_full = [{"date": "2025-12-19", "close": 150.25}] * 90
        mock_price_result = {
            "ticker": "AAPL",
            "count": 90,
            "prices": mock_prices_full,
            "start_date": "2025-09-20",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
        }
        tool_adapter.price_fetcher.run = Mock(return_value=mock_price_result)

        tools = tool_adapter.get_crewai_tools()
        tech_tool = tools[1]

        result = tech_tool.run("AAPL")
        result_dict = json.loads(result)

        # Verify refetch was called
        tool_adapter.price_fetcher.run.assert_called_once()
        # Verify technical tool was called twice
        assert tool_adapter.technical_tool.run.call_count == 2
        # Verify success result
        assert "indicators" in result_dict

    def test_calculate_technical_indicators_error_no_prices(self, tool_adapter):
        """Test error when no price data available and fetch fails."""
        # Empty cache
        tool_adapter._data_cache["prices_AAPL"] = []
        # Mock fetch to fail
        tool_adapter.price_fetcher.run = Mock(return_value={"error": "No data available"})

        tools = tool_adapter.get_crewai_tools()
        tech_tool = tools[1]

        result = tech_tool.run("AAPL")
        result_dict = json.loads(result)

        assert "error" in result_dict

    def test_calculate_technical_indicators_exception(self, tool_adapter):
        """Test exception handling."""
        mock_prices = [{"date": "2025-12-19", "close": 150.25}] * 50
        tool_adapter._data_cache["prices_AAPL"] = mock_prices
        tool_adapter.technical_tool.run = Mock(side_effect=RuntimeError("Calculation error"))

        tools = tool_adapter.get_crewai_tools()
        tech_tool = tools[1]

        result = tech_tool.run("AAPL")
        result_dict = json.loads(result)

        assert "error" in result_dict
        assert "Calculation error" in result_dict["error"]


class TestAnalyzeSentimentTool:
    """Test analyze_sentiment tool."""

    def test_analyze_sentiment_success(self, tool_adapter):
        """Test successful sentiment analysis."""
        mock_articles = [
            {
                "title": "Company announces record profits",
                "summary": "Strong quarterly results",
                "source": "Reuters",
                "published_date": "2025-12-19",
            }
        ]
        mock_result = {"articles": mock_articles, "count": 1}
        tool_adapter.news_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        sentiment_tool = tools[2]

        result = sentiment_tool.run(ticker="AAPL", max_articles=50)
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert len(result_dict["articles"]) == 1
        assert result_dict["total_articles"] == 1

    def test_analyze_sentiment_with_precalculated_scores(self, tool_adapter):
        """Test sentiment with pre-calculated scores."""
        mock_articles = [
            {
                "title": "Company announces record profits",
                "summary": "Strong quarterly results",
                "source": "Reuters",
                "published_date": "2025-12-19",
                "sentiment": "positive",
                "sentiment_score": 0.8,
            },
            {
                "title": "Stock falls on market concerns",
                "summary": "Market volatility impacts",
                "source": "Bloomberg",
                "published_date": "2025-12-18",
                "sentiment": "negative",
                "sentiment_score": -0.5,
            },
        ]
        mock_result = {"articles": mock_articles, "count": 2}
        tool_adapter.news_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        sentiment_tool = tools[2]

        result = sentiment_tool.run(ticker="AAPL")

        # Should return summary string for pre-calculated scores
        assert isinstance(result, str)
        assert "pre-calculated sentiment scores" in result
        assert "positive" in result
        assert "negative" in result

    def test_analyze_sentiment_error_fallback(self, tool_adapter):
        """Test sentiment analysis error fallback."""
        tool_adapter.news_fetcher.run = Mock(return_value={"error": "API unavailable"})

        tools = tool_adapter.get_crewai_tools()
        sentiment_tool = tools[2]

        result = sentiment_tool.run(ticker="AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert result_dict["fallback_mode"] is True
        assert len(result_dict["articles"]) == 0

    def test_analyze_sentiment_no_articles(self, tool_adapter):
        """Test sentiment analysis with no articles."""
        mock_result = {"articles": [], "count": 0}
        tool_adapter.news_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        sentiment_tool = tools[2]

        result = sentiment_tool.run(ticker="AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert len(result_dict["articles"]) == 0
        assert result_dict["count"] == 0

    def test_analyze_sentiment_exception(self, tool_adapter):
        """Test sentiment analysis exception handling."""
        tool_adapter.news_fetcher.run = Mock(side_effect=RuntimeError("Network error"))

        tools = tool_adapter.get_crewai_tools()
        sentiment_tool = tools[2]

        result = sentiment_tool.run(ticker="AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert result_dict["fallback_mode"] is True
        assert "error" in result_dict


class TestFetchFundamentalDataTool:
    """Test fetch_fundamental_data tool."""

    def test_fetch_fundamental_data_success(self, tool_adapter):
        """Test successful fundamental data fetch."""
        mock_result = {
            "analyst_data": {
                "strong_buy": 5,
                "buy": 10,
                "hold": 3,
                "sell": 1,
                "strong_sell": 0,
                "total_analysts": 19,
                "period": "latest",
            },
            "price_context": {
                "change_percent": 5.2,
                "trend": "bullish",
                "latest_price": 150.25,
                "period_days": 30,
            },
            "metrics": {
                "valuation": {"trailing_pe": 28.5},
                "profitability": {"profit_margin": 0.25},
                "financial_health": {"debt_to_equity": 1.5},
                "growth": {"revenue_growth": 0.15},
            },
            "data_availability": "full",
        }
        tool_adapter.fundamental_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        fundamental_tool = tools[3]

        result = fundamental_tool.run("AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert result_dict["data_availability"] == "full"
        assert result_dict["analyst_consensus"]["total_analysts"] == 19
        assert result_dict["price_momentum"]["change_percent"] == 5.2
        assert result_dict["metrics"]["available"] is True

    def test_fetch_fundamental_data_error_fallback(self, tool_adapter):
        """Test fundamental data error fallback."""
        tool_adapter.fundamental_fetcher.run = Mock(return_value={"error": "API limit reached"})

        tools = tool_adapter.get_crewai_tools()
        fundamental_tool = tools[3]

        result = fundamental_tool.run("AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert result_dict["data_availability"] == "limited"
        assert result_dict["analyst_consensus"]["available"] is False

    def test_fetch_fundamental_data_partial_availability(self, tool_adapter):
        """Test fundamental data with partial availability."""
        mock_result = {
            "analyst_data": {"total_analysts": 0},  # Empty analyst data
            "price_context": {"change_percent": 5.2, "trend": "bullish", "latest_price": 150.25},
            "metrics": {},
            "data_availability": "partial",
        }
        tool_adapter.fundamental_fetcher.run = Mock(return_value=mock_result)

        tools = tool_adapter.get_crewai_tools()
        fundamental_tool = tools[3]

        result = fundamental_tool.run("AAPL")
        result_dict = json.loads(result)

        # Check basic structure
        assert result_dict["analyst_consensus"]["available"] is False
        assert result_dict["price_momentum"]["available"] is True
        # Metrics dict should have the expected keys
        assert "available" in result_dict["metrics"]
        assert "valuation" in result_dict["metrics"]
        assert "profitability" in result_dict["metrics"]
        # When metrics are empty, available should be falsy (either False or empty dict)
        assert not result_dict["metrics"]["available"]

    def test_fetch_fundamental_data_exception(self, tool_adapter):
        """Test fundamental data exception handling."""
        tool_adapter.fundamental_fetcher.run = Mock(side_effect=RuntimeError("Network error"))

        tools = tool_adapter.get_crewai_tools()
        fundamental_tool = tools[3]

        result = fundamental_tool.run("AAPL")
        result_dict = json.loads(result)

        assert result_dict["ticker"] == "AAPL"
        assert result_dict["data_availability"] == "unavailable"
        assert "error" in result_dict


class TestToolIntegration:
    """Integration tests for tool interactions."""

    def test_price_data_cache_used_by_technical_tool(self, tool_adapter):
        """Test that technical tool uses cached price data."""
        # Mock price fetch
        mock_prices = [{"date": "2025-12-19", "close": 150.25}] * 50
        mock_price_result = {
            "ticker": "AAPL",
            "count": 50,
            "prices": mock_prices,
            "start_date": "2025-09-20",
            "end_date": "2025-12-19",
            "latest_price": 150.25,
        }
        tool_adapter.price_fetcher.run = Mock(return_value=mock_price_result)

        # Mock technical tool
        mock_tech_result = {"indicators": {"RSI": 65.5}}
        tool_adapter.technical_tool.run = Mock(return_value=mock_tech_result)

        tools = tool_adapter.get_crewai_tools()
        fetch_price_tool = tools[0]
        tech_tool = tools[1]

        # First fetch price data
        fetch_price_tool.run("AAPL")

        # Then calculate technical indicators
        tech_tool.run("AAPL")

        # Price fetch should be called only once (not again for technical tool)
        tool_adapter.price_fetcher.run.assert_called_once()
        # Technical tool should be called with cached prices
        tool_adapter.technical_tool.run.assert_called_once_with(mock_prices)

    def test_tools_work_independently(self, tool_adapter):
        """Test that tools can work independently."""
        # Mock all tools
        tool_adapter.price_fetcher.run = Mock(
            return_value={"ticker": "AAPL", "count": 50, "prices": [], "latest_price": 150.25}
        )
        tool_adapter.news_fetcher.run = Mock(return_value={"articles": [], "count": 0})
        tool_adapter.fundamental_fetcher.run = Mock(
            return_value={"analyst_data": {}, "price_context": {}, "metrics": {}}
        )

        tools = tool_adapter.get_crewai_tools()

        # Each tool should be independently callable
        result1 = tools[0].run("AAPL")  # price
        result2 = tools[2].run(ticker="AAPL")  # sentiment
        result3 = tools[3].run("AAPL")  # fundamental

        # All should return JSON strings
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert isinstance(result3, str)

        # All should be valid JSON
        json.loads(result1)
        json.loads(result2)
        json.loads(result3)
