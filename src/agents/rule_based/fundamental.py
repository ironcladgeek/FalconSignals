"""Fundamental analysis module for rule-based analysis."""

from typing import Any

from src.agents.base import AgentConfig, BaseAgent
from src.analysis.fundamental import FundamentalAnalyzer
from src.tools.fetchers import FinancialDataFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FundamentalAnalysisModule(BaseAgent):
    """Module for fundamental analysis of companies (rule-based)."""

    def __init__(self, tools: list | None = None, db_path: str | None = None):
        """Initialize Fundamental Analysis module.

        Args:
            tools: Optional list of tools
            db_path: Optional path to database for storing analyst ratings
        """
        config = AgentConfig(
            role="Fundamental Analyst",
            goal="Evaluate financial health, growth prospects, and valuation metrics to assess investment quality",
            backstory=(
                "You are an experienced fundamental analyst with deep knowledge of financial statements, "
                "valuation metrics, and business fundamentals. "
                "You analyze earnings growth, profitability, debt levels, and valuations to identify "
                "companies with strong business models and reasonable prices."
            ),
        )
        default_tools = [FinancialDataFetcherTool(db_path=db_path)]
        super().__init__(config, tools or default_tools)

    def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute fundamental analysis.

        Args:
            task: Task description
            context: Context with company data

        Returns:
            Fundamental analysis results with scores
        """
        try:
            context = context or {}
            ticker = context.get("ticker")

            if not ticker:
                return {
                    "status": "error",
                    "message": "No ticker provided",
                    "fundamental_score": 0,
                }

            logger.debug(f"Analyzing fundamentals for {ticker}")

            # Get financial data fetcher tool
            fetcher = next(
                (t for t in self.tools if hasattr(t, "name") and t.name == "FinancialDataFetcher"),
                None,
            )

            if not fetcher:
                return {
                    "status": "error",
                    "message": "Financial data fetcher unavailable",
                    "fundamental_score": 0,
                }

            # Set historical date if provided in context
            if "analysis_date" in context and hasattr(fetcher, "set_historical_date"):
                fetcher.set_historical_date(context["analysis_date"])
                logger.debug(
                    f"Set historical date {context['analysis_date']} for fundamental analysis"
                )

            # Fetch fundamental data (free tier only)
            fundamental_data = fetcher.run(ticker)

            if "error" in fundamental_data:
                return {
                    "status": "error",
                    "message": fundamental_data["error"],
                    "fundamental_score": 0,
                }

            # Extract data sources from free tier endpoints
            analyst_data = fundamental_data.get("analyst_data", {})
            price_context = fundamental_data.get("price_context", {})
            metrics_data = fundamental_data.get("metrics", {})

            # Calculate enhanced fundamental score with metrics
            # Note: Sentiment is analyzed separately by News & Sentiment Agent
            scoring_result = FundamentalAnalyzer.calculate_enhanced_score(
                analyst_data=analyst_data,
                price_context=price_context,
                sentiment_score=50.0,  # Neutral default (analyzed separately by News & Sentiment Agent)
                metrics_data=metrics_data,  # yfinance metrics
            )

            result = {
                "status": "success",
                "ticker": ticker,
                "fundamental_score": scoring_result["overall_score"],
                "baseline_score": scoring_result["baseline_score"],
                "metrics_score": scoring_result["metrics_score"],
                "scoring_details": scoring_result,
                "components": {
                    "baseline": {
                        "analyst_consensus": scoring_result["analyst_score"],
                        "momentum": scoring_result["momentum_score"],
                        "sentiment": {
                            "score": scoring_result["sentiment_score"],
                            "note": "Analyzed by News & Sentiment Agent (CrewAI/LLM)",
                        },
                    },
                    "metrics": {
                        "valuation": scoring_result["valuation_score"],
                        "profitability": scoring_result["profitability_score"],
                        "financial_health": scoring_result["financial_health_score"],
                        "growth": scoring_result["growth_score"],
                        "note": "From yfinance free tier data",
                    },
                },
                "data_sources": {
                    "analyst": analyst_data,
                    "price_context": price_context,
                    "metrics": metrics_data,
                },
                "recommendation": FundamentalAnalyzer.get_recommendation(
                    scoring_result["overall_score"]
                ),
                "note": "Uses free tier APIs only - analyst & momentum (60%) + yfinance metrics (40%)",
            }

            logger.debug(
                f"Fundamental analysis for {ticker}: {scoring_result['overall_score']:.1f}/100"
            )
            self.remember(f"{ticker}_fundamental_score", scoring_result["overall_score"])

            return result

        except Exception as e:
            logger.error(f"Error during fundamental analysis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fundamental_score": 0,
            }
