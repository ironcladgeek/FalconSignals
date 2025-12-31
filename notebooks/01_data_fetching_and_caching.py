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
# # Data Fetching and Caching Exploration
#
# This notebook explores the data fetching and caching mechanisms in FalconSignals.
#
# **Purpose:**
# - Understand how `ProviderManager` and `CacheManager` work
# - Explore cache directory structure and TTL logic
# - Test different data types: prices, fundamentals, news, sentiment
# - Compare fresh fetch vs cached data
#
# **Key Components:**
# - `ProviderManager`: Coordinates multiple data providers (Yahoo Finance, Alpha Vantage, Finnhub)
# - `CacheManager`: Handles file-based caching with configurable TTL
# - Data normalization pipeline: Converts raw API data to standardized Pydantic models

# %% [markdown]
# ## Setup
#
# Initialize the environment and import necessary modules:

# %%
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Cache directory: {project_root / 'data' / 'cache'}")

# %%
from src.cache.manager import CacheManager
from src.config.loader import load_config
from src.data.provider_manager import ProviderManager

# Initialize configuration
config = load_config()
print("✅ Configuration loaded")
print(f"  - Markets: {', '.join(config.markets.included)}")
print(f"  - Database enabled: {config.database.enabled}")

# %% [markdown]
# ## Initialize Provider and Cache Managers

# %%
# Initialize cache manager
cache_dir = str(Path("data") / "cache")
cache_manager = CacheManager(cache_dir)
print("✅ CacheManager initialized")
print(f"  - Cache directory: {cache_dir}")

# Initialize provider manager
provider_manager = ProviderManager(
    primary_provider=config.data.primary_provider,
    backup_providers=config.data.backup_providers,
    db_path=config.database.db_path,
)
print("✅ ProviderManager initialized")
print("  - Primary provider: Yahoo Finance")

# %% [markdown]
# ## Test 1: Fetch Price Data
#
# Let's fetch price data for AAPL and explore the cache:

# %%
# Fetch price data (this will cache the results)
ticker = "AAPL"
print(f"Fetching price data for {ticker}...")

start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()

price_data = provider_manager.get_stock_prices(ticker=ticker, period="30d")

if price_data:
    print(f"✅ Fetched {len(price_data)} price records for {ticker}")
    print("\nLast 5 records:")
    for price in price_data[-5:]:
        print(f"  {price.date}: ${price.close:.2f}")  # type: ignore[attr-defined]
else:
    print(f"❌ Failed to fetch price data for {ticker}")

# %% [markdown]
# ## Explore Cache Directory Structure
#
# Let's see what files were created in the cache:

# %%
cache_dir_path = Path("data") / "cache"
print("Cache directory contents:")
print(f"{'=' * 60}")

