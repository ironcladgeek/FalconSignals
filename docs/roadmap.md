# GenAI Financial Assistant — Implementation Roadmap

## Executive Summary

This roadmap outlines the implementation plan for building an AI-driven financial analysis application using CrewAI. The project spans approximately **2 weeks** of development, with support from Claude Code and GitHub Copilot, targeting a monthly operational cost of **≤€100**.

---

## Project Timeline Overview

| Phase | Duration | Focus | Status |
|-------|----------|-------|--------|
| Phase 1 | Days 1-2 | Foundation & Infrastructure | ✅ Complete |
| Phase 2 | Days 3-5 | Data Layer & Caching | ✅ Complete |
| Phase 3 | Days 6-9 | CrewAI Agents Development | ✅ Complete |
| Phase 4 | Days 10-12 | Signal Synthesis & Reporting | ✅ Complete |
| Phase 5 | Days 13-14 | Integration, Testing & Polish | ✅ Complete |
| Phase 6 | Days 15-18 | CrewAI & LLM Integration | ✅ Complete |
| Phase 7 | Days 19-20 | True Test Mode | ✅ Complete |
| Phase 8.1 | Next | Historical Date Analysis | ✅ **COMPLETE** |
| Phase 8.2 | Next | Backtesting Framework | 📋 HIGH PRIORITY |
| Phase 9 | Future | Per-Agent LLM Model Configuration | 📋 Planned |
| Phase 10 | Future | Devil's Advocate Agent | 📋 Planned |
| Phase 11 | Future | Performance Tracking & Database | 📋 Planned |
| Phase 12 | Future | Enhanced Technical Analysis | 📋 Planned |
| Phase 13 | Future | Advanced Features & Integrations | 📋 Planned |

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

## Phase 3: Agent Pattern Development (Days 6-9)

### Objectives
- Implement specialized agent architecture using custom BaseAgent pattern
- Create custom tools for each agent
- Configure agent orchestration and collaboration

### Tasks

#### 3.1 Custom Tools Development
- [x] **PriceFetcherTool**: Retrieve historical and current prices
- [x] **NewsFetcherTool**: Fetch and filter relevant news
- [x] **FinancialDataTool**: Get earnings, statements, ratios
- [x] **TechnicalIndicatorTool**: Calculate SMA, RSI, MACD, etc.
- [x] **SentimentAnalysisTool**: Basic sentiment scoring

#### 3.2 BaseAgent Pattern Implementation
- [x] Create `BaseAgent` abstract class with:
  - Role, goal, backstory configuration
  - Tool assignment interface
  - Execute method for task handling
- [x] Implement agent configuration with `AgentConfig`
- [x] Create deterministic, rule-based execution logic

#### 3.3 Specialized Agents
- [x] **Market Scanner Agent**: Price/volume anomaly detection
- [x] **Technical Analysis Agent**: Indicator-based scoring
- [x] **Fundamental Analysis Agent**: Financial metrics evaluation
- [x] **Sentiment Analysis Agent**: News sentiment aggregation
- [x] **Signal Synthesis Agent**: Multi-factor combination

#### 3.4 Agent Orchestration
- [x] Create `AnalysisCrew` for agent coordination
- [x] Implement parallel execution for analysis agents
- [x] Sequential synthesis after parallel analysis
- [x] Result aggregation and formatting

### Deliverables
- ✅ 5 specialized rule-based agents
- ✅ 5 custom tools for data access and analysis
- ✅ Agent orchestration with parallel/sequential execution
- ✅ Comprehensive indicator calculations

**Status: COMPLETE**

**Note:** Phase 3 implements a **rule-based system** using custom `BaseAgent` pattern.
**No actual CrewAI framework or LLM integration.** All analysis is deterministic and based on:
- Technical indicators (RSI, MACD, moving averages)
- Mathematical scoring algorithms
- Simple sentiment counting (positive/negative news)
- Weighted score combinations

---

## Phase 4: Signal Synthesis & Reporting (Days 10-12)

### Objectives
- Implement signal generation logic
- Build portfolio allocation engine
- Create daily report generator

### Tasks

#### 4.1 Signal Synthesis & Scoring
- [x] Define signal model with all required fields
- [x] Implement multi-factor scoring:
  - Combine fundamental score (weight: 35%)
  - Combine technical score (weight: 35%)
  - Combine sentiment score (weight: 30%)
- [x] Create confidence calculation:
  - Agreement across factors
  - Data quality assessment
- [x] Generate recommendations:
  - **Buy**: Score > 70, confidence > 60%
  - **Hold**: Score 40-70
  - **Avoid**: Score < 40 or high risk flags

