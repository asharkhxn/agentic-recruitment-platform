from agent.state import AgentState
from agent.utils.llm import llm
from agent.prompts.loader import format_prompt
from agent.tools.job_tools import search_jobs
import json
import re


async def search_jobs_node(state: AgentState) -> AgentState:
    """Search jobs using structured filters."""
    try:
        # Load and format prompt
        extraction_prompt = format_prompt("extract_filters.md", message=state['message'])

        response = llm.invoke(extraction_prompt)
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        filters = {"keywords": "", "location": "", "salary": ""}
        if json_match:
            filters.update(json.loads(json_match.group()))

        # Normalize filters
        for key, value in list(filters.items()):
            if isinstance(value, str):
                filters[key] = value.strip()

        # If everything empty, check if message is actually about jobs
        if not any(filters.values()):
            message_lower = state["message"].lower()
            # Only treat as keywords if message contains job-related terms
            if any(term in message_lower for term in ["job", "role", "position", "opening", "vacancy"]):
                filters["keywords"] = state["message"].strip()
            else:
                # Not a job search query - return helpful message
                state["response"] = (
                    "I didn't detect job search criteria in your message. "
                    "To search for jobs, try:\n"
                    "- 'Jobs in London'\n"
                    "- 'Python developer roles'\n"
                    "- 'Jobs over 100k'\n"
                    "- 'Remote jobs'\n\n"
                    "Or I can help you create a job posting, view applicants, or rank candidates."
                )
                return state

        # Populate tool information for LangSmith tracking
        tool_args = {
            "keywords": filters.get("keywords") or None,
            "location": filters.get("location") or None,
            "salary": filters.get("salary") or None,
        }
        
        state["tool_name"] = "search_jobs"
        state["tool_args"] = tool_args
        
        result = await search_jobs(
            keywords=filters.get("keywords") or None,
            location=filters.get("location") or None,
            salary=filters.get("salary") or None,
        )
        
        # Store tool result for LangSmith
        if isinstance(result, list):
            state["tool_result"] = f"Found {len(result)} jobs"
        elif isinstance(result, dict):
            state["tool_result"] = str(result)
        else:
            state["tool_result"] = "Search completed"

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

