"""MCP学术服务主模块"""

import sys
from .server import mcp as scholar_server
from .scholar import search_scholar, parse_profile
from .__main__ import cli_main

__version__ = "1.0.0"
__all__ = ["scholar_server", "search_scholar", "parse_profile", "cli_main"]
