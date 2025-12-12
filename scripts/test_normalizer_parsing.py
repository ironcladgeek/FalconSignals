#!/usr/bin/env python3
"""Test normalizer regex parsing."""

from src.analysis.normalizer import AnalysisResultNormalizer

# Test technical parsing
tech_text = """
RSI (14): 80.80
MACD Line: 8.36, Signal: 5.52, Histogram: 2.84
ATR: 6.59
Volume Ratio: 0.84
"""

print("=" * 60)
print("Testing Technical Indicators Parsing")
print("=" * 60)
result = AnalysisResultNormalizer._parse_llm_markdown_for_indicators(tech_text)
print(f"Input text:\n{tech_text}")
print(f"\nParsed result: {result}")
print("Expected: rsi=80.80, macd=8.36, macd_signal=5.52, atr=6.59, volume_ratio=0.84")

# Test fundamental parsing
fund_text = """
Strong Buy: 4 analysts
Buy: 11 analysts
Hold: 5 analysts
Sell: 0 analysts
Strong Sell: 0 analysts
**Total: 20 analysts covering the stock**
"""

print("\n" + "=" * 60)
print("Testing Fundamental Metrics Parsing")
print("=" * 60)
result = AnalysisResultNormalizer._parse_llm_markdown_for_fundamentals(fund_text)
print(f"Input text:\n{fund_text}")
print(f"\nParsed result: {result}")
print("Expected: analyst_consensus with total_analysts=20, bullish_count=15, bullish_pct=75")

# Test sentiment parsing
sent_text = """
**Positive Sentiment**: 7 articles
**Negative Sentiment**: 2 articles
**Neutral Sentiment**: 1 article
Total: 10 news articles analyzed
"""

print("\n" + "=" * 60)
print("Testing Sentiment Parsing")
print("=" * 60)
result = AnalysisResultNormalizer._parse_llm_markdown_for_sentiment(sent_text)
print(f"Input text:\n{sent_text}")
print(f"\nParsed result: {result}")
print("Expected: positive_count=7, negative_count=2, neutral_count=1, total_articles=10")
