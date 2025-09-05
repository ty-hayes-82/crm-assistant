from .server import mcp
# Import registers tools via @mcp.tool()
from .tools import jira_tools  # noqa: F401

def main():
    """Entry point to run the MCP toolbox server (no stdout prints)."""
    # The tools are registered at import time; just run the server.
    mcp.run()

if __name__ == "__main__":
    main() 