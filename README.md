# NordInvest

AI-powered financial analysis and investment recommendation system using multi-agent AI orchestration (CrewAI). Analyzes global markets to generate daily investment signals with confidence scores.

📖 **[Complete CLI Documentation](docs/CLI_GUIDE.md)**

## Overview

NordInvest is designed to help investors make informed decisions by providing daily, data-driven investment analysis. The system combines fundamental analysis, technical indicators, and news sentiment to generate actionable investment signals with confidence scores.

**Key Features:**
- 🤖 Multi-agent AI system with 5 specialized analysis agents
- 📊 Dual analysis modes: LLM-powered (AI) and Rule-based (technical indicators)
- 🌐 Static website publishing with MkDocs + GitHub Pages
- 💰 Cost-conscious design: Target €50-90/month operational cost
- 🌍 Global market coverage: 1000+ US, Nordic, and EU instruments
- ⚡ Fast execution: Complete analysis in <15 minutes
- 📈 Confidence-scored recommendations with detailed reasoning

## Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- API keys:
  - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` (required for LLM mode)
  - `ALPHA_VANTAGE_API_KEY` (required - Premium tier recommended for news + earnings)
  - `FINNHUB_API_KEY` (optional - for analyst recommendations)

### Installation

```bash
# Clone and setup
git clone <repository>
cd nordinvest

# Install dependencies
uv sync

# Initialize configuration
uv run python -m src.main config-init

# Edit configuration (optional)
# nano config/local.yaml
```

### Environment Variables

```bash
# LLM API Key (choose one - Anthropic recommended)
export ANTHROPIC_API_KEY=your_key        # For AI-powered analysis
# OR
export OPENAI_API_KEY=your_key           # Alternative to Anthropic

# Financial Data APIs
export ALPHA_VANTAGE_API_KEY=your_key    # Premium tier: 75 requests/min, news + earnings
export FINNHUB_API_KEY=your_key          # Optional: analyst recommendations
```

Or create `.env` file in project root:

```
ANTHROPIC_API_KEY=your_key
FINNHUB_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
```

> **💡 Note on Analysis Modes:**
> - **LLM Mode** (`--llm` flag): AI-powered analysis with enhanced sentiment and qualitative insights
> - **Rule-Based Mode** (default): Technical indicators and quantitative methods
> - Both modes generate valid trading signals

## Usage

### Validate Configuration

```bash
uv run python -m src.main validate-config
```

### Run Analysis

#### Rule-Based Analysis (Default)

```bash
# Quick test
uv run python -m src.main analyze --test

# Analyze specific market
uv run python -m src.main analyze --market us --limit 20

# Analyze global markets
uv run python -m src.main analyze --market global

# Analyze specific stocks
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL

# Analyze by category
uv run python -m src.main analyze --group us_tech_software
uv run python -m src.main analyze --group us_ai_ml,us_cybersecurity --limit 30
```

#### LLM-Powered Analysis 🤖

Use intelligent CrewAI agents with Claude/GPT reasoning:

```bash
# Quick test with LLM
uv run python -m src.main analyze --test --llm

# Single stock with LLM analysis
uv run python -m src.main analyze --ticker INTU --llm

# Multiple stocks with LLM
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL --llm

# With custom config
uv run python -m src.main analyze --ticker INTU --llm --config config/local.yaml

# JSON output instead of Markdown
uv run python -m src.main analyze --ticker INTU --llm --format json

# With LLM debug mode (saves inputs/outputs)
uv run python -m src.main analyze --ticker INTU --llm --debug-llm
```

**What LLM mode does:**
- Activates 5 intelligent agents: Market Scanner, Technical Analyst, Fundamental Analyst, Sentiment Analyst, Signal Synthesizer
- Each agent uses Claude/GPT to reason about the analysis
- Combines insights with proper weighting (35% fundamental, 35% technical, 30% sentiment)
- Tracks token usage and costs in EUR
- Falls back to rule-based analysis if LLM fails

**Cost:** ~€0.65 per stock analyzed (adjustable by model choice)

### List Available Categories

```bash
uv run python -m src.main list-categories
```

### Generate Reports

```bash
# Generate report from cached data
uv run python -m src.main report --date 2024-01-15
```

### Publish to Website

Publish analysis results to a static website:

```bash
# Publish and deploy to GitHub Pages
uv run python -m src.main publish --session-id 123

# Publish specific date
uv run python -m src.main publish --date 2025-12-10

# Build only (no deployment)
uv run python -m src.main publish --session-id 123 --build-only
```

**Features:**
- 🌐 Static site with MkDocs + Material theme
- 🏷️ Tag-based filtering (ticker, signal type, date)
- 🔒 Privacy-first (removes portfolio allocations)
- 🚀 Automated GitHub Actions deployment
- 📱 Responsive design with dark/light mode

See [Website Publishing Guide](docs/WEBSITE.md) for setup and deployment details.

### CLI Help

```bash
uv run python -m src.main --help
uv run python -m src.main analyze --help
```

## Configuration

Create `config/local.yaml` from template:

```bash
uv run python -m src.main config-init --output config/local.yaml
```

Key settings:

```yaml
capital:
  starting_capital_eur: 2000
  monthly_deposit_eur: 500

risk:
  tolerance: moderate              # conservative, moderate, aggressive
  max_position_size_percent: 10
  max_sector_concentration_percent: 20

markets:
  included: [nordic, eu, us]       # Available markets
  included_instruments: [stocks, etfs]

analysis:
  weight_fundamental: 0.35
  weight_technical: 0.35
  weight_sentiment: 0.30

llm:
  provider: anthropic              # anthropic, openai, local
  model: claude-sonnet-4-20250514
  temperature: 0.7
