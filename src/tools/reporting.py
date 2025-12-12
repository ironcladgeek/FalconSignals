"""Report generation tools for agents."""

from datetime import datetime
from typing import Any

from src.tools.base import BaseTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGeneratorTool(BaseTool):
    """Tool for formatting analysis results into reports."""

    def __init__(self):
        """Initialize report generator."""
        super().__init__(
            name="ReportGenerator",
            description=(
                "Format analysis results into structured reports. "
                "Input: Analysis data from agents. "
                "Output: Formatted report text and JSON."
            ),
        )

    def run(self, analysis_data: dict[str, Any], format: str = "text") -> dict[str, Any]:
        """Generate report from analysis data.

        Args:
            analysis_data: Dictionary with all analysis results
            format: Output format ('text', 'json', 'markdown')

        Returns:
            Dictionary with formatted report
        """
        try:
            if format == "markdown":
                return self._format_markdown(analysis_data)
            elif format == "json":
                return self._format_json(analysis_data)
            else:
                return self._format_text(analysis_data)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"error": str(e)}

    @staticmethod
    def _format_text(data: dict[str, Any]) -> dict[str, Any]:
        """Format report as plain text.

        Args:
            data: Analysis data

        Returns:
            Dictionary with text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("INVESTMENT ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        if "ticker" in data:
            lines.append(f"\nSymbol: {data['ticker']}")

        if "price_data" in data:
            lines.append(f"Latest Price: ${data['price_data'].get('latest_price', 'N/A')}")

        if "technical" in data:
            lines.append("\n--- Technical Analysis ---")
            tech = data["technical"]
            lines.append(f"Trend: {tech.get('trend', 'N/A')}")
            lines.append(f"RSI: {tech.get('rsi', 'N/A')}")
            if "sma_200" in tech:
                lines.append(
                    f"SMA 50/200: {tech.get('sma_50', 0):.2f} / {tech.get('sma_200', 0):.2f}"
                )

        if "sentiment" in data:
            lines.append("\n--- Sentiment Analysis ---")
            sent = data["sentiment"]
            lines.append(f"Positive: {sent.get('positive_pct', 0)}%")
            lines.append(f"Negative: {sent.get('negative_pct', 0)}%")
            lines.append(f"Direction: {sent.get('sentiment_direction', 'N/A')}")

        if "recommendation" in data:
            lines.append("\n--- Recommendation ---")
            lines.append(f"Action: {data['recommendation'].get('action', 'N/A')}")
            lines.append(f"Confidence: {data['recommendation'].get('confidence', 'N/A')}%")

        return {
            "format": "text",
            "report": "\n".join(lines),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _format_markdown(data: dict[str, Any]) -> dict[str, Any]:
        """Format report as Markdown.

        Args:
            data: Analysis data

        Returns:
            Dictionary with markdown report
        """
        lines = []
        lines.append("# Investment Analysis Report")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        if "ticker" in data:
            lines.append(f"\n## {data['ticker']}")

        if "price_data" in data:
            lines.append(f"**Latest Price:** ${data['price_data'].get('latest_price', 'N/A')}")

        if "technical" in data:
            lines.append("## Technical Analysis")
            tech = data["technical"]
            lines.append(f"- **Trend:** {tech.get('trend', 'N/A').title()}")
            lines.append(f"- **RSI (14):** {tech.get('rsi', 'N/A')}")
            lines.append(f"- **MACD:** {tech.get('macd', {}).get('histogram', 'N/A')}")

        if "sentiment" in data:
            lines.append("## Sentiment Analysis")
            sent = data["sentiment"]
            lines.append(f"- **Positive:** {sent.get('positive_pct', 0)}%")
            lines.append(f"- **Negative:** {sent.get('negative_pct', 0)}%")
            lines.append(f"- **Direction:** {sent.get('sentiment_direction', 'N/A').title()}")

        if "recommendation" in data:
            lines.append("## Recommendation")
            rec = data["recommendation"]
            lines.append(f"**Action:** {rec.get('action', 'N/A')}")
            lines.append(f"**Confidence:** {rec.get('confidence', 'N/A')}%")
            if "rationale" in rec:
                lines.append(f"**Rationale:** {rec['rationale']}")

        return {
            "format": "markdown",
            "report": "\n".join(lines),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _format_json(data: dict[str, Any]) -> dict[str, Any]:
        """Format report as JSON.

        Args:
            data: Analysis data

        Returns:
            Dictionary with JSON data
        """
        return {
            "format": "json",
            "report": data,
            "timestamp": datetime.now().isoformat(),
        }
