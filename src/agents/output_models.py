"""Pydantic models for structured LLM agent outputs.

These models define the exact structure that LLM agents should return,
eliminating the need for markdown parsing with regex.
"""

from pydantic import BaseModel, Field


class TechnicalAnalysisOutput(BaseModel):
    """Structured output for technical analysis agent."""

    # Technical indicators (extracted from tool outputs)
    rsi: float | None = Field(None, description="RSI value (0-100)", ge=0, le=100)
    macd: float | None = Field(None, description="MACD line value")
    macd_signal: float | None = Field(None, description="MACD signal line value")
    atr: float | None = Field(None, description="Average True Range value", ge=0)

    # Analysis interpretation
    trend_direction: str = Field(..., description="Trend direction: bullish, bearish, or neutral")
    trend_strength: str = Field(..., description="Trend strength: strong, moderate, or weak")
    momentum_status: str = Field(
        ..., description="Momentum status: overbought, oversold, or neutral"
    )

    # Entry/exit signals
    support_level: float | None = Field(None, description="Key support price level", ge=0)
    resistance_level: float | None = Field(None, description="Key resistance price level", ge=0)

    # Score and reasoning
    technical_score: int = Field(
        ..., description="Overall technical strength score (0-100)", ge=0, le=100
    )
    key_findings: list[str] = Field(
        ..., description="3-5 key technical findings (minimum 1)", min_length=1
    )
    reasoning: str = Field(..., description="Brief explanation of technical score and signals")


class FundamentalAnalysisOutput(BaseModel):
    """Structured output for fundamental analysis agent."""

    # Analyst consensus (from tool data)
    total_analysts: int | None = Field(None, description="Total number of analysts", ge=0)
    strong_buy_count: int | None = Field(None, description="Number of Strong Buy ratings", ge=0)
    buy_count: int | None = Field(None, description="Number of Buy ratings", ge=0)
    hold_count: int | None = Field(None, description="Number of Hold ratings", ge=0)
    sell_count: int | None = Field(None, description="Number of Sell ratings", ge=0)
    strong_sell_count: int | None = Field(None, description="Number of Strong Sell ratings", ge=0)
    consensus_rating: str | None = Field(
        None, description="Overall consensus: Strong Buy, Buy, Hold, Sell, or Strong Sell"
    )

    # Financial metrics - Valuation (from tool data)
    pe_ratio: float | None = Field(None, description="Price-to-Earnings ratio (trailing)")
    forward_pe: float | None = Field(None, description="Forward P/E ratio")
    pb_ratio: float | None = Field(None, description="Price-to-Book ratio")
    ps_ratio: float | None = Field(None, description="Price-to-Sales ratio")
    peg_ratio: float | None = Field(None, description="PEG ratio (P/E to growth)")
    ev_ebitda: float | None = Field(None, description="Enterprise Value to EBITDA")

    # Financial metrics - Profitability
    profit_margin: float | None = Field(
        None, description="Net profit margin (as decimal, e.g. 0.15)"
    )
    operating_margin: float | None = Field(
        None, description="Operating margin (as decimal, e.g. 0.20)"
    )
    gross_margin: float | None = Field(None, description="Gross margin (as decimal, e.g. 0.40)")
    roe: float | None = Field(None, description="Return on Equity (as decimal, e.g. 0.18)")
    roa: float | None = Field(None, description="Return on Assets (as decimal, e.g. 0.10)")

    # Financial metrics - Financial Health
    debt_to_equity: float | None = Field(None, description="Debt-to-Equity ratio")
    current_ratio: float | None = Field(
        None, description="Current ratio (current assets/liabilities)"
    )

    # Financial metrics - Growth
    revenue_growth: float | None = Field(
        None, description="Revenue growth YoY (as decimal, e.g. 0.12)"
    )
    earnings_growth: float | None = Field(
        None, description="Earnings growth YoY (as decimal, e.g. 0.15)"
    )

    # Business quality assessment
    competitive_position: str = Field(
        ..., description="Competitive position: strong, moderate, or weak"
    )
    growth_outlook: str = Field(..., description="Growth outlook: high, moderate, or low")

    # Valuation
    valuation_assessment: str = Field(
        ..., description="Valuation: undervalued, fairly valued, or overvalued"
    )

    # Score and reasoning
    fundamental_score: int = Field(
        ..., description="Overall fundamental strength score (0-100)", ge=0, le=100
    )
    key_findings: list[str] = Field(
        ..., description="3-5 key fundamental findings (minimum 1)", min_length=1
    )
    reasoning: str = Field(..., description="Brief explanation of fundamental score")


