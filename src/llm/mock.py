"""Mock LLM client for zero-cost testing."""

import json
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class MockLLMClient:
    """Mock LLM client that returns pre-defined responses for testing.

    Useful for testing without incurring LLM costs.
    """

    # Default mock responses for different agent types
    DEFAULT_RESPONSES = {
        "market_scanner": {
            "status": "success",
            "instruments": [
                {
                    "ticker": "AAPL",
                    "anomalies": [
                        "Strong technical momentum (RSI > 65)",
                        "Positive sentiment shift (recent news +0.70)",
                    ],
                    "anomaly_score": 78,
                    "severity": "high",
                }
            ],
            "message": "Scan complete - 1 instrument with anomalies found",
        },
        "technical_analyst": {
            "analysis": "Technical analysis shows bullish signals with strong uptrend.",
            "indicators": {
                "sma_20": "Above price",
                "rsi": "65 (strong momentum)",
                "macd": "Positive with strong histograms",
            },
            "score": 72,
            "confidence": 0.75,
        },
        "fundamental_analyst": {
            "analysis": "Strong fundamentals with revenue growth and healthy margins.",
            "metrics": {
                "pe_ratio": "29.5 (market average)",
                "roe": "119.5% (excellent)",
                "free_cash_flow": "Healthy and growing",
            },
            "score": 74,
            "confidence": 0.78,
        },
        "sentiment_analyst": {
            "analysis": "Positive sentiment from recent earnings beat and analyst upgrades.",
            "news_sentiment": {
                "positive": 4,
                "neutral": 1,
                "negative": 0,
                "avg_score": 0.68,
            },
            "score": 68,
            "confidence": 0.72,
        },
        "signal_synthesizer": {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "us",
            "sector": "Technology",
            "recommendation": "buy",
            "scores": {"technical": 72, "fundamental": 74, "sentiment": 68},
            "final_score": 71.3,
            "confidence": 0.75,
            "time_horizon": "3M",
            "expected_return_min": 5.0,
            "expected_return_max": 15.0,
            "key_reasons": [
                "Strong Q4 earnings beat",
                "Analyst price target upgrades",
                "Services segment momentum",
                "Solid technical uptrend",
            ],
            "risk": {
                "level": "medium",
                "volatility": "normal",
                "volatility_pct": 2.3,
                "liquidity": "excellent",
                "concentration_risk": False,
                "sector_risk": "Technology sector valuation concerns",
                "flags": ["regulatory_risk_eu"],
            },
            "current_price": 229.10,
            "currency": "USD",
            "rationale": "Apple demonstrates strong fundamentals with Services growth, solid technical position, and positive analyst sentiment. Recent earnings beat supports the bullish case. Primary risk is EU regulatory scrutiny.",
            "caveats": [
                "EU regulatory investigation could impact App Store revenues",
                "Macroeconomic headwinds could affect iPhone demand",
                "Valuation at market multiples suggests limited upside beyond current target",
            ],
        },
    }

    def __init__(self, response_overrides: Optional[dict] = None):
        """Initialize mock LLM client.

        Args:
            response_overrides: Optional dictionary to override default responses
        """
        self.responses = self.DEFAULT_RESPONSES.copy()
        if response_overrides:
            self.responses.update(response_overrides)
        logger.info("Initialized MockLLMClient for zero-cost testing")

    def complete(
        self,
        prompt: str,
        agent_type: str = "generic",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate mock completion.

        Args:
            prompt: Input prompt (ignored for mock)
            agent_type: Type of agent (used to select response template)
            max_tokens: Maximum tokens (ignored for mock)
            temperature: Temperature setting (ignored for mock)

        Returns:
            Mock response as JSON string
        """
        response = self.responses.get(agent_type, {})
        logger.debug(f"MockLLMClient returning response for agent_type={agent_type}")
        return json.dumps(response)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (mock implementation).

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count (1 token per 4 characters)
        """
        return max(1, len(text) // 4)

    def get_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "mock",
    ) -> tuple[float, str]:
        """Get cost for tokens (always zero for mock).

        Args:
            input_tokens: Input token count (ignored)
            output_tokens: Output token count (ignored)
            model: Model name (ignored)

        Returns:
            Tuple of (cost, currency) - always (0.0, "EUR")
        """
        return 0.0, "EUR"

    def set_response_override(self, agent_type: str, response: dict) -> None:
        """Override response for specific agent type.

        Args:
            agent_type: Agent type identifier
            response: Response dictionary to return
        """
        self.responses[agent_type] = response
        logger.debug(f"Set response override for agent_type={agent_type}")

    def reset_responses(self) -> None:
        """Reset responses to defaults."""
        self.responses = self.DEFAULT_RESPONSES.copy()
        logger.debug("Reset MockLLMClient responses to defaults")
