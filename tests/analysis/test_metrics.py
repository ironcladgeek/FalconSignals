"""Tests for fundamental metrics analyzer using yfinance data."""

import pytest

from src.analysis.metrics import FundamentalMetricsAnalyzer


@pytest.mark.unit
class TestFundamentalMetricsAnalyzer:
    """Test FundamentalMetricsAnalyzer class with yfinance metrics."""

    def test_calculate_metrics_score_with_all_data(self):
        """Test scoring with complete metrics data."""
        metrics_data = {
            "valuation": {
                "trailing_pe": 18.5,
                "price_to_book": 2.5,
                "enterprise_to_ebitda": 12.0,
            },
            "profitability": {
                "gross_margin": 0.45,
                "operating_margin": 0.18,
                "profit_margin": 0.12,
                "return_on_equity": 0.18,
            },
            "financial_health": {
                "debt_to_equity": 0.6,
                "current_ratio": 2.0,
                "free_cashflow": 1000000,
            },
            "growth": {
                "revenue_growth": 0.12,
                "earnings_growth": 0.15,
            },
        }

        result = FundamentalMetricsAnalyzer.calculate_metrics_score(metrics_data)

        assert "overall_score" in result
        assert "valuation_score" in result
        assert "profitability_score" in result
        assert "financial_health_score" in result
        assert "growth_score" in result
        assert 0 <= result["overall_score"] <= 100

    def test_calculate_metrics_score_no_data(self):
        """Test scoring with no metrics data."""
        result = FundamentalMetricsAnalyzer.calculate_metrics_score({})

        assert result["overall_score"] == 50  # Neutral
        assert result["valuation_score"] == 50
        assert result["profitability_score"] == 50
        assert result["financial_health_score"] == 50
        assert result["growth_score"] == 50

    def test_score_valuation_cheap(self):
        """Test valuation scoring with cheap stock."""
        valuation_data = {
            "trailing_pe": 12.0,
            "price_to_book": 0.8,
            "enterprise_to_ebitda": 8.0,
        }

        score = FundamentalMetricsAnalyzer._score_valuation(valuation_data)

        assert score > 65  # Should be bullish (cheap)

    def test_score_valuation_expensive(self):
        """Test valuation scoring with expensive stock."""
        valuation_data = {
            "trailing_pe": 60.0,
            "price_to_book": 5.0,
            "enterprise_to_ebitda": 30.0,
        }

        score = FundamentalMetricsAnalyzer._score_valuation(valuation_data)

        assert score < 40  # Should be bearish (expensive)

    def test_score_profitability_high(self):
        """Test profitability scoring with high margins."""
        profitability_data = {
            "gross_margin": 0.65,
            "operating_margin": 0.30,
            "profit_margin": 0.25,
            "return_on_equity": 0.25,
            "return_on_assets": 0.18,
        }

        score = FundamentalMetricsAnalyzer._score_profitability(profitability_data)

        assert score > 70  # Strong profitability

    def test_score_profitability_low(self):
        """Test profitability scoring with low margins."""
        profitability_data = {
            "gross_margin": 0.08,
            "operating_margin": 0.02,
            "profit_margin": -0.01,
            "return_on_equity": 0.02,
        }

        score = FundamentalMetricsAnalyzer._score_profitability(profitability_data)

        assert score < 30  # Weak profitability

    def test_score_financial_health_strong(self):
        """Test financial health scoring with strong balance sheet."""
        financial_health_data = {
            "debt_to_equity": 0.3,
            "current_ratio": 2.5,
            "quick_ratio": 1.8,
            "free_cashflow": 1000000,
            "operating_cashflow": 1500000,
        }

        score = FundamentalMetricsAnalyzer._score_financial_health(financial_health_data)

        assert score > 70  # Strong financial health

    def test_score_financial_health_weak(self):
        """Test financial health scoring with weak balance sheet."""
        financial_health_data = {
            "debt_to_equity": 4.0,
            "current_ratio": 0.8,
            "quick_ratio": 0.5,
            "free_cashflow": -500000,
            "operating_cashflow": -200000,
        }

        score = FundamentalMetricsAnalyzer._score_financial_health(financial_health_data)

        assert score < 30  # Weak financial health

    def test_score_growth_high(self):
        """Test growth scoring with high growth rates."""
        growth_data = {
            "revenue_growth": 0.25,
            "earnings_growth": 0.30,
        }

        score = FundamentalMetricsAnalyzer._score_growth(growth_data)

        assert score > 70  # Strong growth

    def test_score_growth_negative(self):
        """Test growth scoring with negative growth."""
        growth_data = {
            "revenue_growth": -0.10,
            "earnings_growth": -0.15,
        }

        score = FundamentalMetricsAnalyzer._score_growth(growth_data)

        assert score < 40  # Weak growth

    def test_get_recommendation_strong_buy(self):
        """Test recommendation for high metrics score."""
        recommendation = FundamentalMetricsAnalyzer.get_recommendation(80)
        assert recommendation == "strong_buy"

    def test_get_recommendation_buy(self):
        """Test recommendation for good metrics score."""
        recommendation = FundamentalMetricsAnalyzer.get_recommendation(65)
        assert recommendation == "buy"

    def test_get_recommendation_hold(self):
        """Test recommendation for neutral metrics score."""
        recommendation = FundamentalMetricsAnalyzer.get_recommendation(50)
        assert recommendation == "hold"

    def test_get_recommendation_sell(self):
        """Test recommendation for poor metrics score."""
        recommendation = FundamentalMetricsAnalyzer.get_recommendation(30)
        assert recommendation == "sell"

    def test_get_recommendation_strong_sell(self):
        """Test recommendation for very poor metrics score."""
        recommendation = FundamentalMetricsAnalyzer.get_recommendation(10)
        assert recommendation == "strong_sell"

    def test_score_bounds(self):
        """Test that all metrics scores stay within 0-100 bounds."""
        # Extreme positive metrics
        excellent_metrics = {
            "valuation": {
                "trailing_pe": 8.0,
                "price_to_book": 0.5,
                "enterprise_to_ebitda": 5.0,
            },
            "profitability": {
                "gross_margin": 0.80,
                "operating_margin": 0.40,
                "profit_margin": 0.30,
                "return_on_equity": 0.40,
                "return_on_assets": 0.30,
            },
            "financial_health": {
                "debt_to_equity": 0.1,
                "current_ratio": 4.0,
                "quick_ratio": 3.0,
                "free_cashflow": 10000000,
            },
            "growth": {
                "revenue_growth": 0.50,
                "earnings_growth": 0.60,
            },
        }

        result = FundamentalMetricsAnalyzer.calculate_metrics_score(excellent_metrics)
        assert result["overall_score"] <= 100
        assert result["valuation_score"] <= 100
        assert result["profitability_score"] <= 100
        assert result["financial_health_score"] <= 100
        assert result["growth_score"] <= 100

        # Extreme negative metrics
        poor_metrics = {
            "valuation": {
                "trailing_pe": 100.0,
                "price_to_book": 10.0,
                "enterprise_to_ebitda": 50.0,
            },
            "profitability": {
                "gross_margin": 0.02,
                "operating_margin": -0.20,
                "profit_margin": -0.25,
            },
            "financial_health": {
                "debt_to_equity": 10.0,
                "current_ratio": 0.3,
                "quick_ratio": 0.1,
                "free_cashflow": -5000000,
            },
            "growth": {
                "revenue_growth": -0.40,
                "earnings_growth": -0.50,
            },
        }

        result = FundamentalMetricsAnalyzer.calculate_metrics_score(poor_metrics)
        assert result["overall_score"] >= 0
        assert result["valuation_score"] >= 0
        assert result["profitability_score"] >= 0
        assert result["financial_health_score"] >= 0
        assert result["growth_score"] >= 0

    def test_component_weighting(self):
        """Test that component weighting is applied correctly."""
        # High valuation score, neutral others
        mixed_metrics = {
            "valuation": {
                "trailing_pe": 10.0,
                "price_to_book": 0.5,
            },
            "profitability": {
                "profit_margin": 0.10,
            },
            "financial_health": {
                "current_ratio": 1.5,
            },
            "growth": {
                "revenue_growth": 0.05,
            },
        }

        result = FundamentalMetricsAnalyzer.calculate_metrics_score(mixed_metrics)

        # Valuation (30%), Profitability (30%), Financial Health (25%), Growth (15%)
        # Should be skewed towards valuation and profitability
        assert result["overall_score"] > 50
        assert result["valuation_score"] > 60
