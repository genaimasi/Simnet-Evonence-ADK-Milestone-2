# File: agent.py
# ==============
"""Main agent definition with BigQuery logging callbacks"""

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from .prompts import SIMNET_INSTRUCTION
from .bigquery_logger import ConversationLogger
import time
import uuid
from typing import Optional

# Global logging state
_logger = None
_start_time = None
_current_query = None
_session_id = None
_has_image = False

def get_logger():
    """Lazy initialization of BigQuery logger"""
    global _logger
    if _logger is None:
        try:
            _logger = ConversationLogger()
            print("✓ Logger initialized")
        except Exception as e:
            print(f"✗ Logger failed: {e}")
    return _logger

def before_model_callback(
    callback_context: CallbackContext, 
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Called before LLM call - captures query and session info
    """
    global _start_time, _current_query, _session_id, _has_image
    
    _start_time = time.time()
    _has_image = False
    
    # Get or create session ID using callback state
    try:
        state = callback_context.state
        if 'logging_session_id' not in state:
            _session_id = str(uuid.uuid4())
            state['logging_session_id'] = _session_id
        else:
            _session_id = state['logging_session_id']
    except Exception:
        if _session_id is None:
            _session_id = str(uuid.uuid4())
    
    # Extract user query from LLM request
    _current_query = ""
    
    try:
        if llm_request.contents:
            for content in reversed(llm_request.contents):
                if content.role == 'user' and content.parts:
                    text_parts = []
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                        if hasattr(part, 'inline_data') or hasattr(part, 'file_data'):
                            _has_image = True
                    
                    _current_query = " ".join(text_parts)
                    break
        
        if not _current_query:
            _current_query = "Empty query"
    
    except Exception as e:
        _current_query = f"Error: {str(e)}"
    
    print(f"🔵 Session: {_session_id[:12]} | Query: {_current_query[:80]}")
    
    return None

def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Called after LLM response - logs to BigQuery
    """
    global _start_time, _current_query, _session_id, _has_image
    
    if _start_time is None:
        return None
    
    response_time_ms = (time.time() - _start_time) * 1000
    
    # Extract agent response
    agent_response = ""
    try:
        if llm_response.content and llm_response.content.parts:
            text_parts = [
                part.text for part in llm_response.content.parts 
                if hasattr(part, 'text') and part.text
            ]
            agent_response = " ".join(text_parts) if text_parts else "Empty response"
    except Exception as e:
        agent_response = f"Error: {str(e)}"
    
    # Log to BigQuery
    logger = get_logger()
    if logger and _session_id and _current_query:
        try:
            logger.log_conversation(
                session_id=_session_id,
                user_query=_current_query,
                agent_response=agent_response,
                agent_name=callback_context.agent_name,
                has_image_input=_has_image,
                response_time_ms=response_time_ms,
                model_used="gemini-2.5-pro",
                metadata={"status": "success", "source": "adk_web"}
            )
            print(f"✅ Logged | Session: {_session_id[:12]} | {response_time_ms:.0f}ms")
        except Exception as e:
            print(f"✗ Log failed: {e}")
    
    _start_time = None
    
    return None

# Initialize agent with callbacks
root_agent = Agent(
    name="SimnetAgent",
    model="gemini-2.5-pro",
    description="Agent for designing drones, aircraft, and similar systems.",
    instruction=SIMNET_INSTRUCTION,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback
)

print("🚀 SimnetAgent with BigQuery logging ready")