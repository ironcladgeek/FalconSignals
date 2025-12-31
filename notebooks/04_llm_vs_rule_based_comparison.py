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
# # LLM vs Rule-Based Analysis Comparison
#
# This notebook compares LLM-powered and rule-based analysis modes in detail.
#
# **Purpose:**
# - Compare signals, scores, and confidence levels between modes
# - Analyze differences in recommendations
# - Inspect agent outputs (LLM mode)
# - Compare execution time and costs
# - Visualize score distributions
#
# **Key Questions:**
# - How do LLM and rule-based modes differ?
# - When does LLM provide better insights?
# - What's the cost/accuracy tradeoff?

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
# ## Analysis Mode Architecture
#
# Let's first understand the architecture of both modes:

# %%
print("Analysis Mode Architecture")
print(f"{'=' * 80}\n")

print("RULE-BASED MODE")
print("-" * 80)
print("Path: src/agents/rule_based/")
print()
print("Components:")
print("  1. TechnicalAnalysisModule")
print("     - Input: Price data (OHLCV)")
print("     - Process: Calculate SMA, RSI, MACD, ATR indicators")
print("     - Output: Technical score (0-100)")
print()
print("  2. FundamentalAnalysisModule")
print("     - Input: Financial statements, ratios")
print("     - Process: Evaluate P/E, EV/EBITDA, margins, growth")
print("     - Output: Fundamental score (0-100)")
print()
print("  3. SentimentAnalysisModule")
print("     - Input: News articles, analyst ratings")
print("     - Process: Sentiment analysis, rating aggregation")
print("     - Output: Sentiment score (0-100)")
print()
print("  4. SignalSynthesisModule")
print("     - Input: All three scores")
print("     - Process: Weighted combination (35/35/30)")
print("     - Output: Final signal (buy/hold/avoid) + confidence")
print()
print()

print("LLM-POWERED MODE")
print("-" * 80)
print("Path: src/agents/llm/ + src/orchestration/unified.py")
print()
print("Components:")
print("  1. Market Scanner Agent (optional)")
print("     - Detects anomalies for focused analysis")
print()
print("  2. Technical Analysis Agent")
print("     - Uses same data as rule-based")
print("     - LLM interprets patterns and trends")
print()
print("  3. Fundamental Analysis Agent")
print("     - Evaluates financial health with reasoning")
print("     - Provides qualitative insights")
print()
print("  4. Sentiment Analysis Agent")
print("     - Analyzes news with natural language understanding")
print("     - Considers context and nuance")
print()
print("  5. Signal Synthesis Agent")
print("     - Combines all insights")
print("     - Provides detailed reasoning for recommendation")

# %% [markdown]
# ## Compare Recommendations from Database
#
# Let's compare actual recommendations from both modes:

# %%
from datetime import timedelta

# Get recent recommendations
from_date = datetime.now() - timedelta(days=30)

# Get rule-based recommendations
rule_based_recs = [
    r
    for r in repository.get_recommendations(from_date=from_date)
    if r.analysis_mode == "rule-based"
]

# Get LLM recommendations
llm_recs = [
    r for r in repository.get_recommendations(from_date=from_date) if r.analysis_mode == "llm"
]

print("Recent Recommendations (last 30 days)")
print(f"{'=' * 80}")
print(f"Rule-based: {len(rule_based_recs)} recommendations")
print(f"LLM-powered: {len(llm_recs)} recommendations")
print()

if rule_based_recs or llm_recs:
    print("Signal Distribution:")
    print("-" * 80)

    # Calculate signal distribution for each mode
    def get_signal_dist(recs):
        dist = {}
        for rec in recs:
            dist[rec.signal] = dist.get(rec.signal, 0) + 1
        return dist

    rb_dist = get_signal_dist(rule_based_recs)
    llm_dist = get_signal_dist(llm_recs)

    all_signals = set(list(rb_dist.keys()) + list(llm_dist.keys()))

    print(f"{'Signal':15} {'Rule-Based':>15} {'LLM-Powered':>15}")
    print("-" * 50)
    for signal in sorted(all_signals):
        rb_count = rb_dist.get(signal, 0)
        llm_count = llm_dist.get(signal, 0)
        rb_pct = (rb_count / len(rule_based_recs) * 100) if rule_based_recs else 0
        llm_pct = (llm_count / len(llm_recs) * 100) if llm_recs else 0

        print(f"{signal.upper():15} {rb_count:6} ({rb_pct:5.1f}%) {llm_count:6} ({llm_pct:5.1f}%)")
else:
    print("⚠️ No recommendations found in database")
    print("💡 Run analysis in both modes:")
    print("   Rule-based: uv run python -m src.main analyze --test")
    print("   LLM-powered: uv run python -m src.main analyze --test --llm")

# %% [markdown]
# ## Compare Confidence Levels
#
# Let's analyze confidence level distributions:

