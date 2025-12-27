# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 CRITICAL: DRY Principle (Don't Repeat Yourself)

**MANDATORY FOR ALL DEVELOPMENT**: This project MUST follow the DRY principle rigorously.

**Definition**: Every piece of knowledge should have a single, unambiguous representation in the system.

**Current Status** ⚠️:
- The system currently has **TWO SEPARATE EXECUTION PATHS** for LLM and rule-based modes (documented in `docs/ARCHITECTURE_ANALYSIS.md`)
- This is a **KNOWN VIOLATION** that must be eliminated

**Requirements for New Code**:
1. ✅ **Single execution path** - All analysis modes must converge to one pipeline
2. ✅ **No duplicate logic** - If code exists elsewhere, reuse it
3. ✅ **Single source of truth** - One location for each piece of functionality
4. ✅ **Before writing new code**, check if similar functionality already exists

**Before Committing, Ask**:
- Does this logic already exist elsewhere?
- Can I reuse an existing component?
- Will future changes require modifying code in multiple places?

If YES to questions 1 or 3 → **REFACTOR FIRST, then add feature**

See `docs/roadmap.md` and `docs/ARCHITECTURE_ANALYSIS.md` for detailed DRY violations and refactoring plan.

---

## Project Overview

**FalconSignals** is an AI-powered financial analysis and investment recommendation system that generates daily investment signals and portfolio allocation suggestions. It uses a multi-agent CrewAI architecture to analyze global financial markets across fundamental, technical, and sentiment dimensions.

**Key characteristics:**
- Cost-conscious design: Target €50-90/month operational cost
- Multi-agent AI orchestration using CrewAI
- Dual analysis modes: LLM-powered and Rule-based
- Runs once daily, completing analysis in <15 minutes
- Outputs: Markdown reports, JSON signals, portfolio recommendations
- All 6 phases complete: Full-featured production-ready system

## Essential Commands

### Development Workflow

```bash
# Install dependencies
uv sync

# Format and lint code (run before committing)
uv run poe lint

# Run all pre-commit hooks manually
uv run poe pre-commit

# Run tests
pytest

# Run single test file
pytest tests/path/to/test_file.py

# Run tests with specific pattern
pytest -k "test_pattern_name"
```

### Analysis Commands

```bash
# Quick test (rule-based)
uv run python -m src.main analyze --test

# Quick test (LLM mode)
uv run python -m src.main analyze --test --llm

# Analyze specific tickers
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL

# Analyze with LLM
uv run python -m src.main analyze --ticker INTU --llm

# Analyze market/category
uv run python -m src.main analyze --market us --limit 20
uv run python -m src.main analyze --group us_tech_software
```

**Note**: When database is enabled (default), all analysis runs automatically:
- Create a run session to track the analysis
- Store investment signals immediately after creation (non-blocking)
- Enable partial report generation even if some tickers fail
- Track analysis metadata (mode, tickers, timestamps, status)

### Report Generation Commands

```bash
# Generate report from a specific analysis session (using session ID)
uv run python -m src.main report --session-id 1

# Generate report for all signals from a specific date
uv run python -m src.main report --date 2025-12-04

# Generate JSON report instead of markdown
uv run python -m src.main report --session-id 1 --format json

# Preview report without saving to file
uv run python -m src.main report --session-id 1 --no-save
```

**Database Benefits**:
- ✅ Reports generated even when some tickers fail (partial results saved)
- ✅ Historical report regeneration from stored data
- ✅ Audit trail of all analysis runs
- ✅ Foundation for performance tracking

### Performance Tracking Commands

```bash
# Track prices for active recommendations (run daily)
uv run python -m src.main track-performance

# Track with custom parameters
uv run python -m src.main track-performance --max-age 90  # Track up to 90 days old
uv run python -m src.main track-performance --signals buy,strong_buy,hold,hold_bullish  # Specify signal types
uv run python -m src.main track-performance --benchmark QQQ  # Use QQQ as benchmark

# Generate performance reports
uv run python -m src.main performance-report  # 30-day report (default)
uv run python -m src.main performance-report --period 90  # 90-day report
uv run python -m src.main performance-report --ticker AAPL  # Specific ticker
uv run python -m src.main performance-report --signal buy --mode llm  # Filtered
uv run python -m src.main performance-report --format json  # JSON output
```

