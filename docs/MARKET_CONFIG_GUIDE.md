# NordInvest Market Configuration Guide

## How to Configure the App for Full Market Analysis

Currently, the NordInvest application is hardcoded to analyze a limited set of tickers (AAPL, MSFT). To run analysis for the full market, you need to:

1. **Create a market screening system** that fetches available instruments
2. **Configure market preferences** in the YAML configuration
3. **Update the CLI** to use the screening system instead of hardcoded tickers

## Configuration Options

### 1. Market Selection (config/local.yaml)

The configuration file supports multiple market selections:

```yaml
markets:
  included: [nordic, eu, us]  # Options: nordic, eu, us (all markets)
  excluded_markets: []        # Specific markets to exclude

  # Instrument type preferences
  included_instruments: [stocks, etfs, funds]  # Options: stocks, etfs, funds
  exclude_penny_stocks: true
  min_liquidity_usd: 1000000  # Minimum daily trading volume (USD)
```

### Configuration Presets

#### Full Global Market Analysis
```yaml
markets:
  included: [nordic, eu, us]  # All markets
  included_instruments: [stocks, etfs]
  exclude_penny_stocks: true
  min_liquidity_usd: 1000000
```

#### Nordic & EU Only
```yaml
markets:
  included: [nordic, eu]  # European focus
  included_instruments: [stocks, etfs]
  exclude_penny_stocks: true
  min_liquidity_usd: 500000  # Lower threshold for smaller markets
```

#### US Market Only
```yaml
markets:
  included: [us]  # US focus
  included_instruments: [stocks, etfs]
  exclude_penny_stocks: true
  min_liquidity_usd: 2000000
```

#### High-Liquidity Stocks Only
```yaml
markets:
  included: [nordic, eu, us]
  included_instruments: [stocks]  # Exclude ETFs
  exclude_penny_stocks: true
  min_liquidity_usd: 5000000  # Only very liquid stocks
```

## Current Implementation

### Ticker Source: Hardcoded List

**Current behavior in src/main.py:**
```python
tickers = ["AAPL", "MSFT", "GOOGL"][:2]  # Limit to 2 for testing
```

## How to Implement Full Market Analysis

### Option 1: Use a Market Data Provider (Recommended)

You can extend the application to fetch available instruments from a data provider:

```python
# Example: Add a method to DataProvider for instrument listing
def get_instruments(self, market: Market, criteria: ScreeningCriteria) -> list[str]:
    """Fetch list of instruments matching criteria"""
    # Returns list of tickers for screening
```

### Option 2: Create a Ticker Database

Build a local or remote database of tickers for each market:

```python
# Example structure
NORDIC_TICKERS = [
    "AAPL.ST",  # Swedish market
    "NOVOB.ST",
    "VOLV.B",
    # ... hundreds more
]

EU_TICKERS = [
    "SAP.DE",   # German market
    "ASML.AS",  # Dutch market
    # ... thousands more
]

US_TICKERS = [
    "AAPL",
    "MSFT",
    # ... thousands more
]
```

### Option 3: Integrate with Alpha Vantage or Finnhub

These providers have symbol search APIs:

```python
from src.data.alpha_vantage import AlphaVantageProvider

provider = AlphaVantageProvider(api_key="YOUR_KEY")
symbols = provider.get_symbols(keywords="technology", market="US")
```

## Market Information

### Markets Supported

| Market | Code | Description | Min Liquidity |
|--------|------|-------------|---------------|
| Nordic | NORDIC | Sweden, Finland, Denmark, Norway | €500K |
| EU | EU | Germany, France, Netherlands, Italy, etc. | €500K |
| US | US | USA, Canada | $1M |

### Market Identifiers

**Nordic suffixes:**
- `.ST` - Swedish (Nasdaq Stockholm)
- `.HE` - Finnish (Nasdaq Helsinki)
- `.CO` - Danish (Nasdaq Copenhagen)
- `.CSE` - Norwegian (Oslo Børs)

**EU suffixes:**
- `.DE` - German (Xetra)
- `.PA` - French (Euronext Paris)
- `.MI` - Italian (Borsa Italiana)
- `.AS` - Dutch (Euronext Amsterdam)
- `.BR` - Belgian (Euronext Brussels)
- `.VI` - Austrian (Vienna Stock Exchange)

