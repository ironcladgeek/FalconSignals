# Historical Analysis & Look-Ahead Bias Prevention

## Overview

Phase 8.1 implements **comprehensive historical date analysis** with **strict look-ahead bias prevention** across ALL data types. When analyzing as of a specific historical date, the system ensures that only data that would have been available on that date is included in the analysis.

## Look-Ahead Bias Prevention Strategy

Look-ahead bias occurs when a trading system uses information from the future to make trading decisions in the past. This invalidates backtesting results. Our implementation prevents this through **strict date filtering on all data types**.

### Data Types with Date Filtering

**1. Price Data** ✅
```python
# Only include prices dated <= analysis_date
filtered_prices = [
    price for price in all_prices
    if price.date.date() <= as_of_date_only
]
```
- Prevents use of future closing prices
- Prevents use of future highs/lows
- Prevents use of future volume information

**2. Fundamental Metrics** ✅
```python
# Only include financial statements reported before analysis_date
filtered_statements = [
    stmt for stmt in statements
    if stmt.report_date.date() <= as_of_date_only
]
```
- Prevents use of future earnings announcements
- Prevents use of unreleased financial data
- Ensures only historical public statements are used

**3. News Articles** ✅
```python
# Only include news published before analysis_date
filtered_news = [
    article for article in news_articles
    if article.published_date.date() <= as_of_date_only
]
```
- Prevents use of future news events
- Prevents use of future market announcements
- Ensures sentiment analysis uses only available information

**4. Analyst Ratings** ✅
```python
# Only include ratings issued before analysis_date
if rating and rating.rating_date.date() <= as_of_date_only:
    context.analyst_ratings = rating
```
- Prevents use of future analyst upgrades/downgrades
- Prevents use of revised price targets from the future
- Ensures only actual historical consensus is used

**5. Company Metadata** ✅
- Uses most recent metadata available as of analysis date
- Does not include future sector/industry reclassifications

## Implementation Details

### HistoricalDataFetcher Class

Located in `src/data/historical.py`, this class enforces strict date filtering:

```python
class HistoricalDataFetcher:
    def fetch_as_of_date(
        self,
        ticker: str,
        as_of_date,  # datetime or date object
        lookback_days: int = 365,
    ) -> HistoricalContext:
        """
        Fetch all data as it would have been available on as_of_date.

        Implements strict date filtering to prevent future data leakage.
        Only data with dates <= as_of_date is included in the result.
        """
```

### Key Features

1. **Date Type Flexibility**
   - Accepts both `datetime` and `date` objects
   - Automatically converts to correct format
   - Handles edge cases at midnight

2. **Configurable Lookback Period**
   - Default: 365 days of historical data
   - Customizable per analysis
   - Used to fetch sufficient historical context

3. **Data Availability Tracking**
   - Monitors data completeness
   - Warns about sparse data (< 40% of expected trading days)
   - Tracks missing data warnings per data type

4. **Graceful Error Handling**
   - Handles providers that don't support all data types
   - Collects warnings rather than failing
   - Allows analysis to proceed with available data

## HistoricalContext Data Model

The `HistoricalContext` model (in `src/data/models.py`) captures all relevant historical data:

```python
class HistoricalContext(BaseModel):
    ticker: str                              # Stock symbol
    as_of_date: datetime                     # Analysis date
    price_data: list[StockPrice]            # Price data up to as_of_date
    fundamentals: list[FinancialStatement]  # Financial data up to as_of_date
    news: list[NewsArticle]                 # News published before as_of_date
    analyst_ratings: AnalystRating | None   # Ratings before as_of_date
    metadata: InstrumentMetadata | None     # Instrument metadata
    lookback_days: int                      # Historical lookback period
    data_available: bool                    # Whether data was available
    missing_data_warnings: list[str]        # Warnings about missing data
```

## Testing & Verification

All date filtering is verified by comprehensive unit tests in `tests/unit/data/test_historical.py`:

