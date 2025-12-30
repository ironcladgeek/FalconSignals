"""Tests for signal synthesis and scoring."""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.analysis import ComponentScores, InvestmentSignal, RiskAssessment, RiskLevel
from src.analysis.normalizer import AnalysisResultNormalizer
from src.analysis.signal_creator import SignalCreator
from src.cache.manager import CacheManager
from src.pipeline import AnalysisPipeline


@pytest.mark.integration
class TestSignalSynthesis:
    """Test signal creation and scoring."""

    @pytest.fixture
    def cache_manager(self, tmp_path):
        """Create cache manager for tests."""
        return CacheManager(str(tmp_path / "cache"))

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        from src.config.loader import load_config

        # Load default config for testing
        return load_config()

    def test_create_investment_signal(self, config, cache_manager):
        """Test signal creation from analysis data using new unified approach."""
        try:
            pipeline = AnalysisPipeline(config, cache_manager)
        except ValueError as e:
            if "Unknown provider" in str(e):
                pytest.skip(
                    "Provider initialization skipped - data providers not configured for tests"
                )
            raise

        analysis = {
            "ticker": "TEST",
            "final_score": 75,
            "confidence": 80,
            "final_recommendation": "buy",
            "analysis": {
                "technical": {"technical_score": 80},
                "fundamental": {"fundamental_score": 70},
                "sentiment": {
                    "sentiment_score": 75,  # Component score (0-100)
                    "sentiment_metrics": {
                        "avg_sentiment": 0.5,  # Raw sentiment (-1 to 1)
                        "sentiment_direction": "positive",
                        "count": 10,
                    },
                    "news_count": 10,
                    "positive_news": 6,
                    "negative_news": 2,
                    "neutral_news": 2,
                },
                "synthesis": {"component_scores": {}},
            },
            "risk_assessment": {
                "level": "medium",
                "volatility": "normal",
                "volatility_pct": 2.0,
                "liquidity": "highly_liquid",
                "concentration_risk": False,
                "flags": [],
            },
        }
        portfolio_context = {}

        # Mock the cache to return a price (required after bug fix)
        from unittest.mock import Mock, patch

        mock_price = Mock()
        mock_price.close_price = 100.0
        mock_price.currency = "USD"

        # Use new unified approach: normalize -> create signal
        unified_result = AnalysisResultNormalizer.normalize_rule_based_result(analysis)

        signal_creator = SignalCreator(
            cache_manager=cache_manager,
            provider_manager=None,
            risk_assessor=pipeline.risk_assessor,
        )

        # Patch the cache manager's get_latest_price method
        with patch.object(cache_manager, "get_latest_price", return_value=mock_price):
            signal = signal_creator.create_signal(
                result=unified_result,
                portfolio_context=portfolio_context,
                analysis_date=None,
            )

        assert signal is not None
        assert signal.ticker == "TEST"
        assert signal.final_score == 75
        assert signal.confidence == 80
        assert signal.recommendation == "buy"
        assert signal.risk is not None
        assert signal.current_price == 100.0

    def test_signal_to_dict_conversion(self):
        """Test conversion of signal to dictionary."""
        signal = InvestmentSignal(
            ticker="AAPL",
            name="Apple Inc.",
            market="US",
            current_price=150.0,
            scores=ComponentScores(technical=80, fundamental=75, sentiment=70),
            final_score=75,
            recommendation="buy",
            confidence=85,
            expected_return_min=5.0,
            expected_return_max=15.0,
            key_reasons=["Strong momentum", "Positive sentiment"],
            risk=RiskAssessment(
                level=RiskLevel.MEDIUM,
                volatility="normal",
                volatility_pct=2.0,
                liquidity="highly_liquid",
                concentration_risk=False,
                flags=[],
            ),
            generated_at=datetime.now(),
            analysis_date="2024-01-01",
        )

        signal_dict = AnalysisPipeline._signal_to_dict(signal)

        assert signal_dict["ticker"] == "AAPL"
        assert signal_dict["confidence"] == 85
        assert signal_dict["final_score"] == 75
        assert signal_dict["recommendation"] == "buy"

    def test_report_generation(self, config, cache_manager):
        """Test daily report generation from signals."""
        try:
            pipeline = AnalysisPipeline(config, cache_manager)
        except ValueError as e:
            if "Unknown provider" in str(e):
                pytest.skip(
                    "Provider initialization skipped - data providers not configured for tests"
                )
            raise

        signal = InvestmentSignal(
            ticker="AAPL",
            name="Apple Inc.",
            market="US",
            current_price=150.0,
            scores=ComponentScores(technical=80, fundamental=75, sentiment=70),
            final_score=75,
            recommendation="buy",
            confidence=85,
            expected_return_min=5.0,
            expected_return_max=15.0,
            key_reasons=["Strong momentum"],
            risk=RiskAssessment(
                level=RiskLevel.MEDIUM,
                volatility="normal",
                volatility_pct=2.0,
                liquidity="highly_liquid",
                concentration_risk=False,
                flags=[],
            ),
            generated_at=datetime.now(),
            analysis_date="2024-01-01",
        )

        report = pipeline.generate_daily_report([signal])

        assert report is not None
        assert report.total_signals_generated == 1
        assert len(report.strong_signals) >= 0
        assert report.report_date is not None

    def test_custom_weights_respected(self):
        """Test that custom weights from config are used in scoring."""
        from unittest.mock import Mock

        from src.agents.rule_based import SignalSynthesisModule

        # Create a mock config with custom weights (different from default 0.35/0.35/0.30)
        mock_config = Mock()
        mock_config.analysis = Mock()
        mock_config.analysis.weight_fundamental = 0.5
        mock_config.analysis.weight_technical = 0.3
        mock_config.analysis.weight_sentiment = 0.2

        # Mock the get_config to return our custom config
        with patch("src.agents.rule_based.synthesis.get_config", return_value=mock_config):
            agent = SignalSynthesisModule()

            # Test data with known scores
            context = {
                "ticker": "TEST",
                "technical_score": 60,
                "fundamental_score": 80,
                "sentiment_score": 40,
            }

            # Expected score with custom weights:
            # (60 * 0.3) + (80 * 0.5) + (40 * 0.2) = 18 + 40 + 8 = 66
            expected_score = 66.0

            result = agent.execute("Synthesize signals", context)

            assert result["status"] == "success"
            assert result["ticker"] == "TEST"
            # Verify the final score matches custom weights calculation
            assert result["final_score"] == expected_score, (
                f"Expected score {expected_score} with weights "
                f"(tech=0.3, fund=0.5, sent=0.2), got {result['final_score']}"
            )
