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
# # Current Analysis Exploration
#
# This notebook explores the current date analysis workflow in FalconSignals.
#
# **Purpose:**
# - Test current analysis (no `--date` flag)
# - Compare rule-based vs LLM analysis paths
# - Inspect signal creation logic
# - Verify latest price fetching
# - Test database storage
#
# **Key Questions:**
# - How does current analysis differ from historical?
# - Are latest prices fetched correctly?
# - What's the difference between LLM and rule-based paths?

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
from src.data.providers import ProviderManager
from src.data.repository import Repository

# Initialize components
config = load_config()
cache_manager = CacheManager(config.cache_dir)
provider_manager = ProviderManager(config, cache_manager)
price_manager = PriceDataManager(provider_manager)
repository = Repository(config.database_url)

print("✅ Components initialized")

# %% [markdown]
# ## Test 1: Fetch Latest Price
#
# Let's verify that current analysis uses the latest available price:

# %%
ticker = "AAPL"

print(f"Fetching latest price for {ticker}")
print(f"{'=' * 60}")

# Fetch latest price data
latest_prices = provider_manager.get_stock_prices(ticker=ticker, period="5d")

if latest_prices and latest_prices.prices:
    # Get the most recent price
    latest_price = latest_prices.prices[-1]

    print("✅ Latest price data:")
    print(f"  - Ticker: {ticker}")
    print(f"  - Date: {latest_price.date}")
    print(f"  - Close: ${latest_price.close:.2f}")
    print(f"  - Volume: {latest_price.volume:,}")
    print(f"  - High: ${latest_price.high:.2f}")
    print(f"  - Low: ${latest_price.low:.2f}")

    # Check how recent this data is
    days_old = (datetime.now().date() - latest_price.date).days
    print(f"\nData freshness: {days_old} days old")

    if days_old == 0:
        print("✅ Data is from today (most recent)")
    elif days_old == 1:
        print("✅ Data is from yesterday (acceptable)")
    elif days_old <= 3:
        print("⚠️ Data is a few days old (check if market is closed)")
    else:
        print("❌ Data is stale (> 3 days old)")
else:
    print(f"❌ Failed to fetch latest price for {ticker}")

# %% [markdown]
# ## Test 2: Current Analysis with SignalCreator
#
# Let's test signal creation using current date (no historical date):

# %%

# Create SignalCreator
signal_creator = SignalCreator(
    provider_manager=provider_manager, price_manager=price_manager, config=config
)

print("Testing SignalCreator with current date")
print(f"{'=' * 60}")

# Mock analysis results for current date
ticker = "AAPL"
current_date = datetime.now()

mock_analysis = {
    "ticker": ticker,
    "analysis_date": current_date,  # Current date (not historical)
    "signal": "buy",
    "confidence": 80.0,
    "fundamental_score": 85.0,
    "technical_score": 75.0,
    "sentiment_score": 80.0,
    "combined_score": 80.0,
    "reasoning": "Strong current fundamentals and positive momentum",
}

print(f"Mock analysis for {ticker} (current date):")
print(f"  - Analysis Date: {mock_analysis['analysis_date'].strftime('%Y-%m-%d')}")
print(f"  - Signal: {mock_analysis['signal'].upper()}")
print(f"  - Confidence: {mock_analysis['confidence']}%")
print(f"  - Combined Score: {mock_analysis['combined_score']}")

# %% [markdown]
# ## Test 3: Rule-Based Analysis Workflow
#
# Let's explore the rule-based analysis path:

# %%
print("Rule-Based Analysis Workflow")
print(f"{'=' * 60}\n")

print("Components in rule-based pipeline:")
print("1. TechnicalAnalysisModule")
print("   - Calculates technical indicators (SMA, RSI, MACD, ATR)")
print("   - Scores: 0-100 based on trend strength")
print()
print("2. FundamentalAnalysisModule")
print("   - Evaluates earnings, margins, debt ratios")
print("   - Scores: 0-100 based on financial health")
print()
print("3. SentimentAnalysisModule")
print("   - Analyzes news sentiment and analyst ratings")
print("   - Scores: 0-100 based on market sentiment")
print()
print("4. SignalSynthesisModule")
print("   - Combines scores: 35% fundamental + 35% technical + 30% sentiment")
print("   - Generates final signal: buy/hold/avoid")
print("   - Calculates confidence based on factor agreement")

# %% [markdown]
# ## Test 4: Inspect Recent Recommendations from Database
#
# Let's check recently created recommendations in the database:

# %%
from datetime import timedelta

# Get recommendations from the last 7 days
from_date = datetime.now() - timedelta(days=7)
to_date = datetime.now()

recent_recs = repository.get_recommendations(from_date=from_date, to_date=to_date)

