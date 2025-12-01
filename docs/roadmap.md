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
| Phase 7 | Future | Advanced Features & Backtesting | 📋 Planned |

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

## Phase 7: Advanced Features & Backtesting (Future)

### Overview

Phase 7 introduces advanced capabilities for performance tracking, backtesting, enhanced analysis, and system optimization. These features transform NordInvest from a recommendation engine into a complete investment analysis platform with measurable performance metrics.

### 7.1 Per-Agent LLM Model Configuration

**Objective**: Allow different LLM models for different agents based on task complexity and cost optimization.

#### Tasks
- [ ] **Extend configuration schema** for per-agent model settings:
  ```yaml
  llm:
    default:
      provider: anthropic
      model: claude-sonnet-4-20250514
      temperature: 0.7

    agents:
      market_scanner:
        model: claude-haiku  # Faster, cheaper for initial screening
        temperature: 0.3

      technical_analyst:
        model: claude-sonnet-4-20250514
        temperature: 0.5

      fundamental_analyst:
        model: claude-sonnet-4-20250514  # Complex reasoning
        temperature: 0.7

      sentiment_analyst:
        model: claude-haiku  # Good for classification
        temperature: 0.3

      signal_synthesizer:
        model: claude-sonnet-4-20250514  # Critical decisions
        temperature: 0.5

      devil_advocate:  # New agent (see 7.5)
        model: claude-sonnet-4-20250514
        temperature: 0.8  # More creative criticism
  ```
- [ ] **Update CrewAI agent factory** to accept per-agent LLM configs
- [ ] **Implement model fallback chain**: If preferred model fails, try alternatives
- [ ] **Add cost tracking per agent** for optimization insights
- [ ] **Create CLI flag** for model override: `--model-override technical:gpt-4`

#### Benefits
- Optimize costs by using cheaper models for simpler tasks
- Use more powerful models for critical synthesis decisions
- Enable A/B testing of model performance per agent

---

### 7.2 Enhanced Technical Analysis

**Objective**: Expand technical analysis capabilities with advanced indicators and candlestick pattern recognition.

#### Tasks

##### 7.2.1 Additional Technical Indicators
- [ ] **Momentum Indicators**:
  - Stochastic Oscillator (%K, %D)
  - Williams %R
  - Commodity Channel Index (CCI)
  - Rate of Change (ROC)
  - Money Flow Index (MFI)

- [ ] **Trend Indicators**:
  - Average Directional Index (ADX)
  - Parabolic SAR
  - Ichimoku Cloud (Tenkan, Kijun, Senkou A/B, Chikou)
  - SuperTrend

- [ ] **Volatility Indicators**:
  - Bollinger Bands (with %B and Bandwidth)
  - Keltner Channels
  - Donchian Channels
  - Historical Volatility (HV)

- [ ] **Volume Indicators**:
  - On-Balance Volume (OBV)
  - Accumulation/Distribution Line
  - Chaikin Money Flow (CMF)
  - Volume Weighted Average Price (VWAP)

##### 7.2.2 Candlestick Pattern Recognition
- [ ] **Implement pattern detection library** (or integrate TA-Lib):
  ```python
  class CandlestickPatternDetector:
      def detect_patterns(self, ohlcv_data: pd.DataFrame) -> list[CandlestickPattern]:
          patterns = []
          patterns.extend(self._detect_reversal_patterns(ohlcv_data))
          patterns.extend(self._detect_continuation_patterns(ohlcv_data))
          return patterns
  ```

- [ ] **Reversal Patterns**:
  - Hammer / Inverted Hammer
  - Bullish/Bearish Engulfing
  - Morning Star / Evening Star
  - Three White Soldiers / Three Black Crows
  - Doji (Standard, Dragonfly, Gravestone)
  - Piercing Line / Dark Cloud Cover
  - Tweezer Tops / Bottoms

- [ ] **Continuation Patterns**:
  - Rising/Falling Three Methods
  - Bullish/Bearish Marubozu
  - Spinning Tops
  - Windows (Gaps)

- [ ] **Chart Patterns** (multi-day):
  - Head and Shoulders
  - Double Top / Double Bottom
  - Triangle patterns (Ascending, Descending, Symmetrical)
  - Flag and Pennant
  - Cup and Handle

##### 7.2.3 Pattern Scoring Integration
- [ ] **Create pattern strength scoring** (0-100)
- [ ] **Add pattern context analysis** (volume confirmation, trend alignment)
- [ ] **Integrate with Technical Analysis Agent** prompts
- [ ] **Update signal weighting** to include pattern scores

#### Configuration
```yaml
analysis:
  technical:
    indicators:
      - sma: [20, 50, 200]
      - ema: [12, 26]
      - rsi: 14
      - macd: [12, 26, 9]
      - bollinger: [20, 2]
      - stochastic: [14, 3, 3]
      - adx: 14
      - ichimoku: true

    candlestick_patterns:
      enabled: true
      min_confidence: 0.7
      lookback_days: 60
```

