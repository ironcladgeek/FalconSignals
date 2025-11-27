# Quick Start: Running Full Market Analysis

This guide shows you how to quickly configure NordInvest to analyze multiple markets.

## Quickest Option: Use Provided Ticker Database (5 minutes)

### Step 1: Update the CLI to use the ticker database

Edit `src/main.py` line 101:

**Before:**
```python
tickers = ["AAPL", "MSFT", "GOOGL"][:2]  # Limit to 2 for testing
```

**After (Option A - US Market, 50 instruments):**
```python
from src.MARKET_TICKERS import get_tickers_for_markets

# Run analysis on 50 US instruments
tickers = get_tickers_for_markets(["us"], limit=50)
```

**After (Option B - Nordic & EU, 30 instruments):**
```python
from src.MARKET_TICKERS import get_tickers_for_markets

# Run analysis on Nordic and EU markets
tickers = get_tickers_for_markets(["nordic", "eu"], limit=30)
```

**After (Option C - All Available Markets):**
```python
from src.MARKET_TICKERS import get_tickers_for_markets

# Run analysis on all available instruments
tickers = get_tickers_for_markets(["nordic", "eu", "us"])
```

### Step 2: Run the analysis

```bash
uv run python -m src.main run
```

## Configuration Options: config/local.yaml

Update market preferences to control filtering:

### Global Markets (All)
```yaml
markets:
  included: [nordic, eu, us]
  included_instruments: [stocks, etfs]
  exclude_penny_stocks: true
  min_liquidity_usd: 1000000
```

### Nordic & EU Focus
```yaml
markets:
  included: [nordic, eu]
  included_instruments: [stocks, etfs]
  exclude_penny_stocks: true
  min_liquidity_usd: 500000  # Lower for smaller markets
```

### US Only
```yaml
markets:
  included: [us]
  included_instruments: [stocks]  # No ETFs
  exclude_penny_stocks: true
  min_liquidity_usd: 2000000
```

### Blue-Chip Only (High Liquidity)
```yaml
markets:
  included: [nordic, eu, us]
  included_instruments: [stocks]
  exclude_penny_stocks: true
  min_liquidity_usd: 10000000  # Very liquid stocks only
```

## Expected Performance

| Configuration | Tickers | Est. Time | Est. Cost |
|---------------|---------|-----------|-----------|
| 10 instruments | 10 | 30-40s | €0.20 |
| 20 instruments | 20 | 1-1.5 min | €0.40 |
| 50 instruments | 50 | 2-3 min | €1.00 |
| 100 instruments | 100 | 4-6 min | €2.00 |
| Full US (200) | 200 | 8-12 min | €4.00 |
| All Markets (350+) | 350 | 15-20 min | €7.00 |

## What Happens During Analysis

1. **Configuration Loading** (2s)
   - Validates market preferences
   - Initializes all 5 agents

2. **Data Fetching** (per ticker)
   - Fetches 60-day price history from Yahoo Finance
   - Caches data for future runs

3. **Analysis** (per ticker)
   - Technical analysis (0.2s)
   - Fundamental analysis (0.3s)
   - Sentiment analysis (0.5s)
   - Signal synthesis (0.1s)

4. **Report Generation** (2-3s)
   - Creates daily report
   - Generates allocation suggestions
   - Logs execution statistics

## Monitoring Progress

Check the logs in real-time:

```bash
# Watch logs as analysis runs (in separate terminal)
tail -f logs/nordinvest.log
```

Or check the run statistics after completion:

```bash
tail -20 data/runs.jsonl
```

## Understanding Results

### 0 Signals Means

The analysis executed successfully but found no instruments meeting the buy/hold thresholds because:
- Market is stable with no major anomalies
- No instruments have strong technical buy signals
- Sentiment is neutral to negative
- Thresholds are conservative (70 for buy)

### Non-Zero Signals Means

Found instruments with:
- Strong price momentum (technical)
- Improving fundamentals or valuation
- Positive news sentiment
- High confidence scores

## Troubleshooting

### "ModuleNotFoundError: No module named 'src.MARKET_TICKERS'"
Make sure you're in the project root directory:
```bash
cd /Users/s0001860/Academy/Projects/NordInvest
uv run python -m src.main run
```

### "Analysis is too slow (>10 minutes for 100 tickers)"
- Reduce number of tickers
- Increase `min_liquidity_usd` to filter fewer instruments
- Check internet connection (data fetching is I/O bound)
- Consider running in parallel (advanced)

### "API Rate Limits"
The application handles retries automatically. If you see rate limit errors:
- Free tier is limited to 25 calls/day for Alpha Vantage
- Use only Yahoo Finance (unlimited free tier)
- Wait 24 hours before retrying

### "Cost exceeded budget"
Check your `cost_limit_eur_per_month` in config:
```yaml
deployment:
  cost_limit_eur_per_month: 100  # Adjust this
```

Estimated costs:
- 100 instruments/day: €50-70/month
- 500 instruments/day: €250-350/month

## Advanced: Custom Ticker Lists

Create your own ticker list in `src.MARKET_TICKERS.py`:

```python
# Add to src.MARKET_TICKERS.py
MY_CUSTOM_TICKERS = [
    "AAPL", "MSFT", "GOOGL",  # US
    "SAP.DE", "ASML.AS",       # EU
    "NOVOB.ST", "ERIC.ST",     # Nordic
]

def get_my_tickers():
    return MY_CUSTOM_TICKERS
```

Then use in `src/main.py`:

```python
from src.MARKET_TICKERS import get_my_tickers

tickers = get_my_tickers()
```

## Next Steps

1. **Try different market configurations:**
   - Start with 10 US tickers
   - Expand to 50 instruments
   - Move to 100+ global instruments

2. **Monitor results:**
   - Track signal quality
   - Adjust thresholds if needed
   - Monitor execution costs

3. **Automate execution:**
   - Schedule daily runs with cron
   - Archive reports
   - Monitor with alerts

4. **Integrate with trading:**
   - Connect to broker APIs
   - Implement execution logic
   - Track portfolio performance

## Key Files

- `src.MARKET_TICKERS.py` - Ticker database (edit to customize)
- `config/local.yaml` - Market configuration
- `src/main.py` - Entry point (line 101 controls tickers)
- `MARKET_CONFIG_GUIDE.md` - Detailed configuration guide

## See Also

- `README.md` - General project information
- `MARKET_CONFIG_GUIDE.md` - Advanced configuration options
- `docs/architecture.mermaid` - System architecture
