"""MCP学术服务主模块"""
from .server import mcp as scholar_server
from .scholar import search_scholar, parse_profile

__version__ = "1.0.0"
__all__ = ["scholar_server", "search_scholar", "parse_profile"]