---

### 7.3 Historical Date Analysis & Backtesting

**Objective**: Enable analysis based on historical dates for backtesting and performance evaluation.

#### Tasks

##### 7.3.1 Historical Data Fetching
- [ ] **Add `--date` CLI parameter**:
  ```bash
  # Analyze as if it were June 1, 2024
  uv run python -m src.main analyze --ticker AAPL --date 2024-06-01

  # Analyze with LLM using historical data
  uv run python -m src.main analyze --ticker AAPL --date 2024-06-01 --llm
  ```

- [ ] **Implement historical data fetcher**:
  ```python
  class HistoricalDataFetcher:
      def fetch_as_of_date(
          self,
          ticker: str,
          as_of_date: date,
          lookback_days: int = 365
      ) -> HistoricalContext:
          """Fetch all data as it would have been available on as_of_date."""
          return HistoricalContext(
              price_data=self._fetch_prices(ticker, end_date=as_of_date),
              fundamentals=self._fetch_fundamentals(ticker, as_of_date),
              news=self._fetch_news(ticker, as_of_date),
              # Only include data available BEFORE as_of_date
          )
  ```

- [ ] **Update cache manager** for historical queries
- [ ] **Prevent future data leakage** (strict date filtering)

##### 7.3.2 Backtesting Framework
- [ ] **Create backtesting engine**:
  ```python
  class BacktestEngine:
      def run_backtest(
          self,
          tickers: list[str],
          start_date: date,
          end_date: date,
          interval: str = "weekly"  # daily, weekly, monthly
      ) -> BacktestResult:
          """Run analysis at each interval and track outcomes."""
          pass
  ```

- [ ] **Implement backtest CLI command**:
  ```bash
  # Backtest over 6 months
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

##### 7.3.3 Configuration
```yaml
backtesting:
  enabled: true
  default_lookback_days: 365
  benchmark_ticker: "SPY"
  evaluation_periods:
    - 30   # 1 month
    - 90   # 3 months
    - 180  # 6 months
