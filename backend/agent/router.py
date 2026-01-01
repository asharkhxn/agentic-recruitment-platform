from agent.state import AgentState
from agent.utils.safety import contains_dangerous_keywords
from agent.utils.session import get_last_intent, is_follow_up_message


def route_query(state: AgentState) -> str:
    """Determine which tool to use based on the query."""
    message = state["message"].lower()
    conversation_id = state.get("conversation_id", "")
    
    # SAFETY CHECK FIRST - Block dangerous operations
    if contains_dangerous_keywords(message):
        # Check if it's about jobs/data operations
        if any(word in message for word in ["job", "data", "record", "entry", "database", "table"]):
            return "safety_block"
    
    # CONTEXT AWARENESS - Handle follow-up messages
    if is_follow_up_message(message) and conversation_id:
        last_intent = get_last_intent(conversation_id)
        if last_intent:
            return last_intent
    
    # CONTENT GENERATION - Check before other routes
    content_generation_phrases = [
        "draft", "suggest", "write", "compose", "generate message",
        "create message", "help me write", "help me draft"
    ]
    if any(phrase in message for phrase in content_generation_phrases):
        if not any(word in message for word in ["delete", "remove", "update", "modify"]):
            return "general_response"
    
    # SQL QUERIES - Check BEFORE job search to avoid conflicts
    sql_triggers = [
        "how many", "count", "total", "statistics", "stats",
        "list all", "show all", "get all", "query", "search database",
        "in db", "in database"
    ]
    if any(trigger in message for trigger in sql_triggers):
        if not contains_dangerous_keywords(message):
            return "sql_tool"
    
    # JOB CREATION - Comprehensive phrase matching (PRIORITY: Check before search)
    # Expanded list to catch all variations
    create_job_phrases = [
        "create a job", "create job", "post a job", "post job",
        "post a new job", "post new job",  # Added variations
        "new job posting", "add a job", "add job posting",
        "create job for", "post job for",  # Added "for" variations
        "i want to create", "i need to post", "i'd like to add",  # Natural language
        "we're hiring", "we need to post", "we want to create"  # Team language
    ]
    
    # Check if message contains any job creation phrase
    if any(phrase in message for phrase in create_job_phrases):
        # Double check it's not about deleting/updating
        if not contains_dangerous_keywords(message):
            return "create_job_tool"
    
    # RANK APPLICANTS
    if any(word in message for word in ["rank", "shortlist", "ats", "score", "ranking"]):
        return "rank_tool"
    
    # GET APPLICANTS
    if any(word in message for word in ["applicants", "applications", "candidates", "who applied"]):
        return "get_applicants_tool"
    
    # CV SUMMARIZATION
    if any(phrase in message for phrase in ["summarize cv", "cv summary", "summarize resume"]):
        return "general_response"
    
    # GENERATE DESCRIPTION
    if any(phrase in message for phrase in ["generate description", "write description", "create description"]):
        return "general_response"
    
    # JOB SEARCH - Only trigger with explicit search intent (AFTER creation check)
    # Removed generic filter keywords that cause false matches
    job_search_triggers = [
        "view jobs", "view job", "show jobs", "show job",
        "jobs in", "roles in", "find job", "find jobs", "find roles",
        "search jobs", "search for jobs", "look for jobs",  # Explicit search
        "job summary", "job details", "available roles", "openings",
        "vacancies", "open roles", "closed roles", "active jobs",
        "what jobs", "which jobs", "jobs available", "jobs with"  # Search patterns
    ]
    
    # Check for search intent (but NOT if it's a create request)
    if any(trigger in message for trigger in job_search_triggers):
        # Make absolutely sure it's not a create request
        if not any(phrase in message for phrase in create_job_phrases):
            # Make sure it's not a SQL query
            if not any(trigger in message for trigger in sql_triggers):
                return "search_jobs_tool"
    
    # DEFAULT - General response
    return "general_response"
