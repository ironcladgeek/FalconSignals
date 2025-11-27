"""High-level integration of CrewAI and hybrid intelligence system."""

from typing import Any, Optional

from src.agents.analysis import (
    FundamentalAnalysisAgent,
    TechnicalAnalysisAgent,
)
from src.agents.crewai_agents import CrewAIAgentFactory, CrewAITaskFactory
from src.agents.hybrid import HybridAnalysisAgent, HybridAnalysisCrew
from src.agents.scanner import MarketScannerAgent
from src.agents.sentiment import SentimentAgent
from src.config.schemas import LLMConfig
from src.llm.token_tracker import TokenTracker
from src.llm.tools import CrewAIToolAdapter
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LLMAnalysisOrchestrator:
    """Orchestrates LLM-powered analysis using hybrid intelligence."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        token_tracker: Optional[TokenTracker] = None,
        enable_fallback: bool = True,
    ):
        """Initialize analysis orchestrator.

        Args:
            llm_config: LLM configuration
            token_tracker: Token usage tracker
            enable_fallback: Enable fallback to rule-based analysis
        """
        self.llm_config = llm_config or LLMConfig()
        self.token_tracker = token_tracker
        self.enable_fallback = enable_fallback

        # Initialize CrewAI components
        self.agent_factory = CrewAIAgentFactory(self.llm_config)
        self.task_factory = CrewAITaskFactory()
        self.tool_adapter = CrewAIToolAdapter()

        # Initialize hybrid agents with fallback
        self.hybrid_agents = self._create_hybrid_agents()
        self.crew = HybridAnalysisCrew(self.hybrid_agents, self.token_tracker)

        logger.info("Initialized LLM Analysis Orchestrator")

    def _create_hybrid_agents(self) -> dict[str, HybridAnalysisAgent]:
        """Create hybrid agents combining CrewAI with fallback.

        Returns:
            Dictionary mapping agent names to HybridAnalysisAgent instances
        """
        # Create CrewAI agents
        market_scanner_crew = self.agent_factory.create_market_scanner_agent()
        technical_crew = self.agent_factory.create_technical_analysis_agent()
        fundamental_crew = self.agent_factory.create_fundamental_analysis_agent()
        sentiment_crew = self.agent_factory.create_sentiment_analysis_agent()
        synthesizer_crew = self.agent_factory.create_signal_synthesizer_agent()

        # Attach tools to CrewAI agents
        tools = self.tool_adapter.get_crewai_tools()
        for agent in [market_scanner_crew, technical_crew, fundamental_crew, sentiment_crew]:
            agent.tools = tools

        # Create fallback rule-based agents
        market_scanner_fallback = MarketScannerAgent()
        technical_fallback = TechnicalAnalysisAgent()
        fundamental_fallback = FundamentalAnalysisAgent()
        sentiment_fallback = SentimentAgent()

        # Wrap in hybrid agents
        return {
            "market_scanner": HybridAnalysisAgent(
                crewai_agent=market_scanner_crew,
                fallback_agent=market_scanner_fallback,
                token_tracker=self.token_tracker,
                enable_fallback=self.enable_fallback,
            ),
            "technical": HybridAnalysisAgent(
                crewai_agent=technical_crew,
                fallback_agent=technical_fallback,
                token_tracker=self.token_tracker,
                enable_fallback=self.enable_fallback,
            ),
            "fundamental": HybridAnalysisAgent(
                crewai_agent=fundamental_crew,
                fallback_agent=fundamental_fallback,
                token_tracker=self.token_tracker,
                enable_fallback=self.enable_fallback,
            ),
            "sentiment": HybridAnalysisAgent(
                crewai_agent=sentiment_crew,
                fallback_agent=sentiment_fallback,
                token_tracker=self.token_tracker,
                enable_fallback=self.enable_fallback,
            ),
        }

    def analyze_instrument(
        self,
        ticker: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Perform comprehensive analysis of a single instrument.

        Args:
            ticker: Stock ticker symbol
            context: Additional context for analysis

        Returns:
            Analysis results from all agents
        """
        context = context or {}
        context["ticker"] = ticker

        logger.info(f"Starting comprehensive analysis for {ticker}")

        # Create tasks for each agent
        market_scan_task = self.task_factory.create_market_scan_task(
            self.hybrid_agents["market_scanner"].crewai_agent, ticker, context
        )

        technical_task = self.task_factory.create_technical_analysis_task(
            self.hybrid_agents["technical"].crewai_agent, ticker, context
        )

        fundamental_task = self.task_factory.create_fundamental_analysis_task(
            self.hybrid_agents["fundamental"].crewai_agent, ticker, context
        )

        sentiment_task = self.task_factory.create_sentiment_analysis_task(
            self.hybrid_agents["sentiment"].crewai_agent, ticker, context
        )

        # Execute analysis tasks
        tasks = {
            "market_scan": market_scan_task,
            "technical_analysis": technical_task,
            "fundamental_analysis": fundamental_task,
            "sentiment_analysis": sentiment_task,
        }

        results = self.crew.execute_analysis(tasks, context)

        logger.info(f"Analysis complete for {ticker}")

        return results

    def synthesize_signal(
        self,
        ticker: str,
        technical_results: dict[str, Any],
        fundamental_results: dict[str, Any],
        sentiment_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Synthesize individual analyses into investment signal.

        Args:
            ticker: Stock ticker symbol
            technical_results: Technical analysis results
            fundamental_results: Fundamental analysis results
            sentiment_results: Sentiment analysis results

        Returns:
            Investment signal with recommendation
        """
        logger.info(f"Synthesizing investment signal for {ticker}")

        # Create synthesis task
        synthesizer_agent = self.hybrid_agents.get("synthesizer")
        if not synthesizer_agent:
            # Create if not present
            crew_agent = self.agent_factory.create_signal_synthesizer_agent()
            crew_agent.tools = self.tool_adapter.get_crewai_tools()
            synthesizer_hybrid = HybridAnalysisAgent(
                crewai_agent=crew_agent,
                fallback_agent=None,
                token_tracker=self.token_tracker,
                enable_fallback=False,
            )
            self.hybrid_agents["synthesizer"] = synthesizer_hybrid
        else:
            synthesizer_hybrid = synthesizer_agent

        synthesis_task = self.task_factory.create_signal_synthesis_task(
            synthesizer_hybrid.crewai_agent,
            ticker,
            technical_results,
            fundamental_results,
            sentiment_results,
        )

        result = synthesizer_hybrid.execute_task(synthesis_task)

        logger.info(f"Signal synthesis complete for {ticker}")

        return result

    def get_orchestrator_status(self) -> dict[str, Any]:
        """Get status of orchestrator and all agents.

        Returns:
            Status dictionary
        """
        return {
            "llm_provider": self.llm_config.provider,
            "llm_model": self.llm_config.model,
            "token_tracking": self.token_tracker is not None,
            "fallback_enabled": self.enable_fallback,
            "agents": self.crew.get_crew_status(),
            "execution_log_size": len(self.crew.execution_log),
        }

    def log_summary(self) -> None:
        """Log execution summary."""
        self.crew.log_summary()