# %%
if rule_based_recs or llm_recs:
    print("Confidence Level Analysis")
    print(f"{'=' * 80}")

    # Calculate average confidence for each mode
    rb_confidences = [r.confidence for r in rule_based_recs if r.confidence]
    llm_confidences = [r.confidence for r in llm_recs if r.confidence]

    if rb_confidences:
        rb_avg = sum(rb_confidences) / len(rb_confidences)
        rb_min = min(rb_confidences)
        rb_max = max(rb_confidences)
        print("\nRule-Based Confidence:")
        print(f"  - Average: {rb_avg:.1f}%")
        print(f"  - Range: {rb_min:.1f}% - {rb_max:.1f}%")
        print(f"  - Count: {len(rb_confidences)}")

    if llm_confidences:
        llm_avg = sum(llm_confidences) / len(llm_confidences)
        llm_min = min(llm_confidences)
        llm_max = max(llm_confidences)
        print("\nLLM-Powered Confidence:")
        print(f"  - Average: {llm_avg:.1f}%")
        print(f"  - Range: {llm_min:.1f}% - {llm_max:.1f}%")
        print(f"  - Count: {len(llm_confidences)}")

    # Distribution by confidence buckets
    if rb_confidences or llm_confidences:
        print("\nConfidence Distribution:")
        print("-" * 80)

        buckets = [(0, 40), (40, 60), (60, 80), (80, 100)]

        def count_in_bucket(confidences, bucket):
            return sum(1 for c in confidences if bucket[0] <= c < bucket[1])

        print(f"{'Bucket':15} {'Rule-Based':>15} {'LLM-Powered':>15}")
        print("-" * 50)

        for bucket in buckets:
            rb_count = count_in_bucket(rb_confidences, bucket) if rb_confidences else 0
            llm_count = count_in_bucket(llm_confidences, bucket) if llm_confidences else 0

            bucket_label = f"{bucket[0]}-{bucket[1]}%"
            print(f"{bucket_label:15} {rb_count:15} {llm_count:15}")

# %% [markdown]
# ## Compare Same Ticker Across Modes
#
# Let's find tickers analyzed in both modes and compare results:

# %%
if rule_based_recs and llm_recs:
    print("Same Ticker Comparison")
    print(f"{'=' * 80}")

    # Find tickers present in both modes
    rb_tickers = {r.ticker for r in rule_based_recs}
    llm_tickers = {r.ticker for r in llm_recs}
    common_tickers = rb_tickers & llm_tickers

    if common_tickers:
        print(f"Found {len(common_tickers)} tickers analyzed in both modes")
        print()

        # Compare top 5 common tickers
        for ticker in sorted(common_tickers)[:5]:
            print(f"\n{ticker}")
            print("-" * 40)

            # Get most recent recommendation from each mode
            rb_rec = sorted(
                [r for r in rule_based_recs if r.ticker == ticker],
                key=lambda x: x.analysis_date,
                reverse=True,
            )[0]

            llm_rec = sorted(
                [r for r in llm_recs if r.ticker == ticker],
                key=lambda x: x.analysis_date,
                reverse=True,
            )[0]

            print(f"{'':20} {'Rule-Based':>20} {'LLM-Powered':>20}")
            print(f"{'Signal':20} {rb_rec.signal.upper():>20} {llm_rec.signal.upper():>20}")
            print(f"{'Confidence':20} {rb_rec.confidence:>19.1f}% {llm_rec.confidence:>19.1f}%")
            print(
                f"{'Analysis Date':20} {rb_rec.analysis_date.strftime('%Y-%m-%d'):>20} {llm_rec.analysis_date.strftime('%Y-%m-%d'):>20}"
            )

            # Compare reasoning (if available)
            if rb_rec.reasoning and llm_rec.reasoning:
                print("\nRule-Based Reasoning:")
                print(f"  {rb_rec.reasoning[:100]}...")
                print("\nLLM Reasoning:")
                print(f"  {llm_rec.reasoning[:100]}...")
    else:
        print("No common tickers found")
        print("💡 Analyze same ticker in both modes for comparison")

# %% [markdown]
# ## Execution Time Analysis
#
# Let's analyze execution times for both modes using session data:

# %%
recent_sessions = repository.get_recent_sessions(limit=50)

if recent_sessions:
    print("Execution Time Analysis")
    print(f"{'=' * 80}")

    # Separate sessions by mode
    rb_sessions = [s for s in recent_sessions if s.analysis_mode == "rule-based" and s.completed_at]
    llm_sessions = [s for s in recent_sessions if s.analysis_mode == "llm" and s.completed_at]

    rb_avg_time: float = 0.0
    llm_avg_time: float = 0.0

    if rb_sessions:
        rb_times = [(s.completed_at - s.created_at).total_seconds() for s in rb_sessions]
        rb_avg_time = sum(rb_times) / len(rb_times)
        print(f"\nRule-Based Sessions ({len(rb_sessions)} total):")
        print(f"  - Average duration: {rb_avg_time:.1f} seconds")
        print(f"  - Range: {min(rb_times):.1f}s - {max(rb_times):.1f}s")

    if llm_sessions:
        llm_times = [(s.completed_at - s.created_at).total_seconds() for s in llm_sessions]
        llm_avg_time = sum(llm_times) / len(llm_times)
        print(f"\nLLM-Powered Sessions ({len(llm_sessions)} total):")
        print(f"  - Average duration: {llm_avg_time:.1f} seconds")
        print(f"  - Range: {min(llm_times):.1f}s - {max(llm_times):.1f}s")

    if rb_sessions and llm_sessions:
        speedup = llm_avg_time / rb_avg_time
        print("\nComparison:")
        print(f"  - LLM is {speedup:.1f}x slower than rule-based")
        print(f"  - Extra time per ticker: ~{(llm_avg_time - rb_avg_time):.1f} seconds")
