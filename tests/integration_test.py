"""Integration tests for end-to-end pipeline."""

from datetime import datetime

import pytest

from src.analysis import ComponentScores, InvestmentSignal, RiskAssessment, RiskLevel
from src.cache.manager import CacheManager
from src.pipeline import AnalysisPipeline
from src.utils.scheduler import CronScheduler, RunLog


class TestAnalysisPipeline:
    """Test suite for AnalysisPipeline integration."""

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

    def test_pipeline_initialization(self, config, cache_manager):
        """Test pipeline initializes with required components."""
        try:
            pipeline = AnalysisPipeline(config, cache_manager)
            assert pipeline.risk_assessor is not None
            assert pipeline.allocation_engine is not None
            assert pipeline.report_generator is not None
            assert pipeline.config is not None
        except ValueError as e:
            if "Unknown provider" in str(e):
                pytest.skip(
                    "Provider initialization skipped - data providers not configured for tests"
                )
            raise

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


class TestErrorHandling:
    """Test suite for error handling and resilience."""

    def test_retryable_error_detection(self):
        """Test detection of retryable errors."""
        from src.utils.errors import (
            APIException,
            RetryableException,
            is_retryable_error,
        )

        retryable_error = RetryableException("Test error")
        assert is_retryable_error(retryable_error)

        api_error = APIException("API failed", status_code=500)
        assert not is_retryable_error(api_error)

    def test_fallback_error_detection(self):
        """Test detection of errors requiring fallback."""
        from src.utils.errors import (
            DataProviderException,
            should_fallback,
        )

        provider_error = DataProviderException("Provider failed", provider="test")
        assert should_fallback(provider_error)

    def test_circuit_breaker(self):
        """Test circuit breaker pattern."""
        from src.utils.resilience import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=2)

        def failing_operation():
            raise ValueError("Test error")

        def working_operation():
            return "success"

        # First failure
        with pytest.raises(ValueError):
            breaker.call(failing_operation)

        assert breaker.state == "closed"
        assert breaker.failure_count == 1

        # Second failure - opens circuit
        with pytest.raises(ValueError):
            breaker.call(failing_operation)

        assert breaker.state == "open"

        # Attempt in open state
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            breaker.call(working_operation)

    def test_rate_limiter(self):
        """Test rate limiter."""
        from src.utils.resilience import RateLimiter

        limiter = RateLimiter(rate=3, period=1.0)

        # Should allow first 3 operations
        assert limiter.acquire(1)
        assert limiter.acquire(1)
        assert limiter.acquire(1)

        # Should deny 4th without delay
        assert not limiter.acquire(1)


class TestScheduling:
    """Test suite for scheduling utilities."""

    def test_cron_scheduler_initialization(self, tmp_path):
        """Test cron scheduler initialization."""
        scheduler = CronScheduler(tmp_path / "cron.json")
        assert scheduler.config_path == tmp_path / "cron.json"

    def test_daily_cron_expression(self, tmp_path):
        """Test daily cron expression generation."""
        scheduler = CronScheduler(tmp_path / "cron.json")
        cron_expr = scheduler.schedule_daily_run(
            "test_script.py",
            time_of_day="08:30",
        )

        assert cron_expr == "30 8 * * *"

    def test_weekly_cron_expression(self, tmp_path):
        """Test weekly cron expression generation."""
        scheduler = CronScheduler(tmp_path / "cron.json")
        cron_expr = scheduler.schedule_weekly_run(
            "test_script.py",
            day_of_week=1,
            time_of_day="09:00",
        )

        assert cron_expr == "0 9 * * 1"

    def test_run_log_initialization(self, tmp_path):
        """Test run log initialization."""
        log = RunLog(tmp_path / "runs.jsonl")
        assert log.log_path == tmp_path / "runs.jsonl"

    def test_run_log_entry(self, tmp_path):
        """Test logging a run entry."""
        log = RunLog(tmp_path / "runs.jsonl")

        log.log_run(
            success=True,
            duration_seconds=45.5,
            signal_count=10,
            metadata={"test": "data"},
        )

        assert log.log_path.exists()

    def test_run_statistics(self, tmp_path):
        """Test run statistics calculation."""
        log = RunLog(tmp_path / "runs.jsonl")

        log.log_run(success=True, duration_seconds=30, signal_count=5)
        log.log_run(success=True, duration_seconds=40, signal_count=8)
        log.log_run(success=False, duration_seconds=15, error_message="Test error")

        stats = log.get_run_statistics()

        assert stats["total_runs"] == 3
        assert stats["successful_runs"] == 2
        assert stats["failed_runs"] == 1
        assert stats["success_rate"] == pytest.approx(2 / 3)
        assert stats["total_signals_generated"] == 13


class TestResilience:
    """Test suite for resilience patterns."""

    def test_graceful_degrade_decorator(self):
        """Test graceful degradation decorator."""
        from src.utils.resilience import graceful_degrade

        @graceful_degrade(default_value=[])
        def failing_operation():
            raise RuntimeError("Operation failed")

        result = failing_operation()
        assert result == []

    def test_retry_decorator(self):
        """Test retry decorator."""
        from src.utils.errors import RetryableException
        from src.utils.resilience import retry

        attempt_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RetryableException("Temporary failure")
            return "success"

        result = flaky_operation()
        assert result == "success"
        assert attempt_count == 3

    def test_fallback_decorator(self):
        """Test fallback decorator."""
        from src.utils.resilience import fallback

        @fallback(fallback_func=lambda: "fallback_result")
        def primary_operation():
            raise RuntimeError("Primary failed")

        result = primary_operation()
        assert result == "fallback_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
