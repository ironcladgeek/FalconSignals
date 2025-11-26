# GenAI Financial Assistant — Implementation Roadmap

## Executive Summary

This roadmap outlines the implementation plan for building an AI-driven financial analysis application using CrewAI. The project spans approximately **2 weeks** of development, with support from Claude Code and GitHub Copilot, targeting a monthly operational cost of **≤€100**.

---

## Project Timeline Overview

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 | Days 1-2 | Foundation & Infrastructure |
| Phase 2 | Days 3-5 | Data Layer & Caching |
| Phase 3 | Days 6-9 | CrewAI Agents Development |
| Phase 4 | Days 10-12 | Signal Synthesis & Reporting |
| Phase 5 | Days 13-14 | Integration, Testing & Polish |

---

## Phase 1: Foundation & Infrastructure (Days 1-2)

### Objectives
- Set up project structure and development environment
- Configure dependency management
- Implement configuration system

### Tasks

#### 1.1 Project Setup
- [x] Initialize Python project with `pyproject.toml` (using uv)
- [x] Set up Git repository with `.gitignore`
- [x] Create project directory structure:
```
genai-financial-assistant/
├── src/
│   ├── agents/           # CrewAI agent definitions
│   ├── tools/            # Custom CrewAI tools
│   ├── data/             # Data fetching & processing
│   ├── analysis/         # Technical & fundamental analysis
│   ├── cache/            # Caching layer
│   ├── config/           # Configuration management
│   ├── reports/          # Report generation
│   └── utils/            # Shared utilities
├── config/
│   └── default.yaml      # Default configuration
├── data/
│   ├── cache/            # API response cache
│   ├── features/         # Preprocessed features
│   └── reports/          # Generated reports
├── tests/
├── scripts/
└── README.md
```

#### 1.2 Configuration System
- [x] Implement YAML-based configuration loader
- [x] Define configuration schema:
  - Capital settings (starting capital, monthly deposits)
  - Risk tolerance levels (conservative, moderate, aggressive)
  - Market preferences (included/excluded markets)
  - API credentials (environment variables)
  - Output preferences (max recommendations, report format)
- [x] Create CLI interface using Typer
- [x] Implement configuration validation with Pydantic

#### 1.3 Environment Setup
- [x] Configure environment variable management (`.env` support)
- [x] Set up logging with structured output (Loguru)
- [x] Create development and production configurations

### Deliverables
- ✅ Functional project skeleton with src/ package structure
- ✅ CLI with `--help`, `--config`, and 4 main commands (run, report, config-init, validate-config)
- ✅ Configuration loading and validation with Pydantic schemas
- ✅ YAML configuration system with environment variable support
- ✅ Structured logging with Loguru integration
- ✅ Complete data and test directory structure

**Status: COMPLETE** (Commit: 37aa9f5)

### Dependencies
```
crewai
crewai-tools
pydantic
pyyaml
click (or typer)
python-dotenv
loguru
```

---

## Phase 2: Data Layer & Caching (Days 3-5)

### Objectives
- Implement data fetching from multiple APIs
- Build robust caching layer for cost control
- Create data normalization pipeline

### Tasks

#### 2.1 API Integration Layer
- [x] Create abstract `DataProvider` base class
- [x] Implement Yahoo Finance provider (free tier)
- [x] Implement Alpha Vantage provider (backup)
- [x] Implement Finnhub provider (news & sentiment)
- [x] Add rate limiting and retry logic
- [x] Create unified data models with Pydantic:
  - `StockPrice`, `FinancialStatement`, `NewsArticle`, `AnalystRating`

#### 2.2 Caching System
- [x] Implement file-based cache manager:
  - JSON for structured data
  - Parquet support (via pandas)
- [x] Define cache expiration policies:
  - Price data: 1 hour during market hours, 24 hours otherwise
  - News: 4 hours
  - Fundamentals: 24 hours
  - Financial statements: 7 days
- [x] Create cache invalidation utilities
- [x] Implement cache statistics and monitoring

#### 2.3 Data Processing Pipeline
- [x] Build instrument screening module:
  - Filter by market (Nordic, EU, US)
  - Filter by instrument type (stocks, ETFs, funds)
  - Exclude penny stocks and illiquid instruments
- [x] Create data normalization functions
- [x] Implement missing data handling strategies

#### 2.4 Storage Layer
- [x] Create JSON-based portfolio tracker
- [x] Implement watchlist persistence
- [x] Position tracking with cost basis and P&L

### Deliverables
- ✅ Working data fetchers for 3 providers (Yahoo Finance, Alpha Vantage, Finnhub)
- ✅ Caching system with configurable TTL and expiration
- ✅ Instrument screening pipeline with market/type filters
- ✅ Portfolio state management with positions and watchlist
- ✅ Data normalization and validation pipeline
- ✅ Multi-period return calculations

**Status: COMPLETE** (Commits: 7fcfe6d - 6df52c5)

### Dependencies
```
yfinance
alpha-vantage
finnhub-python
pandas
pyarrow (for Parquet)
requests
aiohttp (optional, for async)
```