```

## Architecture

NordInvest uses a multi-agent CrewAI architecture:

```
Configuration Layer (YAML/CLI)
    ↓
Data Fetching (Multiple APIs + Caching)
    ↓
Analysis Mode Selection
    ├─ LLM Mode: CrewAI Multi-Agent System
    │   ├─ Market Scanner Agent (anomaly detection, screening)
    │   ├─ Fundamental Analysis Agent (earnings, valuations, growth)
    │   ├─ Technical Analysis Agent (indicators: SMA, RSI, MACD, ATR)
    │   ├─ News & Sentiment Agent (news processing, sentiment scoring)
    │   └─ Signal Synthesis Agent (weighted scoring + confidence)
    │
    └─ Rule-Based Mode: Direct Analysis Pipeline
        ├─ Technical Indicators (SMA, RSI, MACD, ATR)
        ├─ Fundamental Metrics (P/E, EV/EBITDA, margins)
        └─ Signal Scoring (weighted combination)
    ↓
Report Generation (Markdown/JSON)
    ↓
Output (Files, Terminal)
```

For detailed architecture diagrams, see:
- [System Architecture](docs/architecture.mermaid) - Complete system overview
- [Analyze Command Workflow](docs/analyze_workflow.mermaid) - Detailed command flow

## Project Structure

```
nordinvest/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config/              # Configuration system
│   │   ├── schemas.py       # Pydantic validation
│   │   ├── loader.py        # YAML loading
│   │   └── llm.py           # LLM client initialization
│   ├── data/                # Data layer
│   │   ├── models.py        # Pydantic data models
│   │   ├── providers.py     # Abstract provider
│   │   ├── yahoo_finance.py # Yahoo Finance impl
│   │   ├── alpha_vantage.py # Alpha Vantage impl
│   │   ├── finnhub.py       # Finnhub impl (analyst recommendations only)
│   │   ├── screening.py     # Instrument filtering
│   │   ├── normalization.py # Data cleaning
│   │   └── portfolio.py     # Portfolio state
│   ├── cache/               # Caching layer
│   │   └── manager.py       # Cache management
│   ├── agents/              # Agent system
│   │   ├── base.py          # BaseAgent and AgentConfig
│   │   ├── crew.py          # AnalysisCrew orchestrator
│   │   ├── scanner.py       # MarketScannerAgent
│   │   ├── analysis.py      # Technical & Fundamental agents
│   │   ├── sentiment.py     # Sentiment & Signal Synthesis agents
│   │   ├── crewai_agents.py # CrewAI Agent factory
│   │   └── hybrid.py        # Hybrid intelligence wrapper
│   ├── tools/               # Agent tools
│   │   ├── base.py          # BaseTool and ToolRegistry
│   │   ├── fetchers.py      # PriceFetcherTool, NewsFetcherTool
│   │   ├── analysis.py      # Technical & Sentiment tools
│   │   └── reporting.py     # ReportGeneratorTool
│   ├── llm/                 # LLM integration
│   │   ├── integration.py   # LLMAnalysisOrchestrator
│   │   ├── token_tracker.py # Token usage & cost tracking
│   │   ├── prompts.py       # Prompt templates
│   │   └── tools.py         # CrewAI tool adapters
│   ├── analysis/            # Analysis modules
│   │   ├── technical.py     # Technical indicators
│   │   ├── fundamental.py   # Fundamental analysis
│   │   ├── signals.py       # Signal generation
│   │   └── report.py        # Report generation
│   ├── pipeline/            # Pipeline orchestration
│   │   └── orchestrator.py  # AnalysisPipeline
│   └── utils/               # Utilities
│       ├── logging.py       # Logging setup
│       └── llm_check.py     # LLM configuration check
├── config/
│   └── default.yaml         # Configuration template
├── data/
│   ├── cache/               # API response cache
│   ├── features/            # Preprocessed data
│   ├── reports/             # Generated reports
│   └── tracking/            # Token usage tracking
├── tests/                   # Test suite
└── docs/
    ├── architecture.mermaid     # System architecture
    ├── analyze_workflow.mermaid # Analyze command workflow
    ├── roadmap.md               # Implementation plan
    └── CLI_GUIDE.md             # CLI guide
```

## Development

### Code Quality

```bash
# Format and lint
uv run poe lint

# Run pre-commit hooks
uv run poe pre-commit
```

### Testing

```bash
# Run all tests
pytest

# Run single test file
pytest tests/unit/data/test_models.py

# Run with coverage
pytest --cov=src
```

## Troubleshooting

### "API key not found"
```bash
echo $ANTHROPIC_API_KEY
echo $ALPHA_VANTAGE_API_KEY
echo $FINNHUB_API_KEY
```

### "Config file not found"
```bash
uv run python -m src.main config-init
```

### "Cache permission denied"
```bash
mkdir -p data/cache data/features data/reports
```

### "Pre-commit hooks failing"
```bash
uv run poe lint
```

## Documentation

- **[CLI Guide](docs/CLI_GUIDE.md)** - Complete command reference with examples
- **[Configuration Guide](config/README.md)** - Configuration options and best practices
- **[Architecture](docs/architecture.mermaid)** - System architecture diagrams
- **[Roadmap](docs/roadmap.md)** - Development roadmap and completed features

## Technology Stack

| Component | Technology |
|-----------|-----------|
| CLI | Typer |
| Config | Pydantic + YAML |
| Data | Pydantic models |
| Providers | yfinance, requests |
| Caching | JSON (local) |
| AI/LLM | CrewAI + Anthropic/OpenAI |
| Logging | Loguru |
| Package Manager | UV |
| Code Quality | Black, Ruff, Pre-commit |
