from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from agent.prompts.loader import format_prompt
from agent.state import AgentState
from agent.tools.job_tools import create_job
from agent.utils.llm import llm
from agent.utils.session import (
    get_pending_job,
    store_pending_job,
    clear_pending_job,
)

REQUIRED_FIELDS = ("title", "location")
DISPLAY_FIELDS = ("title", "location", "salary", "description", "requirements")
DEFAULT_REQUIREMENTS = "3+ years of relevant experience and strong communication skills."
INTENT_KEYWORDS = (
    # Direct job creation phrases
    "create a job",
    "post a job",
    "add a job",
    "create job",
    "post job",
    "job posting",
    "role posting",
    "new job",
    "another job",
    "create a new one",
    # Role-based phrases
    "create a role",
    "post a role",
    "add a role",
    "create role",
    "post role",
    "new role",
    # Natural language phrases
    "please post",
    "please create",
    "post an",
    "create an",
    "posting for",
    "role for",
    "role in",
    "position in",
    "position for",
    "hiring for",
    "hiring a",
    "we need a",
    "looking to hire",
    # With job titles - common patterns
    "coordinator role",
    "technician role",
    "developer role",
    "engineer role",
    "manager role",
    "analyst role",
    "specialist role",
)


def _safe_json_loads(blob: str) -> Dict[str, Any]:
    if not blob:
        return {}
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        start = blob.find("{")
        end = blob.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(blob[start : end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _looks_like_job_request(message: str) -> bool:
    lower = message.lower()
    return any(keyword in lower for keyword in INTENT_KEYWORDS)


def _is_follow_up_confirmation(message: str) -> bool:
    """Check if the message is a follow-up confirmation like 'yes', 'sure', 'go ahead'."""
    confirmations = [
        "yes", "yes please", "sure", "ok", "okay", "please", "go ahead",
        "do it", "continue", "proceed", "confirm", "that's correct",
        "that works", "sounds good", "perfect", "great", "yep", "yeah"
    ]
    lower = message.lower().strip()
    # Check exact match or starts with common confirmations
    return (
        lower in confirmations or
        lower.startswith("yes") or
        lower.startswith("sure") or
        lower.startswith("go ahead")
    )


def _is_providing_missing_info(message: str, pending_job: Dict[str, Optional[str]]) -> bool:
    """Check if the message is providing missing info for a pending job."""
    # If we have a pending job with missing fields, any message that doesn't
    # look like a new request is likely providing missing info
    if not pending_job:
        return False
    # Don't treat it as missing info if it's clearly a new job request
    if _looks_like_job_request(message):
        return False
    return True


def _augment_with_heuristics(job: Dict[str, Optional[str]], message: str) -> Dict[str, Optional[str]]:
    # Requirements: capture common "need/require" phrasing if LLM missed it
    if not job.get("requirements"):
        req_match = re.search(
            r"(?:need|requires?|must have|looking for)\s+([^\.\n]+)",
            message,
            re.IGNORECASE,
        )
        if req_match:
            job["requirements"] = req_match.group(1).strip().rstrip(".,")

    # Location (e.g., "in Seattle" or "based in London")
    if not job.get("location"):
        match = re.search(r"(?:in|based in|located in)\s+([A-Z][\w\s,]+)", message, re.IGNORECASE)
        if match:
            job["location"] = match.group(1).strip()

    if not job.get("salary"):
        match = re.search(r"([£$€])\s?(\d{2,3})(?:k|,?\d{3})?", message)
        if match:
            currency, amount = match.groups()
            suffix = "k" if len(amount) <= 3 else ""
            job["salary"] = f"{currency}{amount}{suffix}"

    if not job.get("title"):
        match = re.search(r"(?:for|create)\s+(?:a\s+)?([A-Za-z][\w\s\-/]+?)(?:\s+role|\s+job|\s+position|[,\.])", message, re.IGNORECASE)
        if match:
            job["title"] = match.group(1).strip().title()

    return job


def _ensure_defaults(job: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    title = job.get("title")
    location = job.get("location")
    requirements = job.get("requirements")
    description = job.get("description")

    if title and not requirements:
        job["requirements"] = DEFAULT_REQUIREMENTS

    if title and not description:
        focus = requirements or "daily responsibilities"
        place = location or "our team"
        job["description"] = f"We are seeking a {title} based in {place}. The role focuses on {focus}."

    return job


def _missing_fields_response(job: Dict[str, Optional[str]], missing: list[str]) -> str:
    prompts = {
        "title": "What's the job title (e.g., 'Operations Coordinator')?",
        "description": "Share a 1-2 sentence summary of the role's responsibilities.",
        "requirements": "List key requirements (experience, skills, certifications).",
        "location": "Where is the role based (city/country or Remote)?",
    }
    lines = ["I still need a few details before I can post the job:"]
    for field in missing:
        guidance = prompts.get(field, "Please provide this detail.")
        lines.append(f"• {field.capitalize()}: {guidance}")
    lines.append("Please reply with the missing info in one message.")
    return "\n".join(lines)


def _success_response(job: Dict[str, Optional[str]]) -> str:
    parts = ["✅ **Job Created Successfully!**\n"]
    if job.get("title"):
        parts.append(f"📋 **{job['title']}**")
    if job.get("location"):
        salary = f" — Salary: {job['salary']}" if job.get("salary") else ""
        parts.append(f"📍 **Location:** {job['location']}{salary}")
    parts.append("")
    parts.append("**Job Description:**")
    parts.append(job.get("description") or "Description provided upon request.")
    parts.append("")
    parts.append("**Requirements:**")
    parts.append(job.get("requirements") or DEFAULT_REQUIREMENTS)
    return "\n".join(parts)


async def create_job_node(state: AgentState) -> AgentState:
    """Create a job posting using structured extraction and simple validation.
    
    This node handles:
    1. New job creation requests with all details -> creates immediately
    2. New job requests with missing details -> asks for missing info, stores pending
    3. Follow-up messages providing missing info -> merges and creates
    """

    message = state.get("message", "").strip()
    conversation_id = state.get("conversation_id", "")
    
    if not message:
        state["response"] = "Please provide the job details you'd like me to post."
        return state

    # Check for pending job from previous interaction
    pending_job = get_pending_job(conversation_id) if conversation_id else None
    
    # Handle follow-up providing missing information for a pending job
    if pending_job and not _looks_like_job_request(message):
        # User is providing missing info for a pending job
        # Try to extract the missing fields from this message
        try:
            prompt = format_prompt("extract_job_details.md", message=message)
            llm_response = llm.invoke(prompt)
            extracted = _safe_json_loads(getattr(llm_response, "content", ""))
        except Exception:
            extracted = {}
        
        # Merge new info with pending job
        for field in ["title", "description", "requirements", "location", "salary"]:
            new_val = _clean(extracted.get(field))
            if new_val:
                pending_job[field] = new_val
        
        # Also try heuristics on the new message
        pending_job = _augment_with_heuristics(pending_job, message)
        pending_job = _ensure_defaults(pending_job)
        
        # Check if we now have all required fields
        missing = [field for field in REQUIRED_FIELDS if not pending_job.get(field)]
        if missing:
            # Still missing info, store updated pending and ask again
            store_pending_job(conversation_id, pending_job)
            state["response"] = _missing_fields_response(pending_job, missing)
            return state
        
        # We have all required fields now, create the job
        job = pending_job
        clear_pending_job(conversation_id)
    else:
        # New job creation request - check for intent
        if not _looks_like_job_request(message):
            state["response"] = (
                "I didn't detect a job creation request. Ask me to create a role by sharing the title, "
                "location, and a brief overview."
            )
            return state

        # Extract job details from message
        try:
            prompt = format_prompt("extract_job_details.md", message=message)
            llm_response = llm.invoke(prompt)
            extracted = _safe_json_loads(getattr(llm_response, "content", ""))
        except Exception:
            extracted = {}

        job: Dict[str, Optional[str]] = {
            "title": _clean(extracted.get("title")),
            "description": _clean(extracted.get("description")),
            "requirements": _clean(extracted.get("requirements")),
            "location": _clean(extracted.get("location")),
            "salary": _clean(extracted.get("salary")),
        }

        job = _augment_with_heuristics(job, message)

        if not any(job.values()):
            state["response"] = (
                "I couldn't detect job creation details in that message. "
                "Share the title, location, and key details so I can post it."
            )
            return state

        job = _ensure_defaults(job)

        missing = [field for field in REQUIRED_FIELDS if not job.get(field)]
        if missing:
            # Store as pending job and ask for missing info
            if conversation_id:
                store_pending_job(conversation_id, job)
            state["response"] = _missing_fields_response(job, missing)
            return state

    # We have all required fields - create the job directly (no confirmation needed)
    tool_args = {
        "title": job["title"],
        "description": job["description"],
        "requirements": job["requirements"],
        "location": job["location"],
        "salary": job.get("salary"),
        "user_id": state["user_id"],
    }

    state["tool_name"] = "create_job"
    state["tool_args"] = tool_args

    try:
        result = await create_job(**tool_args)
        state["tool_result"] = str(result)
    except Exception as exc:
        state["tool_result"] = f"Error: {exc}"
        state["response"] = (
            "I parsed the job request but couldn't save it. "
            f"Error: {exc}. Please try again."
        )
        return state

    if isinstance(result, dict) and result.get("error"):
        payload = json.dumps({k: v for k, v in job.items() if k != "salary" or v}, indent=2)
        state["response"] = (
            "I extracted the job details but couldn't persist them automatically. "
            f"Error: {result['error']}\n\nYou can POST this JSON to /jobs as a recruiter:\n{payload}"
        )
        return state

    state["response"] = _success_response(job)

    return state

