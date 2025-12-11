# NordInvest CLI Guide

Complete guide to using the NordInvest command-line interface.

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [Commands](#commands)
  - [analyze](#analyze)
  - [report](#report)
  - [publish](#publish)
  - [track-performance](#track-performance)
  - [performance-report](#performance-report)
  - [list-categories](#list-categories)
  - [list-portfolios](#list-portfolios)
  - [config-init](#config-init)
  - [validate-config](#validate-config)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)

## Overview

The NordInvest CLI provides commands for:
- **Analysis**: Generate investment signals using rule-based or LLM-powered methods
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
# 1. Analyze market with LLM
uv run python -m src.main analyze --market us --limit 50 --llm

# 2. Track performance of active recommendations
uv run python -m src.main track-performance

# 3. Review performance report
uv run python -m src.main performance-report
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

NordInvest loads configuration in this order (later overrides earlier):

1. `config/default.yaml` (base template)
2. `config/local.yaml` (if exists)
3. Custom config via `--config` flag

### Database Location

Default: `data/nordinvest.db`

Configure in `config/local.yaml`:
```yaml
database:
  enabled: true
  db_path: "data/nordinvest.db"
```

### Output Locations

| Output | Location |
|--------|----------|
| Reports | `data/reports/` |
| LLM Debug | `data/llm_debug/` |
| Cache | `data/cache/` |
| Token Tracking | `data/tracking/` |
| Database | `data/nordinvest.db` |
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
tail -f logs/nordinvest.log
```

---

## Related Documentation

- [Configuration Guide](../config/README.md)
- [LLM Configuration](LLM_CONFIGURATION.md)
- [Architecture Overview](architecture.mermaid)
- [Roadmap](roadmap.md)
