"""Agent definitions for financial analysis."""

# Ensure data providers are registered on import
import src.data  # noqa: F401

# Base classes
from src.agents.base import AgentConfig, BaseAgent

# LLM-powered agents
from src.agents.llm import AITechnicalAnalysisAgent, HybridAnalysisAgent, HybridAnalysisCrew

# Rule-based analysis modules
from src.agents.rule_based import (
    FundamentalAnalysisModule,
    SentimentAnalysisModule,
    SignalSynthesisModule,
    TechnicalAnalysisModule,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentConfig",
    # Rule-based modules
    "TechnicalAnalysisModule",
    "FundamentalAnalysisModule",
    "SentimentAnalysisModule",
    "SignalSynthesisModule",
    # LLM agents
    "AITechnicalAnalysisAgent",
    "HybridAnalysisAgent",
    "HybridAnalysisCrew",
]
