# NordInvest

AI-powered financial analysis and investment recommendation system using multi-agent AI orchestration (CrewAI). Analyzes global markets to generate daily investment signals with confidence scores.


## Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- API keys (free tiers supported):
  - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` (for LLM)
  - `FINNHUB_API_KEY` (optional, for news/sentiment)
  - `ALPHA_VANTAGE_API_KEY` (optional, for backup data)

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

### Configuration

Create `config/local.yaml` from template:

```bash
uv run python -m src.main config-init --output config/local.yaml
```

Key settings in `config/local.yaml`:

```yaml
capital:
  starting_capital_eur: 2000
  monthly_deposit_eur: 500

risk:
  tolerance: moderate              # conservative, moderate, aggressive
  max_position_size_percent: 10
  max_sector_concentration_percent: 20

markets:
  included: [nordic, eu]           # nordic, eu, us
  included_instruments: [stocks, etfs]

analysis:
  weight_fundamental: 0.35
  weight_technical: 0.35
  weight_sentiment: 0.30
```

### Environment Variables

```bash
# LLM API Key (choose one - Anthropic recommended)
export ANTHROPIC_API_KEY=your_key        # For AI-powered analysis
# OR
export OPENAI_API_KEY=your_key           # Alternative to Anthropic

# Optional (for extended features)
export FINNHUB_API_KEY=your_key          # For news and sentiment data
export ALPHA_VANTAGE_API_KEY=your_key    # For backup market data
```

Or create `.env` file in project root:

```
ANTHROPIC_API_KEY=your_key
FINNHUB_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
```

> **💡 Note on LLM Configuration:**
> - **With LLM** (ANTHROPIC_API_KEY or OPENAI_API_KEY): AI-powered analysis with enhanced sentiment and qualitative insights
> - **Without LLM**: Automatic fallback to rule-based analysis using technical indicators and quantitative methods
> - Both modes generate valid trading signals - see [docs/LLM_CONFIGURATION.md](docs/LLM_CONFIGURATION.md) for details
> - The system will display clear warnings when running in rule-based mode

## Usage

### Validate Configuration

```bash
uv run python -m src.main validate-config
```

Output:
```
✓ Configuration is valid
  Risk tolerance: moderate
  Capital: €2,000.00
  Markets: nordic, eu
  Instruments: stocks, etfs
  Buy threshold: 70.0
  Cost limit: €100.00/month
```

### Run Analysis

#### Rule-Based Analysis (Default)

```bash
# Analyze specific market
uv run python -m src.main analyze --market us --limit 20

# Analyze global markets
uv run python -m src.main analyze --market global

# Analyze specific stocks
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL

# Dry run (no trades/alerts)
uv run python -m src.main analyze --ticker INTU --dry-run
```

#### LLM-Powered Analysis (New in Phase 6) 🤖

Use intelligent CrewAI agents with Claude/GPT reasoning:

```bash
# Single stock with LLM analysis
uv run python -m src.main analyze --ticker INTU --llm

# Multiple stocks with LLM
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL --llm

# With custom config
uv run python -m src.main analyze --ticker INTU --llm --config config/local.yaml

# JSON output instead of Markdown
uv run python -m src.main analyze --ticker INTU --llm --format json

# Without saving report to disk
uv run python -m src.main analyze --ticker INTU --llm --no-save-report
```

**What LLM mode does:**
- Activates 5 intelligent agents: Market Scanner, Technical Analyst, Fundamental Analyst, Sentiment Analyst, Signal Synthesizer
- Each agent uses Claude/GPT to reason about the analysis
- Combines insights with proper weighting (35% fundamental, 35% technical, 30% sentiment)
- Tracks token usage and costs in EUR
- Falls back to rule-based analysis if LLM fails
- Generates investment recommendations with detailed reasoning

**Cost:** ~€0.065 per stock analyzed (adjustable by model choice)

### Generate Reports

```bash
# Generate report from cached data
uv run python -m src.main report --date 2024-01-15
```

### CLI Help

```bash
uv run python -m src.main --help
uv run python -m src.main analyze --help

# See all LLM options
uv run python -m src.main analyze --help | grep -A2 llm
```

## Development

### Code Quality

```bash
# Format and lint
uv run poe lint

# Run pre-commit hooks
uv run poe pre-commit
```

### Testing (Phase 5)

```bash
# Run all tests
pytest

