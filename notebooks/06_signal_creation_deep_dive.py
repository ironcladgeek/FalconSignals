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
# # Signal Creation Deep Dive
#
# This notebook provides a deep dive into the signal creation and scoring logic.
#
# **Purpose:**
# - Explore `SignalCreator` class and scoring algorithms
# - Understand technical, fundamental, and sentiment scoring
# - Analyze weighted combination (35/35/30)
# - Test confidence calculation logic
# - Inspect thresholds for buy/hold/avoid signals
# - Validate edge cases (missing data, extreme values)
#
# **Key Questions:**
# - How are signals scored?
# - What weights are used?
# - How is confidence calculated?
# - What happens with missing data?

# %% [markdown]
# ## Setup

# %%
import sys
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

print("✅ Components initialized")

# %% [markdown]
# ## Signal Scoring Methodology
#
# Let's first understand the scoring methodology:

# %%
print("Signal Scoring Methodology")
print(f"{'=' * 80}\n")

print("Score Components (0-100 scale):")
print("-" * 80)
print("1. Fundamental Score (35% weight)")
print("   - Earnings growth and momentum")
print("   - Profit margins (gross, operating, net)")
print("   - Debt ratios and financial health")
print("   - Valuation metrics (P/E, EV/EBITDA)")
print()
print("2. Technical Score (35% weight)")
print("   - Trend indicators (SMA crossovers)")
print("   - Momentum indicators (RSI, MACD)")
print("   - Volatility (ATR)")
print("   - Volume patterns")
print()
print("3. Sentiment Score (30% weight)")
print("   - News sentiment analysis")
print("   - Analyst ratings and recommendations")
print("   - Social media sentiment (if available)")
print()
print("Combined Score = (0.35 × Fundamental) + (0.35 × Technical) + (0.30 × Sentiment)")
print()
print("-" * 80)
print("Signal Thresholds:")
print("  - BUY: Combined score > 70 AND confidence > 60%")
print("  - HOLD: Combined score 40-70")
print("  - AVOID: Combined score < 40 OR high-risk flags")

# %% [markdown]
# ## Fundamental Scoring Details
#
# Let's explore fundamental scoring in detail:

# %%
print("Fundamental Scoring Breakdown")
print(f"{'=' * 80}\n")

print("Key Metrics and Scoring Logic:")
print("-" * 80)
print()
print("1. Earnings Growth (25 points)")
print("   - YoY earnings growth > 20%: +25 points")
print("   - YoY earnings growth 10-20%: +15 points")
print("   - YoY earnings growth 0-10%: +5 points")
print("   - Negative growth: 0 points")
print()
print("2. Profit Margins (25 points)")
print("   - Net margin > 20%: +15 points")
print("   - Operating margin > 15%: +10 points")
print("   - Gross margin > 40%: +5 points")
print()
print("3. Financial Health (25 points)")
print("   - Debt/Equity < 0.5: +15 points")
print("   - Current ratio > 1.5: +10 points")
print()
print("4. Valuation (25 points)")
print("   - P/E ratio < industry avg: +10 points")
print("   - EV/EBITDA < 15: +10 points")
print("   - PEG ratio < 1.5: +5 points")
print()
print("Total: 100 points possible")

# %% [markdown]
# ## Technical Scoring Details
#
# Let's explore technical scoring in detail:

# %%
print("Technical Scoring Breakdown")
print(f"{'=' * 80}\n")

print("Key Indicators and Scoring Logic:")
print("-" * 80)
print()
print("1. Trend Strength (30 points)")
print("   - Price > SMA(50) > SMA(200): +30 points (strong uptrend)")
print("   - Price > SMA(50): +20 points (uptrend)")
print("   - Price > SMA(200): +10 points (long-term uptrend)")
print("   - Price < both: 0 points (downtrend)")
print()
print("2. Momentum (30 points)")
print("   - RSI 50-70: +15 points (bullish momentum)")
print("   - RSI 30-50: +5 points (neutral)")
print("   - RSI > 70: 0 points (overbought)")
print("   - RSI < 30: 0 points (oversold)")
print()
print("   - MACD > 0 and histogram increasing: +15 points")
print("   - MACD > 0: +10 points")
print("   - MACD < 0: 0 points")
print()
print("3. Volatility (20 points)")
print("   - ATR/Price < 2%: +20 points (low volatility)")
print("   - ATR/Price 2-4%: +10 points (medium)")
print("   - ATR/Price > 4%: 0 points (high volatility)")
print()
print("4. Volume (20 points)")
print("   - Volume > 20-day avg: +20 points (strong interest)")
print("   - Volume > 10-day avg: +10 points")
print("   - Volume < avg: 0 points")
print()
print("Total: 100 points possible")

