"""Fundamental metrics analysis using yfinance data.

Analyzes valuation, profitability, financial health, and growth metrics
from yfinance free tier data to score fundamental strength.
"""

from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class FundamentalMetricsAnalyzer:
    """Scores fundamental strength based on yfinance metrics.

    Evaluates:
    - Valuation metrics (P/E, P/B, EV/EBITDA, PEG)
    - Profitability metrics (margins, ROE, ROA)
    - Financial health (debt ratios, liquidity, cash flow)
    - Growth metrics (revenue and earnings growth)
    """

    @staticmethod
    def calculate_metrics_score(metrics_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate fundamental score from yfinance metrics.

        Args:
            metrics_data: Dictionary containing yfinance metrics
                Expected keys: valuation, profitability, financial_health, growth

        Returns:
            Dictionary with component scores and overall metrics score
        """
        valuation_score = FundamentalMetricsAnalyzer._score_valuation(
            metrics_data.get("valuation", {})
        )
        profitability_score = FundamentalMetricsAnalyzer._score_profitability(
            metrics_data.get("profitability", {})
        )
        financial_health_score = FundamentalMetricsAnalyzer._score_financial_health(
            metrics_data.get("financial_health", {})
        )
        growth_score = FundamentalMetricsAnalyzer._score_growth(metrics_data.get("growth", {}))

        # Weight the components
        # Valuation: 30%, Profitability: 30%, Financial Health: 25%, Growth: 15%
        overall_score = (
            valuation_score * 0.30
            + profitability_score * 0.30
            + financial_health_score * 0.25
            + growth_score * 0.15
        )

        return {
            "overall_score": max(0, min(100, overall_score)),
            "valuation_score": valuation_score,
            "profitability_score": profitability_score,
            "financial_health_score": financial_health_score,
            "growth_score": growth_score,
            "components": {
                "valuation": {
                    "score": valuation_score,
                    "data": metrics_data.get("valuation", {}),
                },
                "profitability": {
                    "score": profitability_score,
                    "data": metrics_data.get("profitability", {}),
                },
                "financial_health": {
                    "score": financial_health_score,
                    "data": metrics_data.get("financial_health", {}),
                },
                "growth": {
                    "score": growth_score,
                    "data": metrics_data.get("growth", {}),
                },
            },
        }

    @staticmethod
    def _score_valuation(valuation_data: dict[str, Any]) -> float:
        """Score valuation attractiveness.

        Lower is better for most valuation metrics.
        Args:
            valuation_data: Valuation metrics (P/E, P/B, EV/EBITDA, PEG)

        Returns:
            Score 0-100 (higher = cheaper/more attractive)
        """
        if not valuation_data:
            return 50  # Neutral if no data

        score = 50  # Start neutral

        # P/E ratio scoring (lower is better)
        pe = valuation_data.get("trailing_pe")
        if pe and pe > 0:
            if pe < 15:
                score += 15  # Very cheap
            elif pe < 20:
                score += 10  # Cheap
            elif pe < 30:
                score += 5  # Fair
            elif pe > 50:
                score -= 15  # Expensive

        # P/B ratio scoring (lower is better)
        pb = valuation_data.get("price_to_book")
        if pb and pb > 0:
            if pb < 1.0:
                score += 10  # Trading below book value
            elif pb < 2.0:
                score += 5  # Fair
            elif pb > 4.0:
                score -= 10  # Expensive

        # EV/EBITDA scoring (lower is better)
        ev_ebitda = valuation_data.get("enterprise_to_ebitda")
        if ev_ebitda and ev_ebitda > 0:
            if ev_ebitda < 10:
                score += 10  # Reasonable
            elif ev_ebitda < 15:
                score += 5
            elif ev_ebitda > 25:
                score -= 10  # Expensive

        # PEG ratio scoring (lower is better, <1 is ideal)
        peg = valuation_data.get("peg_ratio")
        if peg and peg > 0:
            if peg < 1.0:
                score += 10  # Undervalued relative to growth
            elif peg < 1.5:
                score += 5  # Fair
            elif peg > 2.0:
                score -= 10  # Expensive relative to growth

        return max(0, min(100, score))

    @staticmethod
    def _score_profitability(profitability_data: dict[str, Any]) -> float:
        """Score profitability quality and strength.

        Higher margins and returns are better.
        Args:
            profitability_data: Profitability metrics (margins, ROE, ROA)

        Returns:
            Score 0-100 (higher = more profitable)
        """
        if not profitability_data:
            return 50  # Neutral if no data

        score = 50  # Start neutral

        # Gross margin scoring (higher is better)
        gross_margin = profitability_data.get("gross_margin")
        if gross_margin is not None and gross_margin > 0:
            if gross_margin > 0.50:
                score += 15  # Excellent
            elif gross_margin > 0.40:
                score += 10  # Very good
            elif gross_margin > 0.30:
                score += 5  # Good
            elif gross_margin < 0.10:
                score -= 10  # Poor

        # Operating margin scoring (higher is better)
        operating_margin = profitability_data.get("operating_margin")
        if operating_margin is not None:
            if operating_margin > 0.25:
                score += 12  # Excellent
            elif operating_margin > 0.15:
                score += 8  # Very good
            elif operating_margin > 0.10:
                score += 4  # Good
            elif operating_margin < 0:
                score -= 10  # Unprofitable

        # Net profit margin scoring (higher is better)
        net_margin = profitability_data.get("profit_margin")
        if net_margin is not None:
            if net_margin > 0.20:
                score += 12  # Excellent
            elif net_margin > 0.10:
                score += 8  # Very good
            elif net_margin > 0.05:
                score += 4  # Good
            elif net_margin < 0:
                score -= 10  # Unprofitable

        # Return on Equity scoring (higher is better)
        roe = profitability_data.get("return_on_equity")
        if roe is not None and roe > 0:
            if roe > 0.20:
                score += 10  # Excellent
            elif roe > 0.15:
                score += 7  # Very good
            elif roe > 0.10:
                score += 4  # Good
            elif roe < 0.05:
                score -= 5  # Weak

        # Return on Assets scoring (higher is better)
        roa = profitability_data.get("return_on_assets")
        if roa is not None and roa > 0:
            if roa > 0.15:
                score += 8  # Excellent
            elif roa > 0.10:
                score += 5  # Very good
            elif roa > 0.05:
                score += 2  # Good

        return max(0, min(100, score))

    @staticmethod
    def _score_financial_health(financial_health_data: dict[str, Any]) -> float:
        """Score financial health and stability.

        Lower debt, higher liquidity, positive cash flow are better.
        Args:
            financial_health_data: Financial health metrics (debt ratios, liquidity, cash flow)

        Returns:
            Score 0-100 (higher = healthier)
        """
        if not financial_health_data:
            return 50  # Neutral if no data

        score = 50  # Start neutral

        # Debt-to-Equity scoring (lower is better)
        debt_to_equity = financial_health_data.get("debt_to_equity")
        if debt_to_equity is not None:
            if debt_to_equity < 0.5:
                score += 15  # Very low debt
            elif debt_to_equity < 1.0:
                score += 10  # Low debt
            elif debt_to_equity < 2.0:
                score += 5  # Moderate debt
            elif debt_to_equity > 3.0:
                score -= 15  # High debt

        # Current Ratio scoring (higher is better, 1.5-3.0 is ideal)
        current_ratio = financial_health_data.get("current_ratio")
        if current_ratio is not None:
            if 1.5 <= current_ratio <= 3.0:
                score += 10  # Healthy
            elif current_ratio > 1.0:
                score += 5  # Adequate
            elif current_ratio < 1.0:
                score -= 15  # Liquidity concern

        # Quick Ratio scoring (higher is better, >1.0 ideal)
        quick_ratio = financial_health_data.get("quick_ratio")
        if quick_ratio is not None:
            if quick_ratio > 1.0:
                score += 8  # Strong liquidity
            elif quick_ratio > 0.7:
                score += 3  # Adequate

        # Free Cash Flow (positive is better)
        free_cashflow = financial_health_data.get("free_cashflow")
        if free_cashflow is not None:
            if free_cashflow > 0:
                score += 12  # Positive cash generation
            else:
                score -= 10  # Negative cash flow is concerning

        # Operating Cash Flow (positive is better)
        operating_cashflow = financial_health_data.get("operating_cashflow")
        if operating_cashflow is not None:
            if operating_cashflow > 0:
                score += 8  # Positive from operations
            else:
                score -= 8

        return max(0, min(100, score))

    @staticmethod
    def _score_growth(growth_data: dict[str, Any]) -> float:
        """Score growth prospects and trends.

        Positive growth is better.
        Args:
            growth_data: Growth metrics (revenue growth, earnings growth)

        Returns:
            Score 0-100 (higher = faster growth)
        """
        if not growth_data:
            return 50  # Neutral if no data

        score = 50  # Start neutral

        # Revenue growth scoring (higher is better)
        revenue_growth = growth_data.get("revenue_growth")
        if revenue_growth is not None:
            if revenue_growth > 0.20:
                score += 15  # Strong growth
            elif revenue_growth > 0.10:
                score += 10  # Good growth
            elif revenue_growth > 0.05:
                score += 5  # Modest growth
            elif revenue_growth < 0:
                score -= 10  # Declining

        # Earnings growth scoring (higher is better)
        earnings_growth = growth_data.get("earnings_growth")
        if earnings_growth is not None:
            if earnings_growth > 0.20:
                score += 15  # Strong growth
            elif earnings_growth > 0.10:
                score += 10  # Good growth
            elif earnings_growth > 0.05:
                score += 5  # Modest growth
            elif earnings_growth < 0:
                score -= 10  # Declining

        return max(0, min(100, score))

    @staticmethod
    def get_recommendation(score: float) -> str:
        """Convert metrics score to recommendation.

        Args:
            score: Metrics score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 75:
            return "strong_buy"
        elif score >= 60:
            return "buy"
        elif score >= 40:
            return "hold"
        elif score >= 25:
            return "sell"
        else:
            return "strong_sell"