### Cost Considerations
| Provider | Free Tier Limits | Strategy |
|----------|------------------|----------|
| Yahoo Finance | Unlimited (unofficial) | Primary source |
| Alpha Vantage | 25 requests/day | Backup only |
| Finnhub | 60 calls/minute | News & sentiment |

---

## Phase 3: CrewAI Agents Development (Days 6-9)

### Objectives
- Implement all six specialized agents
- Create custom tools for each agent
- Configure agent collaboration

### Tasks

#### 3.1 Custom Tools Development
- [ ] **PriceFetcherTool**: Retrieve historical and current prices
- [ ] **NewsFetcherTool**: Fetch and filter relevant news
- [ ] **FinancialDataTool**: Get earnings, statements, ratios
- [ ] **TechnicalIndicatorTool**: Calculate SMA, RSI, MACD, etc.
- [ ] **SentimentAnalyzerTool**: Score news sentiment
- [ ] **ReportGeneratorTool**: Format output documents

#### 3.2 Market Scanner Agent
- [ ] Define agent role, goal, and backstory
- [ ] Implement daily scanning logic:
  - Fetch price data for all tracked instruments
  - Detect unusual volume or price movements
  - Identify instruments crossing key technical levels
- [ ] Create anomaly detection heuristics
- [ ] Output: List of instruments requiring analysis

#### 3.3 Fundamental Analysis Agent
- [ ] Define agent configuration
- [ ] Implement analysis capabilities:
  - Revenue & EPS growth (YoY, QoQ)
  - Profit margins and cash flow analysis
  - Debt ratio assessment
  - Valuation metrics (P/E, EV/EBITDA, P/B, PEG)
- [ ] Create fundamental scoring system (0-100)
- [ ] Output: Fundamental scores with explanations

#### 3.4 Technical Analysis Agent
- [ ] Define agent configuration
- [ ] Implement indicator calculations:
  - Moving averages (SMA 20/50/200)
  - RSI (14-day)
  - MACD (12, 26, 9)
  - ATR for volatility
  - Volume analysis
- [ ] Create trend identification logic
- [ ] Implement pattern detection (support/resistance)
- [ ] Output: Technical scores with trend classification

#### 3.5 News & Sentiment Agent
- [ ] Define agent configuration
- [ ] Implement news processing:
  - Fetch recent news (24-48 hours)
  - Filter by relevance
  - Extract key events
- [ ] Create sentiment scoring:
  - Positive/negative/neutral classification
  - Event importance weighting
- [ ] Output: Sentiment scores with event summaries

#### 3.6 Agent Orchestration
- [ ] Configure CrewAI Crew with all agents
- [ ] Define task dependencies and flow
- [ ] Implement parallel execution where possible
- [ ] Set up agent communication protocols

### Deliverables
- ✅ 4 functional analysis agents
- ✅ 6 custom tools
- ✅ Agent orchestration configuration
- ✅ Intermediate output formats defined

### CrewAI Configuration Example
```python
from crewai import Agent, Task, Crew, Process

market_scanner = Agent(
    role="Market Scanner",
    goal="Identify instruments with significant price movements or anomalies",
    backstory="Expert market analyst specializing in detecting emerging trends...",
    tools=[price_fetcher, news_fetcher],
    verbose=True
)

# Similar definitions for other agents...

crew = Crew(
    agents=[market_scanner, fundamental_agent, technical_agent, sentiment_agent],
    tasks=[scan_task, fundamental_task, technical_task, sentiment_task],
    process=Process.sequential  # or Process.hierarchical
)
```

---

## Phase 4: Signal Synthesis & Reporting (Days 10-12)

### Objectives
- Implement signal generation logic
- Build portfolio allocation engine
- Create daily report generator

### Tasks

#### 4.1 Signal Synthesis Agent
- [ ] Define agent configuration
- [ ] Implement multi-factor scoring:
  - Combine fundamental score (weight: 35%)
  - Combine technical score (weight: 35%)
  - Combine sentiment score (weight: 30%)
- [ ] Create confidence calculation:
  - Agreement across factors
  - Data quality assessment
  - Historical accuracy (if available)
- [ ] Generate recommendations:
  - **Buy**: Score > 70, confidence > 60%
  - **Hold**: Score 40-70
  - **Avoid**: Score < 40 or high risk flags
- [ ] Output: Ranked list of opportunities with full context

#### 4.2 Portfolio Allocation Engine
- [ ] Implement position sizing:
  - Kelly criterion (modified)
  - Maximum position size (% of capital)
  - Sector concentration limits
- [ ] Create diversification logic:
  - Market diversification
  - Sector diversification
  - Instrument type balance
- [ ] Calculate allocation suggestions in EUR and %
- [ ] Account for monthly deposits in strategy

#### 4.3 Risk Assessment Module
- [ ] Implement risk scoring:
  - Volatility assessment (ATR-based)
  - Sector risk flags
  - Liquidity concerns
  - Concentration warnings
- [ ] Create risk-adjusted return estimates
- [ ] Add disclaimer generation

