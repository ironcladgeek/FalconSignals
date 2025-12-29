"""Backtesting configuration schemas and validation."""

from enum import Enum

from pydantic import BaseModel, Field


class BacktestFrequency(str, Enum):
    """Supported backtesting frequencies."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class BacktestConfig(BaseModel):
    """Configuration for backtesting framework.

    Defines default parameters, cost controls, and reporting options
    for historical validation of recommendations.
    """

    # Execution parameters
    default_frequency: BacktestFrequency = Field(
        default=BacktestFrequency.WEEKLY,
        description="Default frequency for generating analysis dates",
    )
    default_period_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Default tracking period for measuring recommendation outcomes",
    )
    max_concurrent_analyses: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of concurrent analyses (for parallel execution)",
    )

    # Cost controls (for LLM mode)
    llm_cost_limit_per_backtest: float = Field(
        default=100.0,
        ge=0,
        description="Maximum allowed cost per backtest in EUR (0 = no limit)",
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require user confirmation before running expensive backtests",
    )
    cost_confirmation_threshold: float = Field(
        default=20.0,
        ge=0,
        description="Estimated cost threshold (EUR) above which confirmation is required",
    )

    # Benchmarks
    default_benchmark: str = Field(
        default="SPY",
        description="Default benchmark ticker for performance comparison",
    )
    alternative_benchmarks: list[str] = Field(
        default_factory=lambda: ["QQQ", "IWM"],
        description="Alternative benchmark tickers available for comparison",
    )

    # Reporting
    report_formats: list[str] = Field(
        default_factory=lambda: ["markdown", "json", "csv"],
        description="Supported output formats for backtest reports",
    )
    include_visualizations: bool = Field(
        default=False,
        description="Generate visualization charts in reports (requires additional dependencies)",
    )

    # Resume functionality
    allow_resume: bool = Field(
        default=True,
        description="Allow resuming failed backtests from last checkpoint",
    )
    skip_existing_data: bool = Field(
        default=True,
        description="Skip analysis for dates that already have recommendations in database",
    )