```

---

### 7.4 Performance Tracking Database

**Objective**: Track recommendation performance over time with a local file-based database.

#### Tasks

##### 7.4.1 Database Schema Design
- [ ] **Create SQLite database** (`data/performance.db`):
  ```sql
  -- Recommendations table
  CREATE TABLE recommendations (
      id TEXT PRIMARY KEY,
      ticker TEXT NOT NULL,
      analysis_date DATE NOT NULL,
      signal_type TEXT NOT NULL,  -- BUY, HOLD, AVOID
      score REAL NOT NULL,
      confidence REAL NOT NULL,
      technical_score REAL,
      fundamental_score REAL,
      sentiment_score REAL,
      target_price REAL,
      analysis_mode TEXT,  -- rule_based, llm
      llm_model TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  -- Price tracking table
  CREATE TABLE price_tracking (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      recommendation_id TEXT REFERENCES recommendations(id),
      tracking_date DATE NOT NULL,
      days_since_recommendation INTEGER,
      price REAL NOT NULL,
      price_change_pct REAL,
      benchmark_change_pct REAL,  -- SPY comparison
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  -- Performance summary table (materialized for fast queries)
  CREATE TABLE performance_summary (
      ticker TEXT,
      signal_type TEXT,
      analysis_mode TEXT,
      period_days INTEGER,
      total_recommendations INTEGER,
      avg_return REAL,
      win_rate REAL,
      avg_confidence REAL,
      confidence_accuracy_correlation REAL,
      updated_at TIMESTAMP
  );
  ```

##### 7.4.2 Performance Tracker Implementation
- [ ] **Create PerformanceTracker class**:
  ```python
  class PerformanceTracker:
      def __init__(self, db_path: Path = Path("data/performance.db")):
          self.db = sqlite3.connect(db_path)

      def record_recommendation(self, signal: InvestmentSignal) -> str:
          """Store a new recommendation."""
          pass

      def update_price_tracking(self) -> None:
          """Daily job to update prices for all tracked recommendations."""
          pass

      def get_performance_report(
          self,
          ticker: str = None,
          period_days: int = 30,
          signal_type: str = None
      ) -> PerformanceReport:
          """Generate performance statistics."""
          pass
  ```

##### 7.4.3 Automated Tracking
- [ ] **Create daily tracking job**:
  ```bash
  # Add to cron or scheduler
  uv run python -m src.main track-performance
  ```

- [ ] **Generate performance reports**:
  ```bash
  # View performance summary
  uv run python -m src.main performance-report --period 30

  # Export to CSV
  uv run python -m src.main performance-report --format csv --output performance.csv
  ```

##### 7.4.4 Performance Dashboard (CLI)
- [ ] **Add performance summary to daily reports**
- [ ] **Include historical accuracy in signal confidence**
- [ ] **Show model comparison** (rule-based vs LLM)

#### Configuration
```yaml
performance_tracking:
  enabled: true
  database_path: "data/performance.db"
  tracking_periods: [7, 30, 90, 180]  # days
  benchmark_ticker: "SPY"
  auto_update: true  # Update prices daily
```

---

### 7.5 Devil's Advocate Agent

**Objective**: Add an optional agent that critically challenges recommendations to reduce overconfidence and identify blind spots.

#### Tasks

##### 7.5.1 Agent Design
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

##### 7.5.2 Criticism Framework
- [ ] **Define criticism categories**:
  - **Valuation Concerns**: Is the price justified by fundamentals?
  - **Technical Warnings**: Are there bearish signals being ignored?
  - **Macro Risks**: Sector headwinds, economic factors
  - **Competitive Threats**: Market share risks, disruption
  - **Historical Patterns**: Similar setups that failed
  - **Data Quality Issues**: Missing or stale data
  - **Confidence Calibration**: Is confidence score justified?

##### 7.5.3 Implementation
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

##### 7.5.4 Integration
- [ ] **Add to analysis pipeline** (optional stage):
  ```bash
  # Enable devil's advocate
  uv run python -m src.main analyze --ticker AAPL --llm --with-critique

  # Always enable via config
  ```

- [ ] **Adjust final scores** based on critique:
  - Apply confidence adjustment from critique
  - Flag recommendations with low robustness scores
  - Include critique summary in reports

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

---

### 7.6 Additional Future Enhancements

#### 7.6.1 Multi-Timeframe Analysis
- [ ] Analyze across multiple timeframes (daily, weekly, monthly)
- [ ] Detect timeframe alignment/divergence
- [ ] Weighted multi-timeframe signals

#### 7.6.2 Sector Rotation Analysis
- [ ] Track sector momentum and rotation
- [ ] Identify sector leaders/laggards
- [ ] Sector-relative strength rankings

#### 7.6.3 Correlation Analysis
- [ ] Portfolio correlation matrix
- [ ] Identify diversification opportunities
- [ ] Correlation-adjusted position sizing

#### 7.6.4 Event Calendar Integration
- [ ] Earnings calendar awareness
- [ ] Economic event tracking (FOMC, CPI, etc.)
- [ ] Pre/post event analysis patterns

#### 7.6.5 Alert System
- [ ] Price threshold alerts
- [ ] Signal change notifications
- [ ] Performance milestone alerts
- [ ] Email/Slack integration

#### 7.6.6 Web Dashboard
- [ ] Visual report viewer
- [ ] Interactive charts
- [ ] Performance tracking dashboard
- [ ] Portfolio simulation

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

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API rate limits | Multiple providers, aggressive caching |
| Cost overruns | Daily cost monitoring, hard limits |
| Data quality issues | Validation, multiple sources |
| LLM hallucinations | Structured outputs, fact verification, Devil's Advocate |
| Market data delays | Acknowledge in reports, use EOD data |
| Overconfidence | Devil's Advocate agent, performance tracking |

---

## Success Criteria Checklist

### Current System (Phases 1-6) ✅
- [x] System runs daily in <15 minutes
- [x] Monthly costs ≤€100 (including LLM usage)
- [x] Generates signals with scores and recommendations
- [x] Reports include confidence scores
- [x] Portfolio allocation suggestions provided
- [x] Risk warnings included where appropriate
- [x] System handles API failures gracefully
- [x] LLM agents actively reasoning about analysis
- [x] Natural language insights in reports
- [x] Token usage tracking and cost monitoring
- [x] Hybrid intelligence (LLM + rule-based fallback)

### Target System (Phase 7)
- [ ] Per-agent model configuration working
- [ ] Advanced technical indicators implemented
- [ ] Candlestick pattern recognition functional
- [ ] Historical date analysis (`--date`) working
- [ ] Backtesting framework operational
- [ ] Performance tracking database active
- [ ] Devil's Advocate agent integrated
- [ ] Performance reports with historical accuracy

---

## Quick Start Commands

```bash
# Install dependencies
uv sync

# Configure settings
cp config/default.yaml config/local.yaml
# Edit config/local.yaml with your preferences

# Set API keys
export ANTHROPIC_API_KEY=your_key
export FINNHUB_API_KEY=your_key

# Run analysis (rule-based)
uv run python -m src.main analyze --ticker AAPL,MSFT

# Run analysis (LLM-powered)
uv run python -m src.main analyze --ticker AAPL,MSFT --llm

# Run with devil's advocate (Phase 7)
uv run python -m src.main analyze --ticker AAPL --llm --with-critique

# Historical analysis (Phase 7)
uv run python -m src.main analyze --ticker AAPL --date 2024-06-01

# Run backtest (Phase 7)
uv run python -m src.main backtest --tickers AAPL,MSFT --start 2024-01-01 --end 2024-06-30

# View performance (Phase 7)
uv run python -m src.main performance-report --period 30

# View help
uv run python -m src.main --help
```

---

*This roadmap serves as the canonical implementation guide for the NordInvest project. Update task checkboxes as development progresses.*
