"""Unit tests for PerformanceRepository."""

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.data.repository import PerformanceRepository, RecommendationsRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path


@pytest.fixture
def perf_repo(temp_db):
    """Create a PerformanceRepository instance with a temporary database."""
    return PerformanceRepository(temp_db)


@pytest.fixture
def rec_repo(temp_db):
    """Create a RecommendationsRepository instance with the same database."""
    return RecommendationsRepository(temp_db)


@pytest.fixture
def sample_recommendation(rec_repo):
    """Create a sample recommendation in the database."""
    from src.analysis import InvestmentSignal
    from src.analysis.models import ComponentScores, RiskAssessment

    signal = InvestmentSignal(
        ticker="AAPL",
        name="Apple Inc.",
        market="US",
        current_price=150.0,
        currency="USD",
        scores=ComponentScores(
            technical=80.0,
            fundamental=70.0,
            sentiment=75.0,
        ),
        final_score=75.0,
        recommendation="buy",
        confidence=80.0,
        expected_return_min=5.0,
        expected_return_max=15.0,
        time_horizon="3M",
        key_reasons=["Bullish trend", "Strong earnings"],
        risk=RiskAssessment(
            level="medium",
            volatility="moderate",
            volatility_pct=15.0,
            liquidity="normal",
            concentration_risk=False,
        ),
        generated_at=datetime.now(),
        analysis_date=(date.today() - timedelta(days=30)).isoformat(),
        rationale="Strong technical and fundamental indicators",
        caveats=["Market volatility"],
    )

    rec_id = rec_repo.store_recommendation(signal, run_session_id=1, analysis_mode="rule_based")
    return rec_id


