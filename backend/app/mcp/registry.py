"""Tool registry — central place to register/unregister MCP tools."""
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from app.mcp.tools.base import ToolBase

_registry: dict[str, "ToolBase"] = {}
_on_register: list[Callable[["ToolBase"], None]] = []
_on_unregister: list[Callable[[str], None]] = []


def add_register_callback(cb: Callable[["ToolBase"], None]) -> None:
    _on_register.append(cb)


def add_unregister_callback(cb: Callable[[str], None]) -> None:
    _on_unregister.append(cb)


def register(tool: "ToolBase") -> None:
    _registry[tool.name] = tool
    for cb in _on_register:
        cb(tool)


def unregister(name: str) -> None:
    if name in _registry:
        _registry.pop(name)
        for cb in _on_unregister:
            cb(name)


def get_all() -> list["ToolBase"]:
    return list(_registry.values())


def get(name: str) -> "ToolBase | None":
    return _registry.get(name)
