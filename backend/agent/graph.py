from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from core.config import Config, get_supabase_client
from agent.tools import TOOLS
import json


# In-memory fallback store for sessions (conversation_id -> list of messages)
SESSION_STORE: dict[str, list[dict]] = {}
# Short summaries cache per session
SESSION_SUMMARIES: dict[str, str] = {}

# Simple synonym map for recruiter queries
SYNONYMS = {
    "role": ["job", "position", "opening", "vacancy"],
    "applicant": ["candidate", "person"]
}

# Cached system prompt to avoid re-sending static instructions
SYSTEM_PROMPT = (
    "You are a concise AI recruitment assistant. Answer briefly, ask clarifying questions when needed, "
    "and prefer JSON structured outputs for tool-invocations."
)


llm = ChatGroq(api_key=Config.GROQ_API_KEY, model="llama-3.3-70b-versatile")



import re
import time
from datetime import datetime, timezone
from collections import defaultdict

# Rate limiting store and settings
RATE_LIMIT_STORE: defaultdict[str, list] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 50  # requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds


def check_rate_limit(user_id: str) -> bool:
    """Check if user is within rate limits. Returns True if allowed, False if blocked."""
    now = time.time()
    user_requests = RATE_LIMIT_STORE[user_id]
    # Remove old requests outside the window
    user_requests[:] = [req_time for req_time in user_requests if now - req_time < RATE_LIMIT_WINDOW]
    if len(user_requests) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    user_requests.append(now)
    return True


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
    prompt = f"Summarize the following conversation in 2-3 short bullet points for context:\n\n{combined}\n\nSummary:"
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

def normalize_synonyms(text: str) -> str:
    """Replace simple synonyms with canonical terms to help routing and tooling."""
    lower = text.lower()
    for canonical, variants in SYNONYMS.items():
        for v in variants:
            lower = re.sub(rf"\b{re.escape(v)}\b", canonical, lower)
    return lower






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


async def search_jobs_node(state: AgentState) -> AgentState:
    """Search jobs using structured filters."""
    try:
        extraction_prompt = f"""Extract job search filters from this request: "{state['message']}"

Look for:
- Keywords: job titles, skills, or company types (e.g., "CTO", "software engineering", "startup")
- Location: cities, states, countries, or "remote" (e.g., "San Francisco", "New York", "remote")
- Salary: salary ranges, amounts, or conditions (e.g., "100k", "over 100k", "$150,000", "competitive")

Return a JSON object with:
{{
  "keywords": "<job-related keywords or empty string>",
  "location": "<location or empty string>", 
  "salary": "<salary requirement or empty string>"
}}

Examples:
- "CTO jobs over 100k in San Francisco" → {{"keywords": "CTO", "location": "San Francisco", "salary": "over 100k"}}
- "Find software engineering roles" → {{"keywords": "software engineering", "location": "", "salary": ""}}
- "Remote jobs paying 150k" → {{"keywords": "", "location": "remote", "salary": "150k"}}

Respond with JSON only."""

        response = llm.invoke(extraction_prompt)
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        filters = {"keywords": "", "location": "", "salary": ""}
        if json_match:
            filters.update(json.loads(json_match.group()))

        # Normalize filters
        for key, value in list(filters.items()):
            if isinstance(value, str):
                filters[key] = value.strip()

        # If everything empty, treat entire message as keywords to avoid empty query
        if not any(filters.values()):
            filters["keywords"] = state["message"].strip()

        from agent.tools import search_jobs
        result = await search_jobs(
            keywords=filters.get("keywords") or None,
            location=filters.get("location") or None,
            salary=filters.get("salary") or None,
        )

        if isinstance(result, dict) and "error" in result:
            # Surface a short, safe error message to help debugging without leaking internals
            err = str(result.get("error") or "unknown error")
            short = (err[:300] + "...") if len(err) > 300 else err
            state["response"] = f"I couldn't search the jobs just now. Error: {short} Please try again in a moment."
            return state

        if not result:
            state["response"] = "I didn't find any roles matching those filters. Try tweaking the title, location, or salary range."
            return state

        message_lines = [f"🔍 **Found {len(result)} job{'s' if len(result) != 1 else ''}**", ""]
        for job in result[:5]:
            title = job.get("title", "Untitled role")
            location = job.get("location") or "Location flexible"
            salary = job.get("salary") or "Salary TBD"
            summary = job.get("description", "").strip()
            summary = summary[:160] + ("…" if len(summary) > 160 else "")
            message_lines.append(f"• **{title}** — {location}\n  💰 {salary}\n  ✏️ {summary}")

        if len(result) > 5:
            message_lines.append(f"\n…and {len(result) - 5} more matching job{'s' if len(result) - 5 != 1 else ''}.")

        state["response"] = "\n\n".join(message_lines)
    except Exception:
        state["response"] = "I ran into an issue pulling the job listings. Could you rephrase the request or try again shortly?"

    return state


