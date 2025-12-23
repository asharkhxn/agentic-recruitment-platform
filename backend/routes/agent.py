from fastapi import APIRouter, HTTPException
from core.models import ChatMessage, ChatResponse
from agent.graph import run_agent
import uuid

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with AI agent - uses user_id from the request to track job creation."""
    try:
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Use the user_id from the message to track who is creating jobs
        result = await run_agent(
            message.message,
            user_id=message.user_id,
            conversation_id=conversation_id
        )
        
        return ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            sql_generated=result.get("sql_generated")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
