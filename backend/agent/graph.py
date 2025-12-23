from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from core.config import Config, get_supabase_client
from agent.tools import TOOLS
import json


llm = ChatGroq(api_key=Config.GROQ_API_KEY, model="llama-3.3-70b-versatile")



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

Return a JSON object with:
{{
  "keywords": "<role keywords or empty string>",
  "location": "<location or empty string>",
  "salary": "<salary phrase or empty string>"
}}

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
            state["response"] = "I couldn't search the jobs just now. Please try again in a moment."
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

Provide a JSON response with:
{{
  "title": "<job title>",
  "description": "<brief 2-3 sentence job description>",
  "requirements": "<comma-separated list of requirements>",
  "location": "<primary work location>",
  "salary": "<salary range or empty string>"
}}

Only return the JSON, no other text.
"""
        response = llm.invoke(prompt)
        content = response.content
        
        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            job_data = json.loads(json_match.group())
            # Normalize whitespace
            for key, value in list(job_data.items()):
                if isinstance(value, str):
                    job_data[key] = value.strip()

            required_fields = {
                "title": job_data.get("title"),
                "description": job_data.get("description"),
                "requirements": job_data.get("requirements"),
                "location": job_data.get("location"),
            }
            placeholder_values = {"", "tbd", "n/a", "na", "none", "unspecified"}
            missing = [field for field, value in required_fields.items() if not value or (isinstance(value, str) and value.lower() in placeholder_values)]

            if missing:
                missing_list = ", ".join(field.replace("_", " ") for field in missing)
                state["response"] = (
                    "I’m almost ready to publish this role, but I still need the "
                    f"following details: {missing_list}. Please share them so I can create the posting."
                )
                return state
            
            # Create job
            from agent.tools import create_job
            result = await create_job(
                title=job_data["title"],
                description=job_data["description"],
                requirements=job_data["requirements"],
                location=job_data["location"],
                salary=job_data.get("salary") or None,
                user_id=state["user_id"]
            )
            
            if "error" in result:
                state["response"] = f"Sorry, I couldn't create the job posting. Please try again or contact support."
            else:
                # User-friendly response
                salary_info = f" with a salary of {job_data.get('salary')}" if job_data.get('salary') else " with competitive compensation"
                state["response"] = (
                    f"✅ Great! I've successfully created a job posting for **{job_data['title']}** in {job_data['location']}{salary_info}.\n\n"
                    f"📍 **Location:** {job_data['location']}\n"
                    f"📋 **Job Details:**\n{job_data['description']}\n\n"
                    f"**Requirements:** {job_data['requirements']}\n\n"
                    "The job is now live and candidates can start applying!"
                )
        else:
            state["response"] = "I couldn't extract the job details from your message. Could you please provide:\n- Job title\n- Key requirements\n- Salary range (optional)\n\nFor example: 'Create a job for Senior Python Developer with 5+ years experience, salary £80k-£100k'"
    
    except Exception as e:
        state["response"] = f"I encountered an issue while creating the job posting. Please try again with the job details."
    
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
    """Generate and execute SQL query."""
    try:
        prompt = f"""Convert this natural language query to a SQL SELECT statement for a PostgreSQL database:

Query: "{state['message']}"

Tables available:
- jobs (id, title, description, requirements, salary, created_by, created_at)
- applications (id, applicant_id, job_id, cv_url, cover_letter, created_at)
- users (id, email, role, full_name)

Provide only the SQL query, no explanation.
"""
        response = llm.invoke(prompt)
        sql_query = response.content.strip()
        
        # Clean up SQL
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        state["sql_generated"] = sql_query  # Keep for logging, but don't show to user
        
        # Execute query
        from agent.tools import run_sql_query
        result = await run_sql_query(sql_query)
        
        # Format user-friendly response
        if isinstance(result, dict) and "error" in result:
            state["response"] = "I couldn't find the information you're looking for. Could you rephrase your question?"
        elif not result:
            state["response"] = "No results found for your query."
        else:
            # Format results in a user-friendly way
            if "jobs" in sql_query.lower():
                state["response"] = f"📋 **Found {len(result)} job{'s' if len(result) != 1 else ''}:**\n\n"
                for job in result[:5]:
                    state["response"] += f"• **{job.get('title', 'Untitled')}**\n"
                    if job.get('salary'):
                        state["response"] += f"  💰 {job['salary']}\n"
                    state["response"] += "\n"
            elif "users" in sql_query.lower():
                state["response"] = f"👥 **Found {len(result)} user{'s' if len(result) != 1 else ''}:**\n\n"
                for user in result[:5]:
                    state["response"] += f"• {user.get('email', 'Unknown')}\n"
            else:
                state["response"] = f"Found {len(result)} result{'s' if len(result) != 1 else ''}."
    
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
    
    # Log to database
    try:
        supabase = get_supabase_client()
        supabase.table("ai_search_logs").insert({
            "user_id": user_id,
            "query": message,
            "sql_generated": None  # Will update if SQL is generated
        }).execute()
    except:
        pass  # Don't fail if logging fails
    
    # Use ainvoke for async nodes
    result = await agent_graph.ainvoke(initial_state)
    
    return {
        "response": result["response"],
        "sql_generated": result.get("sql_generated")
    }
