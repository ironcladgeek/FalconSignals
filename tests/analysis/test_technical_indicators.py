"""Unit tests for the technical indicators module."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.technical_indicators import ConfigurableTechnicalAnalyzer
from src.config.schemas import IndicatorConfig, TechnicalIndicatorsConfig


@pytest.fixture
def sample_price_df():
    """Create sample price DataFrame for testing."""
    np.random.seed(42)
    n_periods = 250  # Must be > 200 (min_periods_required default)
    dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="D")
    base_price = 100.0

    # Generate realistic price data with trend
    returns = np.random.normal(0.001, 0.02, n_periods)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame(
        {
            "date": dates,
            "open": prices * (1 - np.random.uniform(0, 0.01, n_periods)),
            "high": prices * (1 + np.random.uniform(0, 0.02, n_periods)),
            "low": prices * (1 - np.random.uniform(0, 0.02, n_periods)),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, n_periods),
        }
    )
    df.set_index("date", inplace=True)
    return df


@pytest.fixture
def short_price_df():
    """Create a short price DataFrame with insufficient data."""
    dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "close": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "volume": [1000000] * 5,
        }
    ).set_index("date")


@pytest.fixture
def default_config():
    """Create default technical indicators config."""
    return TechnicalIndicatorsConfig()


@pytest.fixture
def analyzer(default_config):
    """Create a ConfigurableTechnicalAnalyzer with default config."""
    return ConfigurableTechnicalAnalyzer(default_config)


class TestConfigurableTechnicalAnalyzer:
    """Test suite for ConfigurableTechnicalAnalyzer class."""

    def test_initialization_default_config(self):
        """Test analyzer initializes with default config."""
        analyzer = ConfigurableTechnicalAnalyzer()
        assert analyzer.config is not None
        assert isinstance(analyzer.config, TechnicalIndicatorsConfig)

    def test_initialization_custom_config(self, default_config):
        """Test analyzer initializes with custom config."""
        analyzer = ConfigurableTechnicalAnalyzer(default_config)
        assert analyzer.config == default_config

    def test_calculate_indicators_success(self, analyzer, sample_price_df):
        """Test calculating indicators returns expected structure."""
        results = analyzer.calculate_indicators(sample_price_df)

        assert "periods" in results
        assert "latest_price" in results
        assert "indicators" in results
        assert "trend" in results
        assert "volume_analysis" in results
        assert results["periods"] == 250

    def test_calculate_indicators_empty_df(self, analyzer):
        """Test handling empty DataFrame."""
        empty_df = pd.DataFrame()
        results = analyzer.calculate_indicators(empty_df)

        assert "error" in results
        assert "No price data" in results["error"]

    def test_calculate_indicators_insufficient_data(self, analyzer, short_price_df):
        """Test handling insufficient data."""
        results = analyzer.calculate_indicators(short_price_df)

        assert "error" in results
        assert "Insufficient data" in results["error"]

    def test_normalize_columns(self, analyzer, sample_price_df):
        """Test column normalization works."""
        # Create df with different column names
        df = sample_price_df.copy()
        df = df.rename(columns={"close": "close_price", "high": "high_price", "low": "low_price"})

        normalized = analyzer._normalize_columns(
            df, "close_price", "high_price", "low_price", "volume"
        )

        assert "close" in normalized.columns
        assert "high" in normalized.columns
        assert "low" in normalized.columns

    def test_make_indicator_key_with_length(self, analyzer):
        """Test indicator key generation with length parameter."""
        config = IndicatorConfig(name="sma", params={"length": 50})
        key = analyzer._make_indicator_key(config)
        assert key == "sma_50"

    def test_make_indicator_key_without_length(self, analyzer):
        """Test indicator key generation without length parameter."""
        config = IndicatorConfig(name="macd", params={"fast": 12, "slow": 26})
        key = analyzer._make_indicator_key(config)
        assert key == "macd"

    def test_manual_rsi_calculation(self, analyzer, sample_price_df):
        """Test manual RSI calculation."""
        rsi = analyzer._manual_rsi(sample_price_df["close"], period=14)

        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_manual_macd_calculation(self, analyzer, sample_price_df):
        """Test manual MACD calculation."""
        macd = analyzer._manual_macd(sample_price_df["close"], fast=12, slow=26, signal=9)

        assert isinstance(macd, dict)
        assert "line" in macd
        assert "signal" in macd
        assert "histogram" in macd

    def test_manual_atr_calculation(self, analyzer, sample_price_df):
        """Test manual ATR calculation."""
        atr = analyzer._manual_atr(sample_price_df, period=14)

        assert isinstance(atr, float)
        assert atr > 0

    def test_analyze_trend_neutral(self, analyzer, sample_price_df):
        """Test trend analysis with no clear signals."""
        # Empty indicators means neutral trend
        trend = analyzer._analyze_trend(sample_price_df, {})

        assert trend["direction"] == "neutral"
        assert "signals" in trend

    def test_analyze_trend_bullish(self, analyzer, sample_price_df):
        """Test trend analysis with bullish signals."""
        indicators = {
            "sma_50": {"value": 110.0},
            "sma_200": {"value": 100.0},
            "rsi": {"value": 60.0},
            "macd": {"histogram": 0.5},
        }
        trend = analyzer._analyze_trend(sample_price_df, indicators)

        assert trend["direction"] == "bullish"
        assert "Golden Cross" in " ".join(trend["signals"])

    def test_analyze_trend_bearish(self, analyzer, sample_price_df):
        """Test trend analysis with bearish signals."""
        indicators = {
            "sma_50": {"value": 90.0},
            "sma_200": {"value": 100.0},
            "rsi": {"value": 40.0},
            "macd": {"histogram": -0.5},
        }
        trend = analyzer._analyze_trend(sample_price_df, indicators)

        assert trend["direction"] == "bearish"
        assert "Death Cross" in " ".join(trend["signals"])

    def test_analyze_trend_overbought(self, analyzer, sample_price_df):
        """Test trend analysis detects overbought RSI."""
        indicators = {"rsi": {"value": 75.0}}
        trend = analyzer._analyze_trend(sample_price_df, indicators)

        assert any("overbought" in s for s in trend["signals"])

    def test_analyze_trend_oversold(self, analyzer, sample_price_df):
        """Test trend analysis detects oversold RSI."""
        indicators = {"rsi": {"value": 25.0}}
        trend = analyzer._analyze_trend(sample_price_df, indicators)

        assert any("oversold" in s for s in trend["signals"])

    def test_analyze_volume(self, analyzer, sample_price_df):
        """Test volume analysis."""
        volume_analysis = analyzer._analyze_volume(sample_price_df)

        assert "current" in volume_analysis
        assert "avg_20" in volume_analysis
        assert "ratio" in volume_analysis
        assert "status" in volume_analysis

    def test_analyze_volume_missing_data(self, analyzer):
        """Test volume analysis with missing volume data."""
        df = pd.DataFrame({"close": [100, 101, 102]})
        volume_analysis = analyzer._analyze_volume(df)

        assert "error" in volume_analysis

    def test_get_indicator_summary(self, analyzer, sample_price_df):
        """Test indicator summary generation."""
        results = analyzer.calculate_indicators(sample_price_df)
        summary = analyzer.get_indicator_summary(results)

        assert "latest_price" in summary
        assert "trend" in summary
        assert "trend_strength" in summary

    def test_get_indicator_summary_with_error(self, analyzer):
        """Test indicator summary with error results."""
        error_results = {"error": "No data"}
        summary = analyzer.get_indicator_summary(error_results)

        assert "error" in summary

    def test_get_indicator_summary_rsi(self, analyzer, sample_price_df):
        """Test indicator summary includes RSI."""
        # Create config with RSI enabled
        config = TechnicalIndicatorsConfig(
            indicators=[IndicatorConfig(name="rsi", enabled=True, params={"length": 14})]
        )
        analyzer = ConfigurableTechnicalAnalyzer(config)
        results = analyzer.calculate_indicators(sample_price_df)
        summary = analyzer.get_indicator_summary(results)

        # RSI should be in summary if calculated
        if "rsi" in results.get("indicators", {}):
            assert "rsi" in summary

    def test_calculate_fallback_sma(self, analyzer, sample_price_df):
        """Test fallback SMA calculation."""
        config = IndicatorConfig(name="sma", enabled=True, params={"length": 20})

        # Force fallback by disabling pandas_ta
        original_setting = analyzer.config.use_pandas_ta
        analyzer.config.use_pandas_ta = False

        result = analyzer._calculate_fallback(sample_price_df, config)

        analyzer.config.use_pandas_ta = original_setting

        assert result is not None
        assert "value" in result

    def test_calculate_fallback_ema(self, analyzer, sample_price_df):
        """Test fallback EMA calculation."""
        config = IndicatorConfig(name="ema", enabled=True, params={"length": 20})

        analyzer.config.use_pandas_ta = False
        result = analyzer._calculate_fallback(sample_price_df, config)
        analyzer.config.use_pandas_ta = True

        assert result is not None
        assert "value" in result

    def test_calculate_fallback_unsupported(self, analyzer, sample_price_df):
        """Test fallback with unsupported indicator."""
        config = IndicatorConfig(name="unsupported_indicator", enabled=True, params={})

        analyzer.config.use_pandas_ta = False
        result = analyzer._calculate_fallback(sample_price_df, config)
        analyzer.config.use_pandas_ta = True

        assert result is None

    def test_trend_strength_strong(self, analyzer, sample_price_df):
        """Test trend strength calculation for strong trends."""
        # Multiple bullish signals should result in strong trend
        indicators = {
            "sma_50": {"value": 110.0},
            "sma_200": {"value": 100.0},
            "macd": {"histogram": 0.5},
        }
        trend = analyzer._analyze_trend(sample_price_df, indicators)

        assert trend["strength"] == "strong"

    def test_trend_strength_weak(self, analyzer, sample_price_df):
        """Test trend strength calculation for weak trends."""
        # No clear signals should result in weak trend
        indicators = {"rsi": {"value": 50.0}}  # Neutral RSI
        trend = analyzer._analyze_trend(sample_price_df, indicators)

        # RSI at 50 doesn't generate signals, so strength should be weak
        assert trend["strength"] == "weak"

    def test_volume_status_high(self, analyzer):
        """Test volume status detection for high volume."""
        # Create df with last day having high volume
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        volumes = [1000000] * 29 + [3000000]  # Last day 3x normal
        df = pd.DataFrame(
            {
                "close": [100] * 30,
                "volume": volumes,
            },
            index=dates,
        )

        volume = analyzer._analyze_volume(df)
        assert volume["status"] == "high"

    def test_volume_status_low(self, analyzer):
        """Test volume status detection for low volume."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        volumes = [1000000] * 29 + [200000]  # Last day 0.2x normal
        df = pd.DataFrame(
            {
                "close": [100] * 30,
                "volume": volumes,
            },
            index=dates,
        )

        volume = analyzer._analyze_volume(df)
        assert volume["status"] == "low"

    def test_disabled_indicators_skipped(self, sample_price_df):
        """Test that disabled indicators are not calculated."""
        config = TechnicalIndicatorsConfig(
            indicators=[
                IndicatorConfig(name="rsi", enabled=False, params={"length": 14}),
                IndicatorConfig(name="macd", enabled=True, params={}),
            ]
        )
        analyzer = ConfigurableTechnicalAnalyzer(config)
        results = analyzer.calculate_indicators(sample_price_df)

        # RSI should not be in results since it's disabled
        assert "rsi" not in results.get("indicators", {})


class TestIndicatorConfig:
    """Test suite for IndicatorConfig dataclass."""

    def test_default_indicator_config(self):
        """Test default indicator config values."""
        config = IndicatorConfig(name="rsi")
        assert config.name == "rsi"
        assert config.enabled is True
        assert config.params == {}

    def test_custom_indicator_config(self):
        """Test custom indicator config."""
        config = IndicatorConfig(
            name="sma",
            enabled=True,
            params={"length": 50},
        )
        assert config.name == "sma"
        assert config.params["length"] == 50


class TestTechnicalIndicatorsConfig:
    """Test suite for TechnicalIndicatorsConfig."""

    def test_default_config(self):
        """Test default config has expected defaults."""
        config = TechnicalIndicatorsConfig()
        assert config.use_pandas_ta is True
        assert config.min_periods_required > 0

    def test_config_with_indicators(self):
        """Test config with custom indicators."""
        indicators = [
            IndicatorConfig(name="rsi", params={"length": 14}),
            IndicatorConfig(name="macd", params={"fast": 12, "slow": 26}),
        ]
        config = TechnicalIndicatorsConfig(indicators=indicators)

        assert len(config.indicators) == 2
