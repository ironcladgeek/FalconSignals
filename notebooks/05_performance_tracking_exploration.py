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
# # Performance Tracking Exploration
#
# This notebook explores the performance tracking system in FalconSignals.
#
# **Purpose:**
# - Understand how `PriceDataManager` and performance tracking work
# - Track price changes for active recommendations over time
# - Calculate returns, alpha, and Sharpe ratio
# - Compare against benchmarks (SPY, QQQ)
# - Visualize performance metrics
#
# **Key Questions:**
# - How does performance tracking work?
# - Are returns calculated correctly?
# - How is benchmark comparison done?
# - What happens when prices are missing?

# %% [markdown]
# ## Setup

# %%
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")

# %%
from src.cache.manager import CacheManager
from src.config.loader import load_config
from src.data.price_manager import PriceDataManager
from src.data.provider_manager import ProviderManager

# Initialize components
config = load_config()
cache_dir = str(Path("data") / "cache")
cache_manager = CacheManager(cache_dir)
provider_manager = ProviderManager(
    primary_provider=config.data.primary_provider,
    backup_providers=config.data.backup_providers,
    db_path=config.database.db_path,
)
price_manager = PriceDataManager(prices_dir="data/cache/prices")
from src.data.repository import Repository  # type: ignore[import-not-found]

repository = Repository(config.database.db_path)

print("✅ Components initialized")

# %% [markdown]
# ## Understanding Price Tracking
#
# Let's first understand how price tracking works:

# %%
print("Price Tracking Architecture")
print(f"{'=' * 80}\n")

print("Components:")
print("  1. PriceDataManager")
print("     - Manages unified CSV storage of price data")
print("     - Location: data/prices/{ticker}.csv")
print("     - Downloads and caches historical prices")
print()
print("  2. Repository (price_tracking table)")
print("     - Stores daily price snapshots for recommendations")
print("     - Links to recommendation_id")
print("     - Enables historical performance analysis")
print()
print("  3. Track Performance Command")
print("     - Runs daily to update prices for active recommendations")
print("     - Command: uv run python -m src.main track-performance")
print()
print("  4. Performance Report Command")
print("     - Generates performance metrics and reports")
print("     - Command: uv run python -m src.main performance-report")

# %% [markdown]
# ## Get Active Recommendations
#
# Let's find active recommendations that should be tracked:

# %%

# Get recommendations from last 90 days
max_age_days = 90
from_date = datetime.now() - timedelta(days=max_age_days)

# Filter for actionable signals (buy, strong_buy)
active_recs = repository.get_recommendations(from_date=from_date)
buy_recs = [r for r in active_recs if r.signal in ["buy", "strong_buy"]]

print(f"Active Recommendations (last {max_age_days} days)")
print(f"{'=' * 80}")
print(f"Total recommendations: {len(active_recs)}")
print(f"Buy/Strong Buy signals: {len(buy_recs)}")
print()

if buy_recs:
    # Show top 10 by confidence
    top_recs = sorted(buy_recs, key=lambda x: x.confidence, reverse=True)[:10]

    print("Top 10 BUY recommendations by confidence:")
    print("-" * 80)
    print(f"{'Ticker':8} {'Signal':12} {'Confidence':>11} {'Date':12} {'Price':>10}")
    print("-" * 80)

    for rec in top_recs:
        print(
            f"{rec.ticker:8} {rec.signal.upper():12} {rec.confidence:>10.1f}% "
            f"{rec.analysis_date.strftime('%Y-%m-%d'):12} ${rec.current_price:>9.2f}"
        )
else:
    print("⚠️ No BUY recommendations found in last 90 days")
    print("💡 Run some analysis first:")
    print("   uv run python -m src.main analyze --test")

# %% [markdown]
# ## Track Prices for Recommendations
#
# Let's fetch current prices for active recommendations:

# %%
if buy_recs:
    print(f"Tracking prices for {len(buy_recs)} BUY recommendations")
    print(f"{'=' * 80}\n")

    # Get unique tickers
    tickers = list(set(r.ticker for r in buy_recs))
    print(f"Unique tickers: {len(tickers)}")
    print(f"Tickers: {', '.join(sorted(tickers)[:10])}{'...' if len(tickers) > 10 else ''}")
    print()

    # Fetch latest prices for each ticker
    price_updates = []

    for ticker in tickers[:5]:  # Show first 5 as example
        latest_price = price_manager.get_latest_price(ticker)

        if latest_price:
            price_updates.append(
                {
                    "ticker": ticker,
                    "date": latest_price["date"],
                    "price": latest_price["close"],
                }
            )
            print(f"✅ {ticker:6} ${latest_price['close']:>8.2f} ({latest_price['date']})")
        else:
            print(f"❌ {ticker:6} - Failed to fetch price")

    print()
    print(f"Successfully fetched prices for {len(price_updates)}/{len(tickers[:5])} tickers")

