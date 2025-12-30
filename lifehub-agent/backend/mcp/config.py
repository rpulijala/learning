"""MCP server configuration."""

import os
from typing import TypedDict


class MCPServerConfig(TypedDict):
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    enabled: bool


def get_mcp_servers() -> list[MCPServerConfig]:
    """Get list of configured MCP servers.
    
    Returns servers that are enabled based on environment variables.
    """
    servers: list[MCPServerConfig] = []
    
    # Brave Search MCP Server
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if brave_api_key:
        servers.append({
            "name": "brave-search",
            "command": "npx",
            "args": ["-y", "@brave/brave-search-mcp-server"],
            "env": {"BRAVE_API_KEY": brave_api_key},
            "enabled": True,
        })
    
    return servers


def is_mcp_enabled() -> bool:
    """Check if MCP is enabled (any servers configured)."""
    return len(get_mcp_servers()) > 0
