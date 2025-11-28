# Using LLM-Powered Analysis via CLI

This guide shows you how to run LLM-powered investment analysis using the `--llm` flag with the `analyze` command.

## Quick Start

### Prerequisites

1. **Set your API key** (choose one):
   ```bash
   # For Anthropic Claude (recommended)
   export ANTHROPIC_API_KEY=sk-ant-...

   # OR for OpenAI GPT
   export OPENAI_API_KEY=sk-...

   # For local LLM (Ollama must be running)
   # No key needed
   ```

2. **Optional: Create local configuration**:
   ```bash
   uv run python -m src.main config-init
   # Edit config/local.yaml to customize LLM settings
   ```

## Basic Usage

### Analyze a Single Stock with LLM

```bash
uv run python -m src.main analyze --ticker INTU --llm
```

Output:
```
✓ Configuration loaded successfully
  Risk tolerance: moderate
  Capital: €2,000.00
  Monthly deposit: €500.00
  Markets: nordic, eu

🤖 Using LLM-powered analysis (CrewAI with intelligent agents)
  LLM Provider: anthropic
  Model: claude-sonnet-4-20250514
  Temperature: 0.7
  Token tracking: enabled

📊 Running analysis on 1 specified instruments...
  Tickers: INTU

Analyzing instruments [████████████████] 100%

✓ Analysis complete: 1 signals generated

💰 Token Usage Summary:
  Input tokens: 2,847
  Output tokens: 1,203
  Cost: €0.065
  Requests: 5

📋 Generating report...

📈 Report Summary:
  Strong signals: 1
  Moderate signals: 0
  Total analyzed: 1
  Diversification score: 85%
  Recommended allocation: €1,500.00

  Report saved: data/reports/report_2024-11-28_14-32-45.md

✓ Analysis completed in 45.23s
```

### Analyze Multiple Stocks

```bash
uv run python -m src.main analyze --ticker AAPL,MSFT,GOOGL,INTU --llm
```

### Save in Different Format

```bash
# Save as JSON instead of Markdown
uv run python -m src.main analyze --ticker INTU --llm --format json
```

### Without Saving Report

```bash
uv run python -m src.main analyze --ticker INTU --llm --no-save-report
```

## Configuration

### Via YAML Config File

Edit `config/local.yaml` (or create with `config-init`):

```yaml
llm:
  provider: "anthropic"  # anthropic, openai, or local
  model: "claude-sonnet-4-20250514"
  temperature: 0.7       # Lower = more deterministic, Higher = more creative
  max_tokens: 2000
  enable_fallback: true  # Fall back to rule-based if LLM fails

token_tracker:
  enabled: true
  daily_limit: 100000
  monthly_limit: 1000000
  cost_per_1k_input_tokens: 0.003   # EUR
  cost_per_1k_output_tokens: 0.015  # EUR
  warn_on_daily_usage_percent: 0.8  # Warn at 80%
```

Then use with your custom config:

```bash
uv run python -m src.main analyze --ticker INTU --llm --config config/local.yaml
```

## What Each Agent Analyzes

The `--llm` flag activates 5 intelligent agents that work together:

### 1. **Market Scanner Agent**
- Detects price movements and anomalies
- Identifies unusual volume patterns
- Flags new 30-day highs/lows

### 2. **Technical Analysis Agent**
- Analyzes moving averages (SMA 20, 50, 200)
- Calculates momentum indicators (RSI, MACD)
- Assesses trend strength and volatility
- Identifies support/resistance levels

### 3. **Fundamental Analysis Agent**
- Reviews earnings growth and margins
- Assesses cash flow quality
- Evaluates debt levels
- Analyzes valuation metrics (P/E, EV/EBITDA, P/B, PEG)

### 4. **Sentiment Analysis Agent**
- Processes recent news articles
- Classifies sentiment (positive, negative, neutral)
- Identifies market catalysts
- Assesses analyst rating trends

### 5. **Signal Synthesizer Agent**
- Combines all analyses with proper weighting:
  - Fundamental: 35%
  - Technical: 35%
  - Sentiment: 30%
- Generates investment thesis
- Calculates confidence scores
- Assesses risks

## Cost Monitoring

