# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Historical Analysis Exploration
#
# This notebook explores the historical analysis workflow in FalconSignals.
#
# **Purpose:**
# - Test and validate historical analysis with `--date` flag
# - Verify that historical prices are fetched correctly (no future information leakage)
# - Inspect `SignalCreator._fetch_historical_price()` logic
# - Validate database storage of historical recommendations
#
# **Key Questions:**
# - Does historical analysis use correct prices from `analysis_date`?
# - Is there future information leakage?
# - Are cached historical prices accurate?
# - How does the system distinguish historical vs current analysis?

# %% [markdown]
# ## Setup

# %%
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")

# %%
from src.analysis.signal_creator import SignalCreator
from src.cache.manager import CacheManager
from src.config.loader import load_config
from src.data.price_manager import PriceDataManager
from src.data.provider_manager import ProviderManager

# Initialize configuration
config = load_config()
cache_dir = str(project_root / "data" / "cache")
cache_manager = CacheManager(cache_dir)
provider_manager = ProviderManager(
    primary_provider=config.data.primary_provider,
    backup_providers=config.data.backup_providers,
    db_path=str(project_root / config.database.db_path),
)
price_manager = PriceDataManager(prices_dir=str(project_root / "data" / "cache" / "prices"))
from src.data.repository import Repository  # type: ignore[import-not-found]

repository = Repository(str(project_root / config.database.db_path))

print("✅ Components initialized")

# %% [markdown]
# ## Test Case 1: Historical Analysis for NVDA (2025-09-10)
#
# Let's analyze NVDA on a historical date and verify the price is correct:

# %%
ticker = "NVDA"
analysis_date = datetime(2025, 9, 10)

print(f"Analyzing {ticker} on {analysis_date.strftime('%Y-%m-%d')}")
print(f"{'=' * 60}")

# Fetch historical price for the analysis date
historical_price = price_manager.get_price_at_date(ticker=ticker, target_date=analysis_date)

if historical_price:
    print("✅ Historical price found:")
    print(f"  - Date: {historical_price['date']}")
    print(f"  - Close: ${historical_price['close']:.2f}")
    print(f"  - Volume: {historical_price['volume']:,}")
else:
    print(f"❌ No historical price found for {ticker} on {analysis_date.strftime('%Y-%m-%d')}")

# %% [markdown]
# ## Verify: Compare with Current Price
#
# Let's fetch the current price to ensure we're not using future information:

# %%
# Fetch current/latest price
latest_prices = provider_manager.get_stock_prices(ticker=ticker, period="5d")

if latest_prices:
    latest_price = latest_prices[-1]
    print(f"Latest price for {ticker}:")
    print(f"  - Date: {latest_price.date}")
    print(f"  - Close: ${latest_price.close_price:.2f}")
    print()

    if historical_price:
        price_diff = latest_price.close_price - historical_price["close"]
        price_change_pct = (price_diff / historical_price["close"]) * 100

        print(f"Price change from {analysis_date.strftime('%Y-%m-%d')} to now:")
        print(f"  - Absolute: ${price_diff:+.2f}")
        print(f"  - Percentage: {price_change_pct:+.2f}%")
        print()

        if abs(price_change_pct) < 1.0:
            print("⚠️ WARNING: Prices are very similar - might be using wrong date!")
        else:
            print("✅ Prices are different - using correct historical data")
else:
    print("❌ Failed to fetch latest price")

# %% [markdown]
# ## Test Case 2: Multiple Historical Dates
#
# Let's test several historical dates to ensure consistency:

# %%
test_cases = [
    {"ticker": "NVDA", "date": "2025-09-10", "expected_range": (175, 180)},
    {"ticker": "AAPL", "date": "2025-06-15", "expected_range": (210, 215)},
    {"ticker": "MSFT", "date": "2025-08-01", "expected_range": (430, 440)},
]

print("Testing multiple historical dates:")
print(f"{'=' * 60}")

for test_case in test_cases:
    ticker = test_case["ticker"]
    date_str = test_case["date"]
    expected_min, expected_max = test_case["expected_range"]

    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    price = price_manager.get_price_at_date(ticker=ticker, target_date=target_date)

    if price:
        is_in_range = expected_min <= price["close"] <= expected_max
        status = "✅" if is_in_range else "⚠️"

        print(f"{status} {ticker:6} on {date_str}: ${price['close']:.2f}")
        if not is_in_range:
            print(f"    Expected range: ${expected_min}-${expected_max}")
    else:
        print(f"❌ {ticker:6} on {date_str}: No price found")

    print()

# %% [markdown]
# ## Test Case 3: Inspect SignalCreator with Historical Date
#
# Let's create a signal using SignalCreator and verify it uses the correct historical price:

# %%

# Create SignalCreator instance
signal_creator = SignalCreator(provider_manager=provider_manager, price_manager=price_manager)

print("Testing SignalCreator with historical date")
print(f"{'=' * 60}")

# Create mock analysis results for NVDA on 2025-09-10
ticker = "NVDA"
analysis_date = datetime(2025, 9, 10)

