"""CrewAI Crew orchestration for agent coordination."""

from typing import Any, Optional

from src.agents.analysis import FundamentalAnalysisAgent, TechnicalAnalysisAgent
from src.agents.scanner import MarketScannerAgent
from src.agents.sentiment import SentimentAgent, SignalSynthesisAgent
from src.tools import (
    NewsFetcherTool,
    PriceFetcherTool,
    ReportGeneratorTool,
    SentimentAnalyzerTool,
    TechnicalIndicatorTool,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisCrew:
    """Orchestrates multiple agents for comprehensive analysis."""

    def __init__(self):
        """Initialize the analysis crew."""
        self.market_scanner = MarketScannerAgent()
        self.technical_agent = TechnicalAnalysisAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.sentiment_agent = SentimentAgent()
        self.signal_synthesizer = SignalSynthesisAgent()

        logger.info("Analysis crew initialized with 5 agents")

    def analyze_instrument(
        self,
        ticker: str,
        additional_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Analyze a single instrument comprehensively.

        Executes agents in a coordinated manner:
        1. Technical Analysis (parallel)
        2. Fundamental Analysis (parallel)
        3. Sentiment Analysis (parallel)
        4. Signal Synthesis (sequential, depends on above)

        Args:
            ticker: Stock ticker symbol
            additional_context: Additional context for analysis

        Returns:
            Comprehensive analysis result
        """
        try:
            context = additional_context or {}
            context["ticker"] = ticker

            logger.info(f"Starting comprehensive analysis for {ticker}")

            # Execute parallel analyses
            technical_result = self.technical_agent.execute("Analyze technical indicators", context)
            context["technical_score"] = technical_result.get("technical_score", 50)

            fundamental_result = self.fundamental_agent.execute("Analyze fundamentals", context)
            context["fundamental_score"] = fundamental_result.get("fundamental_score", 50)

            sentiment_result = self.sentiment_agent.execute("Analyze sentiment", context)
            context["sentiment_score"] = sentiment_result.get("sentiment_score", 50)

            # Execute signal synthesis
            synthesis_result = self.signal_synthesizer.execute("Synthesize all signals", context)

            # Aggregate results
            result = {
                "status": "success",
                "ticker": ticker,
                "analysis": {
                    "technical": technical_result,
                    "fundamental": fundamental_result,
                    "sentiment": sentiment_result,
                    "synthesis": synthesis_result,
                },
                "final_recommendation": synthesis_result.get("recommendation", "hold"),
                "confidence": synthesis_result.get("confidence", 0),
                "final_score": synthesis_result.get("final_score", 50),
            }

            logger.info(
                f"Analysis complete for {ticker}: "
                f"{result['final_recommendation']} "
                f"(confidence: {result['confidence']:.0f}%)"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return {
                "status": "error",
                "ticker": ticker,
                "message": str(e),
                "analysis": {},
            }

    def scan_and_analyze(
        self,
        tickers: list[str],
        additional_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Scan markets and analyze flagged instruments.

        Workflow:
        1. Market Scanner identifies anomalies
        2. Comprehensive analysis on flagged instruments
        3. Results ranked by signal strength

        Args:
            tickers: List of tickers to scan
            additional_context: Additional context

        Returns:
            Scan and analysis results
        """
        try:
            context = additional_context or {}
            context["tickers"] = tickers

            logger.info(f"Starting market scan for {len(tickers)} instruments")

            # Execute market scan
            scan_result = self.market_scanner.execute("Scan market for anomalies", context)

            if scan_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": scan_result.get("message"),
                    "analysis_results": [],
                }

            # Analyze flagged instruments
            flagged = scan_result.get("instruments", [])
            logger.info(f"Found {len(flagged)} instruments with anomalies")

            analysis_results = []
            for instrument in flagged:
                ticker = instrument.get("ticker")
                result = self.analyze_instrument(ticker, context)
                if result.get("status") == "success":
                    analysis_results.append(result)

            # Sort by confidence
            analysis_results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

            return {
                "status": "success",
                "scan_results": scan_result,
                "analysis_results": analysis_results,
                "total_analyzed": len(analysis_results),
                "strong_signals": [r for r in analysis_results if r.get("confidence", 0) >= 70],
            }

        except Exception as e:
            logger.error(f"Error in scan and analyze: {e}")
            return {
                "status": "error",
                "message": str(e),
                "analysis_results": [],
            }

    def get_agent_status(self) -> dict[str, Any]:
        """Get status of all agents in crew.

        Returns:
            Dictionary with agent status
        """
        return {
            "crew_name": "AnalysisCrew",
            "total_agents": 5,
            "agents": {
                "market_scanner": {
                    "role": self.market_scanner.role,
                    "goal": self.market_scanner.goal,
                },
                "technical_analyst": {
                    "role": self.technical_agent.role,
                    "goal": self.technical_agent.goal,
                },
                "fundamental_analyst": {
                    "role": self.fundamental_agent.role,
                    "goal": self.fundamental_agent.goal,
                },
                "sentiment_analyst": {
                    "role": self.sentiment_agent.role,
                    "goal": self.sentiment_agent.goal,
                },
                "signal_synthesizer": {
                    "role": self.signal_synthesizer.role,
                    "goal": self.signal_synthesizer.goal,
                },
            },
        }