def route_query(state: AgentState) -> str:
    """Determine which tool to use based on the query."""
    message = state["message"].lower()
    
    # Prioritize job creation - check first
    if any(word in message for word in ["create job", "post job", "new job", "add job", "create a job", "post a job"]):
        return "create_job_tool"
    job_search_triggers = [
        "view jobs",
        "view job",
        "show jobs",
        "show job",
        "jobs in",
        "roles in",
        "find job",
        "find jobs",
        "find roles",
        "job summary",
        "job details",
        "available roles",
        "openings",
        "vacancies",
        "salary",
        "location"
    ]
    if any(trigger in message for trigger in job_search_triggers) and "create job" not in message:
        return "search_jobs_tool"
    elif any(word in message for word in ["rank", "shortlist", "ats", "score"]):
        return "rank_tool"
    elif any(word in message for word in ["applicants", "applications", "candidates"]):
        return "get_applicants_tool"
    elif any(word in message for word in ["summarize cv", "cv summary"]):
        return "summarize_tool"
    elif any(word in message for word in ["generate description", "write description"]):
        return "generate_description_tool"
    elif any(word in message for word in ["query", "search", "find", "show me", "get all", "list"]):
        return "sql_tool"
    else:
        return "general_response"


async def create_job_node(state: AgentState) -> AgentState:
    """Handle job creation using LLM to extract details."""
    try:
        prompt = f"""Extract job details from this request: "{state['message']}"

You are an expert at creating professional job postings. Extract and structure the information carefully.

REQUIRED FIELDS (must be provided):
- title: Clear, professional job title (e.g., "Senior Python Developer", not "dev job")
- description: 2-3 sentence professional description of the role and responsibilities
- requirements: Comma-separated list of specific skills/qualifications (e.g., "Python, Django, 5+ years experience")
- location: Specific work location (e.g., "London, UK" or "Remote")

OPTIONAL FIELDS:
- salary: Salary range or specific amount (e.g., "£50,000 - £70,000" or "Competitive")

IMPORTANT RULES:
- If any required field is missing or unclear, do not guess - ask the user to provide it
- Use professional language
- Be specific about requirements
- If the request is too vague, ask for clarification

Return ONLY a JSON object with the extracted fields. If information is missing, set the field to null.

JSON format:
{{
  "title": "extracted title or null",
  "description": "extracted description or null",
  "requirements": "extracted requirements or null",
  "location": "extracted location or null",
  "salary": "extracted salary or null"
}}
"""
        try:
            response = llm.invoke(prompt)
            content = response.content
        except Exception:
            # If the LLM call fails, proceed to heuristic fallback instead of aborting
            content = ""

        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        job_data = None
        if json_match:
            try:
                job_data = json.loads(json_match.group())
            except Exception:
                job_data = None

        # Fallback: if model did not return JSON, attempt heuristic extraction from the raw message
        if not job_data:
            # Try simple heuristics on the incoming user message to extract fields
            raw = state.get("message", "")
            # Remove any context summary prefix added earlier
            raw = re.sub(r"CONTEXT_SUMMARY:\n.*?\n\nUser:\s*", "", raw, flags=re.DOTALL)

            def extract_between(text, lefts, rights=None):
                for l in lefts:
                    m = re.search(rf"{re.escape(l)}\s*(.*?)($|\\.|;|,|\n)", text, re.IGNORECASE)
                    if m:
                        return m.group(1).strip()
                if rights:
                    for r in rights:
                        m = re.search(rf"(.*)\s*{re.escape(r)}", text, re.IGNORECASE)
                        if m:
                            return m.group(1).strip()
                return None

            title = None
            # Patterns like "Create a job for AI Engineer in Berlin"
            m = re.search(r"create (?:a )?job for\s+([\w\s\-\+\.,()]+?)\s+(?:in|based in)\s+([\w\s\-(),]+)", raw, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
                location = m.group(2).strip()
            else:
                # Try "Create a job for AI Engineer" without location
                m2 = re.search(r"create (?:a )?job for\s+([\w\s\-\+\.,()]+?)(?:\.|,|$)", raw, re.IGNORECASE)
                title = m2.group(1).strip() if m2 else None

            # Location fallback
            if 'location' not in locals():
                loc = extract_between(raw, ["in", "based in"])
                location = loc or ""

            # Salary extraction (e.g., €80k–€110k or 80k-110k)
            salary = None
            sal_match = re.search(r"€?\s?(\d{2,3})\s?k?\s*[–\-to]+\s*€?\s?(\d{2,3})\s?k?", raw, re.IGNORECASE)
            if sal_match:
                a = sal_match.group(1)
                b = sal_match.group(2)
                salary = f"€{a}k–€{b}k" if int(a) < 1000 and int(b) < 1000 else f"€{a}–€{b}"
            else:
                # other formats
                sal_simple = re.search(r"€\s?\d+[kK]?\b", raw)
                if sal_simple:
                    salary = sal_simple.group(0)

            # Requirements extraction: look for 'requires' or 'must have' or sentences starting with 'The role requires'
            req_text = None
            req_match = re.search(r"(?:requires|require|must have|must include|role requires|the role requires)[:\s]+(.+?)(?:\.|$)", raw, re.IGNORECASE)
            if req_match:
                req_text = req_match.group(1).strip()
            else:
                # try to pull common skills list from the end
                m_skills = re.search(r"(Python|TensorFlow|PyTorch|machine learning|deep learning|cloud).*", raw, re.IGNORECASE)
                req_text = m_skills.group(0).strip() if m_skills else None

            # Description extraction: sentence containing 'will work' or the sentence after the title
            desc = None
            desc_match = re.search(r"(The engineer will .*?\.|Responsibilities:? .*?\.)", raw, re.IGNORECASE)
            if desc_match:
                desc = desc_match.group(1).strip()
            else:
                # fallback to whole prompt if short
                desc = raw.strip()

            job_data = {
                "title": title or "AI Engineer",
                "description": desc or None,
                "requirements": req_text or None,
                "location": location or None,
                "salary": salary or None
            }

        # Check for missing required fields
        required_fields = ["title", "description", "requirements", "location"]
        missing = []
        for field in required_fields:
            value = job_data.get(field)
            if value is None or (isinstance(value, str) and str(value).strip().lower() in ["null", "none", "", "tbd", "n/a", "na", "unspecified"]):
                missing.append(field)

        if missing:
            missing_list = ", ".join(missing)
            state["response"] = (
                f"I need more information to create this job posting. Please provide details for: {missing_list}.\n\n"
                "For example: 'Create a Senior Python Developer job in London paying £60k-£80k with requirements for Django and React experience.'"
            )
            return state

        # Validate extracted data quality
        if len(job_data["title"]) < 3:
            state["response"] = "The job title seems too short. Please provide a more complete job title."
            return state

        if len(job_data["description"]) < 20:
            state["response"] = "The job description is too brief. Please provide a more detailed description of the role."
            return state

        # Create job
        from agent.tools import create_job
        try:
            result = await create_job(
                title=job_data["title"],
                description=job_data["description"],
                requirements=job_data["requirements"],
                location=job_data["location"],
                salary=job_data.get("salary"),
                user_id=state["user_id"]
            )
        except Exception as e:
            result = {"error": str(e)}

        if isinstance(result, dict) and result.get("error"):
            # If persistence failed (missing Supabase or other error), return a clear payload the caller can POST
            salary_info = f" with salary {job_data.get('salary')}" if job_data.get('salary') else ""
            payload = {
                "title": job_data.get("title"),
                "description": job_data.get("description"),
                "requirements": job_data.get("requirements"),
                "location": job_data.get("location"),
                "salary": job_data.get("salary")
            }
            state["response"] = (
                "I parsed the job details but couldn't persist the job to the database. "
                f"Error: {result.get('error')}\n\n"
                "You can create the job manually by POSTing the following JSON to the /jobs endpoint as a recruiter:\n\n"
                f"{json.dumps(payload, indent=2)}"
            )
        else:
            # User-friendly response
            salary_info = f" with salary {job_data.get('salary')}" if job_data.get('salary') else ""
            state["response"] = (
                f"✅ **Job Created Successfully!**\n\n"
                f"📋 **{job_data['title']}**\n"
                f"📍 **Location:** {job_data['location']}{salary_info}\n\n"
                f"**Job Description:**\n{job_data['description']}\n\n"
                f"**Requirements:** {job_data['requirements']}\n\n"
                "The job is now live and ready for applications! 🎉"
            )
    except json.JSONDecodeError:
        state["response"] = "I had trouble parsing the job details. Please try rephrasing your request with clear job information."
    except Exception as e:
        state["response"] = f"I encountered an issue while creating the job posting. Please try again."

    return state


async def get_applicants_node(state: AgentState) -> AgentState:
    """Get applicants for a job."""
    try:
        from agent.tools import get_applicants
        
        # Try to extract job_id if mentioned
        job_id = None
        import re
        id_match = re.search(r'job[_\s]?id[:\s]+([a-f0-9-]+)', state["message"], re.IGNORECASE)
        if id_match:
            job_id = id_match.group(1)
        
        result = await get_applicants(job_id)
        
        if isinstance(result, dict) and "error" in result:
            state["response"] = "I couldn't retrieve the applicants at this time. Please try again."
        elif not result:
            if job_id:
                state["response"] = f"No applicants found for this job yet. Once candidates start applying, you'll see them here!"
            else:
                state["response"] = "No applications have been received yet. Candidates will appear here once they start applying to your job postings."
        else:
            applicant_count = len(result)
            state["response"] = f"📊 **Found {applicant_count} applicant{'s' if applicant_count != 1 else ''}**\n\n"
            for i, app in enumerate(result[:5], 1):  # Show top 5
                user_info = app.get('users', {})
                name = user_info.get('full_name', user_info.get('email', 'Unknown'))
                state["response"] += f"{i}. {name}\n"
            
            if applicant_count > 5:
                state["response"] += f"\n...and {applicant_count - 5} more applicants."
    
    except Exception as e:
        state["response"] = "I encountered an issue retrieving the applicants. Please try again."
    
    return state


async def rank_applicants_node(state: AgentState) -> AgentState:
    """Rank applicants for a job."""
    try:
        # Extract job_id
        import re
        id_match = re.search(r'job[_\s]?id[:\s]+([a-f0-9-]+)', state["message"], re.IGNORECASE)
        
        if not id_match:
            state["response"] = "To rank applicants, please provide a job ID. You can find job IDs in your job listings.\n\nExample: 'Rank applicants for job_id: abc-123'"
            return state
        
        job_id = id_match.group(1)
        
        from agent.tools import rank_applicants_for_job
        result = await rank_applicants_for_job(job_id)
        
        if not result.applicants:
            state["response"] = f"No applicants found for the job '{result.job_title}' yet."
        else:
            response_text = f"🏆 **ATS Ranking for '{result.job_title}'**\n\n"
            response_text += f"I've ranked {len(result.applicants)} candidate{'s' if len(result.applicants) != 1 else ''} based on their skills and experience:\n\n"
            
            for i, applicant in enumerate(result.applicants[:10], 1):  # Top 10
                score_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
                response_text += f"{score_emoji} **#{i} - {applicant.name}** (Score: {applicant.score}%)\n"
                response_text += f"   💼 Skills: {', '.join(applicant.skills[:5])}\n"
                if applicant.summary:
                    response_text += f"   📝 {applicant.summary[:100]}...\n"
                response_text += "\n"
            
            if len(result.applicants) > 10:
                response_text += f"...and {len(result.applicants) - 10} more candidates.\n"
            
            state["response"] = response_text
    
    except Exception as e:
        state["response"] = "I couldn't rank the applicants at this time. Please make sure you've provided a valid job ID."
    
    return state


async def sql_query_node(state: AgentState) -> AgentState:
    """Execute predefined safe SQL queries based on user intent."""
    try:
        # Define safe, predefined queries only
        SAFE_QUERIES = {
            "count_jobs": "SELECT COUNT(*) as total_jobs FROM jobs",
            "list_recent_jobs": "SELECT title, location, created_at FROM jobs ORDER BY created_at DESC LIMIT 10",
            "count_applications": "SELECT COUNT(*) as total_applications FROM applications",
            "jobs_by_location": "SELECT location, COUNT(*) as job_count FROM jobs GROUP BY location ORDER BY job_count DESC",
            "recent_applications": "SELECT COUNT(*) as recent_apps FROM applications WHERE created_at >= NOW() - INTERVAL '7 days'",
            "top_job_types": "SELECT title, COUNT(*) as count FROM jobs GROUP BY title ORDER BY count DESC LIMIT 5"
        }

        # Use AI to determine which safe query to run
        prompt = f"""Based on this user query: "{state['message']}"

Choose the most appropriate predefined query from these options:
- count_jobs: Count total jobs
- list_recent_jobs: List recent job postings
- count_applications: Count total applications
- jobs_by_location: Jobs grouped by location
- recent_applications: Applications in the last 7 days
- top_job_types: Most common job types

Respond with only the query key (e.g., "count_jobs"). If none match, respond with "no_match".
"""
        response = llm.invoke(prompt)
        query_key = response.content.strip().lower()

        if query_key not in SAFE_QUERIES:
            state["response"] = "I can help you with job statistics, but I don't have information for that specific query. Try asking about job counts, recent postings, or application statistics."
            return state

        sql_query = SAFE_QUERIES[query_key]
        state["sql_generated"] = sql_query  # For logging only

        # Execute query
        from agent.tools import run_sql_query
        result = await run_sql_query(sql_query)

        # Format user-friendly response
        if isinstance(result, dict) and "error" in result:
            state["response"] = "I couldn't retrieve the information right now. Please try again."
        elif not result:
            state["response"] = "No data found for your query."
        else:
            # Format based on query type
            if query_key == "count_jobs":
                count = result[0].get("total_jobs", 0) if result else 0
                state["response"] = f"� There are currently **{count}** job postings in the system."
            elif query_key == "list_recent_jobs":
                jobs_list = [f"• {job['title']} in {job['location']}" for job in result[:5]]
                state["response"] = f"📋 **Recent Job Postings:**\n\n" + "\n".join(jobs_list)
                if len(result) > 5:
                    state["response"] += f"\n\n...and {len(result) - 5} more recent postings."
            elif query_key == "count_applications":
                count = result[0].get("total_applications", 0) if result else 0
                state["response"] = f"📊 There are currently **{count}** applications submitted."
            elif query_key == "jobs_by_location":
                locations = [f"• {row['location']}: {row['job_count']} jobs" for row in result[:5]]
                state["response"] = f"� **Jobs by Location:**\n\n" + "\n".join(locations)
            elif query_key == "recent_applications":
                count = result[0].get("recent_apps", 0) if result else 0
                state["response"] = f"📊 **{count}** applications have been submitted in the last 7 days."
            elif query_key == "top_job_types":
                types = [f"• {row['title']}: {row['count']} postings" for row in result]
                state["response"] = f"💼 **Most Common Job Types:**\n\n" + "\n".join(types)

    except Exception as e:
        state["response"] = "I encountered an issue processing your request. Please try rephrasing or contact support."

    return state


async def general_response_node(state: AgentState) -> AgentState:
    """Handle general queries."""
    prompt = f"""You are a friendly and professional AI recruitment assistant. 

The user said: "{state['message']}"

Provide a helpful, concise, and professional response. Keep it friendly and to the point.

You can help with:
- Creating job postings (e.g., "Create a job for Senior Developer")
- Viewing applicants (e.g., "Show me applicants for job X")
- Ranking candidates with ATS (e.g., "Rank applicants for job X")
- Searching jobs and applications (e.g., "Show all jobs")

Respond naturally and offer to help.
"""
    response = llm.invoke(prompt)
    state["response"] = response.content
    return state


# Build the graph
workflow = StateGraph(AgentState)

# Add nodes (no route node needed - we use route_query as the routing function)
workflow.add_node("create_job_tool", create_job_node)
workflow.add_node("get_applicants_tool", get_applicants_node)
workflow.add_node("search_jobs_tool", search_jobs_node)
workflow.add_node("rank_tool", rank_applicants_node)
workflow.add_node("sql_tool", sql_query_node)
workflow.add_node("general_response", general_response_node)

# Set conditional entry point based on routing
workflow.set_conditional_entry_point(
    route_query,
    {
        "create_job_tool": "create_job_tool",
        "get_applicants_tool": "get_applicants_tool",
        "rank_tool": "rank_tool",
        "sql_tool": "sql_tool",
        "general_response": "general_response"
        ,"search_jobs_tool": "search_jobs_tool"
    }
)

# All tools end after execution
workflow.add_edge("create_job_tool", END)
workflow.add_edge("get_applicants_tool", END)
workflow.add_edge("rank_tool", END)
workflow.add_edge("sql_tool", END)
workflow.add_edge("general_response", END)
workflow.add_edge("search_jobs_tool", END)

# Compile the graph
agent_graph = workflow.compile()


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

    # Use ainvoke for async nodes
    result = await agent_graph.ainvoke(initial_state)

    assistant_response = result.get("response", "")

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
