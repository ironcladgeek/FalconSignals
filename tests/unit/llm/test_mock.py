"""Tests for MockLLMClient."""

import json

from src.llm.mock import MockLLMClient


class TestMockLLMClient:
    """Test suite for MockLLMClient."""

    def test_initialization(self):
        """Test mock client initialization."""
        client = MockLLMClient()
        assert client is not None
        assert len(client.responses) > 0

    def test_complete_market_scanner(self):
        """Test mock completion for market scanner agent."""
        client = MockLLMClient()
        response = client.complete("dummy prompt", agent_type="market_scanner")

        # Should be JSON string
        assert isinstance(response, str)
        parsed = json.loads(response)
        assert "status" in parsed
        assert "instruments" in parsed

    def test_complete_signal_synthesizer(self):
        """Test mock completion for signal synthesizer agent."""
        client = MockLLMClient()
        response = client.complete("dummy prompt", agent_type="signal_synthesizer")

        parsed = json.loads(response)
        assert "ticker" in parsed
        assert "recommendation" in parsed
        assert "scores" in parsed
        assert "final_score" in parsed
        assert "confidence" in parsed

    def test_complete_technical_analyst(self):
        """Test mock completion for technical analyst."""
        client = MockLLMClient()
        response = client.complete("dummy prompt", agent_type="technical_analyst")

        parsed = json.loads(response)
        assert "analysis" in parsed
        assert "score" in parsed
        assert "confidence" in parsed

    def test_complete_fundamental_analyst(self):
        """Test mock completion for fundamental analyst."""
        client = MockLLMClient()
        response = client.complete("dummy prompt", agent_type="fundamental_analyst")

        parsed = json.loads(response)
        assert "analysis" in parsed
        assert "score" in parsed
        assert "confidence" in parsed

    def test_complete_sentiment_analyst(self):
        """Test mock completion for sentiment analyst."""
        client = MockLLMClient()
        response = client.complete("dummy prompt", agent_type="sentiment_analyst")

        parsed = json.loads(response)
        assert "analysis" in parsed
        assert "score" in parsed
        assert "confidence" in parsed

    def test_count_tokens(self):
        """Test token counting."""
        client = MockLLMClient()
        text = "This is a test message with some words."
        tokens = client.count_tokens(text)

        assert isinstance(tokens, int)
        assert tokens > 0
        # Approximate: 1 token per 4 characters
        assert tokens == max(1, len(text) // 4)

    def test_get_cost_is_zero(self):
        """Test that mock client returns zero cost."""
        client = MockLLMClient()
        cost, currency = client.get_cost(1000, 500)

        assert cost == 0.0
        assert currency == "EUR"

    def test_set_response_override(self):
        """Test setting response override."""
        client = MockLLMClient()
        custom_response = {"custom": "response"}
        client.set_response_override("custom_agent", custom_response)

        response = client.complete("prompt", agent_type="custom_agent")
        assert json.loads(response) == custom_response

    def test_reset_responses(self):
        """Test resetting responses to defaults."""
        client = MockLLMClient()
        custom_response = {"custom": "response"}
        client.set_response_override("market_scanner", custom_response)

        # Verify override works
        response = client.complete("prompt", agent_type="market_scanner")
        assert json.loads(response) == custom_response

        # Reset
        client.reset_responses()

        # Verify default response is restored
        response = client.complete("prompt", agent_type="market_scanner")
        parsed = json.loads(response)
        assert "status" in parsed
        assert "instruments" in parsed

    def test_unknown_agent_type_returns_empty(self):
        """Test handling of unknown agent type."""
        client = MockLLMClient()
        response = client.complete("prompt", agent_type="unknown_agent")

        parsed = json.loads(response)
        assert parsed == {}

    def test_signal_synthesizer_has_all_fields(self):
        """Test that signal synthesizer response has all required fields."""
        client = MockLLMClient()
        response = client.complete("prompt", agent_type="signal_synthesizer")
        parsed = json.loads(response)

        required_fields = [
            "ticker",
            "recommendation",
            "scores",
            "final_score",
            "confidence",
            "risk",
        ]

        for field in required_fields:
            assert field in parsed, f"Missing field: {field}"

    def test_risk_data_structure(self):
        """Test that risk data has proper structure."""
        client = MockLLMClient()
        response = client.complete("prompt", agent_type="signal_synthesizer")
        parsed = json.loads(response)

        risk = parsed["risk"]
        assert "level" in risk
        assert "volatility" in risk
        assert "liquidity" in risk
        assert "concentration_risk" in risk
        assert "flags" in risk

    def test_scores_structure(self):
        """Test that scores have proper structure."""
        client = MockLLMClient()
        response = client.complete("prompt", agent_type="signal_synthesizer")
        parsed = json.loads(response)

        scores = parsed["scores"]
        assert "technical" in scores
        assert "fundamental" in scores
        assert "sentiment" in scores
