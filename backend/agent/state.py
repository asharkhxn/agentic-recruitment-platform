from typing import TypedDict, NotRequired


class AgentState(TypedDict):
    """State for the agent graph."""
    message: str
    response: str
    tool_name: str | None
    tool_args: dict | None
    tool_result: str | None
    sql_generated: str | None
    user_id: str
    conversation_id: str
    last_intent: NotRequired[str | None]  # Track last routing decision for context
    system_prompt: NotRequired[str | None]  # System prompt for LLM