**Performance Tracking Features**:
- ✅ Daily price tracking for active recommendations
- ✅ Benchmark comparison (default: SPY)
- ✅ Returns, win rate, alpha, Sharpe ratio calculation
- ✅ Confidence calibration analysis
- ✅ Multiple time periods (7, 30, 90, 180 days)
- ✅ **Bug Fixed**: Now correctly stores and tracks prices (see Bug Fixes section below)

**Important Notes**:
- Default signal filter is `buy,strong_buy` - add `hold,hold_bullish` if tracking those
- Requires valid `current_price` in recommendations (fixed in December 2025)
- Historical recommendations need historical prices (use `scripts/fix_historical_prices.py`)

### Project Configuration

```bash
# Environment variables required
export ANTHROPIC_API_KEY=your_key        # For Claude API (LLM mode)
export FINNHUB_API_KEY=your_key          # For news/sentiment data
export OPENAI_API_KEY=your_key           # Alternative LLM (optional)

# Create local config from template
cp config/default.yaml config/local.yaml
# Edit config/local.yaml with your preferences
```

## Architecture Overview

### High-Level System Design

```
Configuration Layer (YAML/CLI)
    ↓
Data Fetching (Multiple APIs + Caching)
    ↓
Analysis Mode Selection (--llm flag)
    ├─ LLM Mode: CrewAI Multi-Agent System
    │   ├─ Stage 1: Market Scanner (anomaly detection)
    │   ├─ Stage 2: Parallel Analysis (Technical, Fundamental, Sentiment)
    │   └─ Stage 3: Signal Synthesis (weighted scoring + confidence)
    │
    └─ Rule-Based Mode: Direct Analysis Pipeline
        ├─ Technical Indicators (SMA, RSI, MACD, ATR)
        ├─ Fundamental Metrics (P/E, EV/EBITDA, margins)
        └─ Signal Scoring (weighted combination)
    ↓
Database Storage (SQLite) ← Immediate signal persistence
    ├─ Run Sessions (track each analysis run)
    ├─ Recommendations (investment signals)
    ├─ Price Tracking (performance monitoring)
    └─ Analyst Ratings (historical data)
    ↓
Report Generation (Markdown/JSON)
    ├─ From in-memory signals (during analysis)
    └─ From database (historical regeneration)
    ↓
Output (Files, Terminal, Cost Summary)
```

### Core Components

**1. Agent System (src/agents/)**
- Each agent has a specific role with defined goal, backstory, and tools
- Agents collaborate through CrewAI Crew orchestration
- Six agents: Market Scanner, Fundamental Analysis, Technical Analysis, News/Sentiment, Signal Synthesis, Report Generator
- Hybrid wrapper enables fallback to rule-based analysis

**2. Data Layer (src/data/)**
- Abstract `DataProvider` interface for pluggable API sources
- Implementations: Yahoo Finance (primary), Alpha Vantage (backup), Finnhub (news/sentiment)
- Normalization pipeline converts raw API data to standardized Pydantic models

**3. Caching System (src/cache/)**
- File-based cache with JSON (structured data)
- Configurable TTL per data type:
  - Price data: 1h (market hours), 24h (overnight)
  - News: 4h
  - Fundamentals: 24h
  - Financial statements: 7 days
- Minimizes API calls and costs

**4. Database Layer (src/data/db.py, src/data/repository.py)**
- SQLite database (`data/falconsignals.db`) for persistent storage
- **Auto-incrementing INTEGER primary keys** (migrated from UUID for performance)
- Repository pattern for data access with session management
- **Run Sessions**: Track each analysis run with metadata (mode, tickers, status, timestamps)
- **Recommendations**: Store investment signals immediately after creation
- **Price Tracking**: Monitor recommendation performance over time
- **Analyst Ratings**: Accumulate historical analyst data (APIs only provide 3 months)
- Non-blocking storage: DB failures logged as warnings, don't halt analysis
- Enables partial report generation when some tickers fail

**5. Analysis Modules (src/analysis/)**
- Technical Analysis: Moving averages, RSI, MACD, ATR, volume analysis
- Fundamental Analysis: Earnings growth, margins, debt ratios, valuation metrics
- Signal Synthesis: Multi-factor scoring (35% fundamental, 35% technical, 30% sentiment)

