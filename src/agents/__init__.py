"""CrewAI agent definitions for financial analysis."""

# Ensure data providers are registered on import
import src.data  # noqa: F401
from src.agents.ai_technical_agent import AITechnicalAnalysisAgent
from src.agents.analysis import FundamentalAnalysisAgent, TechnicalAnalysisAgent
from src.agents.base import AgentConfig, BaseAgent
from src.agents.crew import AnalysisCrew
from src.agents.sentiment import SentimentAgent, SignalSynthesisAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "TechnicalAnalysisAgent",
    "AITechnicalAnalysisAgent",
    "FundamentalAnalysisAgent",
    "SentimentAgent",
    "SignalSynthesisAgent",
    "AnalysisCrew",
]
