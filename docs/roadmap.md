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
- [x] **SentimentAnalyzerTool**: Score news sentiment
- [x] **ReportGeneratorTool**: Format output documents

#### 3.2 Market Scanner Agent
- [x] Define agent role, goal, and backstory
- [x] Implement daily scanning logic:
  - Fetch price data for all tracked instruments
  - Detect unusual volume or price movements
  - Identify instruments crossing key technical levels
- [x] Create anomaly detection heuristics
- [x] Output: List of instruments requiring analysis

#### 3.3 Fundamental Analysis Agent
- [x] Define agent configuration
- [x] Implement analysis capabilities:
  - Revenue & EPS growth (YoY, QoQ)
  - Profit margins and cash flow analysis
  - Debt ratio assessment
  - Valuation metrics (P/E, EV/EBITDA, P/B, PEG)
- [x] Create fundamental scoring system (0-100)
- [x] Output: Fundamental scores with explanations

#### 3.4 Technical Analysis Agent
- [x] Define agent configuration
- [x] Implement indicator calculations:
  - Moving averages (SMA 20/50/200)
  - RSI (14-day)
  - MACD (12, 26, 9)
  - ATR for volatility
  - Volume analysis
- [x] Create trend identification logic
- [x] Implement pattern detection (support/resistance)
- [x] Output: Technical scores with trend classification

#### 3.5 News & Sentiment Agent
- [x] Define agent configuration
- [x] Implement news processing:
  - Fetch recent news (24-48 hours)
  - Filter by relevance
  - Extract key events
- [x] Create sentiment scoring:
  - Positive/negative/neutral classification
  - Event importance weighting
- [x] Output: Sentiment scores with event summaries

#### 3.6 Agent Orchestration
- [x] Configure AnalysisCrew with all agents
- [x] Define task dependencies and flow
- [x] Implement parallel execution where possible
- [x] Set up agent communication protocols

### Deliverables
- ✅ 5 functional analysis agents (scanner, technical, fundamental, sentiment, synthesizer)
- ✅ 5 custom tools (price fetcher, news fetcher, technical indicators, sentiment analyzer, report generator)
- ✅ Agent orchestration with AnalysisCrew
- ✅ Parallel execution for technical/fundamental/sentiment with sequential synthesis

**Status: COMPLETE - Rule-Based Implementation** (Commits: c8fa19f - 4e15fe7)

**Note:** Current implementation uses custom `BaseAgent` class with rule-based analysis (mathematical formulas, technical indicators, simple scoring). **No actual CrewAI framework or LLM integration.** All analysis is deterministic and based on:
- Technical indicators (RSI, MACD, moving averages)
- Mathematical scoring algorithms
- Simple sentiment counting (positive/negative news)
- Weighted score combinations

**Next Phase Required:** Actual CrewAI/LLM integration (see Phase 6 below)

### Current Architecture (Custom Agent Pattern)
```python
from src.agents.base import BaseAgent, AgentConfig

class TechnicalAnalysisAgent(BaseAgent):
    def __init__(self, tools: list = None):
        config = AgentConfig(
            role="Technical Analyst",
            goal="Analyze technical indicators",
            backstory="Expert in technical analysis..."
        )
        super().__init__(config, tools or [])

    def execute(self, task: str, context: dict) -> dict:
        # Rule-based logic only - no LLM calls
        indicators = self._calculate_indicators(context)
        score = self._simple_scoring(indicators)
        return {"technical_score": score}
```

**Note:** Despite CrewAI dependency being installed, **no actual CrewAI imports or usage exists**. All agents use custom `BaseAgent` class with deterministic, rule-based `execute()` methods.

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
  - Historical accuracy (if available)
- [x] Generate recommendations:
  - **Buy**: Score > 70, confidence > 60%
  - **Hold**: Score 40-70
  - **Avoid**: Score < 40 or high risk flags
- [x] Output: Ranked list of opportunities with full context

#### 4.2 Portfolio Allocation Engine
- [x] Implement position sizing:
  - Kelly criterion (modified)
  - Maximum position size (% of capital)
  - Sector concentration limits
- [x] Create diversification logic:
  - Market diversification
  - Sector diversification
  - Instrument type balance