**6. LLM Integration (src/llm/)**
- Token tracking for cost monitoring
- Prompt templates for consistent agent behavior
- Tool adapters for CrewAI integration
- High-level orchestrator for LLM analysis

**7. Configuration System (src/config/)**
- YAML-based configuration for market preferences, risk tolerance, capital settings
- LLM configuration (provider, model, temperature)
- Environment variable support for API credentials
- Validation through Pydantic schemas

### Signal Scoring Methodology

**Confidence-Scored Recommendations:**
- **Buy**: Combined score > 70, confidence > 60%
- **Hold**: Combined score 40-70
- **Avoid**: Combined score < 40 or high-risk flags

**Scoring weights:**
- Fundamental score: 35% (earnings, valuations, financial health)
- Technical score: 35% (trend indicators, momentum)
- Sentiment score: 30% (news tone, analyst ratings)

**Confidence calculation:**
- Based on agreement across factors
- Data quality assessment
- LLM reasoning quality (in LLM mode)

## Code Organization

```
FalconSignals/
├── src/
│   ├── main.py              # CLI entry point (16 lines - imports from cli package)
│   ├── cli/                 # Modular CLI structure (NEW - Dec 2025)
│   │   ├── app.py           # Typer app setup and version callback
│   │   ├── commands/        # CLI command modules (15 commands)
│   │   │   ├── analyze.py   # Market analysis command (633 lines)
│   │   │   ├── report.py    # Report generation command (231 lines)
│   │   │   ├── publish.py   # Website publishing command (282 lines)
│   │   │   ├── journal.py   # Trading journal command (721 lines)
│   │   │   ├── watchlist.py # Watchlist management commands (342 lines)
│   │   │   ├── performance.py # Performance tracking commands (304 lines)
│   │   │   ├── download.py  # Price download command (171 lines)
│   │   │   ├── config.py    # Config management commands (94 lines)
│   │   │   └── utils.py     # Utility commands (197 lines)
│   │   ├── helpers/         # Reusable helper functions
│   │   │   ├── filtering.py # Ticker filtering logic (138 lines)
│   │   │   ├── analysis.py  # LLM analysis orchestration (183 lines)
│   │   │   ├── downloads.py # Price data download logic (140 lines)
│   │   │   └── watchlist.py # Watchlist scan logic (176 lines)
│   │   └── shared/          # Shared CLI utilities
│   ├── agents/              # CrewAI agent definitions
│   │   ├── base.py          # BaseAgent and AgentConfig
│   │   ├── crew.py          # AnalysisCrew orchestrator
│   │   ├── scanner.py       # MarketScannerAgent
│   │   ├── analysis.py      # Technical & Fundamental agents
│   │   ├── sentiment.py     # Sentiment & Signal Synthesis agents
│   │   ├── crewai_agents.py # CrewAI Agent factory
│   │   └── hybrid.py        # Hybrid intelligence wrapper
│   ├── tools/               # Custom CrewAI tools for agents
│   │   ├── base.py          # BaseTool and ToolRegistry
│   │   ├── fetchers.py      # PriceFetcherTool, NewsFetcherTool
│   │   ├── analysis.py      # Technical & Sentiment tools
│   │   └── reporting.py     # ReportGeneratorTool
│   ├── data/                # Data providers and fetching logic
│   │   ├── models.py        # Pydantic data models
│   │   ├── providers.py     # Abstract provider
│   │   ├── yahoo_finance.py # Yahoo Finance implementation
│   │   ├── alpha_vantage.py # Alpha Vantage implementation
│   │   ├── finnhub.py       # Finnhub implementation
│   │   ├── screening.py     # Instrument filtering
│   │   └── portfolio.py     # Portfolio state management
│   ├── analysis/            # Technical & fundamental analysis modules
│   │   ├── technical.py     # Technical indicators
│   │   ├── fundamental.py   # Fundamental analysis
│   │   ├── signals.py       # Signal generation
│   │   └── report.py        # Report generation
│   ├── llm/                 # LLM integration (Phase 6)
│   │   ├── integration.py   # LLMAnalysisOrchestrator
│   │   ├── token_tracker.py # Token usage & cost tracking
│   │   ├── prompts.py       # Prompt templates
│   │   └── tools.py         # CrewAI tool adapters
│   ├── cache/               # Caching layer (JSON, Parquet)
│   │   └── manager.py       # Cache management
│   ├── config/              # Configuration system and schemas
│   │   ├── schemas.py       # Pydantic validation
│   │   ├── loader.py        # YAML loading
│   │   └── llm.py           # LLM client initialization
│   ├── pipeline/            # Pipeline orchestration
│   │   └── orchestrator.py  # AnalysisPipeline
│   └── utils/               # Shared utilities
│       ├── logging.py       # Logging setup
│       └── llm_check.py     # LLM configuration check
├── config/
│   ├── default.yaml         # Default configuration template
│   └── local.yaml           # User-specific config (git-ignored)
├── data/
│   ├── cache/               # API response cache (git-ignored)
│   ├── features/            # Preprocessed feature data
│   ├── reports/             # Generated daily reports
│   └── tracking/            # Token usage tracking
├── tests/                   # Test suite
├── pyproject.toml           # Project metadata, dependencies, tool configs
├── uv.lock                  # Dependency lock file
├── .pre-commit-config.yaml  # Git hooks for code quality
└── docs/
    ├── architecture.mermaid     # System architecture diagram
    ├── analyze_workflow.mermaid # Analyze command workflow
    ├── roadmap.md               # Implementation roadmap
    ├── llm_integration.md       # LLM integration guide
    ├── llm_cli_guide.md         # LLM CLI usage
    └── LLM_CONFIGURATION.md     # LLM configuration guide
```