# Run single test file
pytest tests/unit/data/test_models.py

# Run with coverage
pytest --cov=src
```

### Project Structure

```
nordinvest/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config/              # Configuration system
│   │   ├── schemas.py       # Pydantic validation
│   │   └── loader.py        # YAML loading
│   ├── data/                # Data layer
│   │   ├── models.py        # Pydantic data models
│   │   ├── providers.py     # Abstract provider
│   │   ├── yahoo_finance.py # Yahoo Finance impl
│   │   ├── alpha_vantage.py # Alpha Vantage impl
│   │   ├── finnhub.py       # Finnhub impl
│   │   ├── screening.py     # Instrument filtering
│   │   ├── normalization.py # Data cleaning
│   │   └── portfolio.py     # Portfolio state
│   ├── cache/               # Caching layer
│   │   └── manager.py       # Cache management
│   ├── agents/              # CrewAI agents
│   │   ├── base.py          # BaseAgent and AgentConfig
│   │   ├── crew.py          # AnalysisCrew orchestrator
│   │   ├── scanner.py       # MarketScannerAgent
│   │   ├── analysis.py      # Technical & Fundamental agents
│   │   ├── sentiment.py     # Sentiment & Signal Synthesis agents
│   │   ├── crewai_agents.py # CrewAI Agent factory (Phase 6)
│   │   └── hybrid.py        # Hybrid intelligence wrapper (Phase 6)
│   ├── tools/               # Agent tools
│   │   ├── base.py          # BaseTool and ToolRegistry
│   │   ├── fetchers.py      # PriceFetcherTool, NewsFetcherTool
│   │   ├── analysis.py      # Technical & Sentiment tools
│   │   └── reporting.py     # ReportGeneratorTool
│   ├── llm/                 # LLM integration (Phase 6)
│   │   ├── integration.py   # LLMAnalysisOrchestrator
│   │   ├── token_tracker.py # Token usage & cost tracking
│   │   ├── prompts.py       # Prompt templates for agents
│   │   └── tools.py         # CrewAI tool adapters
│   ├── config/              # Configuration
│   │   ├── llm.py           # LLM client initialization (Phase 6)
│   │   ├── schemas.py       # Pydantic validation
│   │   └── loader.py        # YAML loading
│   ├── analysis/            # Analysis modules
│   ├── reports/             # Report generation (Phase 4)
│   └── utils/
│       └── logging.py       # Logging setup
├── config/
│   └── default.yaml         # Configuration template
├── data/
│   ├── cache/               # API response cache
│   ├── features/            # Preprocessed data
│   └── reports/             # Generated reports
├── tests/                   # Test suite
└── docs/
    ├── architecture.mermaid # System design
    └── roadmap.md           # Implementation plan
