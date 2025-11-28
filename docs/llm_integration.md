# LLM Integration Guide - Phase 6

This document describes the CrewAI and LLM integration infrastructure implemented in Phase 6 of NordInvest.

## Overview

Phase 6 adds intelligent LLM-powered analysis to NordInvest using CrewAI framework. The implementation features:

- **CrewAI Agents**: Intelligent agents powered by Claude, GPT-4, or local models
- **Hybrid Intelligence**: Fallback to rule-based analysis on LLM failures
- **Token Tracking**: Comprehensive cost monitoring and budget management
- **Prompt Engineering**: Structured prompts with JSON-formatted outputs
- **Tool Integration**: Seamless integration with existing data fetchers and analyzers

## Architecture

### Core Components

#### 1. LLM Configuration (`src/config/schemas.py`, `src/config/llm.py`)

```python
from src.config.schemas import LLMConfig
from src.config.llm import initialize_llm_client

config = LLMConfig(
    provider="anthropic",  # anthropic, openai, or local
    model="claude-sonnet-4-20250514",
    temperature=0.7,
    max_tokens=2000,
    enable_fallback=True
)

llm_client = initialize_llm_client(config)
```

**Supported Providers:**
- **Anthropic**: Claude models (requires `ANTHROPIC_API_KEY`)
- **OpenAI**: GPT-4, GPT-3.5 (requires `OPENAI_API_KEY`)
- **Local**: Ollama or compatible (no API key needed)

#### 2. CrewAI Agents (`src/agents/crewai_agents.py`)

Five intelligent agents for comprehensive analysis:

```python
from src.agents.crewai_agents import CrewAIAgentFactory

factory = CrewAIAgentFactory(llm_config)

market_scanner = factory.create_market_scanner_agent()
technical = factory.create_technical_analysis_agent()
fundamental = factory.create_fundamental_analysis_agent()
sentiment = factory.create_sentiment_analysis_agent()
synthesizer = factory.create_signal_synthesizer_agent()
```

Each agent has:
- **Role**: Professional title (e.g., "Senior Technical Analyst")
- **Goal**: What the agent aims to accomplish
- **Backstory**: Expertise and experience narrative
- **Tools**: Data fetchers and analysis calculators

#### 3. Hybrid Intelligence (`src/agents/hybrid.py`)

Wraps CrewAI agents with fallback to rule-based analysis:

```python
from src.agents.hybrid import HybridAnalysisAgent

hybrid = HybridAnalysisAgent(
    crewai_agent=technical,
    fallback_agent=TechnicalAnalysisAgent(),
    token_tracker=tracker,
    enable_fallback=True
)

result = hybrid.execute_task(task, context)
```

**Result Structure:**
```python
{
    "status": "success",
    "result": "LLM analysis output",
    "used_llm": True,
    "used_fallback": False
}
```

#### 4. Token Tracking (`src/llm/token_tracker.py`)

Monitor token usage and costs:

```python
from src.llm.token_tracker import TokenTracker
from src.config.schemas import TokenTrackerConfig

config = TokenTrackerConfig(
    enabled=True,
    daily_limit=100000,
    monthly_limit=1000000,
    cost_per_1k_input_tokens=0.003,  # EUR
    cost_per_1k_output_tokens=0.015,  # EUR
    warn_on_daily_usage_percent=0.8
)

tracker = TokenTracker(config, storage_dir="data/tracking")

# Track usage
cost = tracker.track(
    input_tokens=100,
    output_tokens=200,
    model="claude-sonnet-4-20250514",
    success=True
)

# Get statistics
daily = tracker.get_daily_stats()
monthly = tracker.get_monthly_stats()

# Log summary
tracker.log_summary()
```

#### 5. Prompt Engineering (`src/llm/prompts.py`)

Structured prompt templates for each agent:

```python
from src.llm.prompts import PromptTemplates

# System prompts define agent expertise
system_prompt = PromptTemplates.TECHNICAL_SYSTEM

# Task prompts with data injection
task_prompt = PromptTemplates.get_technical_prompt(
    ticker="AAPL",
    data={
        "current_price": 150.25,
        "sma_20": 148.50,
        "rsi": 65.3,
        "macd_line": 2.15,
        ...
    }
)

# Prompts expect JSON-formatted responses
# Example output:
# {
#   "trend": "uptrend",
#   "trend_strength": "strong",
#   "score": 82,
#   "reasoning": "..."
# }
```