if recent_recs:
    print(f"Found {len(recent_recs)} recommendations from last 7 days")
    print(f"{'=' * 60}")

    # Group by signal type
    signal_counts = {}
    for rec in recent_recs:
        signal_counts[rec.signal] = signal_counts.get(rec.signal, 0) + 1

    print("\nSignal distribution:")
    for signal, count in sorted(signal_counts.items()):
        print(f"  - {signal.upper():12} {count:3} ({count / len(recent_recs) * 100:.1f}%)")

    # Show top 5 by confidence
    print("\nTop 5 by confidence:")
    top_recs = sorted(recent_recs, key=lambda x: x.confidence, reverse=True)[:5]

    for i, rec in enumerate(top_recs, 1):
        print(f"\n{i}. {rec.ticker:6} - {rec.signal.upper():12}")
        print(f"   Confidence: {rec.confidence}%")
        print(f"   Analysis Date: {rec.analysis_date.strftime('%Y-%m-%d')}")
        print(f"   Current Price: ${rec.current_price:.2f}")
        print(f"   Mode: {rec.analysis_mode}")
else:
    print("No recommendations found in database from last 7 days")
    print("💡 Run some analysis first using:")
    print("   uv run python -m src.main analyze --ticker AAPL")

# %% [markdown]
# ## Test 5: Analysis Session Tracking
#
# Let's explore how analysis sessions are tracked:

# %%
# Get recent analysis sessions
recent_sessions = repository.get_recent_sessions(limit=10)

if recent_sessions:
    print(f"Found {len(recent_sessions)} recent analysis sessions")
    print(f"{'=' * 60}")

    for session in recent_sessions[:5]:
        print(f"\nSession ID: {session.id}")
        print(f"  - Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  - Mode: {session.analysis_mode}")
        print(f"  - Tickers: {session.ticker_filter or 'All'}")
        print(f"  - Status: {session.status}")

        if session.completed_at:
            duration = (session.completed_at - session.created_at).total_seconds()
            print(f"  - Duration: {duration:.1f} seconds")

        # Count recommendations in this session
        session_recs = repository.get_recommendations_by_session(session.id)
        print(f"  - Recommendations: {len(session_recs)}")
else:
    print("No analysis sessions found in database")
    print("💡 Run some analysis first using:")
    print("   uv run python -m src.main analyze --test")

# %% [markdown]
# ## Test 6: Compare Analysis Modes
#
# Let's compare the characteristics of rule-based vs LLM analysis:

# %%
print("Analysis Mode Comparison")
print(f"{'=' * 80}")

comparison = {
    "Aspect": [
        "Speed",
        "Cost",
        "Reproducibility",
        "Reasoning",
        "Adaptability",
        "Data Requirements",
    ],
    "Rule-Based": [
        "Fast (~1-2s per ticker)",
        "Free (no LLM costs)",
        "100% deterministic",
        "Fixed formula-based",
        "Requires code changes",
        "Structured data only",
    ],
    "LLM-Powered": [
        "Slower (~5-10s per ticker)",
        "~€50-70/month",
        "Can vary slightly",
        "Natural language explanations",
        "Adapts via prompts",
        "Can use unstructured data",
    ],
}

# Display comparison table
for i, aspect in enumerate(comparison["Aspect"]):
    print(f"{aspect:20} | {comparison['Rule-Based'][i]:30} | {comparison['LLM-Powered'][i]}")
    if i == 0:
        print("-" * 80)

# %% [markdown]
# ## Test 7: Verify Price Data Accuracy
#
# Let's verify that current analysis uses accurate, up-to-date prices:


# %%
def verify_current_price_accuracy(ticker: str) -> None:
    """Verify that current price data is accurate and recent."""

    print(f"Verifying current price accuracy for {ticker}")
    print(f"{'=' * 60}")

    # Fetch price data
    price_data = provider_manager.get_stock_prices(ticker=ticker, period="5d")

    if price_data and price_data.prices:
        latest = price_data.prices[-1]

        print("✅ Latest price retrieved:")
        print(f"  - Date: {latest.date}")
        print(f"  - Close: ${latest.close:.2f}")

        # Check data freshness
        age_days = (datetime.now().date() - latest.date).days
        print(f"  - Age: {age_days} days")

        # Check if price is reasonable (not zero or negative)
        if latest.close > 0:
            print("  ✅ Price is valid (> 0)")
        else:
            print(f"  ❌ Invalid price: ${latest.close}")

        # Check volume
        if latest.volume > 0:
            print(f"  ✅ Volume is valid: {latest.volume:,}")
        else:
            print("  ⚠️ Volume is zero or missing")

        return True
    else:
        print("❌ Failed to fetch price data")
        return False


# Test with multiple tickers
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    verify_current_price_accuracy(ticker)
    print()

# %% [markdown]
# ## Summary
#
# **Key Findings:**
#
# 1. **Latest Price Fetching**: Current analysis correctly fetches the most recent available price
# 2. **Database Storage**: Recommendations are stored with metadata (session ID, mode, timestamps)
# 3. **Session Tracking**: Each analysis run is tracked as a session with status and timing
# 4. **Mode Comparison**: Rule-based is faster and free, LLM provides richer reasoning
#
# **Current Analysis Workflow:**
# 1. Fetch latest price data (last 5 days to get most recent)
# 2. Use the last available price as `current_price`
# 3. Run analysis (rule-based OR LLM mode)
# 4. Create investment signal with current price
# 5. Store in database with session tracking
#
# **Next Steps:**
# - Compare LLM vs rule-based in detail in notebook 04
# - Explore performance tracking in notebook 05
# - Deep dive into signal scoring in notebook 06
