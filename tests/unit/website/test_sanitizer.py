"""Tests for content sanitizer functions."""

from copy import deepcopy
from datetime import datetime

import pytest

from src.analysis import (
    ComponentScores,
    DailyReport,
    InvestmentSignal,
    Recommendation,
    RiskAssessment,
    RiskLevel,
)
from src.website.sanitizer import (
    get_safe_signal_summary,
    sanitize_report_for_web,
    sanitize_signal_for_web,
)


def create_test_signal(
    ticker="AAPL",
    recommendation=Recommendation.BUY,
    confidence=90,
    price=150.0,
) -> InvestmentSignal:
    """Helper to create valid test signal."""
    return InvestmentSignal(
        ticker=ticker,
        name=f"{ticker} Inc.",
        market="US",
        sector="Technology",
        current_price=price,
        currency="USD",
        scores=ComponentScores(technical=85, fundamental=80, sentiment=88),
        final_score=84,
        recommendation=recommendation,
        confidence=confidence,
        time_horizon="3M",
        expected_return_min=5.0,
        expected_return_max=15.0,
        key_reasons=["Strong fundamentals", "Positive momentum"],
        risk=RiskAssessment(
            level=RiskLevel.LOW,
            volatility="normal",
            volatility_pct=2.5,
            liquidity="highly_liquid",
            concentration_risk=False,
            sector_risk=None,
            flags=[],
        ),
        allocation=None,
        generated_at=datetime.now(),
        analysis_date="2025-12-10",
        rationale="Test signal",
        caveats=[],
        metadata=None,
    )


@pytest.fixture
def sample_report():
    """Create sample DailyReport with private data."""
    signal = create_test_signal()
    return DailyReport(
        report_date="2025-12-10",
        report_time=datetime.now(),
        analysis_date="2025-12-10",
        market_overview="Test market overview",
        market_indices={},
        strong_signals=[signal],
        moderate_signals=[],
        portfolio_alerts=[{"ticker": "TEST", "alert": "Rebalance needed"}],
        key_news=[],
        watchlist_additions=["NVDA", "MSFT"],
        watchlist_removals=["IBM"],
        allocation_suggestion=None,
        total_signals_generated=1,
        strong_signals_count=1,
        moderate_signals_count=0,
        disclaimers=["Test disclaimer"],
        data_sources=["test_source"],
    )


@pytest.fixture
def sample_signal():
    """Create sample investment signal."""
    return create_test_signal()


