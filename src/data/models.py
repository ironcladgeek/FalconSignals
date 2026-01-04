"""Pydantic models for financial data standardization."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Index, UniqueConstraint
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

    # Raw recommendation counts (optional, for providers like Finnhub
    # that provide detailed breakdowns)
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
    description: str | None = SQLField(default=None, description="Company description")
    sector: str | None = SQLField(default=None, description="Business sector (e.g., TECHNOLOGY)")
    industry: str | None = SQLField(
        default=None, description="Industry classification (e.g., SOFTWARE)"
    )
    currency: str = SQLField(default="USD", description="Trading currency (USD, EUR, etc.)")
    exchange: str | None = SQLField(default=None, description="Stock exchange (e.g., NASDAQ)")
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
    fundamental_snapshots: list["FundamentalSnapshot"] = Relationship(back_populates="ticker_obj")

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
        description=(
            "JSON-serialized AnalysisMetadata "
            "(technical indicators, fundamental metrics, analyst info, sentiment info)"
        ),
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


class Watchlist(SQLModel, table=True):
    """Watchlist for tracking selected tickers.

    Stores tickers that the user wants to monitor closely. Each ticker can only
    appear once in the watchlist (enforced via unique constraint on ticker_id).
    """

    __tablename__ = "watchlist"

    id: int | None = SQLField(default=None, primary_key=True, description="Auto-incrementing ID")
    ticker_id: int = SQLField(
        foreign_key="tickers.id", unique=True, index=True, description="Foreign key to ticker"
    )
    recommendation_id: int | None = SQLField(
        foreign_key="recommendations.id",
        default=None,
        index=True,
        description="Optional foreign key to recommendation that triggered watchlist addition",
    )
    created_at: datetime = SQLField(
        default_factory=datetime.now, description="When ticker was added to watchlist"
    )

    model_config = ConfigDict(from_attributes=True)


class WatchlistSignal(SQLModel, table=True):
    """Technical analysis signals for watchlist tickers.

    Stores periodic technical analysis results for tickers in the watchlist
    to help identify optimal entry points for opening positions.
    """

    __tablename__ = "watchlist_signals"

    id: int | None = SQLField(default=None, primary_key=True, description="Auto-incrementing ID")
    ticker_id: int = SQLField(
        foreign_key="tickers.id", index=True, description="Foreign key to ticker"
    )
    watchlist_id: int = SQLField(
        foreign_key="watchlist.id", index=True, description="Foreign key to watchlist entry"
    )
    analysis_date: date = SQLField(
        index=True, description="Date when technical analysis was performed"
    )
    score: float = SQLField(description="Technical analysis score (0-100)")
    confidence: float = SQLField(description="Confidence level in the analysis (0-100)")
    current_price: float = SQLField(description="Stock price at time of analysis")
    currency: str = SQLField(default="USD", description="Price currency")
    action: str | None = SQLField(default=None, description="Suggested action: Buy, Wait, Remove")
    entry_price: float | None = SQLField(
        default=None, description="Suggested entry price for Buy actions"
    )
    stop_loss: float | None = SQLField(
        default=None, description="Suggested stop loss level for Buy actions"
    )
    take_profit: float | None = SQLField(
        default=None, description="Suggested take profit target for Buy actions"
    )
    wait_for_price: float | None = SQLField(
        default=None, description="Price level to wait for if action is Wait"
    )
    rationale: str | None = SQLField(
        default=None, description="Explanation of the technical analysis and signal"
    )
    created_at: datetime = SQLField(
        default_factory=datetime.now, description="When signal was created"
    )

    model_config = ConfigDict(from_attributes=True)


class TradingJournal(SQLModel, table=True):
    """Trading journal for tracking open and closed positions.

    Records all trade entries and exits with P&L tracking. Supports both
    long and short positions with detailed fee tracking and performance metrics.
    """

    __tablename__ = "trading_journal"

    id: int | None = SQLField(default=None, primary_key=True, description="Auto-incrementing ID")
    ticker_id: int = SQLField(
        foreign_key="tickers.id", index=True, description="Foreign key to ticker"
    )
    recommendation_id: int | None = SQLField(
        foreign_key="recommendations.id",
        default=None,
        index=True,
        description="Optional foreign key to recommendation that triggered the trade",
    )

    # Entry details
    entry_date: date = SQLField(index=True, description="Date when position was opened")
    entry_price: float = SQLField(ge=0, description="Price per share/unit at entry")
    position_size: float = SQLField(ge=0, description="Number of shares/units")
    position_type: str = SQLField(default="long", description="Position type: 'long' or 'short'")
    fees_entry: float = SQLField(default=0.0, ge=0, description="Fees paid at entry")
    total_entry_amount: float = SQLField(
        ge=0, description="Total amount invested: (entry_price * position_size) + fees_entry"
    )

    # Risk management
    stop_loss: float | None = SQLField(default=None, ge=0, description="Stop loss price level")
    take_profit: float | None = SQLField(default=None, ge=0, description="Take profit price level")

    # Exit details (nullable for open positions)
    exit_date: date | None = SQLField(
        default=None, index=True, description="Date when position was closed (None for open)"
    )
    exit_price: float | None = SQLField(
        default=None, ge=0, description="Price per share/unit at exit"
    )
    fees_exit: float | None = SQLField(default=None, ge=0, description="Fees paid at exit")
    total_exit_amount: float | None = SQLField(
        default=None,
        ge=0,
        description="Total amount received: (exit_price * position_size) - fees_exit",
    )

    # Performance metrics (calculated fields)
    profit_loss: float | None = SQLField(
        default=None, description="Absolute profit/loss: total_exit_amount - total_entry_amount"
    )
    profit_loss_pct: float | None = SQLField(
        default=None, description="Percentage profit/loss: (profit_loss / total_entry_amount) * 100"
    )

    # Status and metadata
    status: str = SQLField(
        default="open", index=True, description="Trade status: 'open' or 'closed'"
    )
    currency: str = SQLField(default="USD", description="Trading currency")
    description: str | None = SQLField(default=None, description="Notes about the trade")
    created_at: datetime = SQLField(
        default_factory=datetime.now, description="When trade record was created"
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.now, description="When trade record was last updated"
    )

    # Relationships
    ticker_obj: Ticker = Relationship()

    model_config = ConfigDict(from_attributes=True)


class FundamentalSnapshot(SQLModel, table=True):
    """Historical fundamental data snapshots for backtesting.

    Stores comprehensive fundamental data from all sources (Alpha Vantage, Finnhub,
    Yahoo Finance) as daily snapshots. Enables accurate historical analysis by
    preserving the exact fundamental context available at any point in time.

    The complete data structure is stored in JSON format, with key metrics flattened
    to indexed columns for efficient querying.
    """

    __tablename__ = "fundamental_snapshots"
    __table_args__ = (
        UniqueConstraint("ticker_id", "snapshot_date", name="uq_ticker_snapshot_date"),
        Index("idx_fundamental_snapshots_ticker_date", "ticker_id", "snapshot_date"),
        Index("idx_fundamental_snapshots_date", "snapshot_date"),
        Index("idx_fundamental_snapshots_pe_ratio", "pe_ratio"),
        Index("idx_fundamental_snapshots_market_cap", "market_cap"),
        {"sqlite_autoincrement": True},
    )

    id: int | None = SQLField(default=None, primary_key=True, description="Auto-incrementing ID")
    ticker_id: int = SQLField(
        foreign_key="tickers.id", index=True, description="Foreign key to ticker"
    )
    snapshot_date: date = SQLField(index=True, description="Date of this snapshot")

    # Complete fundamental data (entire JSON structure from cache)
    # Includes: company_info, earnings_estimates, analyst_data, price_context, metrics
    data_json: str = SQLField(
        description="Complete fundamental data as JSON (same structure as cache files)"
    )

    # Flattened key columns for efficient querying (from company_info)
    # Valuation Metrics
    market_cap: float | None = SQLField(default=None, description="Market capitalization")
    pe_ratio: float | None = SQLField(default=None, description="Price-to-Earnings ratio")
    forward_pe: float | None = SQLField(default=None, description="Forward P/E ratio")
    peg_ratio: float | None = SQLField(default=None, description="PEG ratio")
    price_to_book: float | None = SQLField(default=None, description="Price-to-Book ratio")
    price_to_sales: float | None = SQLField(default=None, description="Price-to-Sales ratio")
    ev_to_revenue: float | None = SQLField(
        default=None, description="Enterprise Value to Revenue ratio"
    )
    ev_to_ebitda: float | None = SQLField(
        default=None, description="Enterprise Value to EBITDA ratio"
    )

    # Profitability Metrics
    profit_margin: float | None = SQLField(default=None, description="Profit margin")
    operating_margin: float | None = SQLField(default=None, description="Operating margin")
    return_on_equity: float | None = SQLField(default=None, description="Return on Equity (ROE)")
    return_on_assets: float | None = SQLField(default=None, description="Return on Assets (ROA)")

    # Growth Metrics
    quarterly_earnings_growth_yoy: float | None = SQLField(
        default=None, description="Quarterly earnings growth YoY"
    )
    quarterly_revenue_growth_yoy: float | None = SQLField(
        default=None, description="Quarterly revenue growth YoY"
    )

    # Analyst Data (from analyst_data section)
    analyst_target_price: float | None = SQLField(
        default=None, description="Average analyst target price"
    )
    total_analysts: int | None = SQLField(default=None, description="Total number of analysts")
    strong_buy_count: int | None = SQLField(
        default=None, description="Number of strong buy ratings"
    )
    buy_count: int | None = SQLField(default=None, description="Number of buy ratings")
    hold_count: int | None = SQLField(default=None, description="Number of hold ratings")
    sell_count: int | None = SQLField(default=None, description="Number of sell ratings")
    strong_sell_count: int | None = SQLField(
        default=None, description="Number of strong sell ratings"
    )

    # Price Context (from price_context section)
    latest_price: float | None = SQLField(default=None, description="Latest price at snapshot date")
    price_change_percent: float | None = SQLField(
        default=None, description="Price change % over period"
    )
    price_trend: str | None = SQLField(
        default=None, description="Price trend: bullish, bearish, neutral"
    )

    # Metadata
    data_sources: str | None = SQLField(
        default=None, description="Data sources used (e.g., 'Alpha Vantage + Finnhub + Yahoo')"
    )
    data_availability: str | None = SQLField(
        default=None,
        description="Available data types (e.g., 'company_overview, earnings_estimates, ...')",
    )
    fetched_at: datetime = SQLField(
        default_factory=datetime.now, description="Timestamp when data was fetched"
    )

    # Relationships
    ticker_obj: Ticker = Relationship(back_populates="fundamental_snapshots")

    model_config = ConfigDict(from_attributes=True)