class TestPerformanceRepository:
    """Test suite for PerformanceRepository."""

    def test_repository_initialization(self, temp_db):
        """Test repository initialization."""
        repo = PerformanceRepository(temp_db)
        assert repo.db_manager is not None
        assert repo.db_manager._initialized

    def test_track_price_new(self, perf_repo, sample_recommendation):
        """Test tracking a new price record."""
        tracking_date = date.today()
        price = 160.0
        benchmark_price = 450.0

        result = perf_repo.track_price(
            recommendation_id=sample_recommendation,
            tracking_date=tracking_date,
            price=price,
            benchmark_price=benchmark_price,
            benchmark_ticker="SPY",
        )

        assert result is True

        # Verify tracking data was stored
        tracking_data = perf_repo.get_performance_data(sample_recommendation)
        assert len(tracking_data) == 1
        assert tracking_data[0].price == price
        assert tracking_data[0].benchmark_price == benchmark_price

    def test_track_price_update_existing(self, perf_repo, sample_recommendation):
        """Test updating an existing price tracking record."""
        tracking_date = date.today()

        # Track initial price
        perf_repo.track_price(
            recommendation_id=sample_recommendation,
            tracking_date=tracking_date,
            price=160.0,
            benchmark_price=450.0,
        )

        # Update with new price
        result = perf_repo.track_price(
            recommendation_id=sample_recommendation,
            tracking_date=tracking_date,
            price=165.0,
            benchmark_price=455.0,
        )

        assert result is True

        # Verify only one record exists with updated price
        tracking_data = perf_repo.get_performance_data(sample_recommendation)
        assert len(tracking_data) == 1
        assert tracking_data[0].price == 165.0
        assert tracking_data[0].benchmark_price == 455.0

    def test_track_price_multiple_dates(self, perf_repo, sample_recommendation):
        """Test tracking prices over multiple dates."""
        dates = [date.today() - timedelta(days=i) for i in range(5)]
        prices = [150.0 + i * 2 for i in range(5)]

        for tracking_date, price in zip(dates, prices):
            result = perf_repo.track_price(
                recommendation_id=sample_recommendation,
                tracking_date=tracking_date,
                price=price,
                benchmark_price=450.0,
            )
            assert result is True

        # Verify all records
        tracking_data = perf_repo.get_performance_data(sample_recommendation)
        assert len(tracking_data) == 5

    def test_track_price_calculates_metrics(self, perf_repo, sample_recommendation):
        """Test that price tracking calculates price change and alpha correctly."""
        tracking_date = date.today()

        # Track first price (baseline for benchmark)
        perf_repo.track_price(
            recommendation_id=sample_recommendation,
            tracking_date=tracking_date - timedelta(days=1),
            price=155.0,
            benchmark_price=450.0,
            benchmark_ticker="SPY",
        )

        # Track second price
        result = perf_repo.track_price(
            recommendation_id=sample_recommendation,
            tracking_date=tracking_date,
            price=160.0,
            benchmark_price=455.0,
            benchmark_ticker="SPY",
        )

        assert result is True

        # Get latest tracking data
        tracking_data = perf_repo.get_performance_data(sample_recommendation)
        latest = tracking_data[-1]

        # Price change should be (160 - 150) / 150 * 100 = 6.67%
        # (comparing to original recommendation price of 150.0)
        assert latest.price_change_pct is not None
        assert abs(latest.price_change_pct - 6.67) < 0.1

        # Benchmark change should be (455 - 450) / 450 * 100 = 1.11%
        assert latest.benchmark_change_pct is not None
        assert abs(latest.benchmark_change_pct - 1.11) < 0.1

        # Alpha should be price_change - benchmark_change
        assert latest.alpha is not None
        assert abs(latest.alpha - (latest.price_change_pct - latest.benchmark_change_pct)) < 0.01

    def test_track_price_invalid_recommendation(self, perf_repo):
        """Test tracking price for non-existent recommendation."""
        result = perf_repo.track_price(
            recommendation_id=99999,
            tracking_date=date.today(),
            price=100.0,
        )

        assert result is False

    def test_get_performance_data_empty(self, perf_repo, sample_recommendation):
        """Test getting performance data when no tracking exists."""
        tracking_data = perf_repo.get_performance_data(sample_recommendation)
        assert tracking_data == []

    def test_get_performance_data_ordered(self, perf_repo, sample_recommendation):
        """Test that performance data is returned in chronological order."""
        dates = [date.today() - timedelta(days=i) for i in [5, 2, 8, 1]]

        for tracking_date in dates:
            perf_repo.track_price(
                recommendation_id=sample_recommendation,
                tracking_date=tracking_date,
                price=150.0,
            )

        tracking_data = perf_repo.get_performance_data(sample_recommendation)

        # Verify chronological order
        for i in range(len(tracking_data) - 1):
            assert tracking_data[i].tracking_date <= tracking_data[i + 1].tracking_date

    def test_get_active_recommendations(self, perf_repo, rec_repo):
        """Test retrieving active recommendations."""
        from src.analysis import InvestmentSignal
        from src.analysis.models import ComponentScores, RiskAssessment

        # Create recommendations with different ages
        signals = []
        for days_ago in [10, 50, 200]:
            signal = InvestmentSignal(
                ticker=f"TICK{days_ago}",
                name=f"Test {days_ago}",
                market="US",
                current_price=100.0,
                currency="USD",
                scores=ComponentScores(
                    technical=75.0,
                    fundamental=75.0,
                    sentiment=75.0,
                ),
                final_score=75.0,
                recommendation="buy",
                confidence=80.0,
                expected_return_min=5.0,
                expected_return_max=15.0,
                key_reasons=["Test"],
                risk=RiskAssessment(
                    level="medium",
                    volatility="moderate",
                    volatility_pct=15.0,
                    liquidity="normal",
                    concentration_risk=False,
                ),
                generated_at=datetime.now(),
                analysis_date=(date.today() - timedelta(days=days_ago)).isoformat(),
                rationale="Test",
                caveats=[],
            )
            rec_repo.store_recommendation(signal, run_session_id=1, analysis_mode="rule_based")

        # Get recommendations within 180 days
        active = perf_repo.get_active_recommendations(max_age_days=180)
        assert len(active) == 2  # 10 and 50 days old

        # Get recommendations within 30 days
        active = perf_repo.get_active_recommendations(max_age_days=30)
        assert len(active) == 1  # Only 10 days old

    def test_get_active_recommendations_filter_by_signal(self, perf_repo, rec_repo):
        """Test filtering active recommendations by signal type."""
        from src.analysis import InvestmentSignal
        from src.analysis.models import ComponentScores, RiskAssessment

        # Create recommendations with different signal types
        for signal_type in ["buy", "strong_buy", "hold"]:
            signal = InvestmentSignal(
                ticker=f"TICK_{signal_type}",
                name=f"Test {signal_type}",
                market="US",
                current_price=100.0,
                currency="USD",
                scores=ComponentScores(
                    technical=75.0,
                    fundamental=75.0,
                    sentiment=75.0,
                ),
                final_score=75.0,
                recommendation=signal_type,
                confidence=80.0,
                expected_return_min=5.0,
                expected_return_max=15.0,
                key_reasons=["Test"],
                risk=RiskAssessment(
                    level="medium",
                    volatility="moderate",
                    volatility_pct=15.0,
                    liquidity="normal",
                    concentration_risk=False,
                ),
                generated_at=datetime.now(),
                analysis_date=(date.today() - timedelta(days=10)).isoformat(),
                rationale="Test",
                caveats=[],
            )
            rec_repo.store_recommendation(signal, run_session_id=1, analysis_mode="rule_based")

        # Filter by buy signals only
        active = perf_repo.get_active_recommendations(
            max_age_days=30, signal_types=["buy", "strong_buy"]
        )
        assert len(active) == 2

    def test_update_performance_summary(self, perf_repo, rec_repo):
        """Test updating performance summary."""
        from src.analysis import InvestmentSignal
        from src.analysis.models import ComponentScores, RiskAssessment

        # Create a recommendation
        signal = InvestmentSignal(
            ticker="AAPL",
            name="Apple Inc.",
            market="US",
            current_price=150.0,
            currency="USD",
            scores=ComponentScores(
                technical=75.0,
                fundamental=75.0,
                sentiment=75.0,
            ),
            final_score=75.0,
            recommendation="buy",
            confidence=80.0,
            expected_return_min=5.0,
            expected_return_max=15.0,
            key_reasons=["Test"],
            risk=RiskAssessment(
                level="medium",
                volatility="moderate",
                volatility_pct=15.0,
                liquidity="normal",
                concentration_risk=False,
            ),
            generated_at=datetime.now(),
            analysis_date=(date.today() - timedelta(days=10)).isoformat(),
            rationale="Test",
            caveats=[],
        )
        rec_id = rec_repo.store_recommendation(signal, run_session_id=1, analysis_mode="rule_based")

        # Track some prices
        perf_repo.track_price(rec_id, date.today() - timedelta(days=5), 155.0)
        perf_repo.track_price(rec_id, date.today(), 160.0)

        # Update summary
        result = perf_repo.update_performance_summary(period_days=30)
        assert result is True

    def test_get_performance_report(self, perf_repo, rec_repo):
        """Test generating performance report."""
        from src.analysis import InvestmentSignal
        from src.analysis.models import ComponentScores, RiskAssessment

        # Create recommendations
        for i in range(3):
            signal = InvestmentSignal(
                ticker=f"TICK{i}",
                name=f"Test {i}",
                market="US",
                current_price=100.0,
                currency="USD",
                scores=ComponentScores(
                    technical=75.0,
                    fundamental=75.0,
                    sentiment=75.0,
                ),
                final_score=75.0,
                recommendation="buy",
                confidence=80.0,
                expected_return_min=5.0,
                expected_return_max=15.0,
                key_reasons=["Test"],
                risk=RiskAssessment(
                    level="medium",
                    volatility="moderate",
                    volatility_pct=15.0,
                    liquidity="normal",
                    concentration_risk=False,
                ),
                generated_at=datetime.now(),
                analysis_date=(date.today() - timedelta(days=10)).isoformat(),
                rationale="Test",
                caveats=[],
            )
            rec_id = rec_repo.store_recommendation(
                signal, run_session_id=1, analysis_mode="rule_based"
            )
            # Track prices with varying returns
            perf_repo.track_price(rec_id, date.today(), 100.0 + i * 5)

        # Update summary
        perf_repo.update_performance_summary(period_days=30)

        # Get report
        report = perf_repo.get_performance_report(period_days=30)

        assert report is not None
        assert "total_recommendations" in report
        assert report["total_recommendations"] > 0

    def test_get_performance_report_no_data(self, perf_repo):
        """Test performance report with no data."""
        report = perf_repo.get_performance_report(period_days=30)

        assert report is not None
        assert "message" in report
        assert report["message"] == "No performance data available"
