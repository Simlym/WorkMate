from typing import Any
from app.mcp.tools.base import ToolBase

class EchoTool(ToolBase):
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "Echoes back the input message."

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {"message": {"type": "string", "description": "Text to echo"}}, "required": ["message"]}

    async def run(self, arguments: dict) -> Any:
        return {"echo": arguments.get("message", "")}
