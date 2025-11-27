"""Pydantic models for financial data standardization."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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