```

## Features

### Phase 1: Foundation ✅
- CLI with Typer
- YAML configuration system
- Pydantic validation
- Structured logging with Loguru

### Phase 2: Data Layer ✅
- **3 Data Providers:**
  - Yahoo Finance (unlimited free)
  - Alpha Vantage (25/day free, with retries)
  - Finnhub (60/min free, news/sentiment)
- **Caching System:**
  - Dual-layer (memory + disk)
  - Configurable TTL
  - Automatic expiration cleanup
- **Data Processing:**
  - Pydantic data models
  - Instrument screening
  - Data normalization & validation
  - Multi-period return calculations
- **Portfolio Management:**
  - Position tracking
  - P&L calculations
  - Watchlist management

### Phase 3: CrewAI Agents ✅
- **Market Scanner Agent**: Identifies instruments with price/volume anomalies
- **Fundamental Analysis Agent**: Evaluates financial health and valuation
- **Technical Analysis Agent**: Analyzes technical indicators (SMA, RSI, MACD, ATR)
- **Sentiment Agent**: Analyzes news sentiment (positive/negative/neutral)
- **Signal Synthesis Agent**: Combines signals with weighted scoring (35% technical, 35% fundamental, 30% sentiment)
- **Analysis Crew**: Orchestrates parallel analysis with sequential synthesis

### Phase 4: Signal Synthesis & Reporting ✅
- **InvestmentSignal Model**: Comprehensive signal with component scores, confidence, recommendations
- **AllocationEngine**: Position sizing using modified Kelly criterion with constraint enforcement
- **RiskAssessor**: Multi-factor risk evaluation (volatility, liquidity, sector, concentration)
- **ReportGenerator**: Daily report generation in Markdown and JSON formats
- **PortfolioAllocation**: Allocation suggestions with diversification tracking (Herfindahl index)
- **RiskAssessment**: Risk levels, flags, and warnings for each position

### Phase 5: Integration, Testing & Polish ✅
- **AnalysisPipeline**: End-to-end orchestration from analysis to reports
- **Error Handling**: Custom exceptions hierarchy with 8 types and severity levels
- **Resilience Patterns**: Retry with backoff, fallback, circuit breaker, rate limiter, graceful degradation
- **Scheduling**: CronScheduler for daily automated runs, RunLog for monitoring
- **CLI Integration**: Full pipeline execution in 'run' command with report generation
- **Integration Tests**: Comprehensive test suite for pipeline, errors, scheduling, resilience

### Phase 6: CrewAI & LLM Integration ✅
- **LLM Configuration**: Support for Anthropic Claude, OpenAI GPT, and local models (Ollama)
- **5 Intelligent CrewAI Agents**: Market Scanner, Technical Analyst, Fundamental Analyst, Sentiment Analyst, Signal Synthesizer
- **Hybrid Intelligence**: Automatic fallback to rule-based analysis on LLM failure
- **Token Tracking**: Real-time monitoring of token usage and costs (EUR)
- **Prompt Engineering**: Structured prompts with JSON-formatted responses for consistency
- **CLI Integration**: `--llm` flag for easy switching between rule-based and AI-powered analysis
- **Tool Adapters**: Seamless integration of existing tools with CrewAI agents
- **High-Level Orchestrator**: LLMAnalysisOrchestrator for easy integration
- **Comprehensive Testing**: 12 passing tests covering all LLM components

**Quick start:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run python -m src.main analyze --ticker INTU --llm
```

**See:** [LLM CLI Guide](docs/llm_cli_guide.md) | [LLM Integration Guide](docs/llm_integration.md)

## Cost Target

Monthly operational cost: **€50-90**

- LLM API: €50-70
- Financial Data APIs: €0-20 (free tiers)
- Compute: €0 (local execution)

## Troubleshooting

### "API key not found"
Ensure environment variables are set:
```bash
echo $ANTHROPIC_API_KEY
echo $FINNHUB_API_KEY
```

### "Config file not found"
Create local configuration:
```bash
uv run python -m src.main config-init
```

### "Cache permission denied"
Ensure `data/` directory is writable:
```bash
mkdir -p data/cache data/features data/reports
```

### "Pre-commit hooks failing"
Run linting to fix:
```bash
uv run poe lint
```

## Documentation

### Core Documentation
- **[Architecture](docs/architecture.mermaid)** - System design and component overview
- **[Roadmap](docs/roadmap.md)** - Implementation plan and development phases (5 phases complete, 6 in progress)
- **[Phase 6 Summary](PHASE_6_SUMMARY.md)** - CrewAI & LLM integration implementation details
- **[Developer Guide](CLAUDE.md)** - Development setup and contribution guidelines

### LLM & AI Integration (Phase 6)
- **[LLM CLI Guide](docs/llm_cli_guide.md)** - How to use `--llm` flag with examples and troubleshooting
- **[LLM Integration Guide](docs/llm_integration.md)** - Component architecture, API reference, and advanced usage
- **[LLM Configuration](docs/LLM_CONFIGURATION.md)** - AI vs Rule-based modes, setup instructions

### Configuration & Setup
- **[Market Configuration Guide](docs/MARKET_CONFIG_GUIDE.md)** - Market selection and filtering
- **[Quick Start: Full Market Analysis](docs/QUICK_START_FULL_MARKET.md)** - Running analysis on large market sets
- **[Full Market Analysis Setup](docs/FULL_MARKET_ANALYSIS_SETUP.md)** - Complete setup for comprehensive market coverage

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

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feat/feature-name`
3. Make changes and test: `uv run poe lint && pytest`
4. Commit with semantic messages: `git commit -m "feat: description"`
5. Push and create pull request

## License

[Add your license here]

## Support

For questions or issues:
- Check [Developer Guide](CLAUDE.md) for development guidance
- Review [Roadmap](docs/roadmap.md) for architecture details
- See [LLM Configuration](docs/LLM_CONFIGURATION.md) for setup help
- Open an issue on GitHub