#### 4.2 Portfolio Allocation Engine
- [x] Implement position sizing (Kelly criterion, modified)
- [x] Create diversification logic
- [x] Calculate allocation suggestions in EUR and %

#### 4.3 Risk Assessment Module
- [x] Implement risk scoring (volatility, sector, liquidity)
- [x] Create risk-adjusted return estimates
- [x] Add disclaimer generation

#### 4.4 Daily Report Generation
- [x] Define report model with all required sections
- [x] Implement Markdown and JSON output formats
- [x] Create summary statistics

### Deliverables
- ✅ InvestmentSignal model with component scores
- ✅ AllocationEngine with Kelly criterion
- ✅ RiskAssessor with multi-factor evaluation
- ✅ ReportGenerator in Markdown and JSON

**Status: COMPLETE**

---

## Phase 5: Integration, Testing & Polish (Days 13-14)

### Objectives
- Full system integration testing
- Performance optimization
- Documentation and deployment

### Tasks

#### 5.1 Integration Testing
- [x] End-to-end pipeline test
- [x] Verify agent communication
- [x] Test with various market conditions (mock data)
- [x] Validate output formats
- [x] Cost tracking verification

#### 5.2 Error Handling & Resilience
- [x] Add comprehensive error handling (custom exceptions)
- [x] Implement graceful degradation
- [x] Create alerting for critical failures
- [x] Add retry logic with exponential backoff
- [x] Circuit breaker pattern for cascading failures
- [x] Rate limiter for API protection

#### 5.3 Deployment & Scheduling
- [x] Create run scripts for daily execution
- [x] Set up cron job / scheduler infrastructure
- [x] Configure logging and monitoring (RunLog, statistics)
- [x] Create backup procedures for data

#### 5.4 CLI Integration
- [x] Implement full 'run' command with pipeline
- [x] Add report output formats (markdown, json)
- [x] Implement run timing and logging
- [x] Error tracking and recovery

#### 5.5 Documentation
- [x] Update architecture documentation
- [x] Add deployment guide
- [x] Create usage examples
- [x] Add troubleshooting guide

### Deliverables
- ✅ End-to-end AnalysisPipeline orchestrator
- ✅ Comprehensive error handling (8 exception types)
- ✅ Resilience patterns (retry, fallback, circuit breaker)
- ✅ Scheduling infrastructure
- ✅ Complete documentation

**Status: COMPLETE** (Commit: ab39de1)

---

## Phase 6: CrewAI & LLM Integration (Days 15-18)

### Objectives
- Replace rule-based agents with actual CrewAI LLM-powered agents
- Implement intelligent reasoning for all analysis phases
- Add natural language insight generation
- Enable agent collaboration and delegation

### Tasks

#### 6.1 CrewAI Framework Integration
- [x] Import actual CrewAI classes: `from crewai import Agent, Task, Crew`
- [x] Configure LLM providers (Anthropic, OpenAI, local)
- [x] Implement LLM client initialization (src/config/llm.py)
- [x] Create LLM configuration management

#### 6.2 Convert Agents to CrewAI Agents
- [x] **Market Scanner Agent**: LLM-powered anomaly detection
- [x] **Technical Analysis Agent**: LLM interpretation of indicators
- [x] **Fundamental Analysis Agent**: LLM financial statement analysis
- [x] **Sentiment Analysis Agent**: LLM-powered news analysis
- [x] **Signal Synthesizer Agent**: LLM investment thesis generation

#### 6.3 Create CrewAI Tasks
- [x] Define Task objects for each analysis phase
- [x] Implement sequential task dependencies
- [x] Enable task result sharing between agents
- [x] Add context propagation

#### 6.4 LLM Prompt Engineering
- [x] Design prompts for each agent (src/llm/prompts.py)
- [x] Implement prompt templates with variables
- [x] Create output structure examples
- [x] Add JSON schema for structured responses

#### 6.5 Hybrid Intelligence System
- [x] Keep rule-based calculations as tools
- [x] Use LLM for reasoning and interpretation
- [x] Implement fallback to rule-based on LLM failures
- [x] Create quality scoring for LLM outputs
- [x] Support multiple LLM providers

#### 6.6 Cost Control & Monitoring
- [x] Implement token counting and cost tracking
- [x] Set daily/monthly budget limits
- [x] Create alert system for cost overruns
- [x] Track costs per request and per model

#### 6.7 Testing & Validation
- [x] Comprehensive test suite (12 passing tests)
- [x] Validate configuration loading
- [x] Test token tracking accuracy
- [x] Test orchestrator initialization

