from agent.state import AgentState
from agent.utils.llm import llm
from agent.prompts.loader import format_prompt
from agent.tools.sql_tools import run_sql_query

# Define safe, predefined queries only
SAFE_QUERIES = {
    "count_jobs": "SELECT COUNT(*) as total_jobs FROM jobs",
    "list_recent_jobs": "SELECT title, location, created_at FROM jobs ORDER BY created_at DESC LIMIT 10",
    "count_applications": "SELECT COUNT(*) as total_applications FROM applications",
    "jobs_by_location": "SELECT location, COUNT(*) as job_count FROM jobs GROUP BY location ORDER BY job_count DESC",
    "recent_applications": "SELECT COUNT(*) as recent_apps FROM applications WHERE created_at >= NOW() - INTERVAL '7 days'",
    "top_job_types": "SELECT title, COUNT(*) as count FROM jobs GROUP BY title ORDER BY count DESC LIMIT 5"
}


async def sql_query_node(state: AgentState) -> AgentState:
    """Execute predefined safe SQL queries based on user intent."""
    try:
        # Safety check: block dangerous operations
        from agent.utils.safety import contains_dangerous_keywords
        if contains_dangerous_keywords(state['message']):
            state["response"] = (
                "I cannot perform delete, update, modify, or any data modification operations "
                "through the chatbot for security reasons. I can only provide read-only statistics. "
                "Please use the admin dashboard for data modifications."
            )
            return state
        
        # Use AI to determine which safe query to run
        prompt = format_prompt("sql_query_selection.md", message=state['message'])
        response = llm.invoke(prompt)
        query_key = response.content.strip().lower()

        if query_key not in SAFE_QUERIES:
            state["response"] = "I can help you with job statistics, but I don't have information for that specific query. Try asking about job counts, recent postings, or application statistics."
            return state

        sql_query = SAFE_QUERIES[query_key]
        state["sql_generated"] = sql_query  # For logging only

        # Execute query
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
                state["response"] = f"📊 There are currently **{count}** job postings in the system."
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
                state["response"] = f"📍 **Jobs by Location:**\n\n" + "\n".join(locations)
            elif query_key == "recent_applications":
                count = result[0].get("recent_apps", 0) if result else 0
                state["response"] = f"📊 **{count}** applications have been submitted in the last 7 days."
            elif query_key == "top_job_types":
                types = [f"• {row['title']}: {row['count']} postings" for row in result]
                state["response"] = f"💼 **Most Common Job Types:**\n\n" + "\n".join(types)

    except Exception as e:
        state["response"] = "I encountered an issue processing your request. Please try rephrasing or contact support."

    return state

