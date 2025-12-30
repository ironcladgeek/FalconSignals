"""Base agent interface and abstract class."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.agents.base.config import AgentConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for CrewAI agents."""

    def __init__(self, config: AgentConfig, tools: list = None):
        """Initialize agent.

        Args:
            config: Agent configuration
            tools: List of tools available to agent
        """
        self.config = config
        self.tools = tools or []
        self.memory = {} if config.memory else None
        logger.debug(f"Initialized agent: {config.role}")

    @property
    def role(self) -> str:
        """Get agent role."""
        return self.config.role

    @property
    def goal(self) -> str:
        """Get agent goal."""
        return self.config.goal

    @property
    def backstory(self) -> str:
        """Get agent backstory."""
        return self.config.backstory

    @abstractmethod
    def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Execute agent task.

        Args:
            task: Task description
            context: Additional context for execution

        Returns:
            Agent execution result
        """

    def add_tool(self, tool: Any) -> None:
        """Add tool to agent.

        Args:
            tool: Tool instance
        """
        self.tools.append(tool)
        logger.debug(f"Added tool {tool.name} to {self.role}")

    def remember(self, key: str, value: Any) -> None:
        """Store information in memory.

        Args:
            key: Memory key
            value: Value to store
        """
        if self.memory is not None:
            self.memory[key] = value

    def recall(self, key: str) -> Optional[Any]:
        """Retrieve information from memory.

        Args:
            key: Memory key

        Returns:
            Value or None if not found
        """
        if self.memory is not None:
            return self.memory.get(key)
        return None

    def __str__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(role={self.role})>"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"{self.__class__.__name__}("
            f"role={self.role!r}, "
            f"goal={self.goal!r}, "
            f"tools={len(self.tools)})"
        )
