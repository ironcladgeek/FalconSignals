"""Unified analysis orchestrator supporting both LLM and rule-based modes."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.agents.llm import (
    CrewAIAgentFactory,
    CrewAITaskFactory,
    HybridAnalysisAgent,
    HybridAnalysisCrew,
)
from src.agents.rule_based import (
    FundamentalAnalysisModule,
    SentimentAnalysisModule,
    SignalSynthesisModule,
    TechnicalAnalysisModule,
)
from src.analysis.models import UnifiedAnalysisResult
from src.analysis.normalizer import AnalysisResultNormalizer
from src.config.schemas import LLMConfig
from src.llm.token_tracker import TokenTracker
from src.llm.tools import CrewAIToolAdapter
from src.utils.llm_check import check_llm_configuration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class UnifiedAnalysisOrchestrator:
    """Unified orchestrator that supports both LLM and rule-based analysis modes.

    This is the single source of truth for all analysis orchestration,
    providing a unified interface for both LLM-powered and rule-based analysis.
    """

    def __init__(
        self,
        llm_mode: bool = False,
        llm_config: Optional[LLMConfig] = None,
        llm_provider: Optional[str] = None,
        token_tracker: Optional[TokenTracker] = None,
        enable_fallback: bool = True,
        debug_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        test_mode_config: Optional[Any] = None,
        db_path: Optional[str] = None,
        config=None,
    ):
        """Initialize unified orchestrator.

        Args:
            llm_mode: If True, use LLM-powered agents; if False, use rule-based modules
            llm_config: LLM configuration (only used if llm_mode=True)
            llm_provider: Optional LLM provider to check configuration for
            token_tracker: Token usage tracker (only used if llm_mode=True)
            enable_fallback: Enable fallback to rule-based analysis in LLM mode
            debug_dir: Directory to save debug outputs (LLM mode only)
            progress_callback: Optional callback function(message: str) for progress updates
            test_mode_config: Optional test mode configuration for fixtures/mock LLM
            db_path: Optional path to database for storing analyst ratings
            config: Full configuration object for accessing analysis settings
        """
        self.llm_mode = llm_mode
        self.llm_config = llm_config or LLMConfig()
        self.token_tracker = token_tracker
        self.enable_fallback = enable_fallback
        self.debug_dir = debug_dir
        self.progress_callback = progress_callback
        self.test_mode_config = test_mode_config
        self.db_path = db_path
        self.config = config

        # Create debug directory if needed (LLM mode only)
        if self.llm_mode and self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"LLM debug mode enabled: outputs will be saved to {self.debug_dir}")

        # Initialize agents/modules based on mode
        if self.llm_mode:
            self._initialize_llm_mode()
        else:
            self._initialize_rule_based_mode()

        # Check and log LLM configuration status
        llm_configured, provider = check_llm_configuration(llm_provider)
        if self.llm_mode:
            if llm_configured:
                logger.debug(f"Unified orchestrator initialized in LLM mode with {provider}")
            else:
                logger.warning(
                    "LLM mode requested but no LLM configured. "
                    "Set ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-powered analysis. "
                    "Falling back to rule-based mode."
                )
        else:
            # Rule-based mode is intentional, not a warning condition
            logger.debug(
                "Unified orchestrator initialized in rule-based mode "
                "(using technical indicators and quantitative analysis)"
            )

    def _initialize_llm_mode(self) -> None:
        """Initialize CrewAI components for LLM mode."""
        # Initialize CrewAI components
        self.agent_factory = CrewAIAgentFactory(self.llm_config)
        self.task_factory = CrewAITaskFactory()
        # Type ignore: CrewAIToolAdapter has incorrect type annotation for db_path
        self.tool_adapter = CrewAIToolAdapter(db_path=self.db_path, config=self.config)  # type: ignore[arg-type]

        # Initialize hybrid agents with fallback
        self.hybrid_agents = self._create_hybrid_agents()
        self.crew = HybridAnalysisCrew(self.hybrid_agents, self.token_tracker)

        logger.debug("Initialized LLM mode components")

    def _initialize_rule_based_mode(self) -> None:
        """Initialize rule-based analysis modules."""
        # Initialize analysis modules (no market scanner - filtering handled externally)
        self.technical_agent = TechnicalAnalysisModule()
        self.fundamental_agent = FundamentalAnalysisModule(db_path=self.db_path)
        self.sentiment_agent = SentimentAnalysisModule()
        self.signal_synthesizer = SignalSynthesisModule()

        logger.debug("Initialized rule-based mode modules")

    def _create_hybrid_agents(self) -> dict[str, HybridAnalysisAgent]:
        """Create hybrid agents combining CrewAI with fallback.

        Returns:
            Dictionary mapping agent names to HybridAnalysisAgent instances
        """
        # Get tools before creating agents
        tools = self.tool_adapter.get_crewai_tools()

        # Create CrewAI agents with tools
        technical_crew = self.agent_factory.create_technical_analysis_agent(tools)
        fundamental_crew = self.agent_factory.create_fundamental_analysis_agent(tools)
        sentiment_crew = self.agent_factory.create_sentiment_analysis_agent(tools)
        synthesizer_crew = self.agent_factory.create_signal_synthesizer_agent()

        # Create fallback rule-based modules
        technical_fallback = TechnicalAnalysisModule()
        fundamental_fallback = FundamentalAnalysisModule(db_path=self.db_path)
        sentiment_fallback = SentimentAnalysisModule()

        # Wrap in hybrid agents
        return {
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
            "synthesizer": HybridAnalysisAgent(
                crewai_agent=synthesizer_crew,
                fallback_agent=None,
                token_tracker=self.token_tracker,
                enable_fallback=False,
            ),
        }

    def _save_debug_data(self, ticker: str, stage: str, data: Any) -> None:
        """Save debug data to disk (LLM mode only).

        Args:
            ticker: Stock ticker
            stage: Analysis stage (input/output/synthesis_input/synthesis_output)
            data: Data to save
        """
        if not self.llm_mode or not self.debug_dir:
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
        additional_context: Optional[dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> UnifiedAnalysisResult | dict[str, Any] | None:
        """Analyze a single instrument comprehensively.

        Args:
            ticker: Stock ticker symbol
            additional_context: Additional context for analysis
            progress_callback: Optional callback for progress updates

        Returns:
            UnifiedAnalysisResult (LLM mode) or dict (rule-based mode) or None if failed
        """
        if self.llm_mode:
            return self._analyze_instrument_llm(ticker, additional_context, progress_callback)
        else:
            return self._analyze_instrument_rule_based(ticker, additional_context)

    def _analyze_instrument_rule_based(
        self,
        ticker: str,
        additional_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Analyze instrument using rule-based modules.

        Args:
            ticker: Stock ticker symbol
            additional_context: Additional context for analysis

        Returns:
            Analysis result dictionary
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

    def _analyze_instrument_llm(
        self,
        ticker: str,
        context: Optional[dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> UnifiedAnalysisResult | None:
        """Perform comprehensive analysis using LLM-powered agents.

        Args:
            ticker: Stock ticker symbol
            context: Additional context for analysis
            progress_callback: Optional callback for progress updates

        Returns:
            UnifiedAnalysisResult with normalized data or None if analysis failed
        """
        context = context or {}
        context["ticker"] = ticker

        # Inject config values into context for agents to access
        if self.config:
            if hasattr(self.config.analysis, "historical_data_lookback_days"):
                context["historical_data_lookback_days"] = (
                    self.config.analysis.historical_data_lookback_days
                )
                logger.debug(
                    f"Set historical_data_lookback_days in context: {context['historical_data_lookback_days']}"
                )

        logger.debug(f"Starting comprehensive analysis for {ticker}")

        # Save debug: input context
        self._save_debug_data(ticker, "input_context", context)

        # Create tasks for each agent (no market scan - filtering handled externally)
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
                    "technical": technical_task.description,
                    "fundamental": fundamental_task.description,
                    "sentiment": sentiment_task.description,
                },
            )

        # Execute analysis tasks
        tasks = {
            "technical_analysis": technical_task,
            "fundamental_analysis": fundamental_task,
            "sentiment_analysis": sentiment_task,
        }

        analysis_results = self.crew.execute_analysis(tasks, context, progress_callback)

        # Save debug: analysis outputs
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
            synthesis_result = self._synthesize_signal(
                ticker,
                technical_results.get("result", {}),
                fundamental_results.get("result", {}),
                sentiment_results.get("result", {}),
            )

            # Add synthesis to results
            analysis_results["results"]["synthesis"] = synthesis_result

            # Normalize to unified structure for consistent output
            try:
                unified_result = AnalysisResultNormalizer.normalize_llm_result(
                    ticker=ticker,
                    technical_result=technical_results.get("result", {}),
                    fundamental_result=fundamental_results.get("result", {}),
                    sentiment_result=sentiment_results.get("result", {}),
                    synthesis_result=synthesis_result,
                )
                logger.debug(f"Analysis complete for {ticker}, normalized to unified structure")
                return unified_result
            except Exception as e:
                logger.error(f"Failed to normalize LLM results for {ticker}: {e}", exc_info=True)
                return None
        else:
            logger.warning(
                f"Skipping synthesis for {ticker} - not all analyses succeeded. "
                f"Technical: {technical_results.get('status')}, "
                f"Fundamental: {fundamental_results.get('status')}, "
                f"Sentiment: {sentiment_results.get('status')}"
            )
            return None

    def _synthesize_signal(
        self,
        ticker: str,
        technical_results: dict[str, Any],
        fundamental_results: dict[str, Any],
        sentiment_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Synthesize individual analyses into investment signal (LLM mode).

        Args:
            ticker: Stock ticker symbol
            technical_results: Technical analysis results
            fundamental_results: Fundamental analysis results
            sentiment_results: Sentiment analysis results

        Returns:
            Investment signal with recommendation
        """
        logger.debug(f"Synthesizing investment signal for {ticker}")

        # Notify progress
        if self.progress_callback:
            self.progress_callback("  🔄 Synthesizing investment signal...")

        # Save debug: synthesis inputs
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
            # CRITICAL: Ensure synthesizer has absolutely NO tools
            # It must work only with provided data to avoid tool hallucination
            crew_agent.tools = []
            synthesizer_hybrid = HybridAnalysisAgent(
                crewai_agent=crew_agent,
                fallback_agent=None,
                token_tracker=self.token_tracker,
                enable_fallback=False,
            )
            self.hybrid_agents["synthesizer"] = synthesizer_hybrid
        else:
            synthesizer_hybrid = synthesizer_agent
            # IMPORTANT: Ensure cached synthesizer also has no tools
            synthesizer_hybrid.crewai_agent.tools = []

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
            self.progress_callback("  → Synthesizing investment signal...")

        result = synthesizer_hybrid.execute_task(synthesis_task)

        # Save debug: synthesis output
        self._save_debug_data(ticker, "synthesis_output", result)

        # Notify completion
        if self.progress_callback:
            self.progress_callback("  ✓ Signal synthesis complete")

        logger.debug(f"Signal synthesis complete for {ticker}")

        return result

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

                # Handle both LLM mode (UnifiedAnalysisResult or None) and rule-based (dict)
                if result is not None:
                    if isinstance(result, dict) and result.get("status") == "success":
                        analysis_results.append(result)
                    elif isinstance(result, UnifiedAnalysisResult):
                        # Convert to dict format for consistency
                        analysis_results.append(
                            {
                                "status": "success",
                                "ticker": result.ticker,
                                "final_recommendation": result.recommendation,
                                "confidence": result.confidence,
                                "final_score": result.final_score,
                            }
                        )

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
        """Get status of all agents/modules.

        Returns:
            Dictionary with agent status
        """
        if self.llm_mode:
            return self.get_orchestrator_status()
        else:
            return {
                "crew_name": "UnifiedOrchestrator (rule-based)",
                "mode": "rule-based",
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

    def get_orchestrator_status(self) -> dict[str, Any]:
        """Get status of orchestrator and all agents (LLM mode).

        Returns:
            Status dictionary
        """
        if not self.llm_mode:
            return self.get_agent_status()

        return {
            "crew_name": "UnifiedOrchestrator (LLM)",
            "mode": "llm",
            "llm_provider": self.llm_config.provider,
            "llm_model": self.llm_config.model,
            "token_tracking": self.token_tracker is not None,
            "fallback_enabled": self.enable_fallback,
            "agents": self.crew.get_crew_status(),
            "execution_log_size": len(self.crew.execution_log),
        }

    def log_summary(self) -> None:
        """Log execution summary."""
        if self.llm_mode and hasattr(self, "crew"):
            self.crew.log_summary()
        else:
            logger.debug("Rule-based mode - no execution log available")
