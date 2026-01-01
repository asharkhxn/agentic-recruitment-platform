from agent.state import AgentState
from agent.utils.llm import llm
from agent.utils.safety import contains_dangerous_keywords
from agent.prompts.loader import format_prompt


async def general_response_node(state: AgentState) -> AgentState:
    """Handle general queries."""
    message = state.get("message", "")
    
    # Safety check: if dangerous keywords detected, provide safety warning
    if contains_dangerous_keywords(message):
        if any(word in message.lower() for word in ["job", "data", "record", "entry"]):
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
    
    # Normal general response
    prompt = format_prompt("general_response.md", message=message)
    response = llm.invoke(prompt)
    state["response"] = response.content
    return state

