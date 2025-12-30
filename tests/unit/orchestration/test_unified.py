"""Unit tests for UnifiedAnalysisOrchestrator."""

from unittest.mock import Mock, patch

from src.analysis.models import (
    AnalysisComponentResult,
    UnifiedAnalysisResult,
)
from src.config.schemas import LLMConfig
from src.orchestration import UnifiedAnalysisOrchestrator


class TestUnifiedAnalysisOrchestrator:
    """Test suite for UnifiedAnalysisOrchestrator."""

    def test_initialization_rule_based_mode(self):
        """Test orchestrator initializes correctly in rule-based mode."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        assert orchestrator.llm_mode is False
        assert hasattr(orchestrator, "technical_agent")
        assert hasattr(orchestrator, "fundamental_agent")
        assert hasattr(orchestrator, "sentiment_agent")
        assert hasattr(orchestrator, "signal_synthesizer")
        # LLM components should not be initialized
        assert not hasattr(orchestrator, "agent_factory")
        assert not hasattr(orchestrator, "task_factory")

    @patch("src.orchestration.unified.CrewAIAgentFactory")
    @patch("src.orchestration.unified.CrewAITaskFactory")
    @patch("src.orchestration.unified.CrewAIToolAdapter")
    @patch("src.orchestration.unified.HybridAnalysisCrew")
    def test_initialization_llm_mode(
        self,
        mock_crew,
        mock_tool_adapter,
        mock_task_factory,
        mock_agent_factory,
    ):
        """Test orchestrator initializes correctly in LLM mode."""
        llm_config = LLMConfig(provider="anthropic", model="claude-3-5-sonnet-20241022")

        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=True, llm_config=llm_config)

        assert orchestrator.llm_mode is True
        assert orchestrator.llm_config == llm_config
        # LLM components should be initialized
        mock_agent_factory.assert_called_once_with(llm_config)
        mock_task_factory.assert_called_once()
        mock_tool_adapter.assert_called_once()
        mock_crew.assert_called_once()

    def test_analyze_instrument_rule_based_success(self):
        """Test analyzing instrument in rule-based mode returns correct structure."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        # Mock the agents
        orchestrator.technical_agent = Mock()
        orchestrator.technical_agent.execute = Mock(return_value={"technical_score": 75})

        orchestrator.fundamental_agent = Mock()
        orchestrator.fundamental_agent.execute = Mock(return_value={"fundamental_score": 80})

        orchestrator.sentiment_agent = Mock()
        orchestrator.sentiment_agent.execute = Mock(return_value={"sentiment_score": 70})

        orchestrator.signal_synthesizer = Mock()
        orchestrator.signal_synthesizer.execute = Mock(
            return_value={
                "recommendation": "buy",
                "confidence": 85,
                "final_score": 75,
            }
        )

        result = orchestrator.analyze_instrument("AAPL")

        # Rule-based mode returns dict, not UnifiedAnalysisResult
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["ticker"] == "AAPL"
        assert result["final_recommendation"] == "buy"
        assert result["confidence"] == 85
        assert result["final_score"] == 75
        assert "analysis" in result
        assert "technical" in result["analysis"]
        assert "fundamental" in result["analysis"]
        assert "sentiment" in result["analysis"]
        assert "synthesis" in result["analysis"]

    def test_analyze_instrument_rule_based_error(self):
        """Test analyzing instrument handles errors gracefully."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        # Mock the technical agent to raise an exception
        orchestrator.technical_agent = Mock()
        orchestrator.technical_agent.execute = Mock(side_effect=Exception("Test error"))

        result = orchestrator.analyze_instrument("AAPL")

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert result["ticker"] == "AAPL"
        assert "Test error" in result["message"]

    @patch("src.orchestration.unified.CrewAIAgentFactory")
    @patch("src.orchestration.unified.CrewAITaskFactory")
    @patch("src.orchestration.unified.CrewAIToolAdapter")
    @patch("src.orchestration.unified.HybridAnalysisCrew")
    @patch("src.orchestration.unified.AnalysisResultNormalizer")
    def test_analyze_instrument_llm_mode_success(
        self,
        mock_normalizer,
        mock_crew_cls,
        mock_tool_adapter,
        mock_task_factory_cls,
        mock_agent_factory,
    ):
        """Test analyzing instrument in LLM mode."""
        # Setup mocks
        mock_crew = Mock()
        mock_crew_cls.return_value = mock_crew

        # Mock successful analysis results
        mock_crew.execute_analysis.return_value = {
            "results": {
                "technical_analysis": {"status": "success", "result": {"score": 75}},
                "fundamental_analysis": {"status": "success", "result": {"score": 80}},
                "sentiment_analysis": {"status": "success", "result": {"score": 70}},
            }
        }

        # Mock the UnifiedAnalysisResult
        mock_unified_result = UnifiedAnalysisResult(
            ticker="AAPL",
            mode="llm",
            technical=AnalysisComponentResult(component="technical", score=75),
            fundamental=AnalysisComponentResult(component="fundamental", score=80),
            sentiment=AnalysisComponentResult(component="sentiment", score=70),
            final_score=75,
            recommendation="buy",
            confidence=85,
            expected_return_min=5.0,
            expected_return_max=15.0,
        )
        mock_normalizer.normalize_llm_result.return_value = mock_unified_result

        # Create orchestrator
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=True)

        # Mock the hybrid agents (use type: ignore for test mocking)
        orchestrator.hybrid_agents = {  # type: ignore[assignment]
            "technical": Mock(),
            "fundamental": Mock(),
            "sentiment": Mock(),
            "synthesizer": Mock(),
        }

        # Mock task factory
        mock_task_factory = Mock()
        mock_task_factory.create_technical_analysis_task = Mock(return_value=Mock())
        mock_task_factory.create_fundamental_analysis_task = Mock(return_value=Mock())
        mock_task_factory.create_sentiment_analysis_task = Mock(return_value=Mock())
        mock_task_factory.create_signal_synthesis_task = Mock(return_value=Mock())
        orchestrator.task_factory = mock_task_factory

        # Mock the synthesizer to return result
        orchestrator.hybrid_agents["synthesizer"].execute_task = Mock(
            return_value={"recommendation": "buy", "confidence": 85}
        )

        result = orchestrator.analyze_instrument("AAPL")

        assert isinstance(result, UnifiedAnalysisResult)
        assert result.ticker == "AAPL"
        assert result.recommendation == "buy"
        assert result.confidence == 85

    def test_analyze_instruments_multiple_tickers(self):
        """Test analyzing multiple instruments."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        # Mock analyze_instrument to return success for some tickers
        def mock_analyze(ticker, context=None):
            if ticker in ["AAPL", "MSFT"]:
                return {
                    "status": "success",
                    "ticker": ticker,
                    "final_recommendation": "buy",
                    "confidence": 85,
                    "final_score": 75,
                }
            else:
                return {"status": "error", "ticker": ticker, "message": "Failed"}

        orchestrator.analyze_instrument = Mock(side_effect=mock_analyze)

        result = orchestrator.analyze_instruments(["AAPL", "MSFT", "GOOGL"])

        assert result["status"] == "success"
        assert result["total_analyzed"] == 2
        assert len(result["analysis_results"]) == 2
        # Check that results are sorted by confidence
        assert all(r["ticker"] in ["AAPL", "MSFT"] for r in result["analysis_results"])

    def test_analyze_instruments_llm_mode_unified_result(self):
        """Test analyzing multiple instruments in LLM mode with UnifiedAnalysisResult."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=True)

        # Mock analyze_instrument to return UnifiedAnalysisResult
        mock_result = UnifiedAnalysisResult(
            ticker="AAPL",
            mode="llm",
            technical=AnalysisComponentResult(component="technical", score=75),
            fundamental=AnalysisComponentResult(component="fundamental", score=80),
            sentiment=AnalysisComponentResult(component="sentiment", score=70),
            final_score=75,
            recommendation="buy",
            confidence=85,
            expected_return_min=5.0,
            expected_return_max=15.0,
        )
        orchestrator.analyze_instrument = Mock(return_value=mock_result)

        result = orchestrator.analyze_instruments(["AAPL"])

        assert result["status"] == "success"
        assert result["total_analyzed"] == 1
        assert len(result["analysis_results"]) == 1
        assert result["analysis_results"][0]["ticker"] == "AAPL"
        assert result["analysis_results"][0]["final_recommendation"] == "buy"
        assert result["analysis_results"][0]["confidence"] == 85

    def test_get_agent_status_rule_based(self):
        """Test getting agent status in rule-based mode."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        status = orchestrator.get_agent_status()

        assert status["mode"] == "rule-based"
        assert status["total_agents"] == 4
        assert "agents" in status
        assert "technical_analyst" in status["agents"]
        assert "fundamental_analyst" in status["agents"]
        assert "sentiment_analyst" in status["agents"]
        assert "signal_synthesizer" in status["agents"]

    @patch("src.orchestration.unified.CrewAIAgentFactory")
    @patch("src.orchestration.unified.CrewAITaskFactory")
    @patch("src.orchestration.unified.CrewAIToolAdapter")
    @patch("src.orchestration.unified.HybridAnalysisCrew")
    def test_get_orchestrator_status_llm_mode(
        self,
        mock_crew_cls,
        mock_tool_adapter,
        mock_task_factory,
        mock_agent_factory,
    ):
        """Test getting orchestrator status in LLM mode."""
        mock_crew = Mock()
        mock_crew.get_crew_status.return_value = {"agents": []}
        mock_crew.execution_log = []
        mock_crew_cls.return_value = mock_crew

        llm_config = LLMConfig(provider="anthropic", model="claude-3-5-sonnet-20241022")
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=True, llm_config=llm_config)

        status = orchestrator.get_orchestrator_status()

        assert status["mode"] == "llm"
        assert status["llm_provider"] == "anthropic"
        assert status["llm_model"] == "claude-3-5-sonnet-20241022"
        assert "agents" in status

    def test_analyze_instruments_handles_none_results(self):
        """Test that analyze_instruments handles None results from analyze_instrument."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        # Mock analyze_instrument to return None (failed analysis)
        orchestrator.analyze_instrument = Mock(return_value=None)

        result = orchestrator.analyze_instruments(["AAPL", "MSFT"])

        assert result["status"] == "success"
        assert result["total_analyzed"] == 0
        assert len(result["analysis_results"]) == 0

    def test_analyze_instruments_sorts_by_confidence(self):
        """Test that results are sorted by confidence in descending order."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        # Mock analyze_instrument to return different confidence levels
        def mock_analyze(ticker, context=None):
            confidence_map = {"AAPL": 85, "MSFT": 95, "GOOGL": 70}
            return {
                "status": "success",
                "ticker": ticker,
                "confidence": confidence_map.get(ticker, 50),
                "final_recommendation": "buy",
                "final_score": 75,
            }

        orchestrator.analyze_instrument = Mock(side_effect=mock_analyze)

        result = orchestrator.analyze_instruments(["AAPL", "MSFT", "GOOGL"])

        assert result["total_analyzed"] == 3
        # Check sorting - MSFT (95) should be first, then AAPL (85), then GOOGL (70)
        assert result["analysis_results"][0]["ticker"] == "MSFT"
        assert result["analysis_results"][1]["ticker"] == "AAPL"
        assert result["analysis_results"][2]["ticker"] == "GOOGL"

    def test_strong_signals_filtering(self):
        """Test that strong signals (confidence >= 70) are correctly identified."""
        orchestrator = UnifiedAnalysisOrchestrator(llm_mode=False)

        # Mock analyze_instrument
        def mock_analyze(ticker, context=None):
            confidence_map = {"AAPL": 85, "MSFT": 65, "GOOGL": 75}
            return {
                "status": "success",
                "ticker": ticker,
                "confidence": confidence_map.get(ticker, 50),
                "final_recommendation": "buy",
                "final_score": 75,
            }

        orchestrator.analyze_instrument = Mock(side_effect=mock_analyze)

        result = orchestrator.analyze_instruments(["AAPL", "MSFT", "GOOGL"])

        # AAPL (85) and GOOGL (75) should be strong signals, MSFT (65) should not
        assert len(result["strong_signals"]) == 2
        assert all(r["confidence"] >= 70 for r in result["strong_signals"])
        assert any(r["ticker"] == "AAPL" for r in result["strong_signals"])
        assert any(r["ticker"] == "GOOGL" for r in result["strong_signals"])