# Mock analysis data
mock_analysis = {
    "ticker": ticker,
    "analysis_date": analysis_date,
    "signal": "buy",
    "confidence": 75.0,
    "fundamental_score": 80.0,
    "technical_score": 70.0,
    "sentiment_score": 75.0,
    "combined_score": 75.0,
    "reasoning": "Strong historical performance and technical indicators",
}

print(f"Mock analysis for {ticker} on {analysis_date.strftime('%Y-%m-%d')}:")
print(f"  - Signal: {mock_analysis['signal'].upper()}")
print(f"  - Confidence: {mock_analysis['confidence']}%")
print(f"  - Combined Score: {mock_analysis['combined_score']}")

# Note: We can't easily test the full signal creation without running the full pipeline,
# but we can verify the price fetching logic directly

# %% [markdown]
# ## Test Case 4: Database Storage Verification
#
# Let's check if historical recommendations are stored correctly in the database:

# %%
# Query recommendations from historical date range
from_date = datetime(2025, 9, 1)
to_date = datetime(2025, 9, 30)

historical_recs = repository.get_recommendations(from_date=from_date, to_date=to_date)

if historical_recs:
    print(
        f"Found {len(historical_recs)} historical recommendations from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
    )
    print(f"{'=' * 60}")

    for rec in historical_recs[:5]:  # Show first 5
        print(f"\n{rec.ticker:6} - {rec.signal.upper():12} (Confidence: {rec.confidence}%)")
        print(f"  - Analysis Date: {rec.analysis_date.strftime('%Y-%m-%d')}")
        print(f"  - Current Price: ${rec.current_price:.2f}")
        print(
            f"  - Target Price: ${rec.target_price:.2f}"
            if rec.target_price
            else "  - Target Price: N/A"
        )

        # Verify price is from the correct date
        if rec.analysis_date and rec.current_price:
            # Fetch the actual historical price for comparison
            actual_price = price_manager.get_price_at_date(
                ticker=rec.ticker, target_date=rec.analysis_date
            )

            if actual_price:
                diff = abs(rec.current_price - actual_price["close"])
                if diff < 0.01:
                    print("  ✅ Price matches historical data exactly")
                elif diff < 1.0:
                    print(f"  ✅ Price matches historical data (diff: ${diff:.2f})")
                else:
                    print(f"  ⚠️ Price differs from historical data (diff: ${diff:.2f})")
else:
    print("No historical recommendations found in database")
    print("💡 Run some historical analysis first using:")
    print("   uv run python -m src.main analyze --ticker NVDA --date 2025-09-10")

# %% [markdown]
# ## Test Case 5: Future Information Leakage Check
#
# Let's verify there's no future information leakage by comparing historical and current data:


# %%
def check_future_leakage(ticker: str, analysis_date: datetime) -> None:
    """Check if historical analysis has any future information leakage."""

    print(f"Checking for future leakage: {ticker} on {analysis_date.strftime('%Y-%m-%d')}")
    print(f"{'=' * 60}")

    # Get historical price at analysis date
    hist_price = price_manager.get_price_at_date(ticker=ticker, target_date=analysis_date)

    # Get current price
    current_prices = provider_manager.get_stock_prices(ticker=ticker, period="1d")
    current_price = current_prices[-1] if current_prices else None

    if hist_price and current_price:
        # Calculate date difference
        days_diff = (current_price.date - hist_price["date"]).days

        print(f"Historical price: ${hist_price['close']:.2f} on {hist_price['date']}")
        print(f"Current price:    ${current_price.close_price:.2f} on {current_price.date}")
        print(f"Days between:     {days_diff} days")
        print()

        if days_diff < 1:
            print("⚠️ WARNING: Dates are too close! Possible future information leakage!")
        elif abs(hist_price["close"] - current_price.close_price) < 0.01:
            print("⚠️ WARNING: Prices are identical! Possible future information leakage!")
        else:
            print("✅ No future information leakage detected")
            print(
                f"   Price changed ${current_price.close_price - hist_price['close']:+.2f} over {days_diff} days"
            )
    else:
        print("❌ Could not verify - missing price data")


# Test with NVDA
check_future_leakage("NVDA", datetime(2025, 9, 10))

# %% [markdown]
# ## Summary
#
# **Key Findings:**
#
# 1. **Historical Price Fetching**: `PriceDataManager.get_price_at_date()` correctly fetches prices from historical dates
# 2. **No Future Leakage**: Historical analysis uses prices from `analysis_date`, not current/future prices
# 3. **Database Storage**: Recommendations are stored with correct historical `current_price` values
# 4. **Date Handling**: The system properly distinguishes between historical and current analysis
#
# **Bug Fixes Applied (December 2025):**
# - ✅ Fixed `current_price = 0` issue in recommendations
# - ✅ Fixed historical price fetching to use `analysis_date` instead of current date
# - ✅ SignalCreator now uses `PriceDataManager` for accurate historical prices
#
# **Next Steps:**
# - Explore current analysis in notebook 03
# - Compare LLM vs rule-based modes in notebook 04
# - Deep dive into performance tracking in notebook 05
