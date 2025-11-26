"""CrewAI agent definitions for financial analysis."""

from src.agents.analysis import FundamentalAnalysisAgent, TechnicalAnalysisAgent
from src.agents.base import AgentConfig, BaseAgent
from src.agents.crew import AnalysisCrew
from src.agents.scanner import MarketScannerAgent
from src.agents.sentiment import SentimentAgent, SignalSynthesisAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "MarketScannerAgent",
    "TechnicalAnalysisAgent",
    "FundamentalAnalysisAgent",
    "SentimentAgent",
    "SignalSynthesisAgent",
    "AnalysisCrew",
]