## Key Development Patterns

**⚠️ IMPORTANT**: Before following these patterns, check if functionality already exists. Always prefer **reusing and extending** existing code over creating duplicates.

### Creating New Agents

1. **Check first**: Does a similar agent already exist?
2. Create agent class in `src/agents/`
3. Define role, goal, backstory using clear job descriptions
4. Assign custom tools from `src/tools/`
5. Add to crew configuration in `src/agents/crew.py`
6. Create hybrid wrapper if LLM fallback is needed
7. **DO NOT** create separate orchestration for LLM mode - use existing crew

### Adding New Tools

1. **Check first**: Does `src/tools/` already have this functionality?
2. Create tool class in `src/tools/`
3. Inherit from `BaseTool` and implement `_run()` method
4. Register in `ToolRegistry` for agent assignment
5. Add CrewAI adapter in `src/llm/tools.py` if needed for LLM mode
6. **Ensure** the same tool works for both LLM and rule-based modes

### Data Provider Integration

1. **Check first**: Can existing providers be extended instead?
2. Create provider class inheriting from `DataProvider`
3. Implement required methods: `get_price_data()`, `get_fundamentals()`, etc.
4. Add caching integration via `CacheManager`
5. Register in configuration for selection
6. **Ensure** provider works identically for both analysis modes

### Adding New Analysis Features

**CRITICAL**: The system currently has duplicate execution paths (known issue). When adding features:

1. **Check both paths**: Does the feature need to be added in two places?
2. **If YES** → Document as DRY violation in `docs/ARCHITECTURE_ANALYSIS.md`
3. **Prefer**: Add to `pipeline.py` (rule-based path) as the single source of truth
4. **Avoid**: Adding feature only to LLM path (`llm/integration.py`) or vice versa
5. **Future**: These paths will be unified - design features to work in both contexts

## Code Quality Standards

- **Black**: Code formatting (line length: 100)
- **Ruff**: Linting (Pyflakes, pycodestyle, isort, bandit)
- **Pre-commit hooks**: Run automatically on every commit
- No logging f-string interpolation warnings (G004 ignored)

## Development Workflow

### Commit Guidelines

**IMPORTANT: Keep commits small and focused!**

Each commit should:
- Address a **single task or feature**
- Include **2-4 files** maximum (ideally)
- Have a clear, descriptive message
- Be easy to review and revert if needed

**Why small commits matter:**
- Easier to track changes in git history
- Simpler code reviews
- Faster to identify bugs via `git bisect`
- Cleaner rollbacks when needed

