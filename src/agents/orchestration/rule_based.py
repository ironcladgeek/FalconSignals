"""CrewAI Crew orchestration for agent coordination."""

from typing import Any, Optional

from src.agents.analysis import FundamentalAnalysisAgent, TechnicalAnalysisAgent
from src.agents.sentiment import SentimentAgent, SignalSynthesisAgent
from src.utils.llm_check import check_llm_configuration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisCrew:
    """Orchestrates multiple agents for comprehensive analysis."""

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        test_mode_config: Optional[Any] = None,
        db_path: Optional[str] = None,
        config=None,
    ):
        """Initialize the analysis crew.

        Args:
            llm_provider: Optional LLM provider to check configuration for
            test_mode_config: Optional test mode configuration for fixtures/mock LLM
            db_path: Optional path to database for storing analyst ratings
            config: Configuration object with analysis settings
        """
        self.test_mode_config = test_mode_config

        # Initialize analysis agents (no market scanner - filtering handled externally)
        self.technical_agent = TechnicalAnalysisAgent()
        self.fundamental_agent = FundamentalAnalysisAgent(db_path=db_path)
        self.sentiment_agent = SentimentAgent()
        self.signal_synthesizer = SignalSynthesisAgent()

        # Check LLM configuration and warn if using fallback
        llm_configured, provider = check_llm_configuration(llm_provider)
        if llm_configured:
            logger.debug(f"Analysis crew initialized with 4 agents using {provider} LLM")
        else:
            logger.warning(
                "Analysis crew initialized with 4 agents in RULE-BASED MODE. "
                "No LLM configured - using technical indicators and simple rules. "
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-powered analysis."
            )

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

            logger.debug(f"Starting comprehensive analysis for {ticker}")

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

            logger.debug(
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

    def analyze_instruments(
        self,
        tickers: list[str],
        additional_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Analyze multiple instruments without prior market scanning.

        This method should be used when tickers have been pre-filtered
        by the FilterOrchestrator in main.py, following DRY principles.

        Args:
            tickers: List of pre-filtered tickers to analyze
            additional_context: Additional context

        Returns:
            Analysis results for all tickers
        """
        try:
            context = additional_context or {}
            logger.debug(f"Starting analysis for {len(tickers)} pre-filtered instruments")

            analysis_results = []
            for ticker in tickers:
                result = self.analyze_instrument(ticker, context)
                if result.get("status") == "success":
                    analysis_results.append(result)

            # Sort by confidence
            analysis_results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

            return {
                "status": "success",
                "analysis_results": analysis_results,
                "total_analyzed": len(analysis_results),
                "strong_signals": [r for r in analysis_results if r.get("confidence", 0) >= 70],
            }

        except Exception as e:
            logger.error(f"Error in analyze_instruments: {e}")
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
            "total_agents": 4,
            "agents": {
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
