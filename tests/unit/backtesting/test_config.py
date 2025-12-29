"""Tests for backtesting configuration."""

import pytest

from src.backtesting.config import BacktestConfig, BacktestFrequency


def test_backtest_config_defaults():
    """Test BacktestConfig with default values."""
    config = BacktestConfig()

    assert config.default_frequency == BacktestFrequency.WEEKLY
    assert config.default_period_days == 90
    assert config.max_concurrent_analyses == 5
    assert config.llm_cost_limit_per_backtest == 100.0
    assert config.require_confirmation is True
    assert config.cost_confirmation_threshold == 20.0
    assert config.default_benchmark == "SPY"
    assert config.alternative_benchmarks == ["QQQ", "IWM"]
    assert config.report_formats == ["markdown", "json", "csv"]
    assert config.include_visualizations is False
    assert config.allow_resume is True
    assert config.skip_existing_data is True


def test_backtest_config_custom_values():
    """Test BacktestConfig with custom values."""
    config = BacktestConfig(
        default_frequency=BacktestFrequency.DAILY,
        default_period_days=30,
        max_concurrent_analyses=10,
        llm_cost_limit_per_backtest=50.0,
        require_confirmation=False,
        cost_confirmation_threshold=10.0,
        default_benchmark="QQQ",
        alternative_benchmarks=["SPY"],
        report_formats=["json"],
        include_visualizations=True,
        allow_resume=False,
        skip_existing_data=False,
    )

    assert config.default_frequency == BacktestFrequency.DAILY
    assert config.default_period_days == 30
    assert config.max_concurrent_analyses == 10
    assert config.llm_cost_limit_per_backtest == 50.0
    assert config.require_confirmation is False
    assert config.cost_confirmation_threshold == 10.0
    assert config.default_benchmark == "QQQ"
    assert config.alternative_benchmarks == ["SPY"]
    assert config.report_formats == ["json"]
    assert config.include_visualizations is True
    assert config.allow_resume is False
    assert config.skip_existing_data is False


def test_backtest_config_validation():
    """Test BacktestConfig validation."""
    # Test valid period_days range
    config = BacktestConfig(default_period_days=1)
    assert config.default_period_days == 1

    config = BacktestConfig(default_period_days=365)
    assert config.default_period_days == 365

    # Test invalid period_days (should raise validation error)
    with pytest.raises(ValueError):
        BacktestConfig(default_period_days=0)

    with pytest.raises(ValueError):
        BacktestConfig(default_period_days=366)

    # Test valid max_concurrent_analyses range
    config = BacktestConfig(max_concurrent_analyses=1)
    assert config.max_concurrent_analyses == 1

    config = BacktestConfig(max_concurrent_analyses=20)
    assert config.max_concurrent_analyses == 20

    # Test invalid max_concurrent_analyses
    with pytest.raises(ValueError):
        BacktestConfig(max_concurrent_analyses=0)

    with pytest.raises(ValueError):
        BacktestConfig(max_concurrent_analyses=21)


def test_backtest_frequency_enum():
    """Test BacktestFrequency enum values."""
    assert BacktestFrequency.DAILY.value == "daily"
    assert BacktestFrequency.WEEKLY.value == "weekly"
    assert BacktestFrequency.MONTHLY.value == "monthly"

    # Test enum comparison
    assert BacktestFrequency.DAILY != BacktestFrequency.WEEKLY
    assert BacktestFrequency.WEEKLY != BacktestFrequency.MONTHLY