### Deliverables
- ✅ Actual CrewAI integration with Agent, Task, Crew classes
- ✅ LLM-powered agents with fallback to rule-based
- ✅ Natural language insights via prompt templates
- ✅ Token usage tracking and cost monitoring
- ✅ Hybrid system with HybridAnalysisAgent
- ✅ High-level LLM orchestrator
- ✅ CLI integration with `--llm` flag

**Status: COMPLETE**

### Cost Estimates (Monthly)
| Component | Estimated Cost |
|-----------|---------------|
| Daily scans (200 instruments) | €10-15 |
| Detailed analysis (20 instruments/day) | €30-40 |
| Report generation | €5-10 |
| **Total** | **€45-65** |

---

## Phase 7: True Test Mode

### ✅ **COMPLETE** - Essential for Development & Cost Control

### Overview

**Problem Solved:**

The previous `--test` flag simply ran analysis on `AAPL` with live data, which was problematic:

| Old Behavior | New True Test Mode |
|--------------|-------------------|
| Full LLM costs (~€0.065/run) | Zero cost (MockLLMClient) |
| Required network (API calls) | Fully offline (fixture files) |
| Non-reproducible (data changes) | Reproducible (committed fixtures) |
| Slow (API round-trips) | Fast (<5 seconds) |

**What Was Implemented:**

| Feature | Implementation |
|---------|---------------|
| **Fixture Data Provider** | `src/data/fixture.py` - FixtureDataProvider class |
| **Mock LLM Client** | `src/llm/mock.py` - MockLLMClient with pre-defined responses |
| **Test Mode Config** | `src/config/schemas.py` - TestModeConfig schema |
| **Fixture Data** | `data/fixtures/test_ticker_minimal/` - ZS ticker with anomalies |
| **CLI Integration** | `--test` and `--fixture` flags in analyze command |
| **Comprehensive Tests** | `tests/unit/data/test_fixture.py`, `tests/unit/llm/test_mock.py` |

---

### 7.1 Implementation Details

#### Test Fixture Data ✅
- [x] **Created fixture data directory**: `data/fixtures/test_ticker_minimal/`
  ```
  data/fixtures/test_ticker_minimal/
  ├── price_data.json       # 10 days of OHLCV for ZS
  ├── fundamentals.json     # 30 key metrics
  ├── news.json             # 5 news articles
  └── metadata.json         # Expected output validation
  ```

- [x] **Fixture uses ZS (Zscaler)** - Selected because it has:
  - Large daily price swings (5-7%)
  - Trading near 52-week highs
  - High volume anomalies
  - Perfect for testing anomaly detection

#### FixtureDataProvider ✅
- [x] **Created `src/data/fixture.py`**:
  ```python
  class FixtureDataProvider(DataProvider):
      """Data provider that reads from fixture files instead of APIs."""

      def __init__(self, fixture_path: Path):
          self.fixture_path = Path(fixture_path)
          self._load_all_fixtures()

      def get_stock_prices(self, ticker, start_date, end_date) -> list[StockPrice]:
          # Returns from fixture price_data.json

      def get_news(self, ticker, limit=10) -> list[NewsArticle]:
          # Returns from fixture news.json

      def get_analyst_ratings(self, ticker) -> AnalystRating:
          # Returns from fixture fundamentals.json
  ```

- [x] **Registered with DataProviderFactory** for seamless integration

#### MockLLMClient ✅
- [x] **Created `src/llm/mock.py`**:
  ```python
  class MockLLMClient:
      """Mock LLM client that returns pre-defined responses for testing."""

      DEFAULT_RESPONSES = {
          "market_scanner": {...},
          "technical_analyst": {...},
          "fundamental_analyst": {...},
          "sentiment_analyst": {...},
          "signal_synthesizer": {...},
      }

      def complete(self, prompt, agent_type="generic") -> str:
          return json.dumps(self.responses.get(agent_type, {}))

      def get_cost(self, input_tokens, output_tokens, model) -> tuple[float, str]:
          return 0.0, "EUR"  # Always zero cost
  ```

- [x] **Supports response overrides** for custom test scenarios
- [x] **All agent types covered** with realistic mock responses

#### TestModeConfig ✅
- [x] **Added to `src/config/schemas.py`**:
  ```python
  class TestModeConfig(BaseModel):
      enabled: bool = False
      fixture_name: str = "test_ticker_minimal"
      fixture_path: str | None = None
      use_mock_llm: bool = True
      validate_expected: bool = True
  ```

#### CLI Integration ✅
- [x] **Updated `--test` flag behavior**:
  ```bash
  # TRUE TEST MODE - uses fixtures, no API/LLM calls, zero cost
  uv run python -m src.main analyze --test

  # Test with mock LLM responses (zero cost)
  uv run python -m src.main analyze --test --llm

  # Test with specific fixture
  uv run python -m src.main analyze --test --fixture test_ticker_minimal
  ```

