"""WorkMate MCP Server — exposes registered tools via Streamable HTTP transport."""
from mcp.server.fastmcp import FastMCP
from app.mcp import registry

mcp = FastMCP("WorkMate")


def _register_tool(tool) -> None:
    async def handler(**kwargs):
        return await tool.run(kwargs)

    handler.__name__ = tool.name
    handler.__doc__ = tool.description
    mcp.tool(name=tool.name, description=tool.description)(handler)


def _unregister_tool(name: str) -> None:
    # FastMCP stores tools in _tool_manager._tools (internal dict)
    try:
        mcp._tool_manager._tools.pop(name, None)
    except AttributeError:
        pass


def get_mcp_app():
    """Return the ASGI app for mounting into FastAPI.
    Called once at startup; new tools registered later via callbacks.
    """
    # Sync tools already in registry (e.g. built-ins loaded before startup)
    for tool in registry.get_all():
        _register_tool(tool)

    # Hook callbacks so dynamically loaded skills auto-register
    registry.add_register_callback(_register_tool)
    registry.add_unregister_callback(_unregister_tool)

    return mcp.streamable_http_app()