# List all cache files
for cache_file in sorted(cache_dir_path.rglob("*.json")):
    relative_path = cache_file.relative_to(cache_dir_path)
    file_size = cache_file.stat().st_size / 1024  # KB
    modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
    print(f"{relative_path}")
    print(f"  Size: {file_size:.2f} KB")
    print(f"  Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

# %% [markdown]
# ## Inspect Cache File Contents
#
# Let's look at the structure of a cached price data file:

# %%
# Find the AAPL price cache file
aapl_cache_files = list(cache_dir_path.rglob(f"*{ticker}*.json"))
if aapl_cache_files:
    cache_file = aapl_cache_files[0]
    print(f"Inspecting: {cache_file.name}")
    print(f"{'=' * 60}")

    with open(cache_file, "r") as f:
        cache_data = json.load(f)

    print("Cache data structure:")
    print(f"  - Keys: {list(cache_data.keys())}")
    print(f"  - Timestamp: {cache_data.get('timestamp', 'N/A')}")
    print(f"  - Data type: {type(cache_data.get('data', {}))}")

    # Show sample data (first 2 records)
    data = cache_data.get("data", {})
    if isinstance(data, dict) and "prices" in data:
        prices = data["prices"][:2]
        print("\nSample price records (first 2):")
        print(json.dumps(prices, indent=2))
else:
    print(f"No cache file found for {ticker}")

# %% [markdown]
# ## Test 2: Cache Hit vs Cache Miss
#
# Let's test the cache behavior by fetching the same data again:

# %%
import time

# First fetch (should use cache)
start_time = time.time()
price_data_cached = provider_manager.get_stock_prices(ticker=ticker, period="30d")
cached_fetch_time = time.time() - start_time

print(f"✅ Cached fetch completed in {cached_fetch_time:.4f} seconds")
print("  - This should be very fast (< 0.1s) because data is cached")

# %% [markdown]
# ## Test 3: Fetch Fundamental Data
#
# Let's fetch fundamental data and see how it's cached:

# %%
print(f"Fetching fundamental data for {ticker}...")

fundamentals = provider_manager.primary_provider.get_fundamentals(ticker)  # type: ignore[attr-defined]

if fundamentals:
    print(f"✅ Fetched fundamental data for {ticker}")
    print("\nKey metrics:")
    print(
        f"  - Market Cap: ${fundamentals.market_cap / 1e9:.2f}B"
        if fundamentals.market_cap
        else "  - Market Cap: N/A"
    )
    print(
        f"  - P/E Ratio: {fundamentals.pe_ratio:.2f}"
        if fundamentals.pe_ratio
        else "  - P/E Ratio: N/A"
    )
    print(f"  - EPS: ${fundamentals.eps:.2f}" if fundamentals.eps else "  - EPS: N/A")
    print(
        f"  - Revenue: ${fundamentals.revenue / 1e9:.2f}B"
        if fundamentals.revenue
        else "  - Revenue: N/A"
    )
    print(
        f"  - Profit Margin: {fundamentals.profit_margin * 100:.2f}%"
        if fundamentals.profit_margin
        else "  - Profit Margin: N/A"
    )
else:
    print(f"❌ Failed to fetch fundamental data for {ticker}")

# %% [markdown]
# ## Test 4: Fetch News and Sentiment
#
# Let's fetch news data and explore sentiment analysis:

# %%
print(f"Fetching news for {ticker}...")

news = provider_manager.get_news(ticker, limit=5)

if news:
    print(f"✅ Fetched {len(news)} news articles for {ticker}")
    print("\nLatest news:")
    for i, article in enumerate(news[:3], 1):
        print(f"\n{i}. {article.title}")
        print(f"   Source: {article.source}")
        print(f"   Published: {article.published_date}")
        print(f"   Sentiment: {article.sentiment}")
        print(
            f"   URL: {article.url[:80]}..." if len(article.url) > 80 else f"   URL: {article.url}"
        )
else:
    print(f"❌ Failed to fetch news for {ticker}")

# %% [markdown]
# ## Test 5: Cache TTL Exploration
#
# Let's explore how cache TTL (Time-To-Live) works:

# %%
# Check cache TTL for different data types
cache_ttls = {
    "Price Data (market hours)": 3600,  # 1 hour
    "Price Data (overnight)": 86400,  # 24 hours
    "News": 14400,  # 4 hours
    "Fundamentals": 86400,  # 24 hours
    "Financial Statements": 604800,  # 7 days
}

print("Cache TTL Configuration:")
print(f"{'=' * 60}")
for data_type, ttl_seconds in cache_ttls.items():
    hours = ttl_seconds / 3600
    print(f"{data_type:30} {hours:6.1f} hours ({ttl_seconds:,} seconds)")

# %% [markdown]
# ## Test 6: Multiple Tickers Batch Fetch
#
# Let's test fetching data for multiple tickers:

# %%
tickers = ["AAPL", "MSFT", "GOOGL"]
print(f"Fetching price data for {len(tickers)} tickers: {', '.join(tickers)}")
print(f"{'=' * 60}")

for ticker in tickers:
    start_time = time.time()
    price_data = provider_manager.get_stock_prices(ticker=ticker, period="30d")
    fetch_time = time.time() - start_time

    if price_data:
        print(f"✅ {ticker:6} - {len(price_data):3} records - {fetch_time:.4f}s")
    else:
        print(f"❌ {ticker:6} - Failed - {fetch_time:.4f}s")

# %% [markdown]
# ## Summary
#
# **Key Findings:**
#
# 1. **Cache Structure**: Cache files are stored in `data/cache/` with organized subdirectories
# 2. **TTL Management**: Different data types have different cache lifetimes (1h - 7 days)
# 3. **Performance**: Cached fetches are significantly faster than fresh API calls
# 4. **Data Types**: Price, fundamental, news, and sentiment data are all cached separately
# 5. **Provider Fallback**: ProviderManager can fallback to alternative providers if primary fails
#
# **Next Steps:**
# - Explore historical analysis in notebook 02
# - Test different analysis modes in notebooks 03-04
# - Deep dive into signal creation in notebook 06
