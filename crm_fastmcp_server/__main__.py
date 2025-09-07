"""Main entry point for CRM FastMCP Server."""

import asyncio
import sys
from .stdio_server import main

if __name__ == "__main__":
    asyncio.run(main())
