#!/usr/bin/env python3
"""
Run the simple agent using ADK CLI but bypassing symlink issues.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Monkey patch the symlink creation to avoid Windows privilege issues
def safe_symlink(src, dst):
    """Safe symlink that copies instead of creating symlinks on Windows."""
    try:
        if os.path.exists(dst):
            os.remove(dst)
        # Instead of symlink, just copy the file
        import shutil
        shutil.copy2(src, dst)
    except Exception as e:
        print(f"Note: Could not create symlink {src} -> {dst}: {e}")

# Patch the os.symlink function
original_symlink = os.symlink
os.symlink = safe_symlink

try:
    from google.adk.cli import main
    
    if __name__ == "__main__":
        # Set up arguments for the CLI to run our simple agent
        sys.argv = ["run_simple_agent.py", "run", "yaml_agent"]
        
        print("🚀 Starting Jira Assistant Agent...")
        print("Note: Using safe symlink workaround for Windows")
        
        # Run the CLI
        main()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Restore original symlink function
    os.symlink = original_symlink