- [x] Calculate allocation suggestions in EUR and %
- [x] Account for monthly deposits in strategy

#### 4.3 Risk Assessment Module
- [x] Implement risk scoring:
  - Volatility assessment (ATR-based)
  - Sector risk flags
  - Liquidity concerns
  - Concentration warnings
- [x] Create risk-adjusted return estimates
- [x] Add disclaimer generation

#### 4.4 Daily Report Generation
- [x] Define report model with all required sections
- [x] Implement report sections:
  - Market Overview (index movements, sector heatmap)
  - Top 5-10 Opportunities (with full signal details)
  - Portfolio Alerts (threshold crossings, earnings)
  - Key News Summary (bullet points with scores)
  - Watchlist Updates (additions/removals)
- [x] Create Markdown report template
- [ ] Add HTML report option (optional)
- [ ] Implement email notification (optional)

#### 4.5 Output Formatting
- [x] Define JSON schema for signals
- [x] Create human-readable report templates
- [x] Implement export utilities (Markdown, JSON)

### Deliverables
- ✅ InvestmentSignal model with complete signal data (7 files, 1215 insertions)
- ✅ Portfolio allocation engine using modified Kelly criterion with constraints
- ✅ Risk assessment module with multi-factor risk scoring
- ✅ Daily report generator with Markdown and JSON formats
- ✅ PortfolioAllocation model with diversification tracking
- ✅ RiskAssessment model with risk flags and level determination

**Status: COMPLETE** (Commit: 9ff356b)

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
- [x] End-to-end pipeline test
- [x] Verify agent communication
- [x] Test with various market conditions (mock data)
- [x] Validate output formats
- [x] Cost tracking verification

#### 5.2 Error Handling & Resilience
- [x] Add comprehensive error handling (custom exceptions)
- [x] Implement graceful degradation:
  - Fallback data providers
  - Cached data usage on API failures
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
- [ ] Update architecture documentation
- [ ] Add deployment guide
- [ ] Create usage examples
- [ ] Add troubleshooting guide

### Deliverables
- ✅ End-to-end AnalysisPipeline orchestrator (4 modules, 2100+ lines)
- ✅ Comprehensive error handling (hierarchical exceptions, 8 types)
- ✅ Resilience patterns (retry, fallback, circuit breaker, rate limiter, graceful degradation)
- ✅ Scheduling infrastructure (CronScheduler, RunLog, statistics)
- ✅ Integrated CLI with full pipeline execution
- ✅ Test suite for integration testing (TestAnalysisPipeline, TestErrorHandling, TestScheduling, TestResilience)
- ✅ Production-ready error recovery and monitoring

**Status: COMPLETE** (Commit: ab39de1)

---

## Phase 6: CrewAI & LLM Integration (Days 15-18)

### Implementation Status: **IN PROGRESS**

**Current State Summary:**
- ✅ LLM configuration infrastructure complete
- ✅ CrewAI agents created and configured
- ✅ Hybrid intelligence system with fallback implemented
- ✅ Token tracking and cost monitoring ready
- ⏳ Integration with main pipeline and testing

**What's Being Implemented:**
- Actual CrewAI `Agent` and `Task` classes (replacing custom `BaseAgent`)
- LLM-powered analysis using Anthropic Claude API
- Intelligent reasoning for all analysis phases
- Hybrid system with fallback to rule-based analysis on LLM failures
- Token counting and cost monitoring
- Comprehensive test suite (all tests passing)

### Objectives
- Replace rule-based agents with actual CrewAI LLM-powered agents
- Implement intelligent reasoning for fundamental analysis
- Add natural language insight generation
- Enable agent collaboration and delegation

### Tasks

#### 6.1 CrewAI Framework Integration
- [x] Import actual CrewAI classes: `from crewai import Agent, Task, Crew`
- [x] Configure LLM providers:
  - [x] Set up Anthropic Claude integration
  - [x] Configure OpenAI as fallback
  - [x] Implement LLM client initialization (src/config/llm.py)
- [x] Create LLM configuration management:
  - [x] Model selection (claude-3-5-sonnet, gpt-4, etc.)
  - [x] Temperature and parameter tuning
  - [x] Token usage tracking and logging (src/llm/token_tracker.py)

