# Full Market Analysis Setup

Complete guide to configuring NordInvest for analyzing the full global market.

## Overview

NordInvest now includes:
- **388 global instruments** across 3 markets
  - 75 Nordic market instruments
  - 92 EU market instruments
  - 221 US market instruments

## Quick Setup (5 minutes)

### 1. Edit `src/main.py` (line 101)

Replace:
```python
tickers = ["AAPL", "MSFT", "GOOGL"][:2]
```

With:
```python
from src.MARKET_TICKERS import get_tickers_for_markets
tickers = get_tickers_for_markets(["us"], limit=50)  # 50 US stocks
```

### 2. Run analysis
```bash
uv run python -m src.main run
```

That's it! The application will now analyze 50 US market instruments.

## Configuration Variations

### Analyze Different Market Combinations

**US Market Only (221 instruments)**
```python
tickers = get_tickers_for_markets(["us"])
```
- Time: ~8-12 minutes
- Cost: ~€4

**Nordic & EU Markets (167 instruments)**
```python
tickers = get_tickers_for_markets(["nordic", "eu"])
```
- Time: ~5-8 minutes
- Cost: ~€2.50

**All Global Markets (388 instruments)**
```python
tickers = get_tickers_for_markets(["nordic", "eu", "us"])
```
- Time: ~15-20 minutes
- Cost: ~€7

**Limited Set for Testing (25 instruments)**
```python
tickers = get_tickers_for_markets(["us", "eu"], limit=25)
```
- Time: ~1-1.5 minutes
- Cost: ~€0.50

**Custom Selection**
```python
from src.MARKET_TICKERS import US_TICKERS, EU_TICKERS
tickers = US_TICKERS[:50] + EU_TICKERS[:20]  # 70 instruments
```

## Market Coverage

### Nordic Markets (75 instruments)
- Swedish (Nasdaq Stockholm): 50 instruments
- Finnish (Nasdaq Helsinki): 9 instruments
- Danish (Nasdaq Copenhagen): 10 instruments
- Norwegian (Oslo Børs): 6 instruments

**Major stocks:**
- NOVOB.ST - Novo Nordisk
- ERIC.ST - Ericsson
- VOLV.B - Volvo
- UPM.HE - UPM-Kymmene
- BANG.CO - Bang & Olufsen

### EU Markets (92 instruments)
- German (Xetra): 15 instruments
- French (Euronext Paris): 15 instruments
- Netherlands (Euronext Amsterdam): 15 instruments
- Italy (Borsa Italiana): 10 instruments
- Spain, Belgium, Austria, Switzerland: 37 instruments

**Major stocks:**
- SAP.DE - SAP SE
- ASML.AS - ASML Holding
- LHYFE.PA - LHYFE SA
- ENEL.MI - Enel
- MC.PA - LVMH Moët Hennessy

### US Markets (221 instruments)
- Tech giants: AAPL, MSFT, GOOGL, AMZN, NVDA
- Financials: JPM, BAC, WFC, GS, MS
- Healthcare: JNJ, PFE, MRNA, LLY, ABT
- Consumer: WMT, HD, NKE, SBUX, MCD
- Energy: XOM, CVX, SLB, EOG, MPC
- REITs, ETFs, and sector leaders

**Sample stocks:**
- AAPL - Apple Inc.
- MSFT - Microsoft Corp.
- NVDA - NVIDIA Corp.
- TSLA - Tesla Inc.
- AMZN - Amazon Inc.

## How to Run Different Scenarios

### Scenario 1: Tech Sector Focus
```python
TECH_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN",
    "SAP.DE", "ASML.AS", "ERIC.ST", "NOKIA.HE"
]
tickers = TECH_TICKERS
```

### Scenario 2: Nordic Market Deep Dive
```python
tickers = get_tickers_for_markets(["nordic"])
```

### Scenario 3: European Favorites
```python
tickers = get_tickers_for_markets(["eu"], limit=30)
```

### Scenario 4: Blue Chips Only
```python
BLUE_CHIPS = [
    # US
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    # EU
    "SAP.DE", "ASML.AS", "SHELL.AS", "ENEL.MI",
    # Nordic
    "NOVOB.ST", "ERIC.ST", "NOKIA.HE", "BANG.CO"
]
tickers = BLUE_CHIPS
```

## Performance Expectations

### Time to Complete Analysis
- Setup & Configuration: 2 seconds
- Per ticker analysis: ~2 seconds
- Report generation: 3 seconds
- **Total overhead:** ~5 seconds