- ✅ **test_historical_data_fetcher_filters_price_data**: Verifies price date filtering
- ✅ **test_historical_data_fetcher_filters_fundamentals**: Verifies fundamental data date filtering
- ✅ **test_historical_data_fetcher_filters_news**: Verifies news article date filtering
- ✅ **test_historical_data_fetcher_filters_analyst_ratings**: Verifies analyst rating date filtering
- ✅ **test_historical_data_fetcher_prevents_lookahead_bias**: Integration test with mixed dates
- ✅ **test_historical_data_fetcher_handles_missing_data**: Graceful error handling
- ✅ **test_historical_data_fetcher_lookback_period**: Respects lookback configuration
- ✅ **test_historical_data_fetcher_data_availability_tracking**: Tracks data completeness

## Usage Examples

### Command Line

```bash
# Analyze as of June 1, 2024 (rule-based)
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01

# Analyze as of June 1, 2024 (LLM-powered)
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01 --llm

# Test mode with historical date
uv run python -m src.main analyze --test --date 2024-06-01

# Multiple tickers
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL --date 2024-06-01
```

### Programmatic

```python
from src.data.historical import HistoricalDataFetcher
from src.data.provider_manager import ProviderManager
from datetime import datetime

# Setup
provider_manager = ProviderManager()
historical_fetcher = HistoricalDataFetcher(provider_manager.primary_provider)

# Fetch historical context
analysis_date = datetime(2024, 6, 1)
context = historical_fetcher.fetch_as_of_date(
    "AAPL",
    analysis_date,
    lookback_days=365
)

# Check data availability
if context.data_available:
    print(f"✓ Data available for {context.ticker} on {analysis_date}")
    print(f"  - Price data points: {len(context.price_data)}")
    print(f"  - Financial statements: {len(context.fundamentals)}")
    print(f"  - News articles: {len(context.news)}")
else:
    print(f"⚠ Data issues:")
    for warning in context.missing_data_warnings:
        print(f"  - {warning}")
```

## Design Rationale

### Why Filter All Data Types?

1. **Price Data**: Future prices directly leak market direction
2. **Fundamentals**: Future earnings/financials are material non-public info
3. **News**: Future announcements completely change sentiment
4. **Analyst Ratings**: Future upgrades/downgrades affect decision-making

Each data type must be filtered independently because:
- Each has its own "publication date" concept
- Each represents material information from the future
- Filtering one type but not others still allows look-ahead bias

### Why Strict Filtering?

We use `<=` instead of `<` (i.e., include data on the analysis date itself) because:
- Intraday data from the analysis date is available by end of day
- News published on the analysis date can be known by market close
- Financial reports are public immediately upon release
- Conservative approach: better to be inclusive than overly restrictive

## Cache Integration

The `CacheManager` supports historical queries via `get_historical_cache()`:

```python
cache_manager.get_historical_cache(
    ticker="AAPL",
    as_of_date="2024-06-01"
)
```

This efficiently retrieves cached data without re-fetching:
- Filters cached files by date in filename
- Returns most recent cache before specified date
- Reduces API calls for historical analysis

## Validation & Monitoring

The implementation includes:

1. **Date Validation**
   - Warns if analysis date is in the future
   - Validates date format (YYYY-MM-DD)
   - Handles edge cases around midnight

2. **Data Quality Monitoring**
   - Tracks sparse data warnings
   - Monitors missing data types
   - Reports data availability status

3. **Logging & Debugging**
   - Debug logs for all filtering operations
   - Warning logs for data quality issues
   - Error logs for fetch failures

## Future Enhancements

Potential improvements for Phase 8.2+:

1. **Backtesting Framework**: Run analysis across multiple historical dates
2. **Performance Tracking**: Compare historical recommendations vs actual outcomes
3. **Data Gap Analysis**: Identify and handle missing data periods
4. **Intraday Support**: Handle sub-daily analysis dates with market hours
5. **Corporate Actions**: Adjust prices for splits, dividends before analysis date

## Summary

✅ **All data types are strictly date-filtered to prevent look-ahead bias**
✅ **Comprehensive testing validates the filtering logic**
✅ **Graceful error handling for missing data**
✅ **Cache integration for efficient historical analysis**
✅ **Flexible date handling for various use cases**

The implementation enables reliable backtesting and historical analysis while preventing the subtle but critical bug of look-ahead bias.
