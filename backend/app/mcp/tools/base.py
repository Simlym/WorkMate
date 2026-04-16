"""Base interface for WorkMate MCP tools."""
from abc import ABC, abstractmethod
from typing import Any


class ToolBase(ABC):
    """All MCP tools must implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description shown to LLM."""

    @property
    def input_schema(self) -> dict:
        """JSON Schema for tool input. Override to customize."""
        return {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> Any:
        """Execute the tool and return result."""