**Examples:**
- 10 tickers: 30 seconds
- 25 tickers: 55 seconds
- 50 tickers: 110 seconds (1:50)
- 100 tickers: 210 seconds (3:30)
- 250 tickers: 510 seconds (8:30)
- 388 tickers: 776 seconds (12:56)

### Cost to Run Analysis
- **Fixed cost:** €0.01 per run (fixed LLM calls)
- **Variable cost:** ~€0.01-0.02 per ticker analyzed
- **Total:** €0.01 + (€0.02 × number_of_tickers)

**Examples:**
- 10 tickers: €0.21
- 50 tickers: €1.01
- 100 tickers: €2.01
- 250 tickers: €5.01
- 388 tickers: €7.76

**Monthly cost (daily analysis):**
- 50 tickers/day: €30
- 100 tickers/day: €60
- 250 tickers/day: €150
- 388 tickers/day: €233

## Monitoring Analysis Progress

### Watch logs in real-time
```bash
tail -f logs/nordinvest.log
```

### Check run statistics after completion
```bash
tail -5 data/runs.jsonl | python -m json.tool
```

### See generated reports
```bash
ls -la data/reports/
```

## Customizing Ticker Lists

### Add your own stocks to the database

Edit `src.MARKET_TICKERS.py`:

```python
# Add new custom market
MYPORTFOLIO_TICKERS = [
    "AAPL",      # Apple
    "MSFT",      # Microsoft
    "NOVOB.ST",  # Novo Nordisk
    "SAP.DE",    # SAP
]

# Add to get_tickers_for_markets function
def get_tickers_for_markets(markets, limit=None):
    # ... existing code ...

    if "myportfolio" in markets:
        tickers.extend(MYPORTFOLIO_TICKERS[:limit] if limit else MYPORTFOLIO_TICKERS)

    return tickers
```

Then use:
```python
tickers = get_tickers_for_markets(["myportfolio"])
```

## Troubleshooting

### "Analysis takes too long"
Solutions:
1. Reduce number of tickers
2. Run only one market instead of all three
3. Use `limit=N` parameter to analyze subset

### "Cost is too high"
Solutions:
1. Reduce daily run frequency
2. Analyze fewer tickers
3. Focus on specific sectors/markets

### "0 signals generated"
This is normal! It means:
- No instruments meet the buy threshold
- Market is currently in hold/neutral zone
- Adjust thresholds in config if needed

### "Analysis failed"
Check:
1. Internet connection for data fetching
2. API key availability for LLM
3. Sufficient disk space for cache
4. Check logs: `tail logs/nordinvest.log`

## Automation

### Schedule daily analysis
```bash
# Edit crontab
crontab -e

# Add (run daily at 8 AM UTC)
0 8 * * * cd /Users/s0001860/Academy/Projects/NordInvest && uv run python -m src.main run
```

### Archive reports
```bash
# Keep last 30 days of reports
find data/reports -name "*.md" -mtime +30 -delete
```

## Performance Optimization

### Cache warm-up
First run fetches all prices. Subsequent runs use cache:
```bash
# First run (slow, populates cache)
uv run python -m src.main run

# Second run (fast, uses cache)
uv run python -m src.main run
```

Cache expires based on config:
```yaml
data:
  cache_ttl:
    price_data_market_hours: 1      # 1 hour during market hours
    price_data_overnight: 24        # 24 hours overnight
```

## Files Reference

| File | Purpose |
|------|---------|
| `src.MARKET_TICKERS.py` | 388 global instruments database |
| `QUICK_START_FULL_MARKET.md` | Quick setup guide (5 minutes) |
| `MARKET_CONFIG_GUIDE.md` | Detailed configuration options |
| `src/main.py` | CLI entry point (modify line 101 for tickers) |
| `config/local.yaml` | Market preferences & filtering |
| `MARKET_CONFIG_GUIDE.md` | Advanced options |

## Next Steps

1. ✅ **Read this document** - You're here!
2. 📝 **Edit src/main.py** line 101 with ticker selection
3. 🚀 **Run:** `uv run python -m src.main run`
4. 📊 **Monitor:** Check logs and reports
5. ⚙️ **Configure:** Adjust thresholds in config/local.yaml
6. 🤖 **Automate:** Set up cron for daily runs
7. 📈 **Expand:** Gradually increase market coverage

## Support

- Quick start: `QUICK_START_FULL_MARKET.md`
- Deep dive: `MARKET_CONFIG_GUIDE.md`
- Architecture: `docs/architecture.mermaid`
- General: `README.md`
