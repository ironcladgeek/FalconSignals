"""Tests for signal synthesis and scoring."""

from datetime import datetime

import pytest

from src.analysis import ComponentScores, InvestmentSignal, RiskAssessment, RiskLevel
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
        return {
            "capital_starting": 2000,
            "capital_monthly_deposit": 500,
            "max_position_size_pct": 10,
            "max_sector_concentration_pct": 20,
            "risk_volatility_high": 3.0,
            "risk_volatility_very_high": 5.0,
            "include_disclaimers": True,
        }

    def test_create_investment_signal(self, config, cache_manager):
        """Test signal creation from analysis data."""
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
                "sentiment": {"sentiment_score": 75},
                "synthesis": {"component_scores": {}},
            },
        }
        portfolio_context = {}

        signal = pipeline._create_investment_signal(analysis, portfolio_context)

        assert signal is not None
        assert signal.ticker == "TEST"
        assert signal.final_score == 75
        assert signal.confidence == 80
        assert signal.recommendation == "buy"
        assert signal.risk is not None

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
