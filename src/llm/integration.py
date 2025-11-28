"""High-level integration of CrewAI and hybrid intelligence system."""

import json
from datetime import datetime
from pathlib import Path
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
        debug_dir: Optional[Path] = None,
        progress_callback: Optional[callable] = None,
    ):
        """Initialize analysis orchestrator.

        Args:
            llm_config: LLM configuration
            token_tracker: Token usage tracker
            enable_fallback: Enable fallback to rule-based analysis
            debug_dir: Directory to save debug outputs (inputs/outputs from LLM)
            progress_callback: Optional callback function(message: str) for progress updates
        """
        self.llm_config = llm_config or LLMConfig()
        self.token_tracker = token_tracker
        self.enable_fallback = enable_fallback
        self.debug_dir = debug_dir
        self.progress_callback = progress_callback

        # Create debug directory if needed
        if self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"LLM debug mode enabled: outputs will be saved to {self.debug_dir}")

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
        # Get tools before creating agents
        tools = self.tool_adapter.get_crewai_tools()

        # Create CrewAI agents with tools
        market_scanner_crew = self.agent_factory.create_market_scanner_agent(tools)
        technical_crew = self.agent_factory.create_technical_analysis_agent(tools)
        fundamental_crew = self.agent_factory.create_fundamental_analysis_agent(tools)
        sentiment_crew = self.agent_factory.create_sentiment_analysis_agent(tools)
        synthesizer_crew = self.agent_factory.create_signal_synthesizer_agent()

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

    def _save_debug_data(self, ticker: str, stage: str, data: Any) -> None:
        """Save debug data to disk.

        Args:
            ticker: Stock ticker
            stage: Analysis stage (input/output/synthesis_input/synthesis_output)
            data: Data to save
        """
        if not self.debug_dir:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ticker}_{stage}_{timestamp}.json"
            filepath = self.debug_dir / filename

            # Convert data to JSON-serializable format
            def json_serial(obj):
                """JSON serializer for objects not serializable by default."""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if hasattr(obj, "__dict__"):
                    return obj.__dict__
                return str(obj)

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=json_serial)

            logger.debug(f"Saved debug data: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to save debug data for {ticker} ({stage}): {e}")

    def analyze_instrument(
        self,
        ticker: str,
        context: dict[str, Any] = None,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Perform comprehensive analysis of a single instrument.

        Args:
            ticker: Stock ticker symbol
            context: Additional context for analysis
            progress_callback: Optional callback for progress updates

        Returns:
            Analysis results from all agents including synthesis
        """
        context = context or {}
        context["ticker"] = ticker

        logger.info(f"Starting comprehensive analysis for {ticker}")

        # Save debug: input context
        if self.debug_dir:
            self._save_debug_data(ticker, "input_context", context)

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

        # Save debug: task descriptions
        if self.debug_dir:
            self._save_debug_data(
                ticker,
                "task_inputs",
                {
                    "market_scan": market_scan_task.description,
                    "technical": technical_task.description,
                    "fundamental": fundamental_task.description,
                    "sentiment": sentiment_task.description,
                },
            )

        # Execute analysis tasks
        tasks = {
            "market_scan": market_scan_task,
            "technical_analysis": technical_task,
            "fundamental_analysis": fundamental_task,
            "sentiment_analysis": sentiment_task,
        }

        analysis_results = self.crew.execute_analysis(tasks, context, progress_callback)

        # Save debug: analysis outputs
        if self.debug_dir:
            self._save_debug_data(ticker, "analysis_outputs", analysis_results)

        # Extract individual analysis results for synthesis
        technical_results = analysis_results.get("results", {}).get("technical_analysis", {})
        fundamental_results = analysis_results.get("results", {}).get("fundamental_analysis", {})
        sentiment_results = analysis_results.get("results", {}).get("sentiment_analysis", {})

        # Synthesize signal if all analyses succeeded
        if (
            technical_results.get("status") == "success"
            and fundamental_results.get("status") == "success"
            and sentiment_results.get("status") == "success"
        ):
            synthesis_result = self.synthesize_signal(
                ticker,
                technical_results.get("result", {}),
                fundamental_results.get("result", {}),
                sentiment_results.get("result", {}),
            )

            # Add synthesis to results
            analysis_results["results"]["synthesis"] = synthesis_result
        else:
            logger.warning(
                f"Skipping synthesis for {ticker} - not all analyses succeeded. "
                f"Technical: {technical_results.get('status')}, "
                f"Fundamental: {fundamental_results.get('status')}, "
                f"Sentiment: {sentiment_results.get('status')}"
            )
            analysis_results["results"]["synthesis"] = {
                "status": "skipped",
                "reason": "prerequisite analyses failed",
            }

        logger.info(f"Analysis complete for {ticker}")

        return analysis_results

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

        # Notify progress
        if self.progress_callback:
            self.progress_callback(f"  🔄 Synthesizing investment signal...")

        # Save debug: synthesis inputs
        if self.debug_dir:
            self._save_debug_data(
                ticker,
                "synthesis_input",
                {
                    "technical": technical_results,
                    "fundamental": fundamental_results,
                    "sentiment": sentiment_results,
                },
            )

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

        # Save debug: synthesis task description
        if self.debug_dir:
            self._save_debug_data(
                ticker,
                "synthesis_task",
                {
                    "description": synthesis_task.description,
                    "expected_output": synthesis_task.expected_output,
                },
            )

        # Notify start
        if self.progress_callback:
            self.progress_callback(f"  → Synthesizing investment signal...")

        result = synthesizer_hybrid.execute_task(synthesis_task)

        # Save debug: synthesis output
        if self.debug_dir:
            self._save_debug_data(ticker, "synthesis_output", result)

        # Notify completion
        if self.progress_callback:
            self.progress_callback(f"  ✓ Signal synthesis complete")

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