#### 6.2 Convert Agents to CrewAI Agents
- [x] **Market Scanner Agent**:
  - [x] Replace custom BaseAgent with CrewAI Agent (src/agents/crewai_agents.py)
  - [x] Create LLM-powered task for anomaly detection
  - [x] Use LLM to reason about price movements and patterns
  - [x] Generate natural language explanations for anomalies

- [x] **Technical Analysis Agent**:
  - [x] Convert to CrewAI Agent with technical tools
  - [x] Keep indicator calculations (RSI, MACD) as tools (src/llm/tools.py)
  - [x] Use LLM to interpret indicator combinations
  - [x] Generate trading insights from patterns

- [x] **Fundamental Analysis Agent**:
  - [x] Replace stub implementation with real LLM analysis (src/agents/crewai_agents.py)
  - [x] Use LLM to analyze financial statements
  - [x] Reason about company health and growth prospects
  - [x] Compare metrics against industry benchmarks

- [x] **Sentiment Analysis Agent**:
  - [x] Enhance with LLM-powered news analysis (src/agents/crewai_agents.py)
  - [x] Extract key events and implications
  - [x] Assess market impact of news
  - [x] Generate sentiment narratives

- [x] **Signal Synthesizer Agent**:
  - [x] Use LLM to synthesize all analyses (src/agents/crewai_agents.py)
  - [x] Generate comprehensive investment thesis
  - [x] Provide detailed reasoning for recommendations
  - [x] Create risk-aware narratives

#### 6.3 Create CrewAI Tasks
- [x] Define Task objects for each analysis phase (src/agents/crewai_agents.py):
  - [x] Market scanning task with anomaly detection instructions
  - [x] Technical analysis task with indicator analysis instructions
  - [x] Fundamental analysis task with financial metric instructions
  - [x] Sentiment analysis task with news processing instructions
  - [x] Signal synthesis task combining all analyses
- [x] Implement sequential task dependencies
- [x] Enable task result sharing between agents (HybridAnalysisCrew)
- [x] Add context propagation

#### 6.4 LLM Prompt Engineering
- [x] Design prompts for each agent (src/llm/prompts.py):
  - [x] System prompts defining agent expertise
  - [x] Task-specific prompts with structured JSON outputs
  - [x] Data formatting and context injection
- [x] Implement prompt templates with variables
- [x] Create output structure examples
- [x] Add JSON schema for structured responses

#### 6.5 Hybrid Intelligence System
- [x] Keep rule-based calculations as tools (indicators, metrics) (src/llm/tools.py)
- [x] Use LLM for reasoning and interpretation (HybridAnalysisAgent)
- [x] Implement fallback to rule-based on LLM failures
- [x] Create quality scoring for LLM outputs
- [x] Support multiple LLM providers (Anthropic, OpenAI, local)

#### 6.6 Cost Control & Monitoring
- [x] Implement token counting and cost tracking (src/llm/token_tracker.py)
- [x] Set daily/monthly budget limits (TokenTrackerConfig)
- [x] Create alert system for cost overruns (warning thresholds)
- [x] Track costs per request and per model
- [x] Daily and monthly statistics aggregation

#### 6.7 Testing & Validation
- [x] Comprehensive test suite for all components (tests/unit/llm/test_integration.py)
- [x] Validate configuration loading and validation
- [x] Test token tracking accuracy
- [x] Test orchestrator initialization and status reporting
- [x] All tests passing (12/12)

### Deliverables
- [x] Actual CrewAI integration with Agent, Task, Crew classes
- [x] LLM-powered agents with fallback to rule-based implementations
- [x] Natural language insights enabled via prompt templates (src/llm/prompts.py)
- [x] Token usage tracking and cost monitoring (src/llm/token_tracker.py)
- [x] Hybrid system with HybridAnalysisAgent and HybridAnalysisCrew
- [x] Comprehensive prompt library with system and task templates
- [x] High-level LLM orchestrator (src/llm/integration.py)
- [x] Integration with CrewAI Tool adapters (src/llm/tools.py)
- [x] Full test suite with 12 passing tests

**Status: SUBSTANTIALLY COMPLETE - Core infrastructure and testing done**

