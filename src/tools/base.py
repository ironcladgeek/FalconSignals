"""Base tool class and tool registry for CrewAI agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaseTool(ABC):
    """Abstract base class for CrewAI tools."""

    def __init__(self, name: str, description: str):
        """Initialize tool.

        Args:
            name: Tool name for display
            description: Tool description for agent understanding
        """
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute tool operation.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool result
        """

    def __str__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name={self.name})>"


class ToolRegistry:
    """Registry for managing tools."""

    _tools = {}

    @classmethod
    def register(cls, tool_name: str, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool_name: Tool identifier
            tool: Tool instance
        """
        cls._tools[tool_name] = tool
        logger.debug(f"Registered tool: {tool_name}")

    @classmethod
    def get(cls, tool_name: str) -> Optional[BaseTool]:
        """Get tool by name.

        Args:
            tool_name: Tool identifier

        Returns:
            Tool instance or None
        """
        return cls._tools.get(tool_name)

    @classmethod
    def get_all(cls) -> dict[str, BaseTool]:
        """Get all registered tools.

        Returns:
            Dictionary of tools
        """
        return cls._tools.copy()

    @classmethod
    def unregister(cls, tool_name: str) -> bool:
        """Unregister a tool.

        Args:
            tool_name: Tool identifier

        Returns:
            True if unregistered, False if not found
        """
        if tool_name in cls._tools:
            del cls._tools[tool_name]
            logger.debug(f"Unregistered tool: {tool_name}")
            return True
        return False

    @classmethod
    def reset(cls) -> None:
        """Clear all tools."""
        cls._tools.clear()
