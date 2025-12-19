"""Unit tests for the reporting tools module."""

from unittest.mock import patch

import pytest

from src.tools.reporting import ReportGeneratorTool


class TestReportGeneratorTool:
    """Test suite for ReportGeneratorTool class."""

    @pytest.fixture
    def tool(self):
        """Create ReportGeneratorTool instance."""
        return ReportGeneratorTool()

    @pytest.fixture
    def minimal_data(self):
        """Create minimal analysis data."""
        return {"ticker": "AAPL"}

    @pytest.fixture
    def full_data(self):
        """Create complete analysis data with all fields."""
        return {
            "ticker": "AAPL",
            "price_data": {"latest_price": 150.25},
            "technical": {
                "trend": "bullish",
                "rsi": 65.4,
                "sma_50": 148.5,
                "sma_200": 145.0,
                "macd": {"histogram": 2.3},
            },
            "sentiment": {
                "positive_pct": 65.0,
                "negative_pct": 20.0,
                "sentiment_direction": "positive",
            },
            "recommendation": {
                "action": "BUY",
                "confidence": 85,
                "rationale": "Strong technical and sentiment indicators",
            },
        }

    def test_initialization(self, tool):
        """Test ReportGeneratorTool initialization."""
        assert tool.name == "ReportGenerator"
        assert "Format analysis results" in tool.description
        assert "Input: Analysis data" in tool.description

    def test_run_default_text_format(self, tool, minimal_data):
        """Test run method with default text format."""
        result = tool.run(minimal_data)

        assert result["format"] == "text"
        assert "report" in result
        assert "timestamp" in result
        assert "AAPL" in result["report"]

    def test_run_text_format_explicit(self, tool, minimal_data):
        """Test run method with explicit text format."""
        result = tool.run(minimal_data, format="text")

        assert result["format"] == "text"
        assert isinstance(result["report"], str)

    def test_run_markdown_format(self, tool, minimal_data):
        """Test run method with markdown format."""
        result = tool.run(minimal_data, format="markdown")

        assert result["format"] == "markdown"
        assert "# Investment Analysis Report" in result["report"]
        assert "AAPL" in result["report"]

    def test_run_json_format(self, tool, minimal_data):
        """Test run method with JSON format."""
        result = tool.run(minimal_data, format="json")

        assert result["format"] == "json"
        assert result["report"] == minimal_data
        assert "timestamp" in result

    def test_run_with_error_handling(self, tool):
        """Test run method error handling."""
        # Pass invalid data that will cause an error
        with patch.object(tool, "_format_text", side_effect=Exception("Test error")):
            result = tool.run({}, format="text")

            assert "error" in result
            assert "Test error" in result["error"]

    def test_format_text_minimal_data(self, tool, minimal_data):
        """Test _format_text with minimal data."""
        result = tool._format_text(minimal_data)

        assert result["format"] == "text"
        assert "INVESTMENT ANALYSIS REPORT" in result["report"]
        assert "Symbol: AAPL" in result["report"]
        assert "timestamp" in result
        assert "=" * 80 in result["report"]

    def test_format_text_full_data(self, tool, full_data):
        """Test _format_text with complete data."""
        result = tool._format_text(full_data)

        report = result["report"]
        assert "Symbol: AAPL" in report
        assert "Latest Price: $150.25" in report
        assert "Technical Analysis" in report
        assert "Trend: bullish" in report
        assert "RSI: 65.4" in report
        assert "SMA 50/200: 148.50 / 145.00" in report
        assert "Sentiment Analysis" in report
        assert "Positive: 65.0%" in report
        assert "Negative: 20.0%" in report
        assert "Direction: positive" in report
        assert "Recommendation" in report
        assert "Action: BUY" in report
        assert "Confidence: 85%" in report

    def test_format_text_missing_ticker(self, tool):
        """Test _format_text without ticker."""
        data = {"price_data": {"latest_price": 100.0}}
        result = tool._format_text(data)

        assert "Latest Price: $100.0" in result["report"]
        # Should still generate report without ticker

    def test_format_text_missing_technical_sma(self, tool):
        """Test _format_text with technical data but no SMA."""
        data = {
            "ticker": "TEST",
            "technical": {"trend": "neutral", "rsi": 50.0},
        }
        result = tool._format_text(data)

        assert "Trend: neutral" in result["report"]
        assert "RSI: 50.0" in result["report"]
        # Should not crash on missing sma_200

    def test_format_text_with_timestamp(self, tool, minimal_data):
        """Test _format_text includes timestamp."""
        result = tool._format_text(minimal_data)

        # Verify timestamp fields exist and are properly formatted
        assert "Generated:" in result["report"]
        assert "timestamp" in result
        # Timestamp should be ISO format
        assert "T" in result["timestamp"] or "-" in result["timestamp"]

    def test_format_markdown_minimal_data(self, tool, minimal_data):
        """Test _format_markdown with minimal data."""
        result = tool._format_markdown(minimal_data)

        assert result["format"] == "markdown"
        assert "# Investment Analysis Report" in result["report"]
        assert "## AAPL" in result["report"]
        assert "*Generated:" in result["report"]

    def test_format_markdown_full_data(self, tool, full_data):
        """Test _format_markdown with complete data."""
        result = tool._format_markdown(full_data)

        report = result["report"]
        assert "# Investment Analysis Report" in report
        assert "## AAPL" in report
        assert "**Latest Price:** $150.25" in report
        assert "## Technical Analysis" in report
        assert "- **Trend:** Bullish" in report
        assert "- **RSI (14):** 65.4" in report
        assert "- **MACD:** 2.3" in report
        assert "## Sentiment Analysis" in report
        assert "- **Positive:** 65.0%" in report
        assert "- **Negative:** 20.0%" in report
        assert "- **Direction:** Positive" in report
        assert "## Recommendation" in report
        assert "**Action:** BUY" in report
        assert "**Confidence:** 85%" in report
        assert "**Rationale:** Strong technical and sentiment indicators" in report

    def test_format_markdown_missing_fields(self, tool):
        """Test _format_markdown with missing optional fields."""
        data = {"ticker": "TEST"}
        result = tool._format_markdown(data)

        assert "## TEST" in result["report"]
        # Should not include sections for missing data

    def test_format_markdown_technical_without_macd(self, tool):
        """Test _format_markdown with technical data but no MACD."""
        data = {
            "ticker": "TEST",
            "technical": {"trend": "sideways", "rsi": 45},
        }
        result = tool._format_markdown(data)

        assert "## Technical Analysis" in result["report"]
        assert "- **Trend:** Sideways" in result["report"]
        assert "- **RSI (14):** 45" in result["report"]

    def test_format_markdown_recommendation_without_rationale(self, tool):
        """Test _format_markdown with recommendation but no rationale."""
        data = {
            "ticker": "TEST",
            "recommendation": {"action": "HOLD", "confidence": 60},
        }
        result = tool._format_markdown(data)

        assert "## Recommendation" in result["report"]
        assert "**Action:** HOLD" in result["report"]
        assert "**Confidence:** 60%" in result["report"]
        # Should not crash on missing rationale

    def test_format_json_minimal_data(self, tool, minimal_data):
        """Test _format_json with minimal data."""
        result = tool._format_json(minimal_data)

        assert result["format"] == "json"
        assert result["report"] == minimal_data
        assert "timestamp" in result

    def test_format_json_full_data(self, tool, full_data):
        """Test _format_json with complete data."""
        result = tool._format_json(full_data)

        assert result["format"] == "json"
        assert result["report"] == full_data
        assert result["report"]["ticker"] == "AAPL"
        assert result["report"]["price_data"]["latest_price"] == 150.25

    def test_format_json_preserves_structure(self, tool):
        """Test _format_json preserves data structure."""
        complex_data = {
            "ticker": "TEST",
            "nested": {"deep": {"value": 123}},
            "list": [1, 2, 3],
        }
        result = tool._format_json(complex_data)

        assert result["report"]["nested"]["deep"]["value"] == 123
        assert result["report"]["list"] == [1, 2, 3]

    def test_all_formats_include_timestamp(self, tool, minimal_data):
        """Test that all format methods include timestamp."""
        text_result = tool._format_text(minimal_data)
        markdown_result = tool._format_markdown(minimal_data)
        json_result = tool._format_json(minimal_data)

        assert "timestamp" in text_result
        assert "timestamp" in markdown_result
        assert "timestamp" in json_result

    def test_format_text_na_for_missing_values(self, tool):
        """Test _format_text shows N/A for missing values."""
        data = {
            "price_data": {},
            "technical": {},
            "sentiment": {},
            "recommendation": {},
        }
        result = tool._format_text(data)

        report = result["report"]
        assert "N/A" in report

    def test_format_markdown_na_for_missing_values(self, tool):
        """Test _format_markdown shows N/A for missing values."""
        data = {
            "technical": {"trend": None, "rsi": None},
            "recommendation": {"action": None, "confidence": None},
        }
        result = tool._format_markdown(data)

        # Should handle None values gracefully without crashing
        assert "## Technical Analysis" in result["report"]
        assert "N/A" in result["report"]

    def test_run_with_empty_data(self, tool):
        """Test run with empty data dictionary."""
        result = tool.run({}, format="text")

        assert "report" in result
        assert "INVESTMENT ANALYSIS REPORT" in result["report"]

    def test_format_text_zero_percentages(self, tool):
        """Test _format_text with zero percentages in sentiment."""
        data = {
            "sentiment": {
                "positive_pct": 0,
                "negative_pct": 0,
                "sentiment_direction": "neutral",
            }
        }
        result = tool._format_text(data)

        assert "Positive: 0%" in result["report"]
        assert "Negative: 0%" in result["report"]

    def test_format_markdown_zero_values(self, tool):
        """Test _format_markdown with zero values."""
        data = {
            "sentiment": {"positive_pct": 0, "negative_pct": 0},
        }
        result = tool._format_markdown(data)

        assert "- **Positive:** 0%" in result["report"]
        assert "- **Negative:** 0%" in result["report"]
