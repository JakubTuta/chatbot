"""Talks to external Model Context Protocol servers the user has
configured (models.MCPServer). Each call here opens a fresh connection —
a stdio server means spawning a subprocess, an HTTP server means opening a
streamable-HTTP connection — and closes it again once done. That trades
some latency (a subprocess launch per tool call) for not having to manage
long-lived MCP sessions across unrelated WebSocket requests, which would
need its own lifecycle manager for comparatively little benefit at the
scale this app runs at.
"""

import logging
import re
import shlex
import typing

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from .. import models

logger = logging.getLogger(__name__)


class MCPToolError(Exception):
    pass


class MCPToolInfo(typing.TypedDict):
    name: str
    description: str
    input_schema: dict[str, typing.Any]


def _connect(server: models.MCPServer):
    if server.transport == models.MCPServer.TRANSPORT_STDIO:
        parts = shlex.split(server.command)
        if not parts:
            raise MCPToolError(f"MCP server {server.name!r} has no command configured.")

        return stdio_client(StdioServerParameters(command=parts[0], args=parts[1:]))

    if not server.url:
        raise MCPToolError(f"MCP server {server.name!r} has no URL configured.")

    return streamable_http_client(server.url)


async def list_server_tools(server: models.MCPServer) -> list[MCPToolInfo]:
    """Best-effort — a server that's down or misconfigured returns an empty
    list (logged) rather than raising, the same resilience RAG's collection
    lookup has: one broken integration shouldn't stop a chat response.
    """
    try:
        async with _connect(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()

                return [
                    {"name": t.name, "description": t.description or "", "input_schema": t.inputSchema or {}}
                    for t in result.tools
                ]
    except Exception as e:
        logger.warning("Could not list tools from MCP server %r: %s", server.name, e)
        return []


async def call_server_tool(server: models.MCPServer, tool_name: str, arguments: dict) -> str:
    async with _connect(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            text_parts = [block.text for block in result.content if hasattr(block, "text")]
            output = "\n".join(text_parts) if text_parts else str(result.content)

            return f"Error: {output}" if result.isError else output


_NAME_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9_-]")


class ToolRegistry(typing.NamedTuple):
    # OpenAI-format tool specs — what ChatOllama.bind_tools() expects
    # alongside the @tool-decorated builtins (see functions.py).
    tool_specs: list[dict[str, typing.Any]]
    # Prefixed name -> (server, original tool name). Built once so a tool
    # call never has to parse the prefix back apart — the prefix only
    # exists to keep identically-named tools on different servers from
    # colliding in bind_tools()'s flat tool list.
    lookup: dict[str, tuple[models.MCPServer, str]]


def build_tool_registry(servers_with_tools: list[tuple[models.MCPServer, list[MCPToolInfo]]]) -> ToolRegistry:
    tool_specs: list[dict[str, typing.Any]] = []
    lookup: dict[str, tuple[models.MCPServer, str]] = {}

    for server, tools in servers_with_tools:
        server_slug = _NAME_SANITIZE_RE.sub("_", server.name)

        for tool_info in tools:
            tool_slug = _NAME_SANITIZE_RE.sub("_", tool_info["name"])
            prefixed_name = f"mcp_{server_slug}_{tool_slug}"

            tool_specs.append({
                "type": "function",
                "function": {
                    "name": prefixed_name,
                    "description": tool_info["description"],
                    "parameters": tool_info["input_schema"] or {"type": "object", "properties": {}},
                },
            })
            lookup[prefixed_name] = (server, tool_info["name"])

    return ToolRegistry(tool_specs=tool_specs, lookup=lookup)