- [x] **Clear test mode messaging**:
  ```
  🧪 Running TRUE TEST MODE (offline, zero cost, reproducible)...
    Fixture: test_ticker_minimal
    Data source: Local fixture files (no API calls)
    LLM: MockLLMClient (zero cost)
  ```

#### Test Suite ✅
- [x] **`tests/unit/data/test_fixture.py`** - 12 tests for FixtureDataProvider
- [x] **`tests/unit/llm/test_mock.py`** - 11 tests for MockLLMClient

### Deliverables ✅
- ✅ Fixture data directory with ZS test data
- ✅ FixtureDataProvider implementation
- ✅ MockLLMClient for zero-cost testing
- ✅ Updated `--test` flag with true offline mode
- ✅ `--fixture` flag for selecting fixture
- ✅ TestModeConfig in configuration schema
- ✅ Comprehensive test coverage

**Status: COMPLETE**

---

## Phase 8: Historical Analysis & Backtesting

### 🚨 **HIGH PRIORITY** - Essential for System Validation

### Overview

Enable analysis based on historical dates for backtesting and performance evaluation. This is essential for validating the system's effectiveness before relying on its recommendations.

### 8.1 Historical Date Analysis

✅ **COMPLETE** - Enables backtesting and historical analysis

**Objective**: Run analysis as if it were a specific date in the past.

#### Implementation Details

**1. CLI Parameter** ✅
```bash
# Analyze as if it were June 1, 2024
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01

# Analyze with LLM using historical data
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01 --llm

# Test mode with historical date
uv run python -m src.main analyze --test --date 2024-06-01
```

**2. HistoricalDataFetcher** ✅
- Location: `src/data/historical.py`
- Fetches all data available as of a specific date
- Strict date filtering prevents future data leakage
- Supports both datetime and date objects
- Graceful error handling with missing data warnings

**3. HistoricalContext Model** ✅
- Location: `src/data/models.py`
- Contains price data, fundamentals, news, analyst ratings
- Tracks data availability and missing data warnings
- Configurable lookback period (default: 365 days)

**4. Cache Manager Enhancement** ✅
- Added `get_historical_cache()` method to CacheManager
- Filters cached files by date extracted from filename
- Returns most recent cache available before specified date
- Enables efficient historical analysis without re-fetching

**5. Pipeline Integration** ✅
- Historical date passed through analysis context
- Report generation uses historical date for report_date
- Both rule-based and LLM analysis support historical dates

#### Deliverables
- ✅ `--date` CLI parameter (YYYY-MM-DD format)
- ✅ HistoricalDataFetcher with strict date filtering
- ✅ HistoricalContext Pydantic model
- ✅ Enhanced CacheManager.get_historical_cache()
- ✅ Pipeline integration for historical analysis
- ✅ Test mode support for historical dates
- ✅ Comprehensive error handling and warnings

### 8.2 Backtesting Framework

**Objective**: Run analysis at multiple historical points and track outcomes.

#### Tasks
- [ ] **Create backtesting engine**:
  ```python
  class BacktestEngine:
      def run_backtest(
          self,
          tickers: list[str],
          start_date: date,
          end_date: date,
          interval: str = "weekly"
      ) -> BacktestResult:
          """Run analysis at each interval and track outcomes."""
  ```

- [ ] **Implement backtest CLI command**:
  ```bash
  uv run python -m src.main backtest \
      --tickers AAPL,MSFT,GOOGL \
      --start 2024-01-01 \
      --end 2024-06-30 \
      --interval weekly
  ```

- [ ] **Track signal accuracy**:
  - Buy signals → Did price increase?
  - Confidence correlation with accuracy
  - Per-agent accuracy tracking

- [ ] **Generate backtest reports**:
  - Win rate, average return
  - Sharpe ratio, max drawdown
  - Comparison vs benchmark (S&P 500)

#### Configuration
```yaml
backtesting:
  enabled: true
  default_lookback_days: 365
  benchmark_ticker: "SPY"
  evaluation_periods: [30, 90, 180]
```

#### Deliverables
- [ ] `--date` parameter for historical analysis
- [ ] HistoricalDataFetcher with strict date filtering
- [ ] BacktestEngine with configurable intervals
- [ ] `backtest` CLI command
- [ ] Backtest report generation

---

**Phase 8.1 Status: ✅ COMPLETE**

**Estimated Effort**: 4-5 days
**Priority**: 🔴 High - Essential for system validation

---

## Phase 9: Per-Agent LLM Model Configuration