**Examples of GOOD commits:**
```bash
# Single feature, few files
git commit -m "feat(agents): add RSI calculation to technical agent"
# Files: src/agents/analysis.py, tests/unit/agents/test_analysis.py

# Bug fix, minimal scope
git commit -m "fix(cache): correct TTL calculation for overnight data"
# Files: src/cache/manager.py

# Documentation update
git commit -m "docs: add LLM troubleshooting section"
# Files: docs/llm_cli_guide.md, README.md
```

**Examples of BAD commits (avoid these):**
```bash
# Too broad, too many files
git commit -m "feat: implement technical analysis"
# Files: 15+ files changed - hard to review!

# Mixing unrelated changes
git commit -m "fix: various fixes and improvements"
# Files: random changes across the codebase
```

**If your commit has 5+ files, ask yourself:**
- Can this be split into multiple logical commits?
- Am I mixing unrelated changes?
- Would this be easy to review?

### Before Committing

1. Run linting and formatting:
   ```bash
   uv run poe lint
   ```

2. Pre-commit hooks will automatically:
   - Fix trailing whitespace
   - Fix missing newlines
   - Validate YAML/TOML syntax
   - Sort imports with Ruff
   - Format code with Black
   - Validate conventional commit message

3. Commit with semantic message:
   ```bash
   git commit -m "feat: add new analysis agent"
   git commit -m "fix: cache expiration logic"
   git commit -m "docs: update architecture documentation"
   ```

### Running Tests

- Single test file: `pytest tests/unit/agents/test_scanner.py`
- With pattern matching: `pytest -k "test_fundamental_scoring"`
- Full test suite: `pytest` (from project root)
- With coverage: `pytest --cov=src`

## Implementation Roadmap

The project follows a 6-phase implementation plan (see `docs/roadmap.md`):

| Phase | Timeline | Status | Focus |
|-------|----------|--------|-------|
| Phase 1 | Days 1-2 | ✅ Complete | Foundation, project setup, config system |
| Phase 2 | Days 3-5 | ✅ Complete | Data layer, caching, API integration |
| Phase 3 | Days 6-9 | ✅ Complete | CrewAI agents, custom tools |
| Phase 4 | Days 10-12 | ✅ Complete | Signal synthesis, reporting |
| Phase 5 | Days 13-14 | ✅ Complete | Integration, testing, deployment |
| Phase 6 | Extended | ✅ Complete | CrewAI & LLM integration |

## Cost Control Strategy

The system is designed to maintain €50-90/month operational cost:

- **Aggressive caching**: Minimize repeated API calls (1-24h TTL per data type)
- **Free tier prioritization**: Yahoo Finance as primary data source
- **Market scan filtering**: In LLM mode, only analyze instruments with anomalies
- **Token tracking**: Real-time cost monitoring with daily/monthly limits
- **Batch processing**: Group requests for efficiency
- **Single daily run**: Not continuous execution
- **Token optimization**: Concise LLM prompts and responses

**Cost breakdown:**
- LLM API: €50-70/month
- Financial Data APIs: €0-20/month (free tiers)
- Compute: €0 (local execution)

## Recent Critical Bug Fixes (December 2025)

### Bug Fix #1: Recommendations Stored with current_price=0

**Problem**: Recommendations were being stored with `current_price = 0.0`, breaking all performance tracking calculations.

**Root Cause**: In `src/pipeline.py`, the `_create_investment_signal()` method defaulted to `current_price = 0.0` and only tried to fetch from cache. If the cache didn't have the price (common for new tickers), it would silently continue with 0.

**Solution**:
1. Added `ProviderManager` to `AnalysisPipeline` as a fallback for price fetching
2. Modified price fetching logic to:
   - Try cache first
   - Fallback to provider if cache is empty
   - Return `None` (skip signal creation) if no valid price available
3. Updated `analyze` and `report` commands to initialize and pass provider_manager

**Files Modified**:
- [src/pipeline.py](src/pipeline.py): Added provider_manager parameter, improved price fetching
- [src/main.py](src/main.py): Initialize provider_manager (lines 690-696, 1148-1154)

**Impact**:
- ✅ All new recommendations have valid `current_price > 0`
- ✅ Signals without prices are skipped (no broken data)
- ✅ Performance tracking metrics now calculate correctly

