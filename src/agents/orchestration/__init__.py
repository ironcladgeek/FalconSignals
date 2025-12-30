"""Analysis orchestrators."""

from src.agents.orchestration.rule_based import RuleBasedOrchestrator

# Backward compatibility alias
AnalysisCrew = RuleBasedOrchestrator

__all__ = ["RuleBasedOrchestrator", "AnalysisCrew"]
