"""Agent definitions for financial analysis."""

# Ensure data providers are registered on import
import src.data  # noqa: F401

# Base classes
from src.agents.base import AgentConfig, BaseAgent

# LLM-powered agents
from src.agents.llm import AITechnicalAnalysisAgent, HybridAnalysisAgent, HybridAnalysisCrew

# Orchestrators
from src.agents.orchestration import AnalysisCrew, RuleBasedOrchestrator

# Rule-based analysis modules
from src.agents.rule_based import (
    FundamentalAnalysisModule,
    SentimentAnalysisModule,
    SignalSynthesisModule,
    TechnicalAnalysisModule,
)

# Backward compatibility aliases (old names -> new names)
TechnicalAnalysisAgent = TechnicalAnalysisModule
FundamentalAnalysisAgent = FundamentalAnalysisModule
SentimentAgent = SentimentAnalysisModule
SignalSynthesisAgent = SignalSynthesisModule

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentConfig",
    # Rule-based modules (new names)
    "TechnicalAnalysisModule",
    "FundamentalAnalysisModule",
    "SentimentAnalysisModule",
    "SignalSynthesisModule",
    # Backward compatibility (old names)
    "TechnicalAnalysisAgent",
    "FundamentalAnalysisAgent",
    "SentimentAgent",
    "SignalSynthesisAgent",
    # LLM agents
    "AITechnicalAnalysisAgent",
    "HybridAnalysisAgent",
    "HybridAnalysisCrew",
    # Orchestrators
    "RuleBasedOrchestrator",
    "AnalysisCrew",  # Backward compatibility alias for RuleBasedOrchestrator
]
