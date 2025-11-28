"""Hybrid intelligence system combining LLM and rule-based analysis."""

from typing import Any, Optional

from crewai import Agent, Crew, Task

from src.agents.base import BaseAgent
from src.llm.token_tracker import TokenTracker
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HybridAnalysisAgent:
    """Wraps CrewAI agents with fallback to rule-based analysis."""

    def __init__(
        self,
        crewai_agent: Agent,
        fallback_agent: Optional[BaseAgent] = None,
        token_tracker: Optional[TokenTracker] = None,
        enable_fallback: bool = True,
    ):
        """Initialize hybrid agent.

        Args:
            crewai_agent: CrewAI Agent for LLM-powered analysis
            fallback_agent: Rule-based agent for fallback
            token_tracker: Token usage tracker
            enable_fallback: Whether to use fallback on LLM failure
        """
        self.crewai_agent = crewai_agent
        self.fallback_agent = fallback_agent
        self.token_tracker = token_tracker
        self.enable_fallback = enable_fallback
        self.last_error: Optional[str] = None
        self.used_fallback: bool = False

    def execute_task(
        self,
        task: Task,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Execute task using LLM with fallback to rule-based.

        Args:
            task: CrewAI Task to execute
            context: Additional context

        Returns:
            Task execution result
        """
        context = context or {}

        # Try LLM-based analysis
        try:
            logger.debug(f"Executing LLM task: {task.description[:50]}...")

            # Get the LLM from the agent
            agent_llm = self.crewai_agent.llm if hasattr(self.crewai_agent, "llm") else None

            # Execute using minimal crew with explicit model configuration
            crew = Crew(
                agents=[self.crewai_agent],
                tasks=[task],
                verbose=False,
                manager_llm=agent_llm,  # Ensure crew uses the same LLM
            )
            result = crew.kickoff(inputs=context)

            # Track token usage (approximate)
            if self.token_tracker:
                # LLM execution - estimate tokens used
                est_input_tokens = len(str(task.description).split()) * 1.3
                est_output_tokens = len(str(result).split()) * 1.3
                self.token_tracker.track(
                    input_tokens=int(est_input_tokens),
                    output_tokens=int(est_output_tokens),
                    model=(
                        self.crewai_agent.llm.model
                        if hasattr(self.crewai_agent.llm, "model")
                        else "unknown"
                    ),
                    success=True,
                )

            self.used_fallback = False
            self.last_error = None
            logger.debug("LLM task completed successfully")

            return {
                "status": "success",
                "result": result,
                "used_llm": True,
                "used_fallback": False,
            }

        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"LLM task failed: {e}")

            # Try fallback if enabled
            if self.enable_fallback and self.fallback_agent:
                logger.info("Falling back to rule-based analysis")
                try:
                    result = self.fallback_agent.execute(task.description, context)
                    self.used_fallback = True

                    if self.token_tracker:
                        self.token_tracker.track(
                            input_tokens=0,
                            output_tokens=0,
                            model="rule-based-fallback",
                            success=True,
                        )

                    return {
                        "status": "success",
                        "result": result,
                        "used_llm": False,
                        "used_fallback": True,
                    }
                except Exception as fallback_e:
                    logger.error(f"Fallback analysis also failed: {fallback_e}")
                    if self.token_tracker:
                        self.token_tracker.track(
                            input_tokens=0,
                            output_tokens=0,
                            model="rule-based-fallback",
                            success=False,
                        )
                    return {
                        "status": "error",
                        "error": str(fallback_e),
                        "original_error": self.last_error,
                        "used_llm": False,
                        "used_fallback": False,
                    }
            else:
                return {
                    "status": "error",
                    "error": self.last_error,
                    "used_llm": False,
                    "used_fallback": False,
                }

    def get_status(self) -> dict[str, Any]:
        """Get agent status information.

        Returns:
            Status dictionary
        """
        return {
            "agent_role": self.crewai_agent.role,
            "last_error": self.last_error,
            "used_fallback": self.used_fallback,
            "fallback_available": self.fallback_agent is not None,
            "token_tracking_enabled": self.token_tracker is not None,
        }


class HybridAnalysisCrew:
    """Orchestrates multiple hybrid agents as a crew."""

    def __init__(
        self,
        hybrid_agents: dict[str, HybridAnalysisAgent],
        token_tracker: Optional[TokenTracker] = None,
    ):
        """Initialize hybrid crew.

        Args:
            hybrid_agents: Dictionary mapping agent roles to HybridAnalysisAgent instances
            token_tracker: Token usage tracker
        """
        self.hybrid_agents = hybrid_agents
        self.token_tracker = token_tracker
        self.execution_log: list[dict[str, Any]] = []

    def execute_analysis(
        self,
        tasks: dict[str, Task],
        context: dict[str, Any] = None,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Execute analysis with all agents.

        Args:
            tasks: Dictionary mapping task names to Task objects
            context: Additional context
            progress_callback: Optional callback function(current, total, task_name) for progress updates

        Returns:
            Combined analysis results
        """
        context = context or {}
        results = {}

        logger.info(f"Starting hybrid crew analysis with {len(tasks)} tasks")

        total_tasks = len(tasks)
        for idx, (task_name, task) in enumerate(tasks.items(), 1):
            # Find appropriate agent for this task
            agent_key = None
            for key in self.hybrid_agents.keys():
                if key.lower() in task_name.lower() or task_name.lower() in key.lower():
                    agent_key = key
                    break

            if not agent_key:
                logger.warning(f"No agent found for task: {task_name}")
                results[task_name] = {"status": "skipped", "reason": "No matching agent"}
                if progress_callback:
                    progress_callback(idx, total_tasks, task_name)
                continue

            hybrid_agent = self.hybrid_agents[agent_key]
            logger.debug(f"Executing task {task_name} with agent {agent_key}")

            # Call progress callback before executing task
            if progress_callback:
                progress_callback(idx - 1, total_tasks, task_name)

            result = hybrid_agent.execute_task(task, context)
            results[task_name] = result

            # Call progress callback after executing task
            if progress_callback:
                progress_callback(idx, total_tasks, task_name)

            # Log execution
            self.execution_log.append(
                {
                    "task": task_name,
                    "agent": agent_key,
                    "status": result.get("status"),
                    "used_llm": result.get("used_llm"),
                    "used_fallback": result.get("used_fallback"),
                }
            )

        logger.info(f"Hybrid crew analysis complete. Results: {len(results)} tasks executed")

        # Summary statistics
        successful = sum(1 for r in results.values() if r.get("status") == "success")
        llm_used = sum(1 for r in results.values() if r.get("used_llm"))
        fallback_used = sum(1 for r in results.values() if r.get("used_fallback"))

        return {
            "status": "complete",
            "results": results,
            "summary": {
                "total_tasks": len(tasks),
                "successful": successful,
                "failed": len(tasks) - successful,
                "llm_used": llm_used,
                "fallback_used": fallback_used,
            },
            "log": self.execution_log,
        }

    def get_crew_status(self) -> dict[str, Any]:
        """Get status of all agents in crew.

        Returns:
            Status dictionary for each agent
        """
        return {agent_name: agent.get_status() for agent_name, agent in self.hybrid_agents.items()}

    def log_summary(self) -> None:
        """Log execution summary."""
        if not self.execution_log:
            logger.info("No execution log entries")
            return

        successful = sum(1 for e in self.execution_log if e["status"] == "success")
        llm_used = sum(1 for e in self.execution_log if e["used_llm"])
        fallback_used = sum(1 for e in self.execution_log if e["used_fallback"])

        logger.info(
            f"Hybrid crew execution: {successful}/{len(self.execution_log)} successful, "
            f"{llm_used} LLM, {fallback_used} fallback"
        )

        if self.token_tracker:
            self.token_tracker.log_summary()
