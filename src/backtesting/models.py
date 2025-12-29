"""Data models for backtesting results and summaries."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class BacktestResult(BaseModel):
    """Result of a single backtest run.

    Contains all metadata and references to generated recommendations
    for analysis across a date range.
    """

    # Execution metadata
    start_date: date = Field(description="Start date of backtest period")
    end_date: date = Field(description="End date of backtest period")
    frequency: str = Field(description="Analysis frequency (daily, weekly, monthly)")
    analysis_mode: str = Field(description="Analysis mode used (rule_based, llm)")

    # Scope
    tickers: list[str] = Field(description="List of tickers analyzed")
    analysis_dates: list[date] = Field(description="Dates on which analysis was performed")
    total_analyses: int = Field(description="Total number of analyses run (dates × tickers)")
    successful_analyses: int = Field(description="Number of successful analyses")
    failed_analyses: int = Field(description="Number of failed analyses")

    # Database references
    run_session_ids: list[int] = Field(
        default_factory=list,
        description="Run session IDs created during backtest",
    )
    recommendation_count: int = Field(
        default=0,
        description="Total recommendations generated",
    )

    # Cost tracking (for LLM mode)
    estimated_cost: float | None = Field(
        default=None,
        description="Estimated cost in EUR (for LLM mode)",
    )
    actual_cost: float | None = Field(
        default=None,
        description="Actual cost in EUR (for LLM mode)",
    )

    # Execution timing
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="Backtest start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Backtest completion timestamp",
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Total execution duration in seconds",
    )

    # Error tracking
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of errors encountered (ticker, date, error message)",
    )


class BacktestSummary(BaseModel):
    """High-level summary of backtest results.

    Aggregated statistics for quick assessment of backtest quality.
    """

    backtest_id: str = Field(description="Unique identifier for this backtest")
    date_range: str = Field(
        description="Human-readable date range (e.g., '2024-01-01 to 2024-12-31')"
    )
    total_recommendations: int = Field(description="Total recommendations generated")

    # Signal distribution
    signal_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Count of recommendations by signal type",
    )

    # Success metrics
    success_rate: float = Field(
        description="Percentage of analyses that completed successfully",
    )
    average_confidence: float | None = Field(
        default=None,
        description="Average confidence score across all recommendations",
    )

    # Cost summary (for LLM mode)
    total_cost: float | None = Field(
        default=None,
        description="Total cost in EUR (for LLM mode)",
    )
    cost_per_recommendation: float | None = Field(
        default=None,
        description="Average cost per recommendation in EUR (for LLM mode)",
    )

    # Timing
    total_duration_minutes: float = Field(
        description="Total backtest duration in minutes",
    )
    avg_analysis_time_seconds: float | None = Field(
        default=None,
        description="Average time per analysis in seconds",
    )
