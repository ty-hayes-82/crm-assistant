"""
Chat Interface for Project Manager Agent
Displays A2A communication as a real-time chat thread
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum


class MessageType(Enum):
    USER = "user"
    PROJECT_MANAGER = "project_manager"
    CRM_AGENT = "crm_agent"
    SYSTEM = "system"


class ChatMessage:
    def __init__(self, sender: MessageType, content: str, timestamp: datetime = None, metadata: Dict = None):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def format(self) -> str:
        """Format message for display"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        
        # Color and emoji mapping for different senders
        sender_config = {
            MessageType.USER: {"emoji": "👤", "color": "\033[94m", "name": "User"},
            MessageType.PROJECT_MANAGER: {"emoji": "🎯", "color": "\033[92m", "name": "Project Manager"},
            MessageType.CRM_AGENT: {"emoji": "🤖", "color": "\033[93m", "name": "CRM Agent"},
            MessageType.SYSTEM: {"emoji": "⚙️", "color": "\033[90m", "name": "System"}
        }
        
        config = sender_config[self.sender]
        reset_color = "\033[0m"
        
        # Format the message
        formatted = f"{config['color']}[{time_str}] {config['emoji']} {config['name']}: {self.content}{reset_color}"
        
        # Add metadata if present
        if self.metadata:
            formatted += f"\n{config['color']}   📋 Metadata: {self.metadata}{reset_color}"
        
        return formatted


class ChatInterface:
    """Interactive chat interface for Project Manager Agent"""
    
    def __init__(self):
        self.messages: List[ChatMessage] = []
        self.is_active = True
    
    def add_message(self, sender: MessageType, content: str, metadata: Dict = None):
        """Add a message to the chat"""
        message = ChatMessage(sender, content, metadata=metadata)
        self.messages.append(message)
        self.display_message(message)
    
    def display_message(self, message: ChatMessage):
        """Display a single message"""
        print(message.format())
    
    def display_separator(self, title: str = None):
        """Display a visual separator"""
        if title:
            print(f"\n{'='*20} {title} {'='*20}")
        else:
            print("-" * 60)
    
    def get_user_input(self, prompt: str = "Enter your goal") -> str:
        """Get input from user with formatted prompt"""
        self.add_message(MessageType.SYSTEM, prompt)
        user_input = input("\n👤 You: ")
        self.add_message(MessageType.USER, user_input)
        return user_input
    
    def show_task_progress(self, tasks: List[Dict], current_task: str = None):
        """Show task progress in chat format"""
        progress_msg = "📋 Current Project Tasks:\n"
        for i, task in enumerate(tasks, 1):
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌"
            }
            emoji = status_emoji.get(task.get("status", "pending"), "⏳")
            task_name = task.get("name", f"Task {i}")
            progress_msg += f"   {emoji} {task_name}\n"
        
        if current_task:
            progress_msg += f"\n🎯 Currently executing: {current_task}"
        
        self.add_message(MessageType.PROJECT_MANAGER, progress_msg)
    
    def show_agent_communication(self, from_agent: str, to_agent: str, message: str, response: str = None):
        """Show communication between agents"""
        # Show outgoing message
        self.add_message(
            MessageType.PROJECT_MANAGER, 
            f"📤 Sending to {to_agent}: {message}",
            metadata={"target_agent": to_agent, "action": "send"}
        )
        
        # Show response if provided
        if response:
            agent_type = MessageType.CRM_AGENT if "crm" in to_agent.lower() else MessageType.SYSTEM
            self.add_message(
                agent_type,
                f"📥 Response: {response}",
                metadata={"source_agent": to_agent, "action": "response"}
            )
    
    def show_project_summary(self, result: Dict[str, Any]):
        """Show final project summary"""
        self.display_separator("PROJECT COMPLETE")
        
        status_emoji = "✅" if result.get("status") == "completed" else "❌"
        summary = f"{status_emoji} Project Status: {result.get('status', 'unknown')}\n"
        summary += f"📊 Progress: {result.get('progress', 0):.1f}%\n"
        summary += f"📋 Tasks: {result.get('completed_tasks', 0)}/{result.get('total_tasks', 0)} completed"
        
        if result.get('failed_tasks', 0) > 0:
            summary += f"\n⚠️ Failed tasks: {result.get('failed_tasks', 0)}"
        
        self.add_message(MessageType.PROJECT_MANAGER, summary)
        
        # Show detailed results
        if 'task_results' in result:
            self.add_message(MessageType.PROJECT_MANAGER, "📝 Detailed Results:")
            for task_id, task_result in result['task_results'].items():
                if 'error' in task_result:
                    self.add_message(MessageType.SYSTEM, f"❌ {task_id}: {task_result['error']}")
                else:
                    success_msg = f"✅ {task_id}: Success"
                    if 'management_company' in task_result:
                        success_msg += f" - Management Company: {task_result['management_company']}"
                    if 'companies' in task_result:
                        success_msg += f" - Found {len(task_result['companies'])} companies"
                    self.add_message(MessageType.CRM_AGENT, success_msg)
    
    def clear_screen(self):
        """Clear the screen (optional)"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def start_session(self):
        """Start an interactive chat session"""
        self.clear_screen()
        self.display_separator("PROJECT MANAGER AGENT - CHAT INTERFACE")
        
        self.add_message(
            MessageType.PROJECT_MANAGER,
            "Hello! I'm your Project Manager Agent. I can orchestrate complex CRM tasks by coordinating with specialized agents."
        )
        
        self.add_message(
            MessageType.PROJECT_MANAGER,
            "I can help you with goals like:\n" +
            "• 'Find all golf clubs in Arizona and enrich their records'\n" +
            "• 'Analyze The Golf Club at Mansion Ridge and set up management company'\n" +
            "• 'Review HubSpot data and enrich missing fields'"
        )
        
        return self.get_user_input("What would you like me to help you accomplish?")


# Utility functions for chat formatting
def format_agent_response(agent_name: str, response: Dict[str, Any]) -> str:
    """Format agent response for chat display"""
    if 'error' in response:
        return f"❌ Error: {response['error']}"
    
    # Format based on response type
    if 'companies' in response:
        companies = response['companies']
        if len(companies) == 1:
            company = companies[0]
            return f"✅ Found company: {company.get('name', 'Unknown')} - {company.get('city', '')}, {company.get('state', '')}"
        else:
            return f"✅ Found {len(companies)} companies"
    
    if 'management_company' in response:
        mgmt = response['management_company']
        score = response.get('match_score', 0)
        return f"✅ Identified management company: {mgmt} (confidence: {score}%)"
    
    if 'status' in response:
        return f"✅ Task completed with status: {response['status']}"
    
    # Default formatting
    return f"✅ Task completed successfully"


def simulate_typing_delay(text: str, delay_per_char: float = 0.02):
    """Simulate typing delay for more realistic chat feel"""
    import time
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay_per_char)
    print()  # New line at the end
