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
