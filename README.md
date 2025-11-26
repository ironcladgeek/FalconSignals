# NordInvest

AI-powered financial analysis and investment recommendation system using multi-agent AI orchestration (CrewAI). Analyzes Nordic and European markets to generate daily investment signals with confidence scores.

**Status:** Phase 3 complete (CrewAI Agents Development). Phase 4 ready (Signal Synthesis & Reporting).

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
# Required
export ANTHROPIC_API_KEY=your_key

# Optional (for extended features)
export FINNHUB_API_KEY=your_key
export ALPHA_VANTAGE_API_KEY=your_key
```

Or create `.env` file in project root:

```
ANTHROPIC_API_KEY=your_key
FINNHUB_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
```

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

```bash
# Full analysis with fresh API calls
uv run python -m src.main run --config config/local.yaml

# Dry run (no trades/alerts)
uv run python -m src.main run --config config/local.yaml --dry-run
```

### Generate Reports

```bash
# Generate report from cached data
uv run python -m src.main report --date 2024-01-15
```

### CLI Help

```bash
uv run python -m src.main --help
uv run python -m src.main run --help
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
│   │   └── sentiment.py     # Sentiment & Signal Synthesis agents
│   ├── tools/               # Agent tools
│   │   ├── base.py          # BaseTool and ToolRegistry
│   │   ├── fetchers.py      # PriceFetcherTool, NewsFetcherTool
│   │   ├── analysis.py      # Technical & Sentiment tools
│   │   └── reporting.py     # ReportGeneratorTool
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

### Phase 4: Signal Synthesis & Reporting
- Multi-factor signal generation
- Portfolio allocation engine
- Risk assessment
- Daily report generation

### Phase 5: Testing & Deployment
- Integration tests
- Performance optimization
- Deployment scripts
- Cost monitoring

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

- **Architecture:** See `docs/architecture.mermaid` for system design
- **Roadmap:** See `docs/roadmap.md` for implementation plan
- **Development:** See `CLAUDE.md` for developer guidance

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
- Check `CLAUDE.md` for development guidance
- Review `docs/roadmap.md` for architecture details
- Open an issue on GitHub
