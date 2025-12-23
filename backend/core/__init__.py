"""Core utilities for the backend service."""

from .auth import verify_jwt, verify_recruiter, require_role
from .config import get_supabase_client, get_supabase_anon_client, Config
from .models import (
    User,
    Job,
    JobCreate,
    Application,
    ApplicationCreate,
    ChatMessage,
    ChatResponse,
    RankedApplicant,
    ATSRankingRequest,
    ATSRankingResponse,
)

__all__ = [
    "verify_jwt",
    "verify_recruiter",
    "require_role",
    "get_supabase_client",
    "get_supabase_anon_client",
    "Config",
    "User",
    "Job",
    "JobCreate",
    "Application",
    "ApplicationCreate",
    "ChatMessage",
    "ChatResponse",
    "RankedApplicant",
    "ATSRankingRequest",
    "ATSRankingResponse",
]
