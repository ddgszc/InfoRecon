"""MCP服务端模块

提供基于FastMCP的MCP协议服务，复用现有服务层实现
"""

from .server import mcp_server

__all__ = ["mcp_server"]

