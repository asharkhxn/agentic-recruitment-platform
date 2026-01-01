from agent.state import AgentState
from agent.tools.applicant_tools import rank_applicants_for_job
import re


async def rank_applicants_node(state: AgentState) -> AgentState:
    """Rank applicants for a job."""
    try:
        # Extract job_id
        id_match = re.search(r'job[_\s]?id[:\s]+([a-f0-9-]+)', state["message"], re.IGNORECASE)
        
        if not id_match:
            state["response"] = "To rank applicants, please provide a job ID. You can find job IDs in your job listings.\n\nExample: 'Rank applicants for job_id: abc-123'"
            return state
        
        job_id = id_match.group(1)
        
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