#### 4.4 Daily Report Generation Agent
- [ ] Define agent configuration
- [ ] Implement report sections:
  - Market Overview (index movements, sector heatmap)
  - Top 5-10 Opportunities (with full signal details)
  - Portfolio Alerts (threshold crossings, earnings)
  - Key News Summary (bullet points with scores)
  - Watchlist Updates (additions/removals)
- [ ] Create Markdown report template
- [ ] Add HTML report option (optional)
- [ ] Implement email notification (optional)

#### 4.5 Output Formatting
- [ ] Define JSON schema for signals
- [ ] Create human-readable report templates
- [ ] Implement export utilities

### Deliverables
- ✅ Signal synthesis with confidence scores
- ✅ Portfolio allocation suggestions
- ✅ Risk assessment module
- ✅ Daily report generator (Markdown)

### Signal Output Schema
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "market": "US",
  "sector": "Technology",
  "recommendation": "Buy",
  "time_horizon": "3M",
  "expected_return": {"min": 8, "max": 15},
  "confidence": 78,
  "scores": {
    "fundamental": 82,
    "technical": 75,
    "sentiment": 71
  },
  "key_reasons": [
    "Strong Q4 earnings beat expectations",
    "Golden cross on 50/200 SMA",
    "Positive analyst revisions"
  ],
  "risk_assessment": {
    "level": "Medium",
    "volatility": "Normal",
    "flags": []
  },
  "allocation": {
    "eur": 200,
    "percentage": 10
  }
}
```

---

## Phase 5: Integration, Testing & Polish (Days 13-14)

### Objectives
- Full system integration testing
- Performance optimization
- Documentation and deployment

### Tasks

#### 5.1 Integration Testing
- [ ] End-to-end pipeline test
- [ ] Verify agent communication
- [ ] Test with various market conditions (mock data)
- [ ] Validate output formats
- [ ] Cost tracking verification

#### 5.2 Performance Optimization
- [ ] Profile API call frequency
- [ ] Optimize caching hit rates
- [ ] Reduce LLM token usage where possible
- [ ] Implement batch processing for efficiency

#### 5.3 Error Handling & Resilience
- [ ] Add comprehensive error handling
- [ ] Implement graceful degradation:
  - Fallback data providers
  - Cached data usage on API failures
- [ ] Create alerting for critical failures
- [ ] Add retry logic with exponential backoff

#### 5.4 Documentation
- [ ] Write README with setup instructions
- [ ] Document configuration options
- [ ] Create usage examples
- [ ] Add troubleshooting guide

#### 5.5 Deployment Setup
- [ ] Create run scripts for daily execution
- [ ] Set up cron job / scheduler
- [ ] Configure logging and monitoring
- [ ] Create backup procedures for data

### Deliverables
- ✅ Fully integrated system
- ✅ Comprehensive test coverage
- ✅ Documentation
- ✅ Deployment scripts

---

## Cost Budget Breakdown

| Component | Estimated Monthly Cost |
|-----------|----------------------|
| LLM API (Claude/GPT) | €50-70 |
| Financial Data APIs | €0-20 (free tiers) |
| News API (Finnhub) | €0 (free tier) |
| Compute (local) | €0 |
| **Total** | **€50-90** |

### Cost Control Strategies
1. **Aggressive caching**: Minimize repeated API calls
2. **Batch processing**: Group requests efficiently
3. **Free tier prioritization**: Use Yahoo Finance as primary
4. **Token optimization**: Concise prompts and responses
5. **Scheduled runs**: Once daily, not continuous

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API rate limits | Multiple providers, aggressive caching |
| Cost overruns | Daily cost monitoring, hard limits |
| Data quality issues | Validation, multiple sources |
| LLM hallucinations | Structured outputs, fact verification |
| Market data delays | Acknowledge in reports, use EOD data |

---

## Success Criteria Checklist

- [ ] System runs daily in <15 minutes
- [ ] User review time <1 hour
- [ ] Monthly costs ≤€100
- [ ] Generates 5-10 actionable signals daily
- [ ] Reports include confidence scores and rationale
- [ ] Portfolio allocation suggestions provided
- [ ] Risk warnings included where appropriate
- [ ] System handles API failures gracefully

---

## Post-Launch Enhancements (Future)

1. **Performance tracking**: Log recommendations and actual outcomes
2. **Model improvement**: Refine weights based on historical accuracy
3. **Additional markets**: Expand instrument coverage
4. **Backtesting module**: Test strategies on historical data
5. **Web dashboard**: Visual interface for reports
6. **Mobile notifications**: Push alerts for critical events

---

## Quick Start Commands

```bash
# Install dependencies
poetry install

# Configure settings
cp config/default.yaml config/local.yaml
# Edit config/local.yaml with your preferences

# Set API keys
export FINNHUB_API_KEY=your_key
export OPENAI_API_KEY=your_key  # or ANTHROPIC_API_KEY

# Run daily analysis
python -m src.main run --config config/local.yaml

# Generate report only (using cached data)
python -m src.main report --date 2024-01-15

# View help
python -m src.main --help
```

---

*This roadmap serves as the canonical implementation guide for the GenAI Financial Assistant project. Update task checkboxes as development progresses.*