### Overview - Cost Optimization

**Objective**: Allow different LLM models for different agents based on task complexity and cost optimization.

#### Tasks
- [ ] **Extend configuration schema** for per-agent model settings:
  ```yaml
  llm:
    default:
      provider: anthropic
      model: claude-sonnet-4-20250514
      temperature: 0.7
      max_tokens: 2000

    agents:
      market_scanner:
        model: claude-haiku  # Faster, cheaper for initial screening
        temperature: 0.3
        max_tokens: 1000

      technical_analyst:
        model: claude-sonnet-4-20250514
        temperature: 0.5

      fundamental_analyst:
        model: claude-sonnet-4-20250514  # Complex reasoning needed
        temperature: 0.7

      sentiment_analyst:
        model: claude-haiku  # Good for classification tasks
        temperature: 0.3

      signal_synthesizer:
        model: claude-sonnet-4-20250514  # Critical decisions
        temperature: 0.5

      devils_advocate:  # Future agent (Phase 10)
        model: claude-sonnet-4-20250514
        temperature: 0.8  # More creative criticism
  ```

- [ ] **Update CrewAI agent factory**:
  ```python
  class AgentFactory:
      def create_agent(self, agent_type: str) -> Agent:
          # Get agent-specific config, fallback to default
          agent_config = self.config.llm.agents.get(
              agent_type,
              self.config.llm.default
          )
          llm = initialize_llm(agent_config)
          return Agent(..., llm=llm)
  ```

- [ ] **Implement model fallback chain**: If preferred model fails, try alternatives
- [ ] **Add cost tracking per agent** for optimization insights
- [ ] **Create CLI flag** for model override: `--model-override technical:gpt-4`

#### Benefits
| Benefit | Description |
|---------|-------------|
| **Cost optimization** | Use cheaper models (Haiku) for simple tasks |
| **Quality where needed** | Use powerful models (Sonnet) for synthesis |
| **A/B testing** | Compare model performance per agent |
| **Flexibility** | Override models for specific runs |

**Estimated cost reduction**: 30-40% with strategic model selection

#### Deliverables
- [ ] Per-agent model configuration schema
- [ ] Updated AgentFactory with model selection
- [ ] Model fallback chain
- [ ] Per-agent cost tracking in reports
- [ ] CLI `--model-override` flag

---

**Phase 9 Status: PLANNED**

**Estimated Effort**: 2-3 days
**Priority**: 🟡 High - Significant cost savings potential

---

## Phase 10: Devil's Advocate Agent

### Overview

Add a critical review agent that challenges BUY recommendations to reduce overconfidence and identify blind spots. This agent provides fact-based counter-arguments to ensure recommendations are robust.

### 10.1 Devil's Advocate Agent Design

**Objective**: Optional agent that critically examines investment recommendations.

#### Tasks
- [ ] **Create DevilsAdvocateAgent**:
  ```python
  class DevilsAdvocateAgent:
      """
      An agent that critically examines investment recommendations
      and provides counter-arguments based on facts.
      """

      role = "Senior Risk Analyst & Critical Reviewer"
      goal = "Challenge investment theses and identify potential flaws"
      backstory = """
          You are a contrarian analyst with 25 years of experience.
          You've seen countless investment theses fail. Your job is to
          find the weaknesses in any recommendation - not to be negative,
          but to ensure recommendations are robust and well-reasoned.
          You focus on FACTS, not speculation.
      """
  ```

- [ ] **Define criticism categories**:
  - **Valuation Concerns**: Is the price justified by fundamentals?
  - **Technical Warnings**: Are there bearish signals being ignored?
  - **Macro Risks**: Sector headwinds, economic factors
  - **Competitive Threats**: Market share risks, disruption
  - **Historical Patterns**: Similar setups that failed
  - **Data Quality Issues**: Missing or stale data
  - **Confidence Calibration**: Is confidence score justified?

### 10.2 Critique Implementation

#### Tasks
- [ ] **Create critique prompt template**:
  ```python
  DEVILS_ADVOCATE_PROMPT = """
  You are reviewing the following BUY recommendation:

  Ticker: {ticker}
  Score: {score}/100
  Confidence: {confidence}%

  Technical Analysis Summary:
  {technical_summary}

  Fundamental Analysis Summary:
  {fundamental_summary}

  Sentiment Analysis Summary:
  {sentiment_summary}

  Investment Thesis:
  {investment_thesis}

  YOUR TASK:
  Critically examine this recommendation and identify:
  1. What could go WRONG with this investment?
  2. What facts or data CONTRADICT the bullish thesis?
  3. What risks are being UNDERWEIGHTED?
  4. Is the confidence score JUSTIFIED given the uncertainties?
  5. What would make you change this from BUY to HOLD or AVOID?

  Provide specific, fact-based criticisms. Do not speculate.
  Rate the overall thesis robustness (0-100).

  Output as JSON:
  {
      "robustness_score": int,
      "primary_concerns": [
          {"category": "str", "concern": "str", "severity": "high|medium|low"}
      ],
      "overlooked_risks": ["str"],
      "confidence_adjustment": int,  // Suggested adjustment (-30 to +10)
      "recommendation_change": "maintain|downgrade|upgrade",
      "summary": "str"
  }
  """
  ```

