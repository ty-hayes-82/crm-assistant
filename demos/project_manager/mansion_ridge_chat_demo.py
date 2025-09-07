"""
Automated Mansion Ridge Demo with Chat Interface
Shows A2A communication for the specific Mansion Ridge example
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from project_manager_agent.interactive_coordinator import create_interactive_project_manager


async def demo_mansion_ridge_chat():
    """Demo the Mansion Ridge example with chat interface"""
    
    print("🏌️ Mansion Ridge Golf Club - A2A Communication Demo")
    print("=" * 60)
    print("This demo shows how the Project Manager Agent coordinates with CRM agents")
    print("to analyze The Golf Club at Mansion Ridge and set up the management company.")
    print()
    
    # Create the interactive agent
    pm_agent = create_interactive_project_manager()
    
    # Simulate the user goal
    goal = "Analyze The Golf Club at Mansion Ridge and set up proper management company relationship"
    
    # Context from the user's HubSpot data
    context = {
        "company_domain": "mansionridgegc.com",
        "company_phone": "(845) 782-7888",
        "location": "Monroe, NY",
        "current_data": {
            "management_company": "",  # Currently empty - should be "Troon"
            "parent_company": "",      # Currently empty - should be Troon's ID
            "description": "",         # Currently empty
            "club_type": "Public - High Daily Fee",
            "annual_revenue": "$10,000,000.00"
        }
    }
    
    # Start the chat interface manually
    pm_agent.chat.display_separator("PROJECT MANAGER AGENT - MANSION RIDGE DEMO")
    
    from project_manager_agent.chat_interface import MessageType
    
    pm_agent.chat.add_message(
        MessageType.PROJECT_MANAGER,
        "Hello! I'm analyzing The Golf Club at Mansion Ridge for you."
    )
    
    pm_agent.chat.add_message(
        MessageType.USER,
        goal
    )
    
    # Execute the goal with chat display
    result = await pm_agent.execute_goal_with_chat(goal, context)
    
    # Show what would happen in HubSpot
    pm_agent.chat.display_separator("HUBSPOT UPDATES")
    
    pm_agent.chat.add_message(
        MessageType.PROJECT_MANAGER,
        "📋 The following updates would be made to HubSpot:"
    )
    
    # Check if management company was identified
    management_company = None
    management_company_id = None
    
    for task_result in result.get('task_results', {}).values():
        if 'management_company' in task_result:
            management_company = task_result['management_company']
            management_company_id = task_result.get('management_company_id')
            break
    
    if management_company:
        updates_msg = f"🏢 Company: The Golf Club at Mansion Ridge\n"
        updates_msg += f"   • Management Company: '{management_company}'\n"
        updates_msg += f"   • Parent Company ID: {management_company_id}\n"
        updates_msg += f"   • Status: Ready for HubSpot update"
        
        pm_agent.chat.add_message(
            MessageType.SYSTEM,
            updates_msg
        )
        
        if management_company == "Troon":
            pm_agent.chat.add_message(
                MessageType.PROJECT_MANAGER,
                "✅ SUCCESS: Correctly identified Troon as the management company!\n" +
                "This matches the expected result from your course database."
            )
        else:
            pm_agent.chat.add_message(
                MessageType.PROJECT_MANAGER,
                f"⚠️ Note: Identified {management_company}, but expected Troon based on course database."
            )
    else:
        pm_agent.chat.add_message(
            MessageType.SYSTEM,
            "❌ No management company identification completed."
        )
    
    pm_agent.chat.display_separator("DEMO COMPLETE")
    pm_agent.chat.add_message(
        MessageType.PROJECT_MANAGER,
        "Demo completed! This shows how the Project Manager Agent:\n" +
        "• Parses natural language goals\n" +
        "• Creates structured task plans\n" +
        "• Coordinates with specialized CRM agents\n" +
        "• Shows real-time A2A communication\n" +
        "• Provides comprehensive results"
    )


if __name__ == "__main__":
    try:
        asyncio.run(demo_mansion_ridge_chat())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