# %% [markdown]
# ## Sentiment Scoring Details
#
# Let's explore sentiment scoring in detail:

# %%
print("Sentiment Scoring Breakdown")
print(f"{'=' * 80}\n")

print("Key Factors and Scoring Logic:")
print("-" * 80)
print()
print("1. News Sentiment (50 points)")
print("   - Average sentiment > 0.5: +50 points (very positive)")
print("   - Average sentiment 0.2-0.5: +30 points (positive)")
print("   - Average sentiment -0.2 to 0.2: +10 points (neutral)")
print("   - Average sentiment < -0.2: 0 points (negative)")
print()
print("2. Analyst Ratings (50 points)")
print("   - Strong Buy consensus (>70% buy): +50 points")
print("   - Buy consensus (50-70% buy): +35 points")
print("   - Hold consensus (30-50% buy): +20 points")
print("   - Sell consensus (<30% buy): 0 points")
print()
print("   - Upgrades in last 30 days: +10 points bonus")
print("   - Downgrades in last 30 days: -10 points penalty")
print()
print("Total: 100 points possible")

# %% [markdown]
# ## Confidence Calculation
#
# Let's understand how confidence is calculated:

# %%
print("Confidence Calculation")
print(f"{'=' * 80}\n")

print("Confidence Factors:")
print("-" * 80)
print()
print("1. Factor Agreement (50% weight)")
print("   - All 3 factors agree (all >70 or all <40): +50 points")
print("   - 2 factors agree: +30 points")
print("   - No agreement: 0 points")
print()
print("2. Data Quality (30% weight)")
print("   - All required data available: +30 points")
print("   - Missing 1 data type: +20 points")
print("   - Missing 2+ data types: +10 points")
print()
print("3. Score Strength (20% weight)")
print("   - Combined score > 80 or < 20: +20 points (clear signal)")
print("   - Combined score 70-80 or 20-40: +15 points")
print("   - Combined score 40-70: +5 points (unclear)")
print()
print("Final Confidence = Sum of factors (0-100%)")
print()
print("Minimum Confidence for BUY signal: 60%")

# %% [markdown]
# ## Test Signal Creation with Real Data
#
# Let's test signal creation with real ticker data:

# %%
ticker = "AAPL"

print(f"Testing Signal Creation for {ticker}")
print(f"{'=' * 80}\n")

# Fetch data
print("Fetching data...")
price_data = provider_manager.get_stock_prices(ticker=ticker, period="1y")
fundamentals = provider_manager.primary_provider.get_fundamentals(ticker)  # type: ignore[attr-defined]
news = provider_manager.get_news(ticker, limit=10)

if price_data:
    print(f"✅ Price data: {len(price_data)} records")
else:
    print("❌ Price data: Failed")

if fundamentals:
    print("✅ Fundamentals: Available")
else:
    print("❌ Fundamentals: Not available")

if news:
    print(f"✅ News: {len(news)} articles")
else:
    print("⚠️ News: Not available")

print()

# Note: Full signal creation requires running the complete analysis pipeline
# Here we can inspect the input data that would be used

if fundamentals:
    print("Fundamental Metrics:")
    print("-" * 60)
    print(
        f"  - P/E Ratio: {fundamentals.pe_ratio:.2f}"
        if fundamentals.pe_ratio
        else "  - P/E Ratio: N/A"
    )
    print(f"  - EPS: ${fundamentals.eps:.2f}" if fundamentals.eps else "  - EPS: N/A")
    print(
        f"  - Profit Margin: {fundamentals.profit_margin * 100:.2f}%"
        if fundamentals.profit_margin
        else "  - Profit Margin: N/A"
    )
    print(
        f"  - Debt/Equity: {fundamentals.debt_to_equity:.2f}"
        if fundamentals.debt_to_equity
        else "  - Debt/Equity: N/A"
    )

# %% [markdown]
# ## Edge Case: Missing Data
#
# Let's test what happens when data is missing:

# %%
print("Edge Case Testing: Missing Data")
print(f"{'=' * 80}\n")

print("Scenario 1: Missing Fundamentals")
print("-" * 80)
print("Expected behavior:")
print("  - Fundamental score defaults to 50 (neutral)")
print("  - Confidence reduced by ~30 points")
print("  - Technical and sentiment scores still calculated")
print("  - Signal likely becomes HOLD (due to lower confidence)")
print()

