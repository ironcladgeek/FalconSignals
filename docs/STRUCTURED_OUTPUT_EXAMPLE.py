"""Example: How to update tasks to use structured Pydantic output.

This file demonstrates the changes needed to enforce structured JSON output
from LLM agents instead of parsing unstructured markdown.
"""

from crewai import Agent, Task

from src.agents.output_models import (
    FundamentalAnalysisOutput,
    SentimentAnalysisOutput,
    SignalSynthesisOutput,
    TechnicalAnalysisOutput,
)


# BEFORE (current approach - returns unstructured markdown):
def create_technical_analysis_task_OLD(agent: Agent, ticker: str, context: dict) -> Task:
    return Task(
        description=f"Interpret the pre-calculated technical indicators for {ticker}...",
        agent=agent,
        expected_output=(
            "Technical analysis interpretation with trend assessment, momentum analysis, "
            "signal interpretation, and technical score (0-100)"
        ),
    )


# AFTER (new approach - returns structured Pydantic model):
def create_technical_analysis_task_NEW(agent: Agent, ticker: str, context: dict) -> Task:
    return Task(
        description=f"Interpret the pre-calculated technical indicators for {ticker}...",
        agent=agent,
        expected_output=(
            "Technical analysis interpretation with trend assessment, momentum analysis, "
            "signal interpretation, and technical score (0-100)"
        ),
        output_pydantic=TechnicalAnalysisOutput,  # <-- This enforces structured output!
    )


# The LLM will now automatically return a TechnicalAnalysisOutput object
# with all fields properly populated. No regex parsing needed!

# Example result:
# result = {
#     "rsi": 80.80,
#     "macd": 7.88,
#     "macd_signal": 5.17,
#     "atr": 6.59,
#     "trend_direction": "bullish",
#     "trend_strength": "strong",
#     "momentum_status": "overbought",
#     "support_level": 203.90,
#     "resistance_level": 217.08,
#     "technical_score": 72,
#     "key_findings": [
#         "Strong uptrend with RSI at 80.80 indicating overbought conditions",
#         "MACD confirms bullish momentum with positive histogram",
#         "Below-average volume (0.84) suggests potential consolidation"
#     ],
#     "reasoning": "Stock is in strong uptrend but technically overbought..."
# }


# Similarly for other tasks:


def create_fundamental_analysis_task_NEW(agent: Agent, ticker: str, context: dict) -> Task:
    return Task(
        description=f"Analyze fundamentals of {ticker}...",
        agent=agent,
        expected_output="Fundamental analysis with metrics and scores",
        output_pydantic=FundamentalAnalysisOutput,  # Structured output
    )


def create_sentiment_analysis_task_NEW(agent: Agent, ticker: str, context: dict) -> Task:
    return Task(
        description=f"Analyze news sentiment for {ticker}...",
        agent=agent,
        expected_output="Sentiment analysis with article counts and themes",
        output_pydantic=SentimentAnalysisOutput,  # Structured output
    )


def create_signal_synthesis_task_NEW(agent: Agent, ticker: str, context: dict) -> Task:
    return Task(
        description=f"Synthesize investment signal for {ticker}...",
        agent=agent,
        expected_output="Investment recommendation with scores and rationale",
        output_pydantic=SignalSynthesisOutput,  # Structured output
    )


# Benefits of this approach:
# 1. No regex parsing - LLM returns validated JSON
# 2. Type safety - Pydantic validates all fields
# 3. Consistent output - same structure every time
# 4. Self-documenting - field descriptions guide the LLM
# 5. Easy to extend - just add fields to the model
# 6. Better error handling - validation errors are clear

# The normalizer would then simplify to just extracting from the Pydantic model:


def normalize_llm_technical_result_NEW(result: TechnicalAnalysisOutput):
    """No regex needed - just extract from validated Pydantic model."""
    return AnalysisComponentResult(
        component="technical",
        score=result.technical_score,
        technical_indicators=TechnicalIndicators(
            rsi=result.rsi,
            macd=result.macd,
            macd_signal=result.macd_signal,
            atr=result.atr,
        ),
        reasoning=result.reasoning,
    )