### Bug Fix #2: Historical Price Fetching

**Problem**: When analyzing historical data (`analysis_date` in the past), the code used current/latest price instead of the historical price at `analysis_date`.

**Example**: KEYS analyzed on 2025-09-10 (price was $170.20) was stored with $209.07 (today's price), making historical analysis inaccurate.

**Solution**:
- Enhanced `_create_investment_signal()` to detect historical vs current analysis
- If `analysis_date < today`, fetch historical price using `provider_manager.get_stock_prices(ticker, start_date, end_date)`
- If `analysis_date == today`, fetch latest price as before

**Files Modified**:
- [src/pipeline.py](src/pipeline.py): Lines 338-437 (historical-aware price fetching)

**Tool Created**:
- [scripts/fix_historical_prices.py](scripts/fix_historical_prices.py): Script to fix existing recommendations

**Fix Existing Data**:
```bash
# Dry run (shows what would be fixed)
uv run python scripts/fix_historical_prices.py

# Actually apply fixes
uv run python scripts/fix_historical_prices.py --apply
```

**Impact**:
- ✅ Historical analysis uses correct prices from `analysis_date`
- ✅ Backtesting accuracy improved
- ✅ Performance tracking baseline prices are accurate

### Bug Fix #3: SignalCreator Historical Price Fetching (December 2025)

**Problem**: Even with Bug Fix #2, `SignalCreator._fetch_historical_price()` was still using incorrect historical prices. It called `provider_manager.get_stock_prices(ticker, period="5d")` which fetches the LAST 5 days from TODAY, not from the historical target date.

**Example**: Analyzing NVDA on 2025-09-10 (price was $177.33) showed warning:
```
WARNING - Exact price for NVDA on 2025-09-10 not found, using most recent in range:
$190.53 from 2025-12-26 00:00:00
```

This leaked future information into historical analysis, breaking backtesting validity.

**Root Cause**: The method fetched recent prices using `period="5d"` without specifying a date range, so the provider returned the last 5 days from the current date, not the historical target date.

**Solution**:
1. Use `PriceDataManager.get_price_at_date()` as primary method (reads from unified CSV storage)
2. Falls back to provider with correct date range: `target_date ± 5 days`
3. Improved logging to distinguish exact vs approximate date matches
4. Added type assertion for pyright compliance

**Files Modified**:
- [src/analysis/signal_creator.py](src/analysis/signal_creator.py): Lines 162-266 (complete rewrite of `_fetch_historical_price`)

**Verification**:
```bash
# Test with historical date
uv run python -m src.main analyze --ticker NVDA --llm --date 2025-09-10

# Should now log:
# INFO - Found exact historical price for NVDA on 2025-09-10: $177.33
# (instead of WARNING about using price from 2025-12-26)
```

**Impact**:
- ✅ Historical analysis now uses correct prices from unified CSV storage
- ✅ No more future information leakage in backtesting
- ✅ Backtesting framework can rely on accurate historical signals
- ✅ Reports generated with `--date` flag show correct historical prices

## Common Troubleshooting

### API Rate Limiting
- Check cache TTL settings in config
- Verify cache is populated from previous runs
- Consider rotating between providers (Yahoo Finance → Alpha Vantage)

### Data Quality Issues
- Check data validation in Pydantic models
- Verify normalization in data processing pipeline
- Review cache for stale data (check TTL settings)

### Test Failures
- Ensure mock data matches expected Pydantic schemas
- Verify API provider mocking in fixtures
- Check cache cleanup between test runs

### LLM Mode Issues
- Verify API key is set: `echo $ANTHROPIC_API_KEY`
- Check token limits in config
- Review fallback behavior in logs
- Enable debug mode: `--debug-llm`

## Additional Resources

- Full roadmap: `docs/roadmap.md` (detailed 6-phase plan with cost analysis)
- System architecture: `docs/architecture.mermaid` (system components and data flow)
- Analyze workflow: `docs/analyze_workflow.mermaid` (command execution flow)
- LLM CLI guide: `docs/llm_cli_guide.md` (LLM mode usage)
- LLM integration: `docs/llm_integration.md` (component details)
- README: `README.md` (quick overview)
- Config template: `config/default.yaml` (configuration options)
