"""Main entry point for CRM FastMCP Server."""

import asyncio
import logging
from .server import server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run the CRM FastMCP server."""
    try:
        logger.info("Starting CRM FastMCP Server...")
        
        # The server is already created in server.py
        # This would typically start the MCP server in a real implementation
        logger.info("CRM FastMCP Server is ready")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down CRM FastMCP Server...")
    finally:
        await server.close()

if __name__ == "__main__":
    asyncio.run(main())
