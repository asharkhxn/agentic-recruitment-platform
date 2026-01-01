from agent.state import AgentState
from agent.graph import agent_graph
from agent.utils.rate_limit import check_rate_limit
from agent.utils.session import persist_chat_message, load_recent_messages, summarize_messages_if_needed
from agent.utils.normalization import normalize_synonyms
from agent.utils.llm import llm
from agent.prompts.loader import load_prompt
from core.config import get_supabase_client


# Load system prompt
SYSTEM_PROMPT = load_prompt("system_prompt.md")


async def run_agent(message: str, user_id: str, conversation_id: str) -> dict:
    """Run the agent with a message."""
    # Check rate limit
    if not check_rate_limit(user_id):
        return {
            "response": "You've made too many requests recently. Please wait a moment before trying again."
        }

    initial_state = AgentState(
        message=message,
        response="",
        tool_name=None,
        tool_args=None,
        tool_result=None,
        sql_generated=None,
        user_id=user_id,
        conversation_id=conversation_id
    )
    
    # Persist incoming user message
    persist_chat_message(conversation_id, user_id, "user", message)

    # Load recent history and produce a short summary (rolling context)
    recent = load_recent_messages(conversation_id, limit=12)
    summary = summarize_messages_if_needed(conversation_id, recent, threshold=6, llm=llm)

    # Normalize synonyms in the incoming message (helps routing)
    normalized = normalize_synonyms(message)

    # If we have a summary, prepend it to the message to reduce tokens vs full history
    if summary:
        initial_state["message"] = f"CONTEXT_SUMMARY:\n{summary}\n\nUser: {normalized}"
    else:
        initial_state["message"] = normalized

    # Cache a light system prompt (avoid resending large static instructions)
    initial_state["system_prompt"] = SYSTEM_PROMPT

    # Use ainvoke for async nodes with LangSmith metadata
    # LangSmith will automatically trace this execution
    result = await agent_graph.ainvoke(
        initial_state,
        config={
            "metadata": {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message_preview": message[:100] if len(message) > 100 else message
            },
            "tags": ["recruitment-agent", "chatbot"]
        }
    )

    assistant_response = result.get("response", "")

    # Store last intent for context (infer from response or routing)
    # This helps with follow-up messages
    last_intent = result.get("last_intent")
    if last_intent:
        initial_state["last_intent"] = last_intent

    # Persist assistant response
    persist_chat_message(conversation_id, user_id, "assistant", assistant_response)

    # Also log search queries separately (best-effort)
    try:
        supabase = get_supabase_client()
        supabase.table("ai_search_logs").insert({
            "user_id": user_id,
            "query": message,
            "sql_generated": result.get("sql_generated")
        }).execute()
    except:
        pass

    return {
        "response": assistant_response
    }

