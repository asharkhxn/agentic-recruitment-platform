from agent.state import AgentState
from agent.tools.applicant_tools import get_applicants
import re


async def get_applicants_node(state: AgentState) -> AgentState:
    """Get applicants for a job."""
    try:
        # Try to extract job_id if mentioned
        job_id = None
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