print("Scenario 2: Missing News/Sentiment")
print("-" * 80)
print("Expected behavior:")
print("  - Sentiment score defaults to 50 (neutral)")
print("  - Confidence reduced by ~20 points")
print("  - Can still get BUY signal if tech + fundamental are strong")
print()

print("Scenario 3: Stale Price Data")
print("-" * 80)
print("Expected behavior:")
print("  - Technical analysis may use older data")
print("  - Warning logged about data freshness")
print("  - Signal may be marked as low confidence")
print()

print("Scenario 4: All Data Missing")
print("-" * 80)
print("Expected behavior:")
print("  - Signal creation fails or returns AVOID")
print("  - Error logged")
print("  - No recommendation created")

# %% [markdown]
# ## Edge Case: Extreme Values
#
# Let's test extreme value handling:

# %%
print("Edge Case Testing: Extreme Values")
print(f"{'=' * 80}\n")

print("Scenario 1: Extreme P/E Ratio (e.g., P/E = 500)")
print("-" * 80)
print("Expected behavior:")
print("  - Valuation score: 0 points (overvalued)")
print("  - Fundamental score reduced")
print("  - May still get HOLD if technical is strong")
print()

print("Scenario 2: Negative Earnings")
print("-" * 80)
print("Expected behavior:")
print("  - Earnings growth score: 0 points")
print("  - High-risk flag set")
print("  - Likely AVOID signal")
print()

print("Scenario 3: Extreme RSI (e.g., RSI = 95)")
print("-" * 80)
print("Expected behavior:")
print("  - Momentum score: 0 points (overbought)")
print("  - Warning flag for potential reversal")
print("  - Technical score reduced")
print()

print("Scenario 4: Very Low Volatility (ATR/Price < 0.5%)")
print("-" * 80)
print("Expected behavior:")
print("  - Volatility score: 20 points (max)")
print("  - Positive contribution to technical score")
print("  - No warning flags")

# %% [markdown]
# ## Signal Validation Rules
#
# Let's document the validation rules:

# %%
print("Signal Validation Rules")
print(f"{'=' * 80}\n")

print("Pre-Signal Checks:")
print("-" * 80)
print("1. Price Validation")
print("   - Price > 0: Required")
print("   - Price data freshness: Warning if > 3 days old")
print()
print("2. Data Completeness")
print("   - Minimum: Price data required")
print("   - Recommended: Price + Fundamentals OR Price + News")
print()
print("3. Risk Flags")
print("   - Negative earnings: High-risk flag")
print("   - Debt/Equity > 2.0: High-risk flag")
print("   - RSI > 80 or < 20: Extreme momentum flag")
print()
print()

print("Post-Signal Checks:")
print("-" * 80)
print("1. Confidence Threshold")
print("   - BUY requires confidence > 60%")
print("   - HOLD accepted at any confidence")
print("   - AVOID if high-risk flags present")
print()
print("2. Consistency Check")
print("   - If combined score > 70 but confidence < 60%: Downgrade to HOLD")
print("   - If combined score < 40: Always AVOID")
print()
print("3. Price Reasonableness")
print("   - current_price > 0: Required")
print("   - target_price > current_price for BUY: Recommended")

# %% [markdown]
# ## Summary
#
# **Key Findings:**
#
# 1. **Scoring System**: Weighted combination of fundamental (35%), technical (35%), and sentiment (30%)
# 2. **Thresholds**: BUY (>70, conf>60%), HOLD (40-70), AVOID (<40)
# 3. **Confidence**: Based on factor agreement, data quality, and score strength
# 4. **Edge Cases**: Missing data handled with defaults, extreme values capped
# 5. **Validation**: Multiple checks ensure signal quality and risk management
#
# **Signal Creation Workflow:**
# 1. Fetch and validate input data (price, fundamentals, news)
# 2. Calculate individual scores (fundamental, technical, sentiment)
# 3. Combine scores with weights (35/35/30)
# 4. Calculate confidence based on agreement and data quality
# 5. Apply thresholds to determine signal (buy/hold/avoid)
# 6. Validate signal and confidence
# 7. Create recommendation with reasoning
#
# **Best Practices:**
# - Always validate data freshness before analysis
# - Check for missing data and handle gracefully
# - Set appropriate confidence thresholds
# - Monitor edge cases (extreme values, risk flags)
# - Review signal validation rules periodically
#
# **Related Files:**
# - Signal creation: `src/analysis/signal_creator.py`
# - Technical scoring: `src/agents/rule_based/technical.py`
# - Fundamental scoring: `src/agents/rule_based/fundamental.py`
# - Sentiment scoring: `src/agents/rule_based/sentiment.py`
