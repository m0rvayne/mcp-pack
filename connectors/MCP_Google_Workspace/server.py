"""
Google Workspace MCP Server — Full Coverage
Drive (53) + Calendar (35) + Sheets (47) + Docs (32) = 167 tools
Single MCP endpoint, modular architecture.
"""

import asyncio
import json
import signal
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from googleapiclient.errors import HttpError

import api_drive
import api_calendar
import api_sheets
import api_docs
from utils import safe_error, format_error


# =============================================================================
# Signal handling
# =============================================================================

def _handle_shutdown(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGINT, _handle_shutdown)


# =============================================================================
# Server
# =============================================================================

server = Server("google-workspace")

# Build combined tool list and dispatch map
_ALL_MODULES = [
    ("drive_", api_drive),
    ("cal_", api_calendar),
    ("sheets_", api_sheets),
    ("docs_", api_docs),
]

_TOOL_MAP: dict[str, Any] = {}  # tool_name -> module

for prefix, module in _ALL_MODULES:
    for tool in module.TOOLS:
        _TOOL_MAP[tool.name] = module


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    tools = []
    for _, module in _ALL_MODULES:
        tools.extend(module.TOOLS)
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    try:
        module = _TOOL_MAP.get(name)
        if not module:
            return [types.TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
        result = await asyncio.to_thread(module.handle, name, arguments)
        if isinstance(result, list):
            return result
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str, indent=2))]
    except HttpError as e:
        status = e.resp.status if hasattr(e, 'resp') else 'unknown'
        return [types.TextContent(type="text", text=f"Error: Google API returned HTTP {status}: {safe_error(e)}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {format_error(e)}")]


# =============================================================================
# Entry point
# =============================================================================

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