**US suffixes:**
- None - US tickers (NASDAQ, NYSE)

## Estimated Analysis Times

For reference, here are typical analysis times per instrument:

| Component | Time |
|-----------|------|
| Fetch price data | 0.5-1s |
| Technical analysis | 0.2s |
| Fundamental analysis | 0.3s |
| Sentiment analysis | 0.5s |
| Signal synthesis | 0.1s |
| **Total per instrument** | **~2s** |

**Full market analysis estimates:**
- 100 instruments: ~3-4 minutes
- 500 instruments: ~15-20 minutes
- 1000 instruments: ~30-40 minutes
- 5000 instruments: ~2.5-3 hours

## Recommended Implementation

### Phase 1: Extended Ticker List
Replace the hardcoded list with a larger curated list:

```python
# In src/main.py
src.MARKET_TICKERS = {
    "nordic": ["AAPL.ST", "NOVOB.ST", "VOLV.B", ...],  # ~50
    "eu": ["SAP.DE", "ASML.AS", "LHYFE.PA", ...],      # ~100
    "us": ["AAPL", "MSFT", "GOOGL", "AMZN", ...],      # ~500
}

def get_tickers_for_markets(markets: list[str]) -> list[str]:
    """Get ticker list based on configured markets"""
    tickers = []
    for market in markets:
        if market in src.MARKET_TICKERS:
            tickers.extend(src.MARKET_TICKERS[market])
    return tickers
```

### Phase 2: Market Screener Integration
Integrate with screening system:

```python
# In src/main.py
from src.data.screening import InstrumentScreener, ScreeningCriteria
from src.config import Config

def get_market_tickers(config: Config) -> list[str]:
    """Get tickers based on market configuration"""
    criteria = ScreeningCriteria(
        markets=[m.upper() for m in config.markets.included],
        instrument_types=[t.upper() for t in config.markets.included_instruments],
        exclude_penny_stocks=config.markets.exclude_penny_stocks,
        min_volume_usd=config.markets.min_liquidity_usd,
    )

    # Get instruments from provider
    # Filter with screening criteria
    # Return filtered tickers
    return filtered_tickers
```

### Phase 3: Data Provider Integration
Full integration with external APIs:

```python
# Use provider's symbol search
provider = DataProviderFactory.create("yahoo_finance")
tickers = provider.search_instruments(
    market="US",
    sector="Technology",
    min_volume_usd=1000000,
)
```

## Quick Start: Analyze More Markets Now

### To analyze Nordic & EU markets (broader than just US):

1. **Edit config/local.yaml:**
```yaml
markets:
  included: [nordic, eu]  # Change from default
  min_liquidity_usd: 500000  # Adjust for smaller markets
```

2. **Update src/main.py line 101:**
```python
# Change from:
tickers = ["AAPL", "MSFT", "GOOGL"][:2]

# To:
tickers = [
    # Nordic
    "NOVOB.ST", "VOLV.B", "ERIC.ST", "SEB.ST",
    # EU
    "SAP", "ASML", "ASML.AS", "BABA",
]
```

3. **Run:**
```bash
uv run python -m src.main run --config config/local.yaml
```

## Cost Considerations

**API Costs per analysis:**
- Yahoo Finance: FREE (unlimited)
- Alpha Vantage: 25 calls/day free (or $20/month for unlimited)
- Finnhub: 60 calls/minute free

**For full market analysis:**
- 100 instruments/day: ~€50-70/month LLM cost
- 500 instruments/day: ~€250-350/month LLM cost
- 1000 instruments/day: ~€500-700/month LLM cost

## Next Steps

1. Create a ticker database file or API integration
2. Implement market screening function
3. Update CLI to fetch tickers dynamically
4. Test with different market configurations
5. Monitor API costs and execution times
6. Optimize for your specific market focus

## See Also

- `config/local.yaml` - Configuration template
- `src/data/screening.py` - Market screening logic
- `src/data/providers.py` - Data provider interface
- `src/main.py` - CLI entry point with hardcoded tickers
