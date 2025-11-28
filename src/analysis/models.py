"""Models for analysis signals and allocation recommendations."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    """Investment recommendation levels."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD_BULLISH = "hold_bullish"
    HOLD = "hold"
    HOLD_BEARISH = "hold_bearish"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ComponentScores(BaseModel):
    """Individual component analysis scores."""

    technical: float = Field(ge=0, le=100, description="Technical analysis score 0-100")
    fundamental: float = Field(ge=0, le=100, description="Fundamental analysis score 0-100")
    sentiment: float = Field(ge=0, le=100, description="Sentiment analysis score 0-100")


class RiskAssessment(BaseModel):
    """Risk assessment for an instrument."""

    level: RiskLevel = Field(description="Overall risk level")
    volatility: str = Field(description="Volatility assessment: low, normal, high")
    volatility_pct: float = Field(ge=0, description="ATR volatility as % of price")
    liquidity: str = Field(description="Liquidity assessment: illiquid, normal, highly_liquid")
    concentration_risk: bool = Field(description="Position concentration warning")
    sector_risk: str | None = Field(default=None, description="Sector-specific risks")
    flags: list[str] = Field(default_factory=list, description="Risk warning flags")


class AllocationSuggestion(BaseModel):
    """Position allocation suggestion."""

    ticker: str = Field(description="Stock ticker symbol")
    eur: float = Field(ge=0, description="Suggested allocation in EUR")
    percentage: float = Field(ge=0, le=100, description="Percentage of capital")
    shares: float | None = Field(
        default=None, ge=0, description="Number of shares at current price"
    )


class InvestmentSignal(BaseModel):
    """Complete investment signal with all analysis data."""

    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company or instrument name")
    market: str = Field(description="Market classification")
    sector: str | None = Field(default=None, description="Business sector")
    current_price: float = Field(ge=0, description="Current market price")
    currency: str = Field(default="EUR", description="Price currency")

    # Analysis scores
    scores: ComponentScores = Field(description="Individual component scores")
    final_score: float = Field(ge=0, le=100, description="Final composite score 0-100")

    # Recommendation and confidence
    recommendation: Recommendation = Field(description="Investment recommendation")
    confidence: float = Field(ge=0, le=100, description="Confidence level in recommendation")
    time_horizon: str = Field(default="3M", description="Time horizon: 1W, 1M, 3M, 6M, 1Y")

    # Expected return
    expected_return_min: float = Field(description="Expected return minimum %")
    expected_return_max: float = Field(description="Expected return maximum %")

    # Key reasons for signal
    key_reasons: list[str] = Field(description="Main factors supporting the recommendation")

    # Risk assessment
    risk: RiskAssessment = Field(description="Risk assessment details")

    # Allocation
    allocation: AllocationSuggestion | None = Field(
        default=None, description="Suggested position allocation"
    )

    # Analysis metadata
    generated_at: datetime = Field(description="Signal generation timestamp")
    analysis_date: str = Field(description="Date of analysis (YYYY-MM-DD)")

    # Additional context
    rationale: str | None = Field(
        default=None, description="Detailed rationale for the recommendation"
    )
    caveats: list[str] = Field(default_factory=list, description="Important caveats or limitations")


class PortfolioAllocation(BaseModel):
    """Portfolio allocation suggestion."""

    total_capital: float = Field(ge=0, description="Total capital available in EUR")
    monthly_deposit: float = Field(ge=0, description="Monthly deposit in EUR")
    available_for_allocation: float = Field(
        ge=0, description="Capital available for new allocations"
    )

    # Suggested positions
    suggested_positions: list[AllocationSuggestion] = Field(
        description="List of suggested positions"
    )

    # Diversification
    diversification_score: float = Field(
        ge=0, le=100, description="Portfolio diversification score 0-100"
    )
    market_diversification: dict[str, float] = Field(
        description="Capital allocation by market (market: percentage)"
    )
    sector_diversification: dict[str, float] = Field(
        description="Capital allocation by sector (sector: percentage)"
    )
    instrument_diversification: dict[str, float] = Field(
        description="Capital allocation by type (type: percentage)"
    )

    # Summary
    total_allocated: float = Field(ge=0, description="Total EUR allocated in suggestions")
    total_allocated_pct: float = Field(ge=0, le=100, description="Percentage of capital allocated")
    unallocated: float = Field(ge=0, description="Unallocated capital remaining in EUR")

    # Constraints applied
    constraints_applied: dict[str, float] = Field(
        description="Constraints enforced (max_position_size, max_sector, etc.)"
    )

    generated_at: datetime = Field(description="Allocation generation timestamp")


class DailyReport(BaseModel):
    """Daily market analysis report."""

    report_date: str = Field(description="Report date (YYYY-MM-DD)")
    report_time: datetime = Field(description="Report generation time")

    # Market overview
    market_overview: str = Field(description="Summary of market conditions")

    # Market movements
    market_indices: dict[str, dict[str, float]] = Field(
        description="Market index movements {index: {change_pct: X, direction: up/down}}"
    )

    # Top signals
    strong_signals: list[InvestmentSignal] = Field(
        description="High-confidence buy opportunities (top 10)"
    )

    # Portfolio alerts
    portfolio_alerts: list[dict[str, str]] = Field(
        description="Important alerts for portfolio positions"
    )

    # News summary
    key_news: list[dict[str, str]] = Field(description="Important news items with sentiment tags")

    # Watchlist
    watchlist_additions: list[str] = Field(description="Tickers recommended for watchlist addition")
    watchlist_removals: list[str] = Field(description="Tickers recommended for watchlist removal")

    # Portfolio suggestions
    allocation_suggestion: PortfolioAllocation | None = Field(
        default=None, description="Portfolio allocation suggestion"
    )

    # Summary statistics
    total_signals_generated: int = Field(ge=0, description="Total signals analyzed")
    strong_signals_count: int = Field(ge=0, description="Number of strong signals")
    moderate_signals_count: int = Field(ge=0, description="Number of moderate signals")

    # Disclaimers
    disclaimers: list[str] = Field(description="Important disclaimers and risk warnings")

    # Metadata
    data_sources: list[str] = Field(description="Data sources used for analysis")
    next_update: str | None = Field(default=None, description="Expected time of next update")
    analysis_mode: str = Field(
        default="rule_based", description="Analysis mode: 'llm' or 'rule_based'"
    )