- [ ] **Implement robustness scoring** (0-100)
- [ ] **Add confidence adjustment** based on critique
- [ ] **Flag recommendations** with low robustness scores

### 10.3 Integration

#### Tasks
- [ ] **Add to analysis pipeline** (optional stage):
  ```bash
  # Enable devil's advocate
  uv run python -m src.main analyze --ticker AAPL --llm --with-critique

  # Always enable via config
  ```

- [ ] **Add critique section to reports**:
  ```markdown
  ## Critical Review (Devil's Advocate)

  **Robustness Score**: 65/100

  ### Primary Concerns
  1. **Valuation** (High): P/E ratio of 35 is 40% above sector average
  2. **Technical** (Medium): RSI showing overbought conditions
  3. **Macro** (Medium): Rising interest rates may pressure growth stocks

  ### Overlooked Risks
  - Regulatory scrutiny in EU markets
  - Key patent expiring in 2025

  ### Confidence Adjustment
  Original: 78% → Adjusted: 68% (-10%)
  ```

#### Configuration
```yaml
agents:
  devils_advocate:
    enabled: true
    apply_to: ["BUY"]  # Only critique BUY signals
    min_score_to_critique: 60  # Don't waste tokens on weak signals
    confidence_adjustment_enabled: true
    include_in_report: true
```

#### Deliverables
- [ ] DevilsAdvocateAgent implementation
- [ ] Critique prompt template
- [ ] Robustness scoring (0-100)
- [ ] Confidence adjustment logic
- [ ] CLI `--with-critique` flag
- [ ] Report integration with critique section

---

**Phase 10 Status: PLANNED**

**Estimated Effort**: 2-3 days
**Priority**: 🟡 High - Reduces overconfidence in recommendations

---

## Phase 11: Performance Tracking & Database

**Objective**: Optional agent that critically examines investment recommendations.

#### Tasks
- [ ] **Create DevilsAdvocateAgent**:
  ```python
  class DevilsAdvocateAgent:
      """
      An agent that critically examines investment recommendations
      and provides counter-arguments based on facts.
      """

      role = "Senior Risk Analyst & Critical Reviewer"
      goal = "Challenge investment theses and identify potential flaws"
      backstory = """
          You are a contrarian analyst with 25 years of experience.
          You've seen countless investment theses fail. Your job is to
          find the weaknesses in any recommendation - not to be negative,
          but to ensure recommendations are robust and well-reasoned.
          You focus on FACTS, not speculation.
      """
  ```

- [ ] **Define criticism categories**:
  - **Valuation Concerns**: Is the price justified by fundamentals?
  - **Technical Warnings**: Are there bearish signals being ignored?
  - **Macro Risks**: Sector headwinds, economic factors
  - **Competitive Threats**: Market share risks, disruption
  - **Historical Patterns**: Similar setups that failed
  - **Data Quality Issues**: Missing or stale data
  - **Confidence Calibration**: Is confidence score justified?

### 10.2 Critique Implementation

#### Tasks
- [ ] **Create critique prompt template**:
  ```python
  DEVILS_ADVOCATE_PROMPT = """
  You are reviewing the following BUY recommendation:

  Ticker: {ticker}
  Score: {score}/100
  Confidence: {confidence}%

  Technical Analysis Summary:
  {technical_summary}

  Fundamental Analysis Summary:
  {fundamental_summary}

  Sentiment Analysis Summary:
  {sentiment_summary}

  Investment Thesis:
  {investment_thesis}

  YOUR TASK:
  Critically examine this recommendation and identify:
  1. What could go WRONG with this investment?
  2. What facts or data CONTRADICT the bullish thesis?
  3. What risks are being UNDERWEIGHTED?
  4. Is the confidence score JUSTIFIED given the uncertainties?
  5. What would make you change this from BUY to HOLD or AVOID?

  Provide specific, fact-based criticisms. Do not speculate.
  Rate the overall thesis robustness (0-100).

  Output as JSON:
  {
      "robustness_score": int,
      "primary_concerns": [
          {"category": "str", "concern": "str", "severity": "high|medium|low"}
      ],
      "overlooked_risks": ["str"],
      "confidence_adjustment": int,  // Suggested adjustment (-30 to +10)
      "recommendation_change": "maintain|downgrade|upgrade",
      "summary": "str"
  }
  """
  ```

