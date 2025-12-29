"""Tests for backtesting data models."""

from datetime import date, datetime, timedelta

from src.backtesting.models import BacktestResult, BacktestSummary


def test_backtest_result_creation():
    """Test BacktestResult model creation."""
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    dates = [start, start + timedelta(days=7), start + timedelta(days=14)]

    result = BacktestResult(
        start_date=start,
        end_date=end,
        frequency="weekly",
        analysis_mode="rule_based",
        tickers=["AAPL", "MSFT"],
        analysis_dates=dates,
        total_analyses=6,
        successful_analyses=5,
        failed_analyses=1,
        recommendation_count=5,
    )

    assert result.start_date == start
    assert result.end_date == end
    assert result.frequency == "weekly"
    assert result.analysis_mode == "rule_based"
    assert result.tickers == ["AAPL", "MSFT"]
    assert result.analysis_dates == dates
    assert result.total_analyses == 6
    assert result.successful_analyses == 5
    assert result.failed_analyses == 1
    assert result.recommendation_count == 5
    assert result.run_session_ids == []
    assert result.estimated_cost is None
    assert result.actual_cost is None
    assert isinstance(result.started_at, datetime)
    assert result.completed_at is None
    assert result.duration_seconds is None
    assert result.errors == []


def test_backtest_result_with_costs():
    """Test BacktestResult with cost tracking (LLM mode)."""
    result = BacktestResult(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        frequency="monthly",
        analysis_mode="llm",
        tickers=["NVDA"],
        analysis_dates=[date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)],
        total_analyses=3,
        successful_analyses=3,
        failed_analyses=0,
        recommendation_count=3,
        estimated_cost=1.95,  # 3 analyses × €0.65 each
        actual_cost=2.10,
    )

    assert result.estimated_cost == 1.95
    assert result.actual_cost == 2.10


def test_backtest_result_with_errors():
    """Test BacktestResult with error tracking."""
    errors = [
        {"date": "2024-01-01", "ticker": "AAPL", "error": "No data available"},
        {"date": "2024-01-08", "ticker": "MSFT", "error": "API timeout"},
    ]

    result = BacktestResult(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        frequency="weekly",
        analysis_mode="rule_based",
        tickers=["AAPL", "MSFT"],
        analysis_dates=[date(2024, 1, 1), date(2024, 1, 8)],
        total_analyses=4,
        successful_analyses=2,
        failed_analyses=2,
        recommendation_count=2,
        errors=errors,
    )

    assert len(result.errors) == 2
    assert result.errors[0]["ticker"] == "AAPL"
    assert result.errors[1]["ticker"] == "MSFT"


def test_backtest_summary_creation():
    """Test BacktestSummary model creation."""
    summary = BacktestSummary(
        backtest_id="bt_20240101_20241231",
        date_range="2024-01-01 to 2024-12-31",
        total_recommendations=156,
        signal_distribution={
            "strong_buy": 12,
            "buy": 60,
            "hold": 54,
            "sell": 30,
        },
        success_rate=95.5,
        average_confidence=72.3,
        total_duration_minutes=45.2,
    )

    assert summary.backtest_id == "bt_20240101_20241231"
    assert summary.date_range == "2024-01-01 to 2024-12-31"
    assert summary.total_recommendations == 156
    assert summary.signal_distribution["strong_buy"] == 12
    assert summary.signal_distribution["buy"] == 60
    assert summary.success_rate == 95.5
    assert summary.average_confidence == 72.3
    assert summary.total_duration_minutes == 45.2
    assert summary.total_cost is None
    assert summary.cost_per_recommendation is None
    assert summary.avg_analysis_time_seconds is None


def test_backtest_summary_with_costs():
    """Test BacktestSummary with cost tracking."""
    summary = BacktestSummary(
        backtest_id="bt_llm_test",
        date_range="2024-06-01 to 2024-09-01",
        total_recommendations=39,
        signal_distribution={"buy": 25, "hold": 14},
        success_rate=100.0,
        average_confidence=78.5,
        total_cost=25.35,
        cost_per_recommendation=0.65,
        total_duration_minutes=32.5,
        avg_analysis_time_seconds=50.0,
    )

    assert summary.total_cost == 25.35
    assert summary.cost_per_recommendation == 0.65
    assert summary.avg_analysis_time_seconds == 50.0
