# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NordInvest** is an AI-powered financial analysis and investment recommendation system that generates daily investment signals and portfolio allocation suggestions. It uses a multi-agent CrewAI architecture to analyze global financial markets across fundamental, technical, and sentiment dimensions.

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
uv run python -m src.main analyze --category us_tech_software
```

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
Report Generation (Markdown/JSON)
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

**4. Analysis Modules (src/analysis/)**
- Technical Analysis: Moving averages, RSI, MACD, ATR, volume analysis
- Fundamental Analysis: Earnings growth, margins, debt ratios, valuation metrics
- Signal Synthesis: Multi-factor scoring (35% fundamental, 35% technical, 30% sentiment)

**5. LLM Integration (src/llm/)**
- Token tracking for cost monitoring
- Prompt templates for consistent agent behavior
- Tool adapters for CrewAI integration
- High-level orchestrator for LLM analysis

**6. Configuration System (src/config/)**
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
NordInvest/
├── src/
│   ├── main.py              # CLI entry point
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

### Creating New Agents

1. Create agent class in `src/agents/`
2. Define role, goal, backstory using clear job descriptions
3. Assign custom tools from `src/tools/`
4. Add to crew configuration in `src/agents/crew.py`
5. Create hybrid wrapper if LLM fallback is needed

### Adding New Tools

1. Create tool class in `src/tools/`
2. Inherit from `BaseTool` and implement `_run()` method
3. Register in `ToolRegistry` for agent assignment
4. Add CrewAI adapter in `src/llm/tools.py` if needed for LLM mode

### Data Provider Integration

1. Create provider class inheriting from `DataProvider`
2. Implement required methods: `get_price_data()`, `get_fundamentals()`, etc.
3. Add caching integration via `CacheManager`
4. Register in configuration for selection

### LLM Mode Development

1. Add prompt template in `src/llm/prompts.py`
2. Create CrewAI agent in `src/agents/crewai_agents.py`
3. Wrap with HybridAnalysisAgent for fallback support
4. Ensure token tracking is integrated

## Code Quality Standards

- **Black**: Code formatting (line length: 100)
- **Ruff**: Linting (Pyflakes, pycodestyle, isort, bandit)
- **Pre-commit hooks**: Run automatically on every commit
- No logging f-string interpolation warnings (G004 ignored)

## Development Workflow

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