- [ ] **Implement robustness scoring** (0-100)
- [ ] **Add confidence adjustment** based on critique
- [ ] **Flag recommendations** with low robustness scores

### 10.3 Integration

#### Tasks
- [ ] **Add to analysis pipeline** (optional stage):
  ```bash
  # Enable devil's advocate
  uv run python -m src.main analyze --ticker AAPL --llm --with-critique

  # Always enable via config
  ```

- [ ] **Add critique section to reports**:
  ```markdown
  ## Critical Review (Devil's Advocate)

  **Robustness Score**: 65/100

  ### Primary Concerns
  1. **Valuation** (High): P/E ratio of 35 is 40% above sector average
  2. **Technical** (Medium): RSI showing overbought conditions
  3. **Macro** (Medium): Rising interest rates may pressure growth stocks

  ### Overlooked Risks
  - Regulatory scrutiny in EU markets
  - Key patent expiring in 2025

  ### Confidence Adjustment
  Original: 78% → Adjusted: 68% (-10%)
  ```

#### Configuration
```yaml
agents:
  devils_advocate:
    enabled: true
    apply_to: ["BUY"]  # Only critique BUY signals
    min_score_to_critique: 60  # Don't waste tokens on weak signals
    confidence_adjustment_enabled: true
    include_in_report: true
```

#### Deliverables
- [ ] DevilsAdvocateAgent implementation
- [ ] Critique prompt template
- [ ] Robustness scoring (0-100)
- [ ] Confidence adjustment logic
- [ ] CLI `--with-critique` flag
- [ ] Report integration with critique section

---

**Phase 10 Status: PLANNED**

**Estimated Effort**: 2-3 days
**Priority**: 🟡 High - Reduces overconfidence in recommendations

---

## Phase 11: Performance Tracking & Database

### Overview

Track recommendation performance over time with a local file-based database.

### 9.1 Performance Database

**Objective**: Persist recommendations and track their outcomes.

#### Tasks
- [ ] **Create SQLite database** (`data/performance.db`):
  ```sql
  CREATE TABLE recommendations (
      id TEXT PRIMARY KEY,
      ticker TEXT NOT NULL,
      analysis_date DATE NOT NULL,
      signal_type TEXT NOT NULL,
      score REAL NOT NULL,
      confidence REAL NOT NULL,
      technical_score REAL,
      fundamental_score REAL,
      sentiment_score REAL,
      analysis_mode TEXT,
      llm_model TEXT,
      created_at TIMESTAMP
  );

  CREATE TABLE price_tracking (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      recommendation_id TEXT REFERENCES recommendations(id),
      tracking_date DATE NOT NULL,
      days_since_recommendation INTEGER,
      price REAL NOT NULL,
      price_change_pct REAL,
      benchmark_change_pct REAL
  );

  CREATE TABLE performance_summary (
      ticker TEXT,
      signal_type TEXT,
      analysis_mode TEXT,
      period_days INTEGER,
      total_recommendations INTEGER,
      avg_return REAL,
      win_rate REAL,
      updated_at TIMESTAMP
  );
  ```

- [ ] **Create PerformanceTracker class**
- [ ] **Automated daily price tracking job**
- [ ] **Performance report generation**

#### Configuration
```yaml
performance_tracking:
  enabled: true
  database_path: "data/performance.db"
  tracking_periods: [7, 30, 90, 180]
  benchmark_ticker: "SPY"
  auto_update: true
```

#### Deliverables
- [ ] SQLite database schema
- [ ] PerformanceTracker implementation
- [ ] `track-performance` CLI command
- [ ] `performance-report` CLI command

---

**Phase 11 Status: PLANNED**

**Estimated Effort**: 3-4 days
**Priority**: 🟡 High - Enables measuring system effectiveness

---

## Phase 12: Enhanced Technical Analysis

### Overview

Expand technical analysis with advanced indicators and candlestick patterns.

### 10.1 Additional Indicators

- [ ] **Momentum**: Stochastic, Williams %R, CCI, ROC, MFI
- [ ] **Trend**: ADX, Parabolic SAR, Ichimoku Cloud, SuperTrend
- [ ] **Volatility**: Bollinger Bands, Keltner Channels, Donchian
- [ ] **Volume**: OBV, A/D Line, CMF, VWAP

### 10.2 Candlestick Patterns

