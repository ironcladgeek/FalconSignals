"""Tests for LLM integration module."""

import pytest

from src.config.schemas import LLMConfig, TokenTrackerConfig
from src.llm.integration import LLMAnalysisOrchestrator
from src.llm.token_tracker import TokenTracker


@pytest.fixture
def llm_config():
    """Create test LLM config."""
    return LLMConfig(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        temperature=0.7,
        enable_fallback=True,
    )


@pytest.fixture
def token_tracker_config():
    """Create test token tracker config."""
    return TokenTrackerConfig(
        enabled=True,
        daily_limit=100000,
        monthly_limit=1000000,
    )


@pytest.fixture
def token_tracker(tmp_path, token_tracker_config):
    """Create test token tracker."""
    return TokenTracker(token_tracker_config, storage_dir=tmp_path)


class TestTokenTracker:
    """Test TokenTracker functionality."""

    def test_track_tokens(self, token_tracker):
        """Test basic token tracking."""
        cost = token_tracker.track(
            input_tokens=100,
            output_tokens=200,
            model="test-model",
            success=True,
        )

        assert cost > 0
        assert token_tracker.get_daily_tokens() == 300
        assert token_tracker.get_daily_cost() > 0

    def test_daily_stats(self, token_tracker):
        """Test daily statistics."""
        token_tracker.track(100, 200, "test-model")
        token_tracker.track(50, 150, "test-model")

        stats = token_tracker.get_daily_stats()
        assert stats.total_input_tokens == 150
        assert stats.total_output_tokens == 350
        assert stats.requests == 2

    def test_cost_calculation(self, token_tracker):
        """Test cost calculation."""
        cost = token_tracker.track(1000, 1000, "test-model")

        # Input: (1000 / 1000) * 0.003 = 0.003
        # Output: (1000 / 1000) * 0.015 = 0.015
        # Total: 0.018
        assert abs(cost - 0.018) < 0.001

    def test_warning_threshold(self, token_tracker):
        """Test warning at usage threshold."""
        # Track beyond 80% of daily limit
        num_calls = int((token_tracker.config.daily_limit * 0.85) / 1000) + 1
        for _ in range(num_calls):
            token_tracker.track(500, 500, "test-model")

        # Should have warnings in logs
        assert token_tracker.get_daily_tokens() >= token_tracker.config.daily_limit * 0.8


class TestLLMAnalysisOrchestrator:
    """Test LLM Analysis Orchestrator."""

    def test_orchestrator_initialization(self, llm_config):
        """Test orchestrator initialization."""
        orchestrator = LLMAnalysisOrchestrator(llm_config=llm_config, enable_fallback=True)

        assert orchestrator.llm_config == llm_config
        assert len(orchestrator.hybrid_agents) > 0
        assert "market_scanner" in orchestrator.hybrid_agents
        assert "technical" in orchestrator.hybrid_agents
        assert "fundamental" in orchestrator.hybrid_agents
        assert "sentiment" in orchestrator.hybrid_agents

    def test_orchestrator_status(self, llm_config):
        """Test orchestrator status reporting."""
        orchestrator = LLMAnalysisOrchestrator(llm_config=llm_config)
        status = orchestrator.get_orchestrator_status()

        assert status["llm_provider"] == "anthropic"
        assert status["llm_model"] == llm_config.model
        assert status["fallback_enabled"] is True
        assert "agents" in status

    def test_hybrid_agent_creation(self, llm_config):
        """Test hybrid agent creation."""
        orchestrator = LLMAnalysisOrchestrator(llm_config=llm_config)

        for agent_name, hybrid_agent in orchestrator.hybrid_agents.items():
            assert hybrid_agent.crewai_agent is not None
            assert hybrid_agent.fallback_agent is not None
            assert hybrid_agent.enable_fallback is True

    def test_tool_adapter_creation(self, llm_config):
        """Test tool adapter initialization."""
        orchestrator = LLMAnalysisOrchestrator(llm_config=llm_config)
        tools = orchestrator.tool_adapter.get_crewai_tools()

        assert len(tools) > 0


class TestCrewAIConfiguration:
    """Test CrewAI configuration."""

    def test_anthropic_config(self, llm_config):
        """Test Anthropic configuration."""
        assert llm_config.provider == "anthropic"
        assert "claude" in llm_config.model.lower()

    def test_config_validation(self):
        """Test LLM config validation."""
        # Valid config
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-20250514")
        assert config.provider == "anthropic"

        # Invalid provider
        with pytest.raises(ValueError):
            LLMConfig(provider="invalid_provider")

        # Invalid temperature
        with pytest.raises(ValueError):
            LLMConfig(temperature=3.0)


class TestTokenTrackerConfig:
    """Test token tracker configuration."""

    def test_token_tracker_config_validation(self):
        """Test token tracker config validation."""
        config = TokenTrackerConfig(
            daily_limit=50000,
            monthly_limit=500000,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
        )

        assert config.daily_limit == 50000
        assert config.monthly_limit == 500000

    def test_warning_threshold_validation(self):
        """Test warning threshold validation."""
        config = TokenTrackerConfig(warn_on_daily_usage_percent=0.85)
        assert config.warn_on_daily_usage_percent == 0.85

        with pytest.raises(ValueError):
            TokenTrackerConfig(warn_on_daily_usage_percent=1.5)
