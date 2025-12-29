"""Backtesting framework for validating recommendation quality through historical analysis.

This module provides tools for:
- Automated historical analysis across date ranges
- Cost estimation for LLM-based backtests
- Performance comparison between analysis modes
- Recommendation quality validation

Example usage:
    from src.backtesting import BacktestEngine, BacktestConfig

    engine = BacktestEngine(config, provider_manager, repository)
    result = engine.run(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        tickers=["AAPL", "MSFT"],
        frequency="weekly",
        analysis_mode="rule_based"
    )
"""

from src.backtesting.config import BacktestConfig, BacktestFrequency
from src.backtesting.engine import BacktestEngine
from src.backtesting.models import BacktestResult, BacktestSummary

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestFrequency",
    "BacktestResult",
    "BacktestSummary",
]