class TestSanitizer:
    """Test sanitizer functions."""

    def test_sanitize_report_removes_allocation(self, sample_report):
        """Test that allocation_suggestion is removed."""
        # Add allocation to test removal
        from src.analysis import AllocationSuggestion

        sample_report.allocation_suggestion = AllocationSuggestion(
            ticker="AAPL", eur=2500, percentage=50, shares=16.67
        )

        original = deepcopy(sample_report)
        sanitized = sanitize_report_for_web(sample_report)

        # Check allocation removed
        assert sanitized.allocation_suggestion is None
        assert original.allocation_suggestion is not None  # Original unchanged

    def test_sanitize_report_removes_watchlist(self, sample_report):
        """Test that watchlist fields are removed."""
        sanitized = sanitize_report_for_web(sample_report)

        assert sanitized.watchlist_additions == []
        assert sanitized.watchlist_removals == []

    def test_sanitize_report_removes_alerts(self, sample_report):
        """Test that portfolio_alerts are removed."""
        sanitized = sanitize_report_for_web(sample_report)

        assert sanitized.portfolio_alerts == []

    def test_sanitize_report_keeps_other_fields(self, sample_report):
        """Test that other fields are preserved."""
        sanitized = sanitize_report_for_web(sample_report)

        assert sanitized.report_date == "2025-12-10"
        assert len(sanitized.strong_signals) == 1
        assert sanitized.market_overview == "Test market overview"

    def test_sanitize_report_doesnt_modify_original(self, sample_report):
        """Test that original report is not modified."""
        sample_report.watchlist_additions = ["NVDA"]
        original_watchlist = sample_report.watchlist_additions.copy()

        sanitized = sanitize_report_for_web(sample_report)

        # Original should be unchanged
        assert sample_report.watchlist_additions == original_watchlist
        assert sanitized.watchlist_additions == []

    def test_sanitize_signal_creates_copy(self, sample_signal):
        """Test that signal sanitization creates a copy."""
        sanitized = sanitize_signal_for_web(sample_signal)

        assert sanitized is not sample_signal
        assert sanitized.ticker == sample_signal.ticker

    def test_get_safe_signal_summary(self, sample_signal):
        """Test safe signal summary extraction."""
        summary = get_safe_signal_summary(sample_signal)

        # Check public fields are included
        assert summary["ticker"] == "AAPL"
        assert summary["recommendation"] == "buy"
        assert summary["confidence"] == 90
        assert summary["current_price"] == 150.0
        assert summary["analysis_date"] == "2025-12-10"

        # Check scores are included
        assert summary["component_scores"]["technical"] == 85
        assert summary["component_scores"]["fundamental"] == 80
        assert summary["component_scores"]["sentiment"] == 88

        # Check risk level included
        assert summary["risk_level"] == "low"

    def test_get_safe_signal_summary_handles_none_scores(self):
        """Test summary with missing scores."""
        signal = create_test_signal(ticker="TEST", recommendation=Recommendation.HOLD_BULLISH)
        # Signal will have scores from create_test_signal

        summary = get_safe_signal_summary(signal)

        assert summary["ticker"] == "TEST"
        assert "component_scores" in summary

    def test_sanitize_empty_report(self):
        """Test sanitizing an empty report."""
        report = DailyReport(
            report_date="2025-12-10",
            report_time=datetime.now(),
            analysis_date="2025-12-10",
            market_overview="Empty",
            market_indices={},
            strong_signals=[],
            moderate_signals=[],
            portfolio_alerts=[],
            key_news=[],
            watchlist_additions=[],
            watchlist_removals=[],
            allocation_suggestion=None,
            total_signals_generated=0,
            strong_signals_count=0,
            moderate_signals_count=0,
            disclaimers=[],
            data_sources=[],
        )
        sanitized = sanitize_report_for_web(report)

        assert sanitized.report_date == "2025-12-10"
        assert len(sanitized.strong_signals) == 0

    def test_sanitize_report_with_missing_fields(self):
        """Test sanitizing report that doesn't have all private fields."""
        report = DailyReport(
            report_date="2025-12-10",
            report_time=datetime.now(),
            analysis_date="2025-12-10",
            market_overview="Test",
            market_indices={},
            strong_signals=[],
            moderate_signals=[],
            portfolio_alerts=[],
            key_news=[],
            watchlist_additions=[],
            watchlist_removals=[],
            allocation_suggestion=None,
            total_signals_generated=0,
            strong_signals_count=0,
            moderate_signals_count=0,
            disclaimers=[],
            data_sources=[],
        )

        sanitized = sanitize_report_for_web(report)

        # Should work without errors
        assert sanitized.report_date == "2025-12-10"
        assert len(sanitized.strong_signals) == 0

    def test_sanitize_report_with_nested_data(self):
        """Test sanitization preserves signal data."""
        signal = create_test_signal()
        report = DailyReport(
            report_date="2025-12-10",
            report_time=datetime.now(),
            analysis_date="2025-12-10",
            market_overview="Test",
            market_indices={},
            strong_signals=[signal],
            moderate_signals=[],
            portfolio_alerts=[],
            key_news=[],
            watchlist_additions=[],
            watchlist_removals=[],
            allocation_suggestion=None,
            total_signals_generated=1,
            strong_signals_count=1,
            moderate_signals_count=0,
            disclaimers=[],
            data_sources=[],
        )

        sanitized = sanitize_report_for_web(report)

        # Signal data should be preserved
        assert len(sanitized.strong_signals) == 1
        assert sanitized.strong_signals[0].ticker == "AAPL"