#### 6. Tool Adapters (`src/llm/tools.py`)

Bridges existing tools to CrewAI:

```python
from src.llm.tools import CrewAIToolAdapter

adapter = CrewAIToolAdapter()

# Individual tools
price_data = adapter.fetch_price_data("AAPL", days_back=60)
indicators = adapter.calculate_technical_indicators(price_data)
news = adapter.fetch_news("AAPL", max_articles=10)

# Get tools for CrewAI agents
tools = adapter.get_crewai_tools()
```

#### 7. Orchestrator (`src/llm/integration.py`)

High-level orchestration of all components:

```python
from src.llm.integration import LLMAnalysisOrchestrator

orchestrator = LLMAnalysisOrchestrator(
    llm_config=llm_config,
    token_tracker=tracker,
    enable_fallback=True
)

# Analyze single instrument
results = orchestrator.analyze_instrument("AAPL")

# Get orchestrator status
status = orchestrator.get_orchestrator_status()

# Log summary
orchestrator.log_summary()
```

## Usage Examples

### Basic Analysis

```python
from src.config.schemas import LLMConfig
from src.llm.integration import LLMAnalysisOrchestrator
from src.llm.token_tracker import TokenTracker

# Setup
llm_config = LLMConfig(provider="anthropic")
tracker = TokenTracker(config, storage_dir="data/tracking")
orchestrator = LLMAnalysisOrchestrator(
    llm_config=llm_config,
    token_tracker=tracker,
    enable_fallback=True
)

# Analyze
results = orchestrator.analyze_instrument("MSFT")

# Check what happened
for task_name, task_result in results["results"].items():
    if task_result["status"] == "success":
        method = "LLM" if task_result["used_llm"] else "Fallback"
        print(f"{task_name}: {method}")
    else:
        print(f"{task_name}: Failed - {task_result['error']}")

# Cost summary
orchestrator.log_summary()
```

### With Custom Configuration

```python
from src.config.schemas import LLMConfig, TokenTrackerConfig

# Custom LLM config
llm_config = LLMConfig(
    provider="openai",
    model="gpt-4",
    temperature=0.5,
    max_tokens=1500
)

# Custom token tracking
token_config = TokenTrackerConfig(
    daily_limit=50000,
    monthly_limit=500000,
    cost_per_1k_input_tokens=0.03,
    cost_per_1k_output_tokens=0.06
)

tracker = TokenTracker(token_config)
orchestrator = LLMAnalysisOrchestrator(
    llm_config=llm_config,
    token_tracker=tracker
)
```

### Hybrid with Fallback

```python
# Enable fallback for resilience
orchestrator = LLMAnalysisOrchestrator(
    llm_config=llm_config,
    token_tracker=tracker,
    enable_fallback=True  # Fall back to rule-based on failure
)

results = orchestrator.analyze_instrument("AAPL")

# Check execution method
status = orchestrator.get_orchestrator_status()
for agent_name, agent_status in status["agents"].items():
    if agent_status["last_error"]:
        print(f"{agent_name} failed, used fallback: {agent_status['used_fallback']}")
```

## Configuration

### Environment Variables

```bash
# Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI GPT
export OPENAI_API_KEY=sk-...

# For local LLM (Ollama)
# No key needed, but Ollama must be running on localhost:11434
```

### YAML Configuration

Add to `config/local.yaml`:

```yaml
llm:
  provider: "anthropic"  # anthropic, openai, or local
  model: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000
  enable_fallback: true

token_tracker:
  enabled: true
  daily_limit: 100000
  monthly_limit: 1000000
  cost_per_1k_input_tokens: 0.003
  cost_per_1k_output_tokens: 0.015
  warn_on_daily_usage_percent: 0.8
```

## Testing

Run the test suite:

```bash
# All LLM integration tests
uv run pytest tests/unit/llm/test_integration.py -v

# Specific test classes
uv run pytest tests/unit/llm/test_integration.py::TestTokenTracker -v
uv run pytest tests/unit/llm/test_integration.py::TestLLMAnalysisOrchestrator -v

# Specific tests
uv run pytest tests/unit/llm/test_integration.py::TestTokenTracker::test_track_tokens -v
```

## Cost Monitoring

### Daily Monitoring

```python
tracker = TokenTracker(config)

# During the day, tokens are tracked
tracker.track(100, 200, "model")
tracker.track(150, 250, "model")

# Check progress
daily = tracker.get_daily_stats()
print(f"Used: {daily.total_input_tokens + daily.total_output_tokens} tokens")
print(f"Cost: €{daily.total_cost_eur:.2f}")
print(f"Requests: {daily.requests}")
```

### Warning Thresholds

When daily usage exceeds 80% of limit:
- Warning logged to console
- Continued tracking until limit reached
- No hard stop (can be configured)

### Monthly Reporting

```python
# Get complete month statistics
monthly = tracker.get_monthly_stats()
print(f"Month: {monthly.date}")
print(f"Total tokens: {monthly.total_input_tokens + monthly.total_output_tokens}")
print(f"Total cost: €{monthly.total_cost_eur:.2f}")
print(f"Requests: {monthly.requests}")
```

## Troubleshooting

### LLM Connection Issues

```python
# Check API key
import os
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY not set")

# Test LLM initialization
from src.config.llm import initialize_llm_client
try:
    client = initialize_llm_client(llm_config)
    print("LLM initialized successfully")
except Exception as e:
    print(f"LLM init failed: {e}")
```

### Fallback to Rule-Based

If LLM fails and fallback is enabled:

```python
result = hybrid.execute_task(task)
if result["used_fallback"]:
    print(f"Using fallback: {result.get('error')}")
    # Result still contains analysis from rule-based agent
```

### Cost Overruns

```python
# Monitor daily cost
tracker = TokenTracker(config)
daily = tracker.get_daily_stats()

if daily.total_cost_eur > 50:
    print(f"Warning: Daily cost is €{daily.total_cost_eur:.2f}")
    # Consider pausing analysis or using cheaper model
```

## Integration with Main Pipeline

The LLM integration is designed to work alongside the existing rule-based system:

1. **Phase 6 Complete**: LLM infrastructure ready
2. **Next Step**: Integrate with `AnalysisPipeline` (src/pipeline/orchestrator.py)
3. **Toggle**: Use config to switch between LLM and rule-based
4. **Monitor**: Use token tracker for budget management

## File Structure

```
src/
├── agents/
│   ├── crewai_agents.py       # CrewAI Agent and Task factories
│   ├── hybrid.py               # Hybrid intelligence wrappers
│   └── [existing agents]       # Rule-based fallback agents
├── config/
│   ├── llm.py                  # LLM client initialization
│   ├── schemas.py              # LLMConfig, TokenTrackerConfig
│   └── [existing configs]
├── llm/
│   ├── __init__.py
│   ├── token_tracker.py        # Token usage and cost tracking
│   ├── prompts.py              # Prompt templates for all agents
│   ├── tools.py                # CrewAI tool adapters
│   └── integration.py          # High-level orchestrator
└── [other modules]

tests/
└── unit/
    └── llm/
        ├── __init__.py
        └── test_integration.py # Comprehensive tests (12 passing)

docs/
├── llm_integration.md          # This file
├── roadmap.md                  # Phase 6 details
└── [other docs]
```

## Next Steps

1. **Pipeline Integration**: Connect `LLMAnalysisOrchestrator` to main `AnalysisPipeline`
2. **End-to-End Testing**: Test with real market data
3. **Prompt Optimization**: Tune prompts based on results
4. **Cost Dashboard**: Add UI for monitoring token usage and costs
5. **Performance Comparison**: Compare LLM vs rule-based output quality

## References

- [CrewAI Documentation](https://docs.crewai.com)
- [Anthropic Claude API](https://docs.anthropic.com)
- [OpenAI API](https://platform.openai.com/docs)
- [Project Roadmap](./roadmap.md)