**Remaining Work:**
- Integration with main AnalysisPipeline orchestrator
- End-to-end testing with real market data
- Performance optimization and prompt tuning
- Cost monitoring dashboard/reports

### Code Architecture Example

**What We've Built:**

1. **CrewAI Agents** (src/agents/crewai_agents.py):
```python
technical_agent = Agent(
    role="Senior Technical Analyst",
    goal="Analyze price charts and indicators to identify trading opportunities",
    backstory="Expert technical analyst...",
    tools=[fetch_price_data, calculate_indicators],
    llm=initialize_llm_client(llm_config),
    verbose=False
)

technical_task = Task(
    description="Analyze {ticker} using technical indicators...",
    agent=technical_agent,
    expected_output="Structured technical analysis with score (0-100)"
)
```

2. **Hybrid Wrapper** (src/agents/hybrid.py):
```python
hybrid_agent = HybridAnalysisAgent(
    crewai_agent=technical_agent,
    fallback_agent=TechnicalAnalysisAgent(),  # Rule-based fallback
    token_tracker=tracker,
    enable_fallback=True
)

result = hybrid_agent.execute_task(task)
# Returns: {"status": "success", "result": analysis, "used_llm": True, "used_fallback": False}
```

3. **Prompt Templates** (src/llm/prompts.py):
```python
prompt = PromptTemplates.get_technical_prompt(ticker, data)
# Structured prompt with data fields and JSON output schema
```

4. **Cost Monitoring** (src/llm/token_tracker.py):
```python
tracker = TokenTracker(config)
cost = tracker.track(input_tokens=100, output_tokens=50, model="claude-3-5-sonnet")
daily_stats = tracker.get_daily_stats()
# Tracks: total tokens, cost (€), requests, warnings at 80% threshold
```

### Migration Strategy
1. **Phase 6.1**: Set up LLM infrastructure without breaking existing system
2. **Phase 6.2**: Create parallel LLM agents alongside rule-based ones
3. **Phase 6.3**: A/B test LLM vs rule-based outputs
4. **Phase 6.4**: Gradually transition to LLM as primary with rule-based fallback
5. **Phase 6.5**: Full LLM integration with monitoring and optimization

### Expected Benefits
- **Richer Insights**: Natural language explanations instead of just scores
- **Better Reasoning**: LLM can consider nuanced factors and market context
- **Adaptability**: LLM can handle novel situations beyond programmed rules
- **Natural Reports**: Human-readable analysis narratives
- **Learning**: Can incorporate new analysis techniques via prompt updates

### Cost Estimates (Monthly)
| Component | Estimated Cost |
|-----------|---------------|
| Daily scans (200 instruments) | €10-15 |
| Detailed analysis (20 instruments/day) | €30-40 |
| Report generation | €5-10 |
| **Total** | **€45-65** |

*Assumes Claude 4 Sonnet pricing, efficient prompting, and caching strategies*

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

### Current System (Rule-Based)
- [x] System runs daily in <15 minutes
- [x] Monthly costs ≤€20 (data APIs only, no LLM costs)
- [x] Generates signals with scores and recommendations
- [x] Reports include confidence scores
- [x] Portfolio allocation suggestions provided
- [x] Risk warnings included where appropriate
- [x] System handles API failures gracefully
- [x] Progress bars and clean console output
- [x] Comprehensive error handling and resilience patterns

### Target System (LLM-Powered)
- [ ] LLM agents actively reasoning about analysis
- [ ] Natural language insights in reports
- [ ] Token usage tracking and cost monitoring
- [ ] Monthly costs ≤€100 (including LLM usage)
- [ ] User review time <1 hour
- [ ] Generates 5-10 actionable signals with narratives
- [ ] LLM-generated investment theses
- [ ] Hybrid intelligence (LLM + rule-based fallback)
- [ ] Quality metrics for LLM outputs

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
python -m src.main analyze --config config/local.yaml

# Generate report only (using cached data)
python -m src.main report --date 2024-01-15

# View help
python -m src.main --help
```

---

*This roadmap serves as the canonical implementation guide for the GenAI Financial Assistant project. Update task checkboxes as development progresses.*
