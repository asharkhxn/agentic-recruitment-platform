from datetime import datetime, timezone
from core.config import get_supabase_client

# In-memory fallback store for sessions (conversation_id -> list of messages)
SESSION_STORE: dict[str, list[dict]] = {}
# Short summaries cache per session
SESSION_SUMMARIES: dict[str, str] = {}
# Pending job details awaiting confirmation (session_id -> job dict)
PENDING_JOBS: dict[str, dict] = {}


def store_pending_job(session_id: str, job_details: dict):
    """Store pending job details for a session awaiting confirmation."""
    PENDING_JOBS[session_id] = job_details


def get_pending_job(session_id: str) -> dict | None:
    """Retrieve pending job details for a session."""
    return PENDING_JOBS.get(session_id)


def clear_pending_job(session_id: str):
    """Clear pending job details after creation or cancellation."""
    PENDING_JOBS.pop(session_id, None)


def persist_chat_message(session_id: str, user_id: str, role: str, content: str):
    """Persist a chat message to Supabase if available, else store in-memory."""
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        supabase = get_supabase_client()
        supabase.table("chat_messages").insert({
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": timestamp
        }).execute()
    except Exception:
        SESSION_STORE.setdefault(session_id, []).append({
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": timestamp
        })


def load_recent_messages(session_id: str, limit: int = 12) -> list[dict]:
    """Load recent messages for a session from Supabase or in-memory store."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(limit).execute()
        if response.data:
            return list(reversed(response.data))
    except Exception:
        pass
    return SESSION_STORE.get(session_id, [])[-limit:]


def summarize_messages_if_needed(session_id: str, messages: list[dict], threshold: int = 6, llm=None) -> str | None:
    """Return a short summary if conversation is long, cache per session."""
    if session_id in SESSION_SUMMARIES:
        return SESSION_SUMMARIES[session_id]
    if len(messages) <= threshold:
        return None
    combined = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages[-threshold:]])
    from agent.prompts.loader import format_prompt
    prompt = format_prompt("conversation_summary.md", conversation=combined)
    try:
        if llm is not None:
            resp = llm.invoke(prompt)
            summary = (resp.content or "").strip()
            if summary:
                SESSION_SUMMARIES[session_id] = summary
                return summary
    except Exception:
        return None
    return None


def get_last_intent(session_id: str) -> str | None:
    """Get the last intent/routing decision from conversation history."""
    # First, check if there's a pending job - if so, route to create_job_tool
    if session_id in PENDING_JOBS:
        return "create_job_tool"
    
    try:
        messages = load_recent_messages(session_id, limit=5)
        # Look for assistant messages that indicate what action was taken
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                content = msg.get("content", "").lower()
                # Check for pending job creation (asking for missing info)
                if "need a few details" in content or "before i can post" in content:
                    return "create_job_tool"
                # Try to infer intent from response patterns
                if "job created" in content or "create" in content:
                    return "create_job_tool"
                elif "found" in content and "job" in content:
                    return "search_jobs_tool"
                elif "applicant" in content or "candidate" in content:
                    if "rank" in content or "score" in content:
                        return "rank_tool"
                    return "get_applicants_tool"
        return None
    except Exception:
        return None


def is_follow_up_message(message: str) -> bool:
    """Check if message is a follow-up (yes, sure, ok, etc.)."""
    follow_ups = ["yes", "yes please", "sure", "ok", "okay", "please", "go ahead", "do it", "continue"]
    message_lower = message.lower().strip()
    return message_lower in follow_ups or message_lower.startswith("yes") or message_lower.startswith("sure")

