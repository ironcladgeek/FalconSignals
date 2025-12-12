# Structured LLM Output - Solution to Metadata Extraction Issues

## Problem

The current implementation has LLM agents returning **unstructured markdown text**, which requires complex regex parsing to extract metadata like:
- Technical indicators (RSI, MACD, ATR)
- Analyst ratings (Strong Buy, Buy, Hold counts)
- Sentiment distribution (positive/negative/neutral article counts)

This approach is **fragile** because:
1. LLM markdown formatting varies between runs
2. Regex patterns must handle many formatting variations
3. Parsing failures lead to empty metadata tables in reports
4. Difficult to debug when extraction fails

## Solution: Pydantic Structured Output

CrewAI supports **enforcing structured output** using Pydantic models via the `output_pydantic` parameter on tasks. This eliminates regex parsing entirely.

### Implementation Steps

#### 1. Define Pydantic Output Models

Created `src/agents/output_models.py` with models for each agent:

```python
class TechnicalAnalysisOutput(BaseModel):
    """Structured output for technical analysis agent."""
    rsi: float | None = Field(None, description="RSI value (0-100)")
    macd: float | None = Field(None, description="MACD line value")
    macd_signal: float | None = Field(None, description="MACD signal line value")
    atr: float | None = Field(None, description="Average True Range value")

    trend_direction: str = Field(..., description="bullish, bearish, or neutral")
    momentum_status: str = Field(..., description="overbought, oversold, or neutral")

    technical_score: int = Field(..., description="Score 0-100", ge=0, le=100)
    key_findings: list[str] = Field(..., description="3-5 key findings")
    reasoning: str = Field(..., description="Brief explanation")
```

Similar models for:
- `FundamentalAnalysisOutput` (with analyst counts)
- `SentimentAnalysisOutput` (with article counts)
- `SignalSynthesisOutput` (final recommendation)

#### 2. Update Task Creation

Modify `src/agents/crewai_agents.py` to use `output_pydantic`:

```python
def create_technical_analysis_task(agent: Agent, ticker: str, context: dict) -> Task:
    return Task(
        description=f"Interpret technical indicators for {ticker}...",
        agent=agent,
        expected_output="Technical analysis with scores",
        output_pydantic=TechnicalAnalysisOutput,  # <-- KEY CHANGE
    )
```

#### 3. Simplify Normalizer

Update `src/analysis/normalizer.py` to extract from Pydantic models instead of parsing markdown:

```python
@staticmethod
def _extract_technical_llm(tech_result: TechnicalAnalysisOutput) -> AnalysisComponentResult:
    """Extract from validated Pydantic model - no regex needed!"""
    return AnalysisComponentResult(
        component="technical",
        score=tech_result.technical_score,
        technical_indicators=TechnicalIndicators(
            rsi=tech_result.rsi,
            macd=tech_result.macd,
            macd_signal=tech_result.macd_signal,
            atr=tech_result.atr,
        ),
        reasoning=tech_result.reasoning,
    )
```

## Benefits

### ✅ Reliability
- **Guaranteed structure**: Pydantic validates all fields before returning
- **Type safety**: Fields are correctly typed (int, float, str, list)
- **No parsing errors**: No regex pattern matching failures

### ✅ Consistency
- **Same format every run**: LLM must follow the schema
- **All metadata populated**: Required fields must be provided
- **Validation errors**: Clear error messages if LLM output is invalid

### ✅ Maintainability
- **Self-documenting**: Field descriptions guide the LLM
- **Easy to extend**: Just add fields to the Pydantic model
- **No regex complexity**: No need to maintain complex regex patterns
- **Better debugging**: Pydantic validation errors are explicit

### ✅ Performance
- **Faster**: No regex processing needed
- **Less code**: Simpler normalizer logic
- **Fewer API calls**: LLM gets the structure right first time

## Migration Path

To implement this solution:

### Phase 1: Update Task Definitions
1. Import output models in `crewai_agents.py`
2. Add `output_pydantic` parameter to all task creation methods
3. Test one agent at a time

### Phase 2: Update Normalizer
1. Update `_extract_technical_llm()` to accept `TechnicalAnalysisOutput`
2. Update `_extract_fundamental_llm()` to accept `FundamentalAnalysisOutput`
3. Update `_extract_sentiment_llm()` to accept `SentimentAnalysisOutput`
4. Remove all `_parse_llm_markdown_for_*()` methods

### Phase 3: Cleanup
1. Remove regex parsing code
2. Update tests to use Pydantic models
3. Update documentation

## Testing

After implementation, verify:
- [ ] All metadata tables populated (Technical, Fundamental, Sentiment, Analyst)
- [ ] Pydantic validation catches malformed outputs
- [ ] Reports show correct data
- [ ] No regression in rule-based mode

## Example Output

With structured output, the LLM returns:

```json
{
  "rsi": 80.80,
  "macd": 7.88,
  "macd_signal": 5.17,
  "atr": 6.59,
  "trend_direction": "bullish",
  "trend_strength": "strong",
  "momentum_status": "overbought",
  "technical_score": 72,
  "key_findings": [
    "Strong uptrend with RSI at 80.80",
    "MACD confirms bullish momentum",
    "Below-average volume suggests consolidation"
  ],
  "reasoning": "Stock is in strong uptrend but overbought..."
}
```

This is directly accessible as `result.rsi`, `result.macd`, etc. - **no parsing needed**!

## Recommendation

**Implement this solution** to fix the metadata extraction issues permanently. It's the proper way to handle LLM outputs and will make the system much more robust and maintainable.

The current regex-based approach is a workaround that will continue to have reliability issues as LLM output formatting varies.
