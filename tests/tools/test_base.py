"""Unit tests for the tools base module."""

from typing import Any

import pytest

from src.tools.base import BaseTool, ToolRegistry


class MockTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""

    def run(self, *args, **kwargs) -> Any:
        """Execute the mock tool."""
        return {"args": args, "kwargs": kwargs}


class TestBaseTool:
    """Test suite for BaseTool class."""

    def test_initialization(self):
        """Test BaseTool initialization."""
        tool = MockTool(name="mock_tool", description="A mock tool for testing")

        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"

    def test_str_representation(self):
        """Test string representation of tool."""
        tool = MockTool(name="test_tool", description="Test")

        result = str(tool)

        assert "MockTool" in result
        assert "test_tool" in result

    def test_run_with_args(self):
        """Test tool run with positional arguments."""
        tool = MockTool(name="test", description="test")

        result = tool.run("arg1", "arg2")

        assert result["args"] == ("arg1", "arg2")
        assert result["kwargs"] == {}

    def test_run_with_kwargs(self):
        """Test tool run with keyword arguments."""
        tool = MockTool(name="test", description="test")

        result = tool.run(key1="value1", key2="value2")

        assert result["args"] == ()
        assert result["kwargs"] == {"key1": "value1", "key2": "value2"}

    def test_run_with_both(self):
        """Test tool run with both args and kwargs."""
        tool = MockTool(name="test", description="test")

        result = tool.run("arg1", key1="value1")

        assert result["args"] == ("arg1",)
        assert result["kwargs"] == {"key1": "value1"}


class TestToolRegistry:
    """Test suite for ToolRegistry class."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before and after each test."""
        ToolRegistry.reset()
        yield
        ToolRegistry.reset()

    def test_register_tool(self):
        """Test registering a tool."""
        tool = MockTool(name="registered_tool", description="Test")

        ToolRegistry.register("my_tool", tool)

        assert ToolRegistry.get("my_tool") == tool

    def test_get_unregistered_tool(self):
        """Test getting unregistered tool returns None."""
        result = ToolRegistry.get("nonexistent")

        assert result is None

    def test_get_all_tools(self):
        """Test getting all registered tools."""
        tool1 = MockTool(name="tool1", description="Tool 1")
        tool2 = MockTool(name="tool2", description="Tool 2")

        ToolRegistry.register("tool_a", tool1)
        ToolRegistry.register("tool_b", tool2)

        all_tools = ToolRegistry.get_all()

        assert len(all_tools) == 2
        assert "tool_a" in all_tools
        assert "tool_b" in all_tools

    def test_get_all_returns_copy(self):
        """Test that get_all returns a copy."""
        tool = MockTool(name="test", description="Test")
        ToolRegistry.register("test", tool)

        all_tools = ToolRegistry.get_all()
        all_tools["new_key"] = "new_value"

        # Original registry should be unchanged
        assert "new_key" not in ToolRegistry.get_all()

    def test_unregister_tool_success(self):
        """Test unregistering an existing tool."""
        tool = MockTool(name="temp", description="Temporary")
        ToolRegistry.register("temp_tool", tool)

        result = ToolRegistry.unregister("temp_tool")

        assert result is True
        assert ToolRegistry.get("temp_tool") is None

    def test_unregister_tool_not_found(self):
        """Test unregistering non-existent tool."""
        result = ToolRegistry.unregister("nonexistent")

        assert result is False

    def test_reset_clears_all(self):
        """Test reset clears all tools."""
        tool1 = MockTool(name="tool1", description="Tool 1")
        tool2 = MockTool(name="tool2", description="Tool 2")
        ToolRegistry.register("tool_a", tool1)
        ToolRegistry.register("tool_b", tool2)

        ToolRegistry.reset()

        assert ToolRegistry.get_all() == {}

    def test_register_overwrites_existing(self):
        """Test registering with same name overwrites."""
        tool1 = MockTool(name="original", description="Original")
        tool2 = MockTool(name="replacement", description="Replacement")

        ToolRegistry.register("my_tool", tool1)
        ToolRegistry.register("my_tool", tool2)

        assert ToolRegistry.get("my_tool") == tool2
        assert ToolRegistry.get("my_tool").name == "replacement"
