"""CRM FastMCP Server for multi-agent CRM enrichment and cleanup."""

# Import only the stdio server for MCP protocol
from . import stdio_server

__all__ = ["stdio_server"]
