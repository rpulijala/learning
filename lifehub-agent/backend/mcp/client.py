"""MCP client for connecting to external MCP servers."""

import asyncio
import logging
import os
from typing import Any, Callable

from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.mcp.config import get_mcp_servers, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages connections to MCP servers and provides tools."""
    
    def __init__(self):
        self._tools: list[StructuredTool] = []
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize connections to all configured MCP servers."""
        if self._initialized:
            return
        
        servers = get_mcp_servers()
        if not servers:
            logger.info("No MCP servers configured")
            self._initialized = True
            return
        
        for server_config in servers:
            if server_config["enabled"]:
                try:
                    tools = await self._connect_to_server(server_config)
                    self._tools.extend(tools)
                    logger.info(f"Connected to MCP server '{server_config['name']}' with {len(tools)} tools")
                except Exception as e:
                    logger.error(f"Failed to connect to MCP server '{server_config['name']}': {e}")
        
        self._initialized = True
    
    async def _connect_to_server(self, config: MCPServerConfig) -> list[StructuredTool]:
        """Connect to an MCP server and get its tools."""
        tools = []
        
        # Merge environment variables
        env = {**os.environ, **config.get("env", {})}
        
        server_params = StdioServerParameters(
            command=config["command"],
            args=config["args"],
            env=env,
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List available tools from the server
                tools_response = await session.list_tools()
                
                for tool_info in tools_response.tools:
                    # Create a LangChain-compatible tool wrapper
                    langchain_tool = self._create_langchain_tool(
                        tool_info=tool_info,
                        server_config=config,
                    )
                    tools.append(langchain_tool)
        
        return tools
    
    def _create_langchain_tool(
        self,
        tool_info: Any,
        server_config: MCPServerConfig,
    ) -> StructuredTool:
        """Create a LangChain StructuredTool from an MCP tool definition."""
        
        # Capture tool_info and server_config in closure
        _tool_name = tool_info.name
        _server_config = server_config
        _self = self  # Capture self reference
        
        # LangChain unpacks the dict and passes as **kwargs matching function params
        # We use **kwargs to capture all arguments dynamically
        def sync_call_mcp_tool(**kwargs) -> str:
            # Filter out None values - MCP doesn't accept them
            filtered_args = {k: v for k, v in kwargs.items() if v is not None}
            logger.info(f"MCP tool {_tool_name} sync called with args: {filtered_args}")
            
            # Define the coroutine inside to capture args properly
            async def _run():
                return await _self._execute_mcp_tool(
                    server_config=_server_config,
                    tool_name=_tool_name,
                    arguments=filtered_args,
                )
            
            # Run in a new thread with its own event loop to avoid conflicts
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, _run())
                return future.result(timeout=60)
        
        # Async version
        async def async_call_mcp_tool(**kwargs) -> str:
            # Filter out None values - MCP doesn't accept them
            filtered_args = {k: v for k, v in kwargs.items() if v is not None}
            logger.info(f"MCP tool {_tool_name} async called with args: {filtered_args}")
            return await _self._execute_mcp_tool(
                server_config=_server_config,
                tool_name=_tool_name,
                arguments=filtered_args,
            )
        
        # Build args_schema from MCP tool's inputSchema for LangChain
        # This tells LangChain what parameters the tool expects
        args_schema = None
        if tool_info.inputSchema:
            from pydantic import create_model, Field
            from typing import Optional, Any
            
            properties = tool_info.inputSchema.get("properties", {})
            required = tool_info.inputSchema.get("required", [])
            
            # Build field definitions for pydantic model
            field_definitions = {}
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "string")
                prop_desc = prop_info.get("description", "")
                
                # Map JSON schema types to Python types
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": float,
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                python_type = type_map.get(prop_type, str)
                
                if prop_name in required:
                    field_definitions[prop_name] = (python_type, Field(description=prop_desc))
                else:
                    field_definitions[prop_name] = (Optional[python_type], Field(default=None, description=prop_desc))
            
            if field_definitions:
                args_schema = create_model(f"{tool_info.name}Args", **field_definitions)
        
        return StructuredTool.from_function(
            func=sync_call_mcp_tool,
            coroutine=async_call_mcp_tool,
            name=tool_info.name,
            description=tool_info.description or f"MCP tool: {tool_info.name}",
            args_schema=args_schema,
        )
    
    async def _execute_mcp_tool(
        self,
        server_config: MCPServerConfig,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """Execute an MCP tool and return the result."""
        logger.info(f"Executing MCP tool '{tool_name}' with arguments: {arguments}")
        
        env = {**os.environ, **server_config.get("env", {})}
        
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"],
            env=env,
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Pass arguments directly - MCP expects them as a dict
                result = await session.call_tool(tool_name, arguments=arguments)
                
                # Extract text content from result
                if result.content:
                    text_parts = []
                    for content in result.content:
                        if hasattr(content, "text"):
                            text_parts.append(content.text)
                    return "\n".join(text_parts) if text_parts else str(result)
                
                return str(result)
    
    def get_tools(self) -> list[StructuredTool]:
        """Get all available MCP tools."""
        return self._tools


# Global instance
_mcp_manager: MCPClientManager | None = None


async def get_mcp_tools() -> list[StructuredTool]:
    """Get all tools from configured MCP servers.
    
    This is the main entry point for getting MCP tools.
    Returns an empty list if no MCP servers are configured.
    """
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
        await _mcp_manager.initialize()
    
    return _mcp_manager.get_tools()


def get_mcp_tools_sync() -> list[StructuredTool]:
    """Synchronous version of get_mcp_tools."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, return empty
            # Tools will be loaded async later
            return []
        return loop.run_until_complete(get_mcp_tools())
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(get_mcp_tools())
