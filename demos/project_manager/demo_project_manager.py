"""
Demo: Project Manager Agent

This demo shows how the Project Manager Agent can orchestrate complex CRM tasks
by coordinating with specialized CRM agents.
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from project_manager_agent import create_project_manager


async def demo_project_manager():
    """Demonstrate the Project Manager Agent functionality."""
    
    print("🎯 Project Manager Agent Demo")
    print("=" * 60)
    print()
    
    # Create the project manager agent
    pm_agent = create_project_manager()
    
    # Demo goals to test
    demo_goals = [
        {
            "goal": "Analyze The Golf Club at Mansion Ridge and set up proper management company relationship",
            "description": "Single company analysis - should identify Troon as management company"
        },
        {
            "goal": "Find all golf clubs in Arizona and enrich their records",
            "description": "Multi-step workflow - search, enrich, and set management companies"
        },
        {
            "goal": "Review HubSpot data and enrich missing fields for top prospects",
            "description": "Data quality analysis and systematic enrichment"
        }
    ]
    
    for i, demo in enumerate(demo_goals, 1):
        print(f"Demo {i}: {demo['description']}")
        print(f"Goal: {demo['goal']}")
        print("-" * 50)
        
        try:
            # Execute the goal
            result = await pm_agent.execute_goal(demo['goal'])
            
            # Display results
            print(f"📊 Project Results:")
            print(f"   Status: {result['status']}")
            print(f"   Progress: {result['progress']:.1f}%")
            print(f"   Tasks: {result['completed_tasks']}/{result['total_tasks']} completed")
            
            if result['failed_tasks'] > 0:
                print(f"   ⚠️ Failed tasks: {result['failed_tasks']}")
            
            # Show task details
            if 'task_results' in result:
                print(f"\n📋 Task Details:")
                for task_id, task_result in result['task_results'].items():
                    if 'error' in task_result:
                        print(f"   ❌ {task_id}: {task_result['error']}")
                    else:
                        print(f"   ✅ {task_id}: Completed successfully")
                        if 'companies' in task_result:
                            print(f"      Found {len(task_result['companies'])} companies")
                        if 'management_company' in task_result:
                            print(f"      Management company: {task_result['management_company']}")
            
        except Exception as e:
            print(f"❌ Error executing goal: {str(e)}")
        
        print("\n" + "="*60 + "\n")
    
    # Show project management capabilities
    print("🚀 Project Manager Capabilities Demonstrated:")
    print("✅ Goal parsing and task decomposition")
    print("✅ A2A coordination with CRM agents")
    print("✅ Task dependency management")
    print("✅ Progress monitoring and reporting")
    print("✅ Error handling and recovery")
    print("✅ Multi-step workflow orchestration")
    
    print("\n💡 Key Features:")
    print("• Intelligent goal-to-task mapping")
    print("• Coordination with specialized CRM agents")
    print("• Support for complex multi-step workflows")
    print("• Real-time progress tracking")
    print("• Comprehensive result reporting")


async def demo_mansion_ridge_specific():
    """Demo specifically for The Golf Club at Mansion Ridge"""
    
    print("\n🏌️ Mansion Ridge Specific Demo")
    print("=" * 60)
    
    pm_agent = create_project_manager()
    
    # Use the exact company from the user's example
    goal = "Analyze The Golf Club at Mansion Ridge (mansionridgegc.com) and ensure proper management company setup"
    
    print(f"Goal: {goal}")
    print()
    
    result = await pm_agent.execute_goal(goal, context={
        "company_domain": "mansionridgegc.com",
        "company_phone": "(845) 782-7888",
        "location": "Monroe, NY",
        "current_data": {
            "management_company": "",  # Currently empty
            "parent_company": "",      # Currently empty
            "description": "",         # Currently empty
            "club_type": "Public - High Daily Fee"
        }
    })
    
    print(f"📊 Results for Mansion Ridge:")
    print(f"   Project Status: {result['status']}")
    print(f"   Tasks Completed: {result['completed_tasks']}/{result['total_tasks']}")
    
    # Check if management company was identified
    for task_id, task_result in result.get('task_results', {}).items():
        if 'management_company' in task_result:
            mgmt_company = task_result['management_company']
            print(f"   🎯 Management Company Identified: {mgmt_company}")
            if mgmt_company == "Troon":
                print("   ✅ Correct! Should set Troon as parent company")
            else:
                print(f"   ⚠️ Unexpected result: {mgmt_company}")


if __name__ == "__main__":
    # Run the demos
    asyncio.run(demo_project_manager())
    asyncio.run(demo_mansion_ridge_specific())