class SentimentAnalysisOutput(BaseModel):
    """Structured output for sentiment analysis agent."""

    # News sentiment distribution
    total_articles: int | None = Field(None, description="Total number of articles analyzed", ge=0)
    positive_count: int | None = Field(None, description="Number of positive articles", ge=0)
    negative_count: int | None = Field(None, description="Number of negative articles", ge=0)
    neutral_count: int | None = Field(None, description="Number of neutral articles", ge=0)

    # Overall sentiment
    overall_sentiment: str = Field(
        ..., description="Overall sentiment: positive, negative, or neutral"
    )
    sentiment_score: float = Field(
        ...,
        description="Sentiment score from -1 (very negative) to +1 (very positive)",
        ge=-1,
        le=1,
    )

    # Key themes
    major_themes: list[str] = Field(
        ..., description="2-4 major themes from news coverage (minimum 1)", min_length=1
    )

    # Score and reasoning
    sentiment_strength_score: int = Field(
        ..., description="Sentiment strength score (0-100)", ge=0, le=100
    )
    key_findings: list[str] = Field(
        ..., description="3-5 key sentiment findings (minimum 1)", min_length=1
    )
    reasoning: str = Field(..., description="Brief explanation of sentiment assessment")


class SignalSynthesisOutput(BaseModel):
    """Structured output for signal synthesis agent."""

    # Component scores
    technical_score: int = Field(..., description="Technical analysis score (0-100)", ge=0, le=100)
    fundamental_score: int = Field(
        ..., description="Fundamental analysis score (0-100)", ge=0, le=100
    )
    sentiment_score: int = Field(..., description="Sentiment score (0-100)", ge=0, le=100)

    # Final recommendation
    final_score: int = Field(..., description="Final composite score (0-100)", ge=0, le=100)
    recommendation: str = Field(
        ...,
        description="Investment recommendation: strong_buy, buy, hold, sell, or strong_sell",
    )
    confidence: int = Field(..., description="Confidence in recommendation (0-100)", ge=0, le=100)

    # Investment thesis
    key_reasons: list[str] = Field(
        ..., description="3-5 key reasons for recommendation (minimum 1)", min_length=1
    )
    rationale: str = Field(..., description="Detailed investment thesis (2-3 paragraphs)")
    caveats: list[str] = Field(
        default_factory=list, description="Important caveats or risks (0-4 items)"
    )

    # Risk assessment
    risk_level: str = Field(default="medium", description="Risk level: low, medium, or high")
    volatility: str = Field(
        default="normal", description="Expected volatility: low, normal, or high"
    )
    risk_factors: list[str] = Field(
        default_factory=lambda: ["General market risk"],
        description="2-4 key risk factors (minimum 1)",
        min_length=1,
    )

    # Return expectations
    expected_return_min: float = Field(..., description="Expected return minimum percentage")
    expected_return_max: float = Field(..., description="Expected return maximum percentage")
    time_horizon: str = Field(..., description="Time horizon: 1W, 1M, 3M, 6M, or 1Y")

    # Company context
    company_name: str | None = Field(None, description="Company name")
    sector: str | None = Field(None, description="Business sector")
    market: str | None = Field(None, description="Market classification")
