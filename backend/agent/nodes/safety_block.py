from agent.state import AgentState
from agent.utils.safety import contains_dangerous_keywords
from agent.prompts.loader import format_prompt


async def safety_block_node(state: AgentState) -> AgentState:
    """Block dangerous operations and return safety warning."""
    message = state.get("message", "").lower()
    
    # Detect what operation was attempted
    operation = "perform that operation"
    if any(word in message for word in ["delete", "remove"]):
        operation = "delete or remove data"
    elif any(word in message for word in ["update", "modify", "change", "edit"]):
        operation = "update or modify data"
    else:
        operation = "perform that operation"
    
    # Generate safety warning
    try:
        warning = format_prompt("safety_warning.md", operation=operation)
        state["response"] = warning
    except Exception:
        # Fallback message if prompt loading fails
        state["response"] = (
            "I understand you'd like to perform that operation, but I cannot perform "
            "delete, update, modify, or any data modification operations through the chatbot "
            "for security reasons.\n\n"
            "For data modification operations, please use the admin dashboard or contact your system administrator.\n\n"
            "I can help you with:\n"
            "- Creating new job postings\n"
            "- Searching and viewing jobs\n"
            "- Viewing applicants\n"
            "- Ranking candidates with ATS\n\n"
            "Is there something else I can help you with?"
        )
    
    return state

