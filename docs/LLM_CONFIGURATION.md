# LLM Configuration and Fallback Mode

## Overview

NordInvest supports two analysis modes:

1. **AI-Powered Mode** (Recommended): Uses LLM for advanced sentiment analysis and qualitative insights
2. **Rule-Based Mode** (Fallback): Uses technical indicators and quantitative rules only

## How It Works

### With LLM Configured (AI-Powered)
When you configure an LLM API key (Anthropic or OpenAI), the system uses AI agents for:
- Advanced sentiment analysis of news and market data
- Qualitative fundamental analysis
- Enhanced pattern recognition
- Natural language insights in reports

### Without LLM (Rule-Based Fallback)
When no LLM is configured, the system automatically falls back to:
- Technical indicators (RSI, MACD, Moving Averages, etc.)
- Price pattern analysis
- Volume analysis
- Basic fundamental metrics from Yahoo Finance
- Simple rule-based scoring

**You will still get valid trading signals**, but they are based on quantitative analysis only.

## Warning Messages

The system provides clear warnings when running in fallback mode:

### CLI Warnings
When you run `uv run python -m src.main run`, you'll see:
```
⚠️  RULE-BASED MODE: No LLM configured.
   Analysis uses technical indicators and simple rules only.
   For AI-powered analysis, set ANTHROPIC_API_KEY in .env file.
   See .env.sample for setup instructions.
```

### Log Warnings
In the application logs:
```
WARNING - ⚠️  LLM NOT CONFIGURED - Using rule-based analysis fallback.
WARNING - Analysis crew initialized with 5 agents in RULE-BASED MODE.
WARNING - Analysis pipeline initialized in RULE-BASED MODE.
```

### Report Warnings
In generated Markdown reports, you'll see a prominent notice:
```markdown
---
⚠️ **RULE-BASED ANALYSIS MODE**

This report was generated using **quantitative rule-based analysis** without AI/LLM enhancement.
Signals are based on:
- Technical indicators (RSI, MACD, Moving Averages)
- Price patterns and momentum
- Volume analysis
- Basic fundamental metrics (when available)

For AI-powered analysis with enhanced sentiment and qualitative insights,
configure `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in your `.env` file.
---
```

## Setting Up LLM (Recommended)

To enable AI-powered analysis:

1. Copy the sample environment file:
   ```bash
   cp .env.sample .env
   ```

2. Edit `.env` and add your API key:
   ```bash
   # For Anthropic (recommended)
   ANTHROPIC_API_KEY=your_actual_api_key_here

   # OR for OpenAI
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. Run the application - it will automatically detect and use the LLM:
   ```bash
   uv run python -m src.main run
   ```

## Checking LLM Status

You can verify LLM configuration using the utility:

```python
from src.utils.llm_check import check_llm_configuration, log_llm_status

# Check configuration
is_configured, provider = check_llm_configuration()
print(f"LLM configured: {is_configured}")
print(f"Provider: {provider}")  # 'Anthropic', 'OpenAI', or None

# Log status (also logs warnings)
log_llm_status()
```

## Cost Considerations

- **Rule-Based Mode**: Free - uses only free data sources (Yahoo Finance)
- **AI-Powered Mode**: Incurs LLM API costs based on usage
  - Check `config/default.yaml` for `cost_limit_eur_per_month` setting
  - Monitor costs in your LLM provider's dashboard

## Which Mode Should I Use?

| Scenario | Recommended Mode |
|----------|------------------|
| Learning/Testing | Rule-Based (Free) |
| Limited Budget | Rule-Based (Free) |
| Production Trading | AI-Powered (Better insights) |
| Research/Backtesting | Either (depends on needs) |

Both modes generate legitimate signals - AI-powered mode provides enhanced qualitative analysis and sentiment interpretation.