- [ ] **Reversal**: Hammer, Engulfing, Morning/Evening Star, Doji
- [ ] **Continuation**: Three Methods, Marubozu
- [ ] **Chart Patterns**: Head & Shoulders, Double Top/Bottom, Triangles

### 10.3 Integration

- [ ] Pattern strength scoring
- [ ] Context analysis
- [ ] Technical Agent prompt updates

---

**Phase 12 Status: PLANNED**

**Estimated Effort**: 4-5 days
**Priority**: 🟢 Medium - Enhances analysis quality

---

## Phase 13: Advanced Features & Integrations

### Overview

Additional advanced features for power users and system integration.

### 13.1 Multi-Timeframe Analysis

- [ ] Analyze across daily, weekly, monthly timeframes
- [ ] Detect timeframe alignment/divergence
- [ ] Weighted multi-timeframe signals

### 13.2 Sector Analysis

- [ ] Sector rotation tracking
- [ ] Sector-relative strength rankings
- [ ] Sector concentration warnings

### 13.3 Correlation Analysis

- [ ] Portfolio correlation matrix
- [ ] Diversification scoring
- [ ] Correlation-adjusted position sizing

### 13.4 Event Calendar Integration

- [ ] Earnings calendar awareness
- [ ] Economic event tracking (FOMC, CPI, etc.)
- [ ] Pre/post event analysis patterns

### 13.5 Alerts & Notifications

- [ ] Price threshold alerts
- [ ] Signal change notifications
- [ ] Performance milestone alerts
- [ ] Email/Slack integration

### 13.6 Web Dashboard (Optional)

- [ ] Visual report viewer
- [ ] Interactive charts
- [ ] Performance tracking dashboard
- [ ] Portfolio simulation

---

**Phase 13 Status: PLANNED**

**Estimated Effort**: 5-7 days
**Priority**: 🟢 Low - Nice-to-have features

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
6. **Per-agent model selection**: Use cheaper models for simple tasks
7. **True test mode**: Zero-cost development testing

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API rate limits | Multiple providers, aggressive caching |
| Cost overruns | Daily monitoring, hard limits, test mode |
| Data quality issues | Validation, multiple sources |
| LLM hallucinations | Structured outputs, Devil's Advocate |
| Overconfidence | Devil's Advocate, performance tracking |
| Expensive testing | True test mode with fixtures |

---

## Success Criteria Checklist

### Completed (Phases 1-7) ✅
- [x] System runs daily in <15 minutes
- [x] Monthly costs ≤€100
- [x] Generates signals with scores and recommendations
- [x] Reports include confidence scores
- [x] Portfolio allocation suggestions
- [x] Risk warnings included
- [x] Handles API failures gracefully
- [x] LLM agents reasoning about analysis
- [x] Natural language insights
- [x] Token usage tracking
- [x] Hybrid intelligence with fallback
- [x] True test mode with zero API/LLM costs
- [x] Reproducible test results with fixtures
- [x] MockLLMClient for offline testing

### Phase 8 Targets (HIGH PRIORITY)
- [ ] Historical date analysis (`--date`) working
- [ ] Backtesting framework operational
- [ ] Backtest reports with accuracy metrics

### Phase 9-13 Targets
- [ ] Per-agent model configuration
- [ ] Devil's Advocate agent integrated
- [ ] Performance tracking database
- [ ] Advanced technical indicators

---

## Quick Start Commands

```bash
# Install dependencies
uv sync

# Configure settings
cp config/default.yaml config/local.yaml

# Set API keys
export ANTHROPIC_API_KEY=your_key
export FINNHUB_API_KEY=your_key

# TRUE TEST MODE (Phase 7) ✅ - No API/LLM calls, zero cost
uv run python -m src.main analyze --test
uv run python -m src.main analyze --test --llm  # Uses MockLLMClient

# Test with specific fixture
uv run python -m src.main analyze --test --fixture test_ticker_minimal

# Live analysis
uv run python -m src.main analyze --ticker AAPL,MSFT
uv run python -m src.main analyze --ticker AAPL --llm

# Historical analysis (Phase 8 - HIGH PRIORITY)
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01

# Backtest (Phase 8 - HIGH PRIORITY)
uv run python -m src.main backtest --tickers AAPL,MSFT --start 2024-01-01 --end 2024-06-30

# With critique (Phase 10 - Planned)
uv run python -m src.main analyze --ticker AAPL --llm --with-critique

# Performance report (Phase 11 - Planned)
uv run python -m src.main performance-report --period 30

# Help
uv run python -m src.main --help
```

---

*This roadmap serves as the canonical implementation guide for the NordInvest project. Update task checkboxes as development progresses.*