# %% [markdown]
# ## Calculate Returns
#
# Let's calculate returns for tracked recommendations:

# %%
returns_data = []
if buy_recs:
    print("Return Calculation")
    print(f"{'=' * 80}\n")

    for rec in buy_recs[:10]:  # Analyze first 10
        # Get latest price
        latest_price = price_manager.get_latest_price(rec.ticker)

        if latest_price and rec.current_price > 0:
            # Calculate return
            price_change = latest_price["close"] - rec.current_price
            return_pct = (price_change / rec.current_price) * 100

            # Calculate days held
            days_held = (latest_price["date"] - rec.analysis_date.date()).days

            returns_data.append(
                {
                    "ticker": rec.ticker,
                    "entry_price": rec.current_price,
                    "current_price": latest_price["close"],
                    "return_pct": return_pct,
                    "days_held": days_held,
                    "signal": rec.signal,
                    "confidence": rec.confidence,
                }
            )

    if returns_data:
        # Sort by return percentage
        returns_data.sort(key=lambda x: x["return_pct"], reverse=True)

        print("Returns Analysis (Top 10):")
        print("-" * 80)
        print(
            f"{'Ticker':8} {'Entry':>8} {'Current':>8} {'Return':>8} {'Days':>5} {'Confidence':>11}"
        )
        print("-" * 80)

        for item in returns_data:
            print(
                f"{item['ticker']:8} "
                f"${item['entry_price']:>7.2f} "
                f"${item['current_price']:>7.2f} "
                f"{item['return_pct']:>7.2f}% "
                f"{item['days_held']:>5} "
                f"{item['confidence']:>10.1f}%"
            )

        print()

# Calculate aggregate metrics
avg_return: float = 0.0
if returns_data:
    avg_return = sum(x["return_pct"] for x in returns_data) / len(returns_data)
    win_rate = sum(1 for x in returns_data if x["return_pct"] > 0) / len(returns_data) * 100

    print("Aggregate Metrics:")
    print(f"  - Average Return: {avg_return:+.2f}%")
    print(f"  - Win Rate: {win_rate:.1f}%")
    print(f"  - Winners: {sum(1 for x in returns_data if x['return_pct'] > 0)}")
    print(f"  - Losers: {sum(1 for x in returns_data if x['return_pct'] <= 0)}")

# %% [markdown]
# ## Benchmark Comparison
#
# Let's compare returns against a benchmark (SPY):

# %%
if buy_recs and returns_data:
    print("Benchmark Comparison (SPY)")
    print(f"{'=' * 80}\n")

    # Get SPY prices for the same period
    # Find earliest and latest dates from our recommendations
    earliest_date = min(rec.analysis_date for rec in buy_recs)
    latest_date = datetime.now()

    # Fetch SPY prices (approximate period)
    days_diff = (latest_date - earliest_date).days
    spy_prices = provider_manager.get_stock_prices(ticker="SPY", period=f"{days_diff}d")

    if spy_prices:
        spy_start = spy_prices[0].close  # type: ignore[attr-defined]
        spy_end = spy_prices[-1].close  # type: ignore[attr-defined]
        spy_return = ((spy_end - spy_start) / spy_start) * 100

        print("SPY Performance:")
        print(f"  - Start Price: ${spy_start:.2f}")
        print(f"  - End Price: ${spy_end:.2f}")
        print(f"  - Return: {spy_return:+.2f}%")
        print()

        # Calculate alpha (excess return over benchmark)
        alpha = avg_return - spy_return

        print("Comparison:")
        print(f"  - Portfolio Return: {avg_return:+.2f}%")
        print(f"  - SPY Return: {spy_return:+.2f}%")
        print(f"  - Alpha (excess return): {alpha:+.2f}%")
        print()

        if alpha > 0:
            print(f"✅ Portfolio outperformed SPY by {alpha:.2f}%")
        else:
            print(f"❌ Portfolio underperformed SPY by {abs(alpha):.2f}%")
    else:
        print("❌ Failed to fetch SPY benchmark data")

# %% [markdown]
# ## Confidence Calibration
#
# Let's check if confidence levels correlate with returns:

# %%
if returns_data:
    print("Confidence Calibration Analysis")
    print(f"{'=' * 80}\n")

    # Group by confidence buckets
    buckets = {
        "60-70%": [],
        "70-80%": [],
        "80-90%": [],
        "90-100%": [],
    }

    for item in returns_data:
        conf = item["confidence"]
        if 60 <= conf < 70:
            buckets["60-70%"].append(item["return_pct"])
        elif 70 <= conf < 80:
            buckets["70-80%"].append(item["return_pct"])
        elif 80 <= conf < 90:
            buckets["80-90%"].append(item["return_pct"])
        elif 90 <= conf <= 100:
            buckets["90-100%"].append(item["return_pct"])

    print("Average Return by Confidence Level:")
    print("-" * 60)
    print(f"{'Confidence':15} {'Count':>8} {'Avg Return':>12} {'Win Rate':>10}")
    print("-" * 60)

    for bucket_name, returns in buckets.items():
        if returns:
            avg_ret = sum(returns) / len(returns)
            win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100
            print(f"{bucket_name:15} {len(returns):>8} {avg_ret:>11.2f}% {win_rate:>9.1f}%")
        else:
            print(f"{bucket_name:15} {0:>8} {'N/A':>12} {'N/A':>10}")

    print()
    print("💡 Expected: Higher confidence → Higher returns and win rate")

# %% [markdown]
# ## Risk Metrics
#
# Let's calculate risk-adjusted metrics (Sharpe ratio):

# %%
if returns_data:
    print("Risk-Adjusted Metrics")
    print(f"{'=' * 80}\n")

    # Calculate standard deviation of returns (volatility)
    returns = [x["return_pct"] for x in returns_data]
    mean_return = sum(returns) / len(returns)

    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance**0.5

    # Calculate Sharpe ratio (assuming 0% risk-free rate for simplicity)
    sharpe_ratio = mean_return / std_dev if std_dev > 0 else 0

    print("Risk Metrics:")
    print(f"  - Average Return: {mean_return:.2f}%")
    print(f"  - Standard Deviation: {std_dev:.2f}%")
    print(f"  - Sharpe Ratio: {sharpe_ratio:.2f}")
    print()

    # Interpret Sharpe ratio
    if sharpe_ratio > 2.0:
        print("✅ Excellent risk-adjusted performance (Sharpe > 2.0)")
    elif sharpe_ratio > 1.0:
        print("✅ Good risk-adjusted performance (Sharpe > 1.0)")
    elif sharpe_ratio > 0:
        print("⚠️ Moderate risk-adjusted performance (Sharpe > 0)")
    else:
        print("❌ Poor risk-adjusted performance (Sharpe < 0)")

# %% [markdown]
# ## Price Tracking Table Inspection
#
# Let's inspect the price_tracking table:

# %%
# Get price tracking records
if buy_recs:
    sample_rec = buy_recs[0]

    # Get price tracking records for this recommendation
    tracking_records = repository.get_price_tracking(sample_rec.id)

    if tracking_records:
        print(f"Price Tracking Records for {sample_rec.ticker}")
        print(f"Recommendation ID: {sample_rec.id}")
        print(f"{'=' * 80}\n")

        print(f"Found {len(tracking_records)} price tracking records:")
        print("-" * 60)
        print(f"{'Date':12} {'Price':>10} {'Benchmark':>10} {'Days Since':>12}")
        print("-" * 60)

        for record in tracking_records[:10]:  # Show first 10
            days_since = (record.tracking_date - sample_rec.analysis_date.date()).days
            print(
                f"{record.tracking_date} ${record.price:>9.2f} ${record.benchmark_price:>9.2f} "
                if record.benchmark_price
                else " N/A " * 10 + f"{days_since:>12}"
            )

        print()
        print("💡 Price tracking enables historical performance analysis")
    else:
        print(f"No price tracking records found for {sample_rec.ticker}")
        print("💡 Run price tracking first:")
        print("   uv run python -m src.main track-performance")

# %% [markdown]
# ## Summary
#
# **Key Findings:**
#
# 1. **Price Tracking**: Daily price snapshots stored in `price_tracking` table
# 2. **Return Calculation**: Compares current price vs entry price (from analysis_date)
# 3. **Benchmark Comparison**: Calculates alpha (excess return over SPY/QQQ)
# 4. **Confidence Calibration**: Analyzes if high confidence → high returns
# 5. **Risk Metrics**: Sharpe ratio measures risk-adjusted performance
#
# **Performance Tracking Workflow:**
# 1. `track-performance` command runs daily
# 2. Fetches latest prices for active recommendations
# 3. Stores in `price_tracking` table
# 4. `performance-report` command generates metrics
# 5. Calculates returns, win rate, alpha, Sharpe ratio
#
# **Bug Fixes (December 2025):**
# - ✅ Fixed `current_price = 0` issue (recommendations now have valid prices)
# - ✅ Fixed historical price fetching (uses correct date, not future prices)
# - ✅ Performance tracking now works correctly
#
# **Next Steps:**
# - Deep dive into signal creation logic in notebook 06
# - Explore scoring algorithms and thresholds
