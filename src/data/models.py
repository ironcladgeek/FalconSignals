"""Pydantic models for financial data standardization."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, SQLModel


class Market(str, Enum):
    """Supported markets."""

    NORDIC = "nordic"
    EU = "eu"
    US = "us"


class InstrumentType(str, Enum):
    """Supported instrument types."""

    STOCK = "stock"
    ETF = "etf"
    FUND = "fund"


class StockPrice(BaseModel):
    """Stock price data point."""

    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company or instrument name")
    market: Market = Field(description="Market classification")
    instrument_type: InstrumentType = Field(description="Type of instrument")
    date: datetime = Field(description="Date of price data")
    open_price: float = Field(ge=0, description="Opening price in EUR/USD")
    high_price: float = Field(ge=0, description="High price in EUR/USD")
    low_price: float = Field(ge=0, description="Low price in EUR/USD")
    close_price: float = Field(ge=0, description="Closing price in EUR/USD")
    volume: int = Field(ge=0, description="Trading volume")
    adjusted_close: float | None = Field(default=None, ge=0, description="Adjusted closing price")
    currency: str = Field(default="EUR", description="Price currency (EUR, USD, etc.)")

    model_config = ConfigDict(use_enum_values=True)


class FinancialStatement(BaseModel):
    """Financial statement data."""

    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company name")
    statement_type: str = Field(description="Type: income_statement, balance_sheet, cash_flow")
    fiscal_year: int = Field(description="Fiscal year")
    fiscal_quarter: int | None = Field(
        default=None, description="Fiscal quarter (1-4), None for annual"
    )
    report_date: datetime = Field(description="Report publication date")
    metric: str = Field(description="Metric name (e.g., revenue, net_income)")
    value: float = Field(description="Metric value")
    unit: str = Field(default="USD", description="Value unit (USD, millions, etc.)")

    model_config = ConfigDict(use_enum_values=True)


class NewsArticle(BaseModel):
    """News article data."""

    ticker: str = Field(description="Stock ticker symbol")
    title: str = Field(description="Article title")
    summary: str | None = Field(default=None, description="Article summary")
    source: str = Field(description="News source name")
    url: str = Field(description="Article URL")
    published_date: datetime = Field(description="Publication date")
    sentiment: str | None = Field(
        default=None, description="Sentiment: positive, negative, neutral"
    )
    sentiment_score: float | None = Field(
        default=None, ge=-1, le=1, description="Sentiment score from -1 to 1"
    )
    importance: int | None = Field(default=None, ge=0, le=100, description="Importance score 0-100")

    model_config = ConfigDict(use_enum_values=True)


class AnalystRating(BaseModel):
    """Analyst rating and price target."""

    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company name")
    rating_date: datetime = Field(description="Rating date")
    rating: str = Field(description="Rating: buy, hold, sell")
    price_target: float | None = Field(default=None, ge=0, description="Price target in EUR/USD")
    num_analysts: int | None = Field(default=None, ge=1, description="Number of analysts")
    consensus: str | None = Field(default=None, description="Consensus rating from aggregates")

    # Raw recommendation counts (optional, for providers like Finnhub that provide detailed breakdowns)
    strong_buy: int | None = Field(default=None, ge=0, description="Number of strong buy ratings")
    buy: int | None = Field(default=None, ge=0, description="Number of buy ratings")
    hold: int | None = Field(default=None, ge=0, description="Number of hold ratings")
    sell: int | None = Field(default=None, ge=0, description="Number of sell ratings")
    strong_sell: int | None = Field(default=None, ge=0, description="Number of strong sell ratings")

    model_config = ConfigDict(use_enum_values=True)


class InstrumentMetadata(BaseModel):
    """Metadata about a financial instrument."""

    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company or instrument name")
    market: Market = Field(description="Market classification")
    instrument_type: InstrumentType = Field(description="Type of instrument")
    sector: str | None = Field(default=None, description="Business sector")
    industry: str | None = Field(default=None, description="Industry classification")
    currency: str = Field(default="EUR", description="Trading currency")
    last_updated: datetime = Field(description="Last data update time")

    model_config = ConfigDict(use_enum_values=True)


class HistoricalContext(BaseModel):
    """Historical data context for a specific date.

    Contains all data that would have been available for analysis on a given date.
    """

    ticker: str = Field(description="Stock ticker symbol")
    as_of_date: datetime = Field(description="Date for which this context is valid")
    price_data: list[StockPrice] = Field(
        default_factory=list, description="Historical price data up to as_of_date"
    )
    fundamentals: list[FinancialStatement] = Field(
        default_factory=list, description="Financial statements available as of date"
    )
    news: list[NewsArticle] = Field(
        default_factory=list, description="News articles published before as_of_date"
    )
    analyst_ratings: AnalystRating | None = Field(
        default=None, description="Most recent analyst ratings as of date"
    )
    metadata: InstrumentMetadata | None = Field(default=None, description="Instrument metadata")
    earnings_estimates: dict | None = Field(
        default=None,
        description="Earnings estimates (None for historical dates to prevent look-ahead bias)",
    )
    lookback_days: int = Field(default=365, description="Number of days of historical data")
    data_available: bool = Field(
        default=True, description="Whether sufficient data was available for analysis"
    )
    missing_data_warnings: list[str] = Field(
        default_factory=list, description="Warnings about missing or sparse data"
    )

    model_config = ConfigDict(use_enum_values=True)


class Ticker(SQLModel, table=True):
    """Normalized ticker table for data consistency and relationships.

    Stores unique ticker symbols and metadata. Used as a foreign key reference
    by other tables (analyst_ratings, recommendations, price_tracking, etc.)
    to avoid duplication and enable efficient queries.
    """

    __tablename__ = "tickers"

    id: int | None = SQLField(default=None, primary_key=True)
    symbol: str = SQLField(unique=True, index=True, description="Ticker symbol (e.g., AAPL)")
    name: str = SQLField(description="Company or instrument name")
    market: str = SQLField(default="us", description="Market: nordic, eu, us")
    instrument_type: str = SQLField(default="stock", description="Type: stock, etf, fund")
    created_at: datetime = SQLField(
        default_factory=datetime.now, description="When ticker was first added"
    )
    last_updated: datetime = SQLField(
        default_factory=datetime.now, description="Last update timestamp"
    )

    # Relationships
    analyst_ratings: list["AnalystData"] = Relationship(back_populates="ticker_obj")
    recommendations: list["Recommendation"] = Relationship(back_populates="ticker_obj")
    performance_summaries: list["PerformanceSummary"] = Relationship(back_populates="ticker_obj")

    model_config = ConfigDict(from_attributes=True)


class AnalystData(SQLModel, table=True):
    """Historical analyst ratings data stored in database.

    Stores monthly snapshots of analyst ratings. APIs typically only provide
    current + 3 months, so this table accumulates ratings over time.
    References Ticker table for normalized ticker data.
    """

    __tablename__ = "analyst_ratings"

    id: int | None = SQLField(default=None, primary_key=True)
    ticker_id: int = SQLField(
        foreign_key="tickers.id", index=True, description="Foreign key to ticker"
    )
    period: date = SQLField(index=True, description="First day of the month (e.g., 2025-09-01)")
    strong_buy: int = SQLField(description="Count of strong buy ratings")
    buy: int = SQLField(description="Count of buy ratings")
    hold: int = SQLField(description="Count of hold ratings")
    sell: int = SQLField(description="Count of sell ratings")
    strong_sell: int = SQLField(description="Count of strong sell ratings")
    total_analysts: int = SQLField(description="Total number of analysts")
    data_source: str = SQLField(description="Data source: Finnhub, AlphaVantage, Yahoo, etc.")
    fetched_at: datetime = SQLField(
        default_factory=datetime.now, description="Timestamp when data was fetched"
    )

    # Relationships
    ticker_obj: Ticker = Relationship(back_populates="analyst_ratings")

    def to_analyst_rating(self) -> AnalystRating:
        """Convert database record to AnalystRating model."""
        # Determine consensus based on distribution
        ratings = [
            ("strong_buy", self.strong_buy),
            ("buy", self.buy),
            ("hold", self.hold),
            ("sell", self.sell),
            ("strong_sell", self.strong_sell),
        ]
        consensus = max(ratings, key=lambda x: x[1])[0] if self.total_analysts > 0 else None

        return AnalystRating(
            ticker=self.ticker_obj.symbol if self.ticker_obj else "",
            name=self.ticker_obj.name if self.ticker_obj else "",
            rating_date=datetime.combine(self.period, datetime.min.time()),
            rating=consensus or "hold",
            price_target=None,
            num_analysts=self.total_analysts,
            consensus=consensus,
        )

    model_config = ConfigDict(from_attributes=True)


class RunSession(SQLModel, table=True):
    """Analysis run session tracking.

    Tracks each analysis run with metadata for grouping signals and monitoring progress.
    Enables partial report generation and audit trail of all analysis runs.
    """

    __tablename__ = "run_sessions"

    id: int | None = SQLField(default=None, primary_key=True, description="Auto-incrementing ID")
    started_at: datetime = SQLField(
        default_factory=datetime.now, description="When analysis run started"
    )
    completed_at: datetime | None = SQLField(
        default=None, description="When analysis run completed"
    )

    # Run context
    analysis_mode: str = SQLField(description="Analysis mode: 'rule_based' or 'llm'")
    analyzed_category: str | None = SQLField(
        default=None, description="Category analyzed (e.g., 'us_tech_software')"
    )
    analyzed_market: str | None = SQLField(
        default=None, description="Market analyzed: 'us', 'nordic', 'eu', 'global'"
    )
    analyzed_tickers_specified: str | None = SQLField(
        default=None, description="JSON array of tickers if --ticker flag used"
    )

    # Two-stage LLM tracking
    initial_tickers_count: int = SQLField(default=0, description="Total tickers before filtering")
    anomalies_count: int = SQLField(
        default=0, description="Number of anomalies detected in stage 1"
    )
    force_full_analysis: bool = SQLField(
        default=False, description="Whether --force-full-analysis was used"
    )

    # Results
    signals_generated: int = SQLField(
        default=0, description="Number of signals successfully created"
    )
    signals_failed: int = SQLField(default=0, description="Number of tickers that failed analysis")

    # Status
    status: str = SQLField(description="Run status: 'running', 'completed', 'failed', 'partial'")
    error_message: str | None = SQLField(default=None, description="Error message if run failed")

    created_at: datetime = SQLField(
        default_factory=datetime.now, description="Record creation timestamp"
    )

    # Relationships
    recommendations: list["Recommendation"] = Relationship(back_populates="run_session_obj")

    model_config = ConfigDict(from_attributes=True)


class Recommendation(SQLModel, table=True):
    """Investment recommendation/signal stored in database.

    Stores every investment signal immediately after creation, enabling partial report
    generation and historical analysis. Contains all fields from InvestmentSignal Pydantic model.
    """

    __tablename__ = "recommendations"

    id: int | None = SQLField(default=None, primary_key=True, description="Auto-incrementing ID")
    ticker_id: int = SQLField(
        foreign_key="tickers.id", index=True, description="Foreign key to ticker"
    )
    run_session_id: int = SQLField(
        foreign_key="run_sessions.id", index=True, description="Foreign key to run session"
    )

    # Analysis metadata
    analysis_date: date = SQLField(index=True, description="Date when analysis was performed")
    analysis_mode: str = SQLField(description="Analysis mode: 'rule_based' or 'llm'")
    llm_model: str | None = SQLField(default=None, description="LLM model name if applicable")

    # Recommendation details
    signal_type: str = SQLField(
        index=True, description="Signal: 'strong_buy', 'buy', 'hold', 'sell', 'avoid'"
    )
    final_score: float = SQLField(description="Final combined score (0-100)")
    confidence: float = SQLField(description="Confidence score (0-100)")

    # Component scores
    technical_score: float | None = SQLField(default=None, description="Technical analysis score")
    fundamental_score: float | None = SQLField(
        default=None, description="Fundamental analysis score"
    )
    sentiment_score: float | None = SQLField(default=None, description="Sentiment analysis score")

    # Pricing
    current_price: float = SQLField(description="Current price at time of recommendation")
    currency: str = SQLField(default="USD", description="Price currency")
    expected_return_min: float | None = SQLField(
        default=None, description="Expected minimum return %"
    )
    expected_return_max: float | None = SQLField(
        default=None, description="Expected maximum return %"
    )
    time_horizon: str | None = SQLField(default=None, description="Time horizon (e.g., '3M', '6M')")

    # Risk assessment (JSON serialized for complex nested data)
    risk_level: str | None = SQLField(
        default=None, description="Risk: 'low', 'medium', 'high', 'very_high'"
    )
    risk_volatility: str | None = SQLField(default=None, description="Volatility description")
    risk_volatility_pct: float | None = SQLField(default=None, description="Volatility percentage")
    risk_flags: str | None = SQLField(default=None, description="JSON array of risk flags")

    # Context (JSON serialized)
    key_reasons: str | None = SQLField(default=None, description="JSON array of key reasons")
    rationale: str | None = SQLField(default=None, description="Investment rationale text")
    caveats: str | None = SQLField(default=None, description="JSON array of caveats")

    # Enhanced metadata (JSON serialized AnalysisMetadata)
    metadata_json: str | None = SQLField(
        default=None,
        description="JSON-serialized AnalysisMetadata (technical indicators, fundamental metrics, analyst info, sentiment info)",
    )

    created_at: datetime = SQLField(
        default_factory=datetime.now, description="When recommendation was created"
    )

    # Relationships
    ticker_obj: Ticker = Relationship(back_populates="recommendations")
    run_session_obj: RunSession = Relationship(back_populates="recommendations")
    price_tracking: list["PriceTracking"] = Relationship(back_populates="recommendation_obj")

    model_config = ConfigDict(from_attributes=True)


class PriceTracking(SQLModel, table=True):
    """Price tracking for performance analysis.

    Tracks price changes after recommendation to measure actual returns vs predictions.
    Updated daily by automated job.
    """

    __tablename__ = "price_tracking"

    id: int | None = SQLField(default=None, primary_key=True)
    recommendation_id: int = SQLField(
        foreign_key="recommendations.id", index=True, description="Foreign key to recommendation"
    )
    tracking_date: date = SQLField(index=True, description="Date when price was tracked")
    days_since_recommendation: int = SQLField(
        description="Number of days since recommendation was made"
    )

    # Price data
    price: float = SQLField(description="Stock price on tracking date")
    price_change_pct: float | None = SQLField(
        default=None, description="Price change % vs recommendation price"
    )

    # Benchmark comparison
    benchmark_ticker: str = SQLField(default="SPY", description="Benchmark ticker symbol")
    benchmark_price: float | None = SQLField(
        default=None, description="Benchmark price on tracking date"
    )
    benchmark_change_pct: float | None = SQLField(
        default=None, description="Benchmark change % since recommendation"
    )
    alpha: float | None = SQLField(
        default=None, description="Alpha: price_change_pct - benchmark_change_pct"
    )

    created_at: datetime = SQLField(
        default_factory=datetime.now, description="When tracking record was created"
    )

    # Relationships
    recommendation_obj: Recommendation = Relationship(back_populates="price_tracking")

    model_config = ConfigDict(from_attributes=True)


class PerformanceSummary(SQLModel, table=True):
    """Aggregated performance metrics.

    Pre-calculated performance statistics for quick analysis and reporting.
    Updated periodically by automated job.
    """

    __tablename__ = "performance_summary"

    id: int | None = SQLField(default=None, primary_key=True)

    # Aggregation dimensions
    ticker_id: int | None = SQLField(
        foreign_key="tickers.id",
        default=None,
        index=True,
        description="Ticker ID (NULL for overall summary)",
    )
    signal_type: str | None = SQLField(default=None, index=True, description="Signal type filter")
    analysis_mode: str | None = SQLField(default=None, description="Analysis mode filter")
    period_days: int = SQLField(index=True, description="Tracking period in days (7, 30, 90, 180)")

    # Performance metrics
    total_recommendations: int = SQLField(description="Total number of recommendations in sample")
    avg_return: float | None = SQLField(default=None, description="Average return %")
    median_return: float | None = SQLField(default=None, description="Median return %")
    win_rate: float | None = SQLField(default=None, description="Win rate % (positive returns)")
    avg_alpha: float | None = SQLField(default=None, description="Average alpha vs benchmark")
    sharpe_ratio: float | None = SQLField(default=None, description="Sharpe ratio")
    max_drawdown: float | None = SQLField(default=None, description="Maximum drawdown %")

    # Confidence calibration
    avg_confidence: float | None = SQLField(default=None, description="Average confidence score")
    actual_win_rate: float | None = SQLField(
        default=None, description="Actual win rate for calibration"
    )
    calibration_error: float | None = SQLField(
        default=None, description="Absolute difference: |avg_confidence - actual_win_rate|"
    )

    updated_at: datetime = SQLField(
        default_factory=datetime.now, description="When summary was last updated"
    )

    # Relationships
    ticker_obj: Ticker | None = Relationship(back_populates="performance_summaries")

    model_config = ConfigDict(from_attributes=True)
