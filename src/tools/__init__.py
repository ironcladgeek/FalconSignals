"""Custom CrewAI tools for agent tasks."""

from src.tools.analysis import SentimentAnalyzerTool, TechnicalIndicatorTool
from src.tools.base import BaseTool, ToolRegistry
from src.tools.fetchers import NewsFetcherTool, PriceFetcherTool
from src.tools.reporting import ReportGeneratorTool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "PriceFetcherTool",
    "NewsFetcherTool",
    "TechnicalIndicatorTool",
    "SentimentAnalyzerTool",
    "ReportGeneratorTool",
]
