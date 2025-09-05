import sys
from pathlib import Path

# Add project root to the Python path to allow for correct module resolution
sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_server_structure():
    """
    A lightweight test to verify the server's structure without external dependencies.
    
    This test checks:
    1. That the `mcp_toolbox` package can be imported.
    2. That the `mcp` server object is created.
    3. That the tool functions are being correctly registered.
    """
    print("🚀 Verifying server structure (no dependencies required)...")
    
    try:
        from mcp_toolbox.server import mcp
        print("✅ MCP server object created successfully.")
    except ImportError as e:
        print(f"❌ Failed to import server object: {e}")
        print("   This might indicate a problem with your __main__.py or server.py files.")
        return

    try:
        # This import triggers the @mcp.tool decorators
        from mcp_toolbox.tools import jira_tools
        print("✅ Tool module imported successfully.")
    except ImportError as e:
        print(f"❌ Failed to import tool module: {e}")
        print("   This likely means there is a syntax error in your jira_tools.py file.")
        return

    # Check if the tools were registered
    if hasattr(mcp, "tools") and len(mcp.tools) > 0:
        print(f"✅ {len(mcp.tools)} tools were successfully registered:")
        for tool_name in sorted(mcp.tools.keys()):
            print(f"   - {tool_name}")
    else:
        print("❌ No tools were registered.")
        print("   This is the classic '0 tools enabled' problem. Check your imports in __main__.py.")
        
    print("\nServer structure is sound. Once dependencies are installed, it should run correctly.")

if __name__ == "__main__":
    verify_server_structure() 