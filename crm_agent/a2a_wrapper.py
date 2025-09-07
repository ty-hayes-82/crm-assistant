"""
A2A wrapper for CRM agent following Google's A2A framework guide.
Implements the invoke method pattern for proper agent-to-agent communication.
"""

import asyncio
import uuid
from typing import AsyncIterable, Dict, Any
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from .coordinator import create_crm_coordinator


class CRMAgentA2AWrapper:
    """
    A2A-compatible wrapper for the CRM agent following Google's guide.
    Implements the invoke method pattern for agent-to-agent communication.
    """
    
    def __init__(self):
        """Initialize the CRM agent wrapper with proper A2A support"""
        self.crm_agent = create_crm_coordinator()
        self._user_id = "a2a_user"
        
        # Initialize the Runner for proper ADK execution
        self._runner = Runner(
            app_name="crm_a2a_agent",
            agent=self.crm_agent,
            session_service=InMemorySessionService()
        )
    
    async def invoke(self, query: str, session_id: str) -> AsyncIterable[Dict[str, Any]]:
        """
        Entry point for A2A communication following Google's guide.
        
        This method is called by other agents and yields streaming updates.
        """
        try:
            # Create proper content object for the message
            from google.adk.events import Event
            
            # Create a simple content object (avoiding complex type imports)
            content_obj = type('Content', (), {
                'parts': [type('Part', (), {'text': query})]
            })()
            
            # Track if we've sent any updates
            has_sent_update = False
            
            # Run the CRM agent using the Runner
            events = self._runner.run(
                user_id=self._user_id,
                session_id=session_id,
                new_message=content_obj
            )
            
            # Process events and yield A2A-compatible responses
            result_text = ""
            for event in events:
                # Send progress updates
                if not has_sent_update:
                    yield {'is_task_complete': False, 'updates': "Processing CRM request..."}
                    has_sent_update = True
                
                # Collect the final response
                if hasattr(event, 'content'):
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                result_text += part.text
                    elif hasattr(event.content, 'text'):
                        result_text += event.content.text
                elif hasattr(event, 'text'):
                    result_text += event.text
            
            # Yield the final result
            final_response = result_text or "CRM task completed successfully"
            yield {'is_task_complete': True, 'content': final_response}
            
        except Exception as e:
            # Yield error response
            error_message = f"CRM agent error: {str(e)}"
            yield {'is_task_complete': True, 'content': error_message, 'error': True}


def create_crm_a2a_agent():
    """Create an A2A-compatible CRM agent"""
    return CRMAgentA2AWrapper()