The system automatically tracks token usage and costs:

```bash
# Check daily stats
cat data/tracking/tokens_$(date +%Y-%m-%d).json

# Example output:
# {
#   "date": "2024-11-28",
#   "usages": [
#     {
#       "timestamp": "2024-11-28T14:32:30.123456",
#       "input_tokens": 2847,
#       "output_tokens": 1203,
#       "model": "claude-sonnet-4-20250514",
#       "cost_eur": 0.065,
#       "success": true
#     },
#     ...
#   ]
# }
```

### Cost Estimates

Based on default Anthropic Claude pricing:

| Task | Tokens | Cost |
|------|--------|------|
| Single stock analysis | ~4,000 | ~€0.065 |
| 10 stocks | ~40,000 | ~€0.65 |
| 100 stocks | ~400,000 | ~€6.50 |

### Daily Budget

Default: 100,000 tokens/day (~€1.65)
Monthly: 1,000,000 tokens (~€16.50)

Warnings triggered at 80% of daily limit.

## Comparing LLM vs Rule-Based

### Using Rule-Based (Default)
```bash
uv run python -m src.main analyze --ticker INTU
# Uses technical indicators + simple scoring
# ~0 cost (no API calls)
# Fast (~5 seconds)
```

### Using LLM (Intelligent)
```bash
uv run python -m src.main analyze --ticker INTU --llm
# Uses Claude/GPT for reasoning
# ~€0.065 cost per stock
# Slower (~45 seconds, limited by API)
```

## Switching LLM Providers

### Use OpenAI GPT-4

Edit config/local.yaml:
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.7
```

Set API key:
```bash
export OPENAI_API_KEY=sk-...
```

Run:
```bash
uv run python -m src.main analyze --ticker INTU --llm --config config/local.yaml
```

### Use Local Ollama Model

Edit config/local.yaml:
```yaml
llm:
  provider: "local"
  model: "llama2"  # or other Ollama model
  temperature: 0.7
```

Ensure Ollama is running:
```bash
ollama serve  # in another terminal
```

Run:
```bash
uv run python -m src.main analyze --ticker INTU --llm --config config/local.yaml
```

## Troubleshooting

### API Key Not Set
```
❌ LLM Analysis Error: ANTHROPIC_API_KEY environment variable not set.
```

Solution:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Token Limit Exceeded
```
❌ LLM Analysis Error: Daily token limit exceeded
```

Solution: Increase daily limit in config or wait for reset.

### Fallback to Rule-Based

If LLM fails and fallback is enabled, analysis continues with rule-based system.

View logs to see what happened:
```bash
tail -f logs/nordinvest.log | grep -i "fallback\|error"
```

### Cost Overruns

Monitor your spending:
```bash
# Get today's usage
python -c "
from pathlib import Path
from src.llm.token_tracker import TokenTracker
from src.config.schemas import TokenTrackerConfig

tracker = TokenTracker(TokenTrackerConfig(), Path('data/tracking'))
stats = tracker.get_daily_stats()
print(f'Cost today: €{stats.total_cost_eur:.2f}')
print(f'Tokens: {stats.total_input_tokens + stats.total_output_tokens:,}')
"
```

## Advanced: Using Both Rule-Based and LLM

Generate both reports for comparison:

```bash
# Rule-based
uv run python -m src.main analyze --ticker INTU \
  --format markdown --save-report \
  --output rule-based.md

# LLM-powered
uv run python -m src.main analyze --ticker INTU --llm \
  --format markdown --save-report
```

Compare the signals and recommendations.

## Environment Variables

```bash
# Required (choose one)
export ANTHROPIC_API_KEY=sk-ant-...     # Anthropic Claude
export OPENAI_API_KEY=sk-...             # OpenAI GPT
# None needed for local Ollama

# Optional
export NORDINVEST_LOG_LEVEL=DEBUG        # More verbose logging
export NORDINVEST_CONFIG=config/local.yaml  # Default config path
```

## See Also

- [LLM Integration Guide](./llm_integration.md) - Detailed component documentation
- [Phase 6 Summary](../PHASE_6_SUMMARY.md) - Architecture and implementation details
- [Project Roadmap](./roadmap.md) - Full project status
