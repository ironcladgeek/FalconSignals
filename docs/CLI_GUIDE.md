# FalconSignals CLI Guide

Complete guide to using the FalconSignals command-line interface.

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [Commands](#commands)
  - [analyze](#analyze)
  - [collect-fundamentals](#collect-fundamentals)
  - [report](#report)
  - [publish](#publish)
  - [watchlist](#watchlist)
  - [watchlist-scan](#watchlist-scan)
  - [watchlist-report](#watchlist-report)
  - [journal](#journal)
  - [track-performance](#track-performance)
  - [performance-report](#performance-report)
  - [list-categories](#list-categories)
  - [list-portfolios](#list-portfolios)
  - [config-init](#config-init)
  - [validate-config](#validate-config)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)

## Overview

The FalconSignals CLI provides commands for:
- **Analysis**: Generate investment signals using rule-based or LLM-powered methods
- **Data Collection**: Collect and persist fundamental data for historical analysis and backtesting
- **Watchlist Management**: AI-powered technical analysis with tactical trading recommendations
- **Reporting**: Generate reports from historical analysis sessions
- **Performance Tracking**: Track and analyze recommendation performance
- **Configuration**: Initialize and validate configuration files
- **Discovery**: List available categories and portfolios

All commands follow the pattern:
```bash
uv run python -m src.main <command> [options]
```

## Global Options

Available for all commands:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version information |

## Commands

### analyze

Analyze markets and generate investment signals.

**Syntax:**
```bash
uv run python -m src.main analyze [OPTIONS]
```

#### Required Options (choose one)

| Option | Description | Example |
|--------|-------------|---------|
| `--market`, `-m` | Market(s) to analyze | `--market us` |
| `--group`, `-g` | Category or portfolio | `--group us_tech_software` |
| `--ticker`, `-t` | Specific ticker(s) | `--ticker AAPL,MSFT` |
| `--test` | Run test mode with fixtures | `--test` |

#### Optional Settings

| Option | Default | Description |
|--------|---------|-------------|
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |
| `--limit`, `-l` | None | Maximum instruments per market |
| `--format`, `-f` | `markdown` | Output format: `markdown` or `json` |
| `--save-report` / `--no-save-report` | `True` | Save report to disk |
| `--dry-run` | `False` | Run without trades/alerts |
| `--force-reanalysis` | `False` | Force re-analysis even if recommendations exist for date/mode |

#### Analysis Mode Options

| Option | Description |
|--------|-------------|
| `--llm` | Use LLM-powered analysis (costs apply) |
| `--debug-llm` | Save LLM inputs/outputs for debugging |
| `--strategy`, `-s` | Filtering strategy: `anomaly`, `volume`, or `all` (default: `anomaly`) |
| `--force-full-analysis` | Use 'all' strategy regardless of specified strategy |

**Available Filtering Strategies:**
- `anomaly`: Filter tickers with price/volume anomalies (large moves, spikes, extremes)
- `volume`: Filter tickers with significant volume activity and trends
- `all`: Include all tickers without filtering (no cost optimization)

#### Historical Analysis

| Option | Description | Example |
|--------|-------------|---------|
| `--date`, `-d` | Historical date for backtesting | `--date 2024-06-01` |

#### Test Mode

| Option | Default | Description |
|--------|---------|-------------|
| `--test` | - | Offline test mode (zero cost) |
| `--fixture` | `test_ticker_minimal` | Fixture name in `data/fixtures/` |

#### Examples

**Quick Test:**
```bash
# Rule-based test (instant, zero cost)
uv run python -m src.main analyze --test

# LLM test with mock data
uv run python -m src.main analyze --test --llm
```

**Market Analysis:**
```bash
# Analyze US market
uv run python -m src.main analyze --market us

# Multiple markets with limit
uv run python -m src.main analyze --market us,eu --limit 50

# Global markets
uv run python -m src.main analyze --market global
```

**Specific Tickers:**
```bash
# Single ticker (rule-based)
uv run python -m src.main analyze --ticker AAPL

# Multiple tickers (rule-based)
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL

# With LLM analysis
uv run python -m src.main analyze --ticker AAPL --llm

# LLM with debug mode
uv run python -m src.main analyze --ticker AAPL --llm --debug-llm
```

**Filtering Strategy Examples:**
```bash
# Default anomaly strategy
uv run python -m src.main analyze --market us --limit 50

# Volume-based filtering
uv run python -m src.main analyze --market us --limit 50 --strategy volume

# No filtering (analyze all tickers)
uv run python -m src.main analyze --group us_tech_software --strategy all

# Force full analysis (override strategy)
uv run python -m src.main analyze --market us --limit 30 --force-full-analysis

# LLM with volume strategy
uv run python -m src.main analyze --group us_ai_ml --llm --strategy volume
```

**Category Analysis:**
```bash
# Tech software companies
uv run python -m src.main analyze --group us_tech_software

# Multiple categories with limit
uv run python -m src.main analyze --group us_ai_ml,us_cybersecurity --limit 30

# Large-cap stocks
uv run python -m src.main analyze --group us_mega_cap

# Portfolio analysis
uv run python -m src.main analyze --group us_portfolio_balanced_conservative
```

**Historical Analysis (Backtesting):**
```bash
# Historical rule-based analysis
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01

# Historical LLM analysis
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01 --llm

# Historical market analysis
uv run python -m src.main analyze --market us --date 2024-06-01 --limit 20

# Force re-analysis (ignore existing recommendations)
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01 --force-reanalysis
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01 --llm --force-reanalysis
```

**Output Formats:**
```bash
# JSON output
uv run python -m src.main analyze --ticker AAPL --format json

# Don't save report
uv run python -m src.main analyze --ticker AAPL --no-save-report
```

**Custom Configuration:**
```bash
uv run python -m src.main analyze --ticker AAPL --config config/production.yaml
```

---

### collect-fundamentals

Collect comprehensive fundamental data and persist to database for historical analysis and backtesting.

**Syntax:**
```bash
uv run python -m src.main collect-fundamentals [OPTIONS]
```

#### Required Options (choose one)

| Option | Description | Example |
|--------|-------------|---------|
| `--market`, `-m` | Market(s) to collect | `--market us` |
| `--group`, `-g` | Category or portfolio | `--group us_tech_software` |
| `--ticker`, `-t` | Specific ticker(s) | `--ticker AAPL,MSFT` |

#### Optional Settings

| Option | Default | Description |
|--------|---------|-------------|
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |
| `--limit`, `-l` | None | Maximum instruments per market/group |
| `--dry-run` | `False` | Preview without storing to database |
| `--force` | `False` | Re-fetch even if snapshot exists |
| `--date` | Today | Snapshot date (YYYY-MM-DD format) |

#### What Gets Collected

The command fetches and stores comprehensive fundamental data from multiple sources:

**Data Sources:**
- **Alpha Vantage**: Company overview, earnings estimates, financial ratios
- **Finnhub**: Analyst ratings and consensus
- **Yahoo Finance**: Current prices, technical metrics, market data

**Stored Data:**
- Complete fundamental snapshot (as JSON)
- 29 flattened key metrics for efficient querying:
  - Valuation: P/E ratio, PEG ratio, Price-to-Book, Price-to-Sales, EV/Revenue, EV/EBITDA
  - Profitability: Profit margin, Operating margin, ROE, ROA
  - Growth: Quarterly earnings growth, Quarterly revenue growth
  - Analyst data: Target price, ratings breakdown, total analysts
  - Price context: Latest price, price change %, trend

#### Examples

**Basic Collection:**
```bash
# Collect for specific tickers (today's date)
uv run python -m src.main collect-fundamentals --ticker AAPL,MSFT,GOOGL

# Collect for a market
uv run python -m src.main collect-fundamentals --market us --limit 50

# Collect for a category
uv run python -m src.main collect-fundamentals --group us_tech_software

# Collect for multiple markets
uv run python -m src.main collect-fundamentals --market us,eu --limit 30
```

**Preview Mode:**
```bash
# Dry run to see what would be collected
uv run python -m src.main collect-fundamentals --ticker AAPL,MSFT --dry-run

# Preview market collection
uv run python -m src.main collect-fundamentals --market nordic --dry-run
```

**Force Refresh:**
```bash
# Re-fetch even if snapshot exists for today
uv run python -m src.main collect-fundamentals --ticker AAPL --force

# Force refresh for entire group
uv run python -m src.main collect-fundamentals --group us_mega_cap --force
```

**Historical Snapshots:**
```bash
# Collect snapshot for specific date
uv run python -m src.main collect-fundamentals --ticker AAPL --date 2025-12-01

# Backfill historical data for backtesting
uv run python -m src.main collect-fundamentals --ticker AAPL,MSFT --date 2024-06-01

# Collect group snapshot for historical date
uv run python -m src.main collect-fundamentals --group us_ai_ml --date 2024-12-31
```

**Custom Configuration:**
```bash
uv run python -m src.main collect-fundamentals --ticker AAPL --config config/production.yaml
```

#### Output Example

```
📊 Fundamental Data Collection Pipeline
  Snapshot date: 2026-01-03
  Data sources: Alpha Vantage, Finnhub, Yahoo Finance
  Mode: Specific tickers (3 specified)
  Tickers to process: 3

[1/3] AAPL: Fetching data... ✓ Stored
[2/3] MSFT: ⊘ Skipped (snapshot exists)
[3/3] GOOGL: Fetching data... ✓ Stored

======================================================================
✅ COLLECTION SUMMARY
======================================================================
Successfully stored: 2
Skipped (already exists): 1
Errors: 0
Total processed: 3

💾 Database: data/falconsignals.db

📈 2 fundamental snapshot(s) stored for 2026-01-03
```

#### Use Cases

**Daily Data Collection:**
Run daily to maintain fresh fundamental data snapshots.
```bash
# Collect for watchlist or portfolio
uv run python -m src.main collect-fundamentals --group us_portfolio_balanced_moderate
```

**Backtesting Preparation:**
Backfill historical snapshots for accurate backtesting.
```bash
# Collect historical data points
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-01-01
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-04-01
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-07-01
```

**Research & Analysis:**
Collect comprehensive data for deep-dive research.
```bash
# Collect full sector data
uv run python -m src.main collect-fundamentals --group us_tech_software
```

#### Important Notes

- **Rate Limiting**: Command automatically limits to 1 request per second to respect API limits
- **Database Required**: Database must be enabled in configuration (`database.enabled: true`)
- **Storage Location**: Data stored in `fundamental_snapshots` table
- **Duplicate Protection**: Unique constraint on (ticker, date) prevents duplicate snapshots
- **Skip Behavior**: By default, skips if snapshot exists for date (use `--force` to override)
- **API Costs**: Uses Alpha Vantage Premium API - monitor your usage limits
- **Data Freshness**: Snapshots are point-in-time - daily collection recommended

#### Database Schema

Snapshots are stored with:
- Complete JSON data structure (same as cache files)
- 29 flattened columns with indexes for fast queries
- Foreign key to tickers table
- Unique constraint on (ticker_id, snapshot_date)
- Indexes on: ticker+date, date, P/E ratio, market cap

**Notes:**
- Enables accurate historical backtesting with fundamental context
- Foundation for fundamental-based screening and filtering
- Complements price data for comprehensive analysis
- Can be queried directly via repository methods

---

### report

Generate report from stored database results.

**Syntax:**
```bash
uv run python -m src.main report [OPTIONS]
```

#### Required Options (choose one)

| Option | Description | Example |
|--------|-------------|---------|
| `--session-id` | Run session ID (integer) | `--session-id 1` |
| `--date` | Analysis date | `--date 2025-12-04` |

#### Optional Filtering

| Option | Description | Example |
|--------|-------------|---------|
| `--analysis-mode` | Filter by analysis mode | `--analysis-mode llm` |
| `--signal-type` | Filter by signal type | `--signal-type strong_buy` |
| `--confidence-threshold` | Minimum confidence score (exclusive) | `--confidence-threshold 70` |
| `--final-score-threshold` | Minimum final score (exclusive) | `--final-score-threshold 70` |

**Valid analysis modes:** `llm`, `rule_based`

**Valid signal types:** `strong_buy`, `buy`, `hold_bullish`, `hold`, `hold_bearish`, `sell`, `strong_sell`

#### Optional Settings

| Option | Default | Description |
|--------|---------|-------------|
| `--format` | `markdown` | Output format: `markdown` or `json` |
| `--save` / `--no-save` | `True` | Save report to file |
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |

#### Examples

```bash
# Generate report from specific session
uv run python -m src.main report --session-id 1

# Generate report for specific date
uv run python -m src.main report --date 2025-12-04

# Filter by analysis mode
uv run python -m src.main report --date 2025-12-04 --analysis-mode llm

# Filter by signal type
uv run python -m src.main report --date 2025-12-04 --signal-type strong_buy

# Filter by confidence threshold (only signals with confidence > 70)
uv run python -m src.main report --date 2025-12-04 --confidence-threshold 70

# Filter by final score threshold (only signals with final_score > 80)
uv run python -m src.main report --session-id 1 --final-score-threshold 80

# Combine multiple filters
uv run python -m src.main report --date 2025-12-04 --analysis-mode llm --confidence-threshold 80 --signal-type buy

# JSON format without saving
uv run python -m src.main report --session-id 1 --format json --no-save

# With custom config
uv run python -m src.main report --session-id 1 --config config/local.yaml
```

**Notes:**
- Database must be enabled in configuration
- Session IDs are integers (auto-incremented)
- Reports include recommendations matching the specified filters
- Threshold filters are exclusive (e.g., `--confidence-threshold 70` means confidence > 70)

---

### publish

Publish analysis results to static website.

**Syntax:**
```bash
uv run python -m src.main publish [OPTIONS]
```

#### Required Options (choose one)

| Option | Description | Example |
|--------|-------------|---------|
| `--session-id` | Run session ID | `--session-id 123` |
| `--date` | Analysis date | `--date 2025-12-10` |
| `--ticker` | Specific ticker symbol | `--ticker NVDA` |

#### Optional Filtering

| Option | Description | Example |
|--------|-------------|---------|
| `--analysis-mode` | Filter by analysis mode | `--analysis-mode llm` |
| `--signal-type` | Filter by signal type | `--signal-type strong_buy` |
| `--confidence-threshold` | Minimum confidence score (exclusive) | `--confidence-threshold 70` |
| `--final-score-threshold` | Minimum final score (exclusive) | `--final-score-threshold 70` |

**Valid analysis modes:** `llm`, `rule_based`

**Valid signal types:** `strong_buy`, `buy`, `hold_bullish`, `hold`, `hold_bearish`, `sell`, `strong_sell`

#### Optional Settings

| Option | Default | Description |
|--------|---------|-------------|
| `--build-only` | `False` | Build site but don't deploy to GitHub Pages |
| `--no-build` | `False` | Skip MkDocs build (for testing content) |
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |

#### Examples

```bash
# Publish from session and deploy to GitHub Pages
uv run python -m src.main publish --session-id 123

# Publish all signals from specific date
uv run python -m src.main publish --date 2025-12-10

# Publish only one ticker
uv run python -m src.main publish --ticker NVDA --date 2025-12-10

# Filter by analysis mode
uv run python -m src.main publish --date 2025-12-10 --analysis-mode llm

# Filter by signal type
uv run python -m src.main publish --date 2025-12-10 --signal-type strong_buy

# Filter by confidence threshold (only signals with confidence > 80)
uv run python -m src.main publish --date 2025-12-10 --confidence-threshold 80

# Filter by final score threshold (only signals with final_score > 70)
uv run python -m src.main publish --session-id 123 --final-score-threshold 70

# Combine multiple filters
uv run python -m src.main publish --date 2025-12-10 --analysis-mode llm --confidence-threshold 80 --signal-type buy

# Generate content without building site (for testing)
uv run python -m src.main publish --session-id 123 --no-build

# Build site but don't deploy (for local preview)
uv run python -m src.main publish --session-id 123 --build-only
```

**What Gets Published:**
- Report pages with signals grouped by strength
- Individual ticker history pages
- Tag pages for filtering (by ticker, signal type, date)
- Updated index page with recent reports

**What Gets Removed (Privacy):**
- Portfolio allocations
- Watchlist additions/removals
- Portfolio alerts
- Personal investment amounts

**Notes:**
- Database must be enabled in configuration
- Requires `mkdocs`, `mkdocs-material`, and `mkdocs-awesome-pages-plugin`
- Site is deployed to `gh-pages` branch
- Available at: `https://<username>.github.io/<repo>/`
- See [Website Guide](WEBSITE.md) for detailed setup

---

### watchlist

Manage your watchlist of tickers to monitor.

**Syntax:**
```bash
uv run python -m src.main watchlist [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--add-ticker`, `-a` | Add ticker to watchlist by symbol |
| `--add-recommendation`, `-r` | Add ticker to watchlist by recommendation ID |
| `--remove-ticker`, `-d` | Remove ticker from watchlist |
| `--list`, `-l` | List all tickers in watchlist |
| `--config`, `-c` | Path to configuration file |

#### Examples

```bash
# Add ticker to watchlist
uv run python -m src.main watchlist --add-ticker AAPL

# Add ticker by recommendation ID
uv run python -m src.main watchlist --add-recommendation 123

# Remove ticker from watchlist
uv run python -m src.main watchlist --remove-ticker AAPL

# List all watchlist tickers
uv run python -m src.main watchlist --list
```

**Features:**
- Add tickers by symbol or from recommendation IDs
- Each ticker can only appear once in watchlist
- View watchlist with company names and metadata
- Track when each ticker was added
- Links to recommendation ID if added from analysis

**Watchlist Display:**
When using `--list`, shows:
- Ticker symbol
- Company name
- Recommendation ID (if added from analysis)
- Date added
- Total ticker count

**Notes:**
- Database must be enabled in configuration
- Tickers are validated and company info is stored
- Use `watchlist-scan` to run AI analysis on watchlist tickers
- Use `watchlist-report` to view historical signals

---

### watchlist-scan

Run AI-powered technical analysis on watchlist tickers with tactical trading recommendations.

**Syntax:**
```bash
uv run python -m src.main watchlist-scan [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--ticker`, `-t` | All watchlist tickers | Comma-separated list of specific tickers to scan |
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |

#### Examples

```bash
# Scan all watchlist tickers
uv run python -m src.main watchlist-scan

# Scan specific tickers from watchlist
uv run python -m src.main watchlist-scan --ticker AAPL,NVDA

# Use custom config
uv run python -m src.main watchlist-scan --ticker MSFT --config config/local.yaml
```

**What It Does:**
- **Refreshes price data**: Downloads latest historical prices for all tickers (force refresh)
- Uses AI-powered `AITechnicalAnalysisAgent` with tactical prompt mode
- Analyzes technical indicators, price action, and volume patterns
- Generates actionable recommendations: **Buy**, **Wait**, or **Remove**
- Provides specific trading levels:
  - Entry price (suggested buy price)
  - Stop loss level (risk management)
  - Take profit target (exit strategy)
  - Wait for price (if action is "Wait")
- Stores comprehensive analysis in `watchlist_signals` table

**Analysis Output:**
- Technical score (0-100)
- Confidence level (0-100)
- Recommended action with fact-based rationale
- Specific price levels for trade execution
- Complete analysis stored for historical tracking

**Notes:**
- Requires LLM API key (Anthropic or OpenAI)
- Database must be enabled in configuration
- Automatically downloads fresh price data before analysis (force refresh)
- Tickers must exist in watchlist (use `watchlist --add-ticker` first)
- Results can be viewed with `watchlist-report` command

---

### watchlist-report

Display historical watchlist signals with full analysis details and trading levels.

**Syntax:**
```bash
uv run python -m src.main watchlist-report [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--ticker`, `-t` | All tickers | Filter by specific ticker(s), comma-separated |
| `--days`, `-d` | `30` | Number of days of history to show |
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |

#### Examples

```bash
# Show all recent signals (last 30 days)
uv run python -m src.main watchlist-report

# Show signals for specific ticker
uv run python -m src.main watchlist-report --ticker AAPL

# Show signals for multiple tickers
uv run python -m src.main watchlist-report --ticker AAPL,NVDA,MSFT

# Show last 90 days of history
uv run python -m src.main watchlist-report --days 90

# Combine filters: specific tickers with extended history
uv run python -m src.main watchlist-report --ticker ADBE,CFLT --days 60
```

**Report Contents:**

For each signal, displays:
- **Ticker Symbol**
- **Analysis Date**
- **Action**: Buy, Wait, or Remove
- **Technical Score**: 0-100 rating
- **Confidence**: Analysis confidence level (0-100)
- **Full Rationale**: Complete fact-based reasoning (not truncated)
- **Trading Levels**:
  - Entry Price: Suggested buy price
  - Stop Loss: Risk management level
  - Take Profit: Exit target
  - Wait For Price: Price to wait for (if action is "Wait")

**Display Format:**
- Rich Panel-based display with color coding
- Signals grouped by ticker and sorted by date
- Full rationale text (no truncation)
- Clear presentation of all tactical trading levels

**Notes:**
- Database must be enabled in configuration
- Displays signals from `watchlist_signals` table
- Requires prior execution of `watchlist-scan`
- Supports filtering by single or multiple tickers
- All prices and levels displayed in local currency format

---

### journal

Manage your trading journal with interactive prompts for tracking trades, performance, and P&L.

**Syntax:**
```bash
uv run python -m src.main journal [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--action`, `-a` | Action to perform: `add`, `update`, `close`, `list`, `view`, `performance` |
| `--config`, `-c` | Path to configuration file |

If no action is specified, the command will display an interactive menu.

#### Actions

##### add - Add New Trade

Add a new trade to your journal with interactive prompts.

**Prompts:**
- Ticker symbol
- Entry date (default: today)
- Position type (long/short)
- Entry price
- Currency (default: USD)
- Position size (number of shares)
- Entry fees (default: 0.0)
- Stop loss (optional)
- Take profit (optional)
- Description (optional)
- Recommendation ID (optional - link to analysis)

**Example:**
```bash
uv run python -m src.main journal --action add
```

##### update - Update Open Trade

Update stop loss, take profit, or description for an open trade.

**Prompts:**
- Trade ID
- New stop loss (optional)
- New take profit (optional)
- New description (optional)

**Example:**
```bash
uv run python -m src.main journal --action update
```

##### close - Close Trade

Close an open position and calculate P&L.

**Prompts:**
- Trade ID
- Exit date (default: today)
- Exit price
- Exit fees (default: 0.0)

**Calculation:**
- Automatically calculates profit/loss
- Calculates profit/loss percentage
- Updates trade status to "closed"

**Example:**
```bash
uv run python -m src.main journal --action close
```

##### list - List Trades

Display trades in a formatted table.

**List Types:**
- `open` - Show only open positions
- `closed` - Show only closed positions
- `ticker` - Show all trades for specific ticker
- `all` - Show all trades

**Table Columns:**
- ID, Ticker, Type (long/short)
- Entry Date, Entry Price
- Currency
- Position Size
- Exit Date, Exit Price (if closed)
- Status (open/closed)
- P&L (with currency)
- P&L % (percentage return)

**Example:**
```bash
uv run python -m src.main journal --action list
```

##### view - View Trade Details

Display comprehensive details for a specific trade.

**Shows:**
- Position details (type, status)
- Entry information (date, price, size, fees, total)
- Risk management (stop loss, take profit)
- Exit information (if closed)
- Performance metrics (P&L, P&L %)
- Notes/description
- Timestamps (created, updated)

**Example:**
```bash
uv run python -m src.main journal --action view
```

##### performance - Performance Statistics

Calculate and display comprehensive trading performance metrics with multi-currency support.

**Date Range Filtering:**
- Optional start date (YYYY-MM-DD)
- Optional end date (YYYY-MM-DD)
- Press Enter to analyze all trades

**Realized Performance (Closed Trades):**
- Total closed trades count
- Winning trades and win rate
- Losing trades count
- Total realized P&L
- Average P&L per trade
- Average return percentage
- Average win amount
- Average loss amount
- Profit factor (avg win / avg loss)

**Unrealized Performance (Open Trades):**
- Fetches current prices for all open positions
- Total unrealized P&L (in USD)
- Average unrealized P&L per position (in USD)
- Average unrealized return percentage
- Top 3 best performing positions
- Top 3 worst performing positions (if more than 3)
- Multi-currency display with USD conversion

**Multi-Currency Support:**
- Each position displayed in native currency
- USD equivalent shown in parentheses (if different)
- Exchange rates fetched on-the-fly via Yahoo Finance
- Totals normalized to USD for comparison
- Supports SEK, EUR, USD, and other major currencies

**Overall Performance:**
- Combined P&L (realized + unrealized)

**Example:**
```bash
# All-time performance
uv run python -m src.main journal --action performance

# Performance for specific date range
uv run python -m src.main journal --action performance
# Then enter dates when prompted (e.g., 2025-01-01 to 2025-12-31)
```

**Sample Output:**
```
📊 Unrealized Performance (Open Trades):
  Total open positions: 3
  Total unrealized P&L (USD): $1,274.87
  Average unrealized P&L per position (USD): $424.96

  📈 Top performing open positions:
    1. LUG.ST: SEK 1,040.00 ($94.50 USD) 47.36%
    2. BITTI.HE: EUR 187.96 ($197.80 USD) 121.39%
    3. NVDA: $46.91 (34.54%)
```

#### Complete Examples

```bash
# Interactive mode (shows menu)
uv run python -m src.main journal

# Add a new trade
uv run python -m src.main journal --action add

# Update an existing trade
uv run python -m src.main journal --action update

# Close a trade and calculate P&L
uv run python -m src.main journal --action close

# List all open positions
uv run python -m src.main journal --action list
# Then choose: open

# List all closed trades
uv run python -m src.main journal --action list
# Then choose: closed

# View specific trade details
uv run python -m src.main journal --action view
# Then enter trade ID

# View performance statistics
uv run python -m src.main journal --action performance

# View performance for specific date range
uv run python -m src.main journal --action performance
# Then enter start date: 2025-01-01
# Then enter end date: 2025-12-31

# Use custom config
uv run python -m src.main journal --action add --config config/local.yaml
```

#### Journal Features

**Trade Tracking:**
- Long and short positions
- Entry and exit dates with prices
- Position sizing and fees tracking
- Stop loss and take profit levels
- Link trades to analysis recommendations
- Custom notes/descriptions

**P&L Calculation:**
- Automatic profit/loss calculation on close
- Percentage returns
- Includes all fees (entry and exit)
- Handles long and short positions correctly

**Multi-Currency Support:**
- Track trades in native currencies (USD, SEK, EUR, etc.)
- Display positions in their original currency
- Automatic currency conversion to USD for totals
- Real-time exchange rates from Yahoo Finance
- Fair comparison across different markets

**Risk Management:**
- Track stop loss and take profit levels
- Update risk parameters for open trades
- Monitor position sizing

**Performance Analysis:**
- Win rate and profit factor
- Average wins vs average losses
- Unrealized P&L for open positions
- Date range filtering for period analysis
- Top/worst performers ranking

**Database Storage:**
- All trades stored in `trading_journal` table
- Complete audit trail with timestamps
- Query by ticker, status, or date
- Linked to recommendations via optional foreign key

**Notes:**
- Database must be enabled in configuration
- All trades stored in `trading_journal` table
- Supports multiple currencies (defaults to USD)
- P&L calculated automatically on trade close
- Performance action fetches real-time prices for open positions
- Exchange rates cached during performance calculation
- Can link trades to recommendation IDs for tracking signal performance

---

### track-performance

Track performance of active recommendations by fetching current prices.

**Syntax:**
```bash
uv run python -m src.main track-performance [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--max-age`, `-m` | `180` | Maximum age of recommendations (days) |
| `--signals`, `-s` | `buy,strong_buy` | Signal types to track (comma-separated) |
| `--benchmark`, `-b` | `SPY` | Benchmark ticker for comparison |
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |

#### Examples

```bash
# Track all active buy/strong_buy recommendations
uv run python -m src.main track-performance

# Track recommendations up to 90 days old
uv run python -m src.main track-performance --max-age 90

# Track buy, strong_buy, and hold signals
uv run python -m src.main track-performance --signals buy,strong_buy,hold

# Use NASDAQ (QQQ) as benchmark
uv run python -m src.main track-performance --benchmark QQQ

# Combined options
uv run python -m src.main track-performance --max-age 90 --signals buy,strong_buy,hold --benchmark QQQ
```

**Notes:**
- Should be run daily to maintain accurate performance data
- Fetches current prices from data provider
- Calculates price changes, alpha vs benchmark
- Stores tracking data in `price_tracking` table

---

### performance-report

Generate performance analytics report for tracked recommendations.

**Syntax:**
```bash
uv run python -m src.main performance-report [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--period`, `-p` | `30` | Tracking period in days (7, 30, 90, 180) |
| `--ticker`, `-t` | None | Filter by ticker symbol |
| `--signal`, `-s` | None | Filter by signal type |
| `--mode`, `-m` | None | Filter by analysis mode (rule_based, llm) |
| `--update` / `--no-update` | `True` | Update summary before reporting |
| `--format`, `-f` | `text` | Output format: `text` or `json` |
| `--config`, `-c` | `config/default.yaml` | Path to configuration file |

#### Examples

```bash
# Default 30-day performance report
uv run python -m src.main performance-report

# 90-day performance report
uv run python -m src.main performance-report --period 90

# Performance for specific ticker
uv run python -m src.main performance-report --ticker AAPL

# Performance of buy signals only
uv run python -m src.main performance-report --signal buy

# Performance of LLM recommendations
uv run python -m src.main performance-report --mode llm

# Combined filters
uv run python -m src.main performance-report --period 90 --signal buy --mode llm

# JSON output without updating summary
uv run python -m src.main performance-report --format json --no-update
```

**Notes:**
- Requires prior execution of `track-performance`
- Shows metrics: avg return, win rate, alpha, Sharpe ratio, calibration error
- Can filter by ticker, signal type, or analysis mode

---

### list-categories

List all available US ticker categories.

**Syntax:**
```bash
uv run python -m src.main list-categories
```

**No options required.**

**Output:**
- Organized by category type (Market Cap, Technology, Healthcare, etc.)
- Shows ticker count for each category
- Includes usage examples

**Example:**
```bash
uv run python -m src.main list-categories
```

**Sample Output:**
```
🇺🇸 Available US Ticker Categories:

📊 Market Cap:
  us_mega_cap                      (25 tickers)
  us_large_cap                     (150 tickers)
  ...

💻 Technology:
  us_tech_software                 (45 tickers)
  us_ai_ml                        (30 tickers)
  ...
```

---

### list-portfolios

List all available diversified portfolio categories.

**Syntax:**
```bash
uv run python -m src.main list-portfolios
```

**No options required.**

**Output:**
- Organized by portfolio type (Balanced, Income, Growth, etc.)
- Shows ticker count for each portfolio
- Includes usage examples

**Example:**
```bash
uv run python -m src.main list-portfolios
```

**Sample Output:**
```
💼 Available Diversified Portfolio Categories:

💰 Balanced Portfolios:
  us_portfolio_balanced_conservative    (20 tickers)
  us_portfolio_balanced_moderate        (25 tickers)
  ...

📈 Growth Portfolios:
  us_portfolio_tech_growth             (30 tickers)
  ...
```

---

### config-init

Initialize local configuration from template.

**Syntax:**
```bash
uv run python -m src.main config-init [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o` | `config/local.yaml` | Output path for config file |

#### Examples

```bash
# Create default local.yaml
uv run python -m src.main config-init

# Create config in custom location
uv run python -m src.main config-init --output config/production.yaml
```

**Notes:**
- Creates config file from `config/default.yaml` template
- Edit the generated file to customize settings
- Automatically creates parent directories if needed

---

### validate-config

Validate configuration file.

**Syntax:**
```bash
uv run python -m src.main validate-config [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--config`, `-c` | Auto-detected | Path to configuration file |

#### Examples

```bash
# Validate default config
uv run python -m src.main validate-config

# Validate specific config
uv run python -m src.main validate-config --config config/production.yaml
```

**Sample Output:**
```
✓ Configuration is valid
  Risk tolerance: moderate
  Capital: €2,000.00
  Monthly deposit: €500.00
  Markets: us, nordic
```

---

## Common Workflows

### Daily Analysis Workflow

```bash
# 1. Collect fundamental data for portfolio (daily routine)
uv run python -m src.main collect-fundamentals --group us_portfolio_balanced_moderate

# 2. Analyze market with LLM
uv run python -m src.main analyze --market us --limit 50 --llm

# 3. Track performance of active recommendations
uv run python -m src.main track-performance

# 4. Review performance report
uv run python -m src.main performance-report
```

### Data Collection and Backtesting Workflow

```bash
# 1. Backfill historical fundamental data
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-01-01
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-04-01
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-07-01
uv run python -m src.main collect-fundamentals --ticker NVDA --date 2024-10-01

# 2. Run historical analysis using collected snapshots
uv run python -m src.main analyze --ticker NVDA --date 2024-01-01
uv run python -m src.main analyze --ticker NVDA --date 2024-04-01
uv run python -m src.main analyze --ticker NVDA --date 2024-07-01
uv run python -m src.main analyze --ticker NVDA --date 2024-10-01

# 3. Track performance across time periods
uv run python -m src.main track-performance --max-age 365

# 4. Generate comprehensive backtesting report
uv run python -m src.main performance-report --period 180 --ticker NVDA
```

### Backtesting Workflow

```bash
# 1. Historical analysis
uv run python -m src.main analyze --ticker AAPL,MSFT --date 2024-06-01

# 2. Continue tracking at later dates
uv run python -m src.main analyze --ticker AAPL,MSFT --date 2024-07-01

# 3. Generate performance report
uv run python -m src.main performance-report --period 90
```

### Testing Before Production

```bash
# 1. Test with fixtures
uv run python -m src.main analyze --test
uv run python -m src.main analyze --test --llm

# 2. Test with real data (single ticker)
uv run python -m src.main analyze --ticker AAPL --dry-run

# 3. Validate configuration
uv run python -m src.main validate-config

# 4. Run production analysis
uv run python -m src.main analyze --ticker AAPL
```

### Research Workflow

```bash
# 1. Discover available categories
uv run python -m src.main list-categories
uv run python -m src.main list-portfolios

# 2. Analyze interesting category
uv run python -m src.main analyze --group us_ai_ml --limit 20

# 3. Deep dive with LLM on top picks
uv run python -m src.main analyze --ticker NVDA,AMD --llm --debug-llm

# 4. Review LLM debug outputs
ls -la data/llm_debug/
```

### Watchlist Management Workflow

```bash
# 1. Add tickers to watchlist
uv run python -m src.main watchlist --add-ticker AAPL
uv run python -m src.main watchlist --add-ticker NVDA
uv run python -m src.main watchlist --add-ticker MSFT

# Or add from analysis recommendations
uv run python -m src.main watchlist --add-recommendation 42

# View current watchlist
uv run python -m src.main watchlist --list

# 2. Run AI technical analysis with tactical recommendations
uv run python -m src.main watchlist-scan

# 3. View detailed signals with trading levels
uv run python -m src.main watchlist-report

# 4. Check specific ticker's history
uv run python -m src.main watchlist-report --ticker AAPL --days 90

# 5. Re-scan specific tickers after market moves
uv run python -m src.main watchlist-scan --ticker NVDA,AMD

# 6. Compare multiple tickers
uv run python -m src.main watchlist-report --ticker AAPL,NVDA,MSFT --days 60
```

### Trading Journal Workflow

```bash
# 1. Add a new trade when entering position
uv run python -m src.main journal --action add
# Enter: NVDA, today's date, long, $140.50, 10 shares, etc.

# 2. Update stop loss after market moves
uv run python -m src.main journal --action update
# Enter trade ID, new stop loss: $135.00

# 3. List open positions to monitor
uv run python -m src.main journal --action list
# Choose: open

# 4. Close position when exiting
uv run python -m src.main journal --action close
# Enter trade ID, exit date, exit price: $152.30

# 5. View detailed trade information
uv run python -m src.main journal --action view
# Enter trade ID to see complete details

# 6. Analyze trading performance
uv run python -m src.main journal --action performance
# Review win rate, profit factor, top performers

# 7. Check specific period performance
uv run python -m src.main journal --action performance
# Enter start date: 2025-01-01
# Enter end date: 2025-03-31

# 8. List all closed trades to review history
uv run python -m src.main journal --action list
# Choose: closed

# 9. View trades for specific ticker
uv run python -m src.main journal --action list
# Choose: ticker
# Enter: NVDA
```

### Integrated Trading Workflow

```bash
# Complete workflow from analysis to journal

# 1. Analyze market and get recommendations
uv run python -m src.main analyze --market us --limit 50 --llm

# 2. Add promising ticker to watchlist
uv run python -m src.main watchlist --add-recommendation 123

# 3. Run tactical analysis for entry timing
uv run python -m src.main watchlist-scan --ticker NVDA

# 4. Review entry price and levels
uv run python -m src.main watchlist-report --ticker NVDA

# 5. Enter position and log in journal
uv run python -m src.main journal --action add
# Include recommendation ID: 123

# 6. Monitor and update as needed
uv run python -m src.main journal --action update

# 7. Exit and close trade
uv run python -m src.main journal --action close

# 8. Review performance
uv run python -m src.main journal --action performance
```

---

## Advanced Usage

### Environment Variables

Set these for API access:

```bash
# LLM Provider (choose one)
export ANTHROPIC_API_KEY=your_key
# OR
export OPENAI_API_KEY=your_key

# Data Providers
export ALPHA_VANTAGE_API_KEY=your_key    # Required
export FINNHUB_API_KEY=your_key          # Optional
```

### Configuration Hierarchy

FalconSignals loads configuration in this order (later overrides earlier):

1. `config/default.yaml` (base template)
2. `config/local.yaml` (if exists)
3. Custom config via `--config` flag

### Database Location

Default: `data/falconsignals.db`

Configure in `config/local.yaml`:
```yaml
database:
  enabled: true
  db_path: "data/falconsignals.db"
```

### Output Locations

| Output | Location |
|--------|----------|
| Reports | `data/reports/` |
| LLM Debug | `data/llm_debug/` |
| Cache | `data/cache/` |
| Token Tracking | `data/tracking/` |
| Database | `data/falconsignals.db` |
| Run Log | `data/runs.jsonl` |

### Error Handling

All commands exit with appropriate codes:
- `0`: Success
- `1`: Error (check stderr for details)

Use `--help` on any command for detailed options:
```bash
uv run python -m src.main analyze --help
```

### Performance Tips

1. **Use test mode** for development:
   ```bash
   uv run python -m src.main analyze --test --llm
   ```

2. **Limit scope** for faster results:
   ```bash
   uv run python -m src.main analyze --market us --limit 20
   ```

3. **Use rule-based** for daily bulk analysis:
   ```bash
   uv run python -m src.main analyze --market us
   ```

4. **Use LLM selectively** for deep analysis:
   ```bash
   uv run python -m src.main analyze --ticker AAPL,MSFT --llm
   ```

5. **Cache usage**: Data is cached automatically in `data/cache/`

### Cost Management

**Rule-based mode**: Free (only API costs for data)

**LLM mode costs** (approximate):
- **Per ticker**: €0.50-0.80 (varies by model and data volume)
- **Market scan**: €0.10-0.20
- **Total for 50 tickers**: €25-40

**Tips to reduce costs:**
1. Use two-stage analysis (market scan filters before LLM)
2. Choose cost-effective models (Haiku vs Sonnet)
3. Use `--limit` to cap analysis scope
4. Test with `--test --llm` (zero cost)

### Troubleshooting

**"Database not enabled"**
- Enable database in config: `database.enabled: true`

**"No LLM API key found"**
- Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Or use rule-based mode (remove `--llm` flag)

**"Must specify --session-id or --date"**
- Report command requires one of these filters

**"No anomalies found"**
- Market scan found no trading opportunities
- Use `--force-full-analysis` to analyze anyway
- Or use rule-based mode

**Check logs:**
```bash
tail -f logs/falconsignals.log
```

---

## Related Documentation

- [Configuration Guide](../config/README.md)
- [LLM Configuration](LLM_CONFIGURATION.md)
- [Architecture Overview](architecture.mermaid)
- [Roadmap](roadmap.md)