else:
    print("No session data available")

# %% [markdown]
# ## Cost Analysis
#
# Let's estimate costs for both modes:

# %%
print("Cost Analysis")
print(f"{'=' * 80}\n")

# Rule-based costs
print("Rule-Based Mode:")
print("  - LLM costs: €0 (no LLM calls)")
print("  - API costs: €0-10/month (free tier Yahoo Finance)")
print("  - Total: ~€0-10/month")
print()

# LLM costs (estimated)
print("LLM-Powered Mode:")
print("  - LLM costs: €50-70/month (Claude API)")
print("  - API costs: €0-20/month (free tier + Finnhub)")
print("  - Total: ~€50-90/month")
print()

print("Cost per ticker (estimated):")
print("  - Rule-based: €0.00")
print("  - LLM-powered: €0.10-0.20 (depending on usage)")
print()

print("💡 For cost optimization in LLM mode:")
print("  - Use market scanner to filter tickers (only analyze anomalies)")
print("  - Cache aggressively (reduce redundant API calls)")
print("  - Run once daily (not continuous)")
print("  - Set token limits in config")

# %% [markdown]
# ## Strengths and Weaknesses
#
# Let's summarize the strengths and weaknesses of each mode:

# %%
print("Strengths and Weaknesses")
print(f"{'=' * 80}\n")

print("RULE-BASED MODE")
print("-" * 40)
print("Strengths:")
print("  ✅ Fast execution (1-2s per ticker)")
print("  ✅ Zero LLM costs")
print("  ✅ 100% reproducible results")
print("  ✅ Easy to debug and understand")
print("  ✅ Scales well to many tickers")
print()
print("Weaknesses:")
print("  ❌ Fixed scoring formulas")
print("  ❌ No natural language reasoning")
print("  ❌ Requires code changes to adapt")
print("  ❌ Limited context understanding")
print("  ❌ Can't handle unstructured data")
print()
print()

print("LLM-POWERED MODE")
print("-" * 40)
print("Strengths:")
print("  ✅ Natural language reasoning")
print("  ✅ Contextual understanding")
print("  ✅ Can adapt via prompt changes")
print("  ✅ Handles unstructured data (news)")
print("  ✅ More nuanced analysis")
print()
print("Weaknesses:")
print("  ❌ Slower execution (5-10s per ticker)")
print("  ❌ Monthly LLM costs (€50-70)")
print("  ❌ Slight non-determinism")
print("  ❌ Harder to debug")
print("  ❌ Requires API key and quota")

# %% [markdown]
# ## Use Case Recommendations
#
# When to use each mode:

# %%
print("Use Case Recommendations")
print(f"{'=' * 80}\n")

print("Use RULE-BASED MODE when:")
print("  • You need fast, low-cost analysis")
print("  • Analyzing many tickers (>50)")
print("  • You want deterministic, reproducible results")
print("  • You have clear quantitative criteria")
print("  • Budget is limited (€0-10/month)")
print()

print("Use LLM-POWERED MODE when:")
print("  • You need detailed reasoning and explanations")
print("  • Analyzing few tickers (<20)")
print("  • You want to incorporate unstructured data (news)")
print("  • You value contextual understanding")
print("  • Budget allows for LLM costs (€50-90/month)")
print()

print("HYBRID APPROACH (Recommended):")
print("  1. Use rule-based for initial screening (filter 100s of tickers)")
print("  2. Use LLM for deep dive on top candidates (10-20 tickers)")
print("  3. Get best of both: speed + depth")
print("  4. Keep costs under control")

# %% [markdown]
# ## Summary
#
# **Key Findings:**
#
# 1. **Performance**: Rule-based is 5-10x faster than LLM mode
# 2. **Cost**: Rule-based is essentially free, LLM costs €50-90/month
# 3. **Quality**: LLM provides richer reasoning, rule-based is more consistent
# 4. **Use Cases**: Both have valid use cases depending on requirements
#
# **Recommendation**:
# - Use rule-based as the default for daily analysis
# - Use LLM for deep dives on specific opportunities
# - Consider hybrid approach for optimal cost/quality balance
#
# **Next Steps:**
# - Explore performance tracking in notebook 05
# - Deep dive into signal creation logic in notebook 06
