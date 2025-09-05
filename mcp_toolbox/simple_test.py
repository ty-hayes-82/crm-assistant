#!/usr/bin/env python3
"""
Simple test runner that directly calls the utility functions.
This bypasses the MCP layer and tests the core functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_simple_tests():
    """Run tests directly on the utility functions."""
    print("🧪 Testing Jira Analysis Functions Directly")
    print("=" * 50)
    
    try:
        from mcp_toolbox.utils.jira_reader import (
            read_jira_csv_summary,
            get_status_distribution,
            get_project_distribution,
            get_priority_distribution,
            get_assignee_workload,
            search_issues_by_text
        )
        
        tests = [
            ("📊 CSV Summary", lambda: read_jira_csv_summary()),
            ("📈 Status Distribution", lambda: get_status_distribution()),
            ("🏢 Project Distribution", lambda: get_project_distribution()),
            ("⚡ Priority Distribution", lambda: get_priority_distribution()),
            ("👥 Top 5 Assignees", lambda: get_assignee_workload(5)),
            ("🔍 Search for 'data'", lambda: search_issues_by_text("data")),
        ]
        
        for name, test_func in tests:
            print(f"\n{name}:")
            print("-" * 30)
            try:
                result = test_func()
                # Truncate long results
                if len(result) > 400:
                    print(result[:400] + "...")
                else:
                    print(result)
                print("✅ Success!")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ All direct tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the right directory and dependencies are installed.")

def run_interactive():
    """Run interactive mode for testing individual functions."""
    print("🎯 Interactive Function Tester")
    print("=" * 50)
    
    try:
        from mcp_toolbox.utils.jira_reader import (
            read_jira_csv_summary,
            get_status_distribution,
            get_project_distribution,
            get_priority_distribution,
            get_assignee_workload,
            search_issues_by_text
        )
        
        functions = {
            "1": ("CSV Summary", lambda: read_jira_csv_summary()),
            "2": ("Status Distribution", lambda: get_status_distribution()),
            "3": ("Project Distribution", lambda: get_project_distribution()),
            "4": ("Priority Distribution", lambda: get_priority_distribution()),
            "5": ("Assignee Workload", lambda: get_assignee_workload(
                int(input("How many top assignees? (default 10): ").strip() or "10")
            )),
            "6": ("Search Issues", lambda: search_issues_by_text(
                input("Enter search term: ").strip()
            )),
        }
        
        while True:
            print("\nAvailable functions:")
            for key, (name, _) in functions.items():
                print(f"  {key}. {name}")
            print("  7. Run all tests")
            print("  8. Quit")
            
            choice = input("\nEnter choice (1-8): ").strip()
            
            if choice == "8":
                print("👋 Goodbye!")
                break
            elif choice == "7":
                run_simple_tests()
                continue
            
            if choice in functions:
                name, func = functions[choice]
                print(f"\n🔧 Running {name}...")
                print("-" * 30)
                try:
                    result = func()
                    print(result)
                    print("✅ Success!")
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("❌ Invalid choice. Please enter 1-8.")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive()
    else:
        run_simple_tests() 