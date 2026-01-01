from typing import Dict, List, Any
from core.config import get_supabase_client
from core.models import RankedApplicant, ATSRankingResponse
from agent.utils.llm import llm
import json
import re


async def get_applicants(job_id: str = None) -> List[Dict[str, Any]]:
    """Get applicants, optionally filtered by job_id."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("applications").select("*, applicant:users!applications_applicant_id_fkey(*)")
        
        if job_id:
            query = query.eq("job_id", job_id)
        
        response = query.execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}


async def rank_applicants_for_job(job_id: str) -> ATSRankingResponse:
    """
    ATS-style ranking of applicants for a specific job.
    Uses LLM to analyze CV and cover letter against job requirements.
    """
    try:
        supabase = get_supabase_client()
        
        # Get job details
        job_response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        job = job_response.data
        
        # Get all applications for this job
        apps_response = (
            supabase
            .table("applications")
            .select("*, applicant:users!applications_applicant_id_fkey(*)")
            .eq("job_id", job_id)
            .execute()
        )
        applications = apps_response.data
        
        if not applications:
            return ATSRankingResponse(
                job_id=job_id,
                job_title=job["title"],
                applicants=[]
            )
        
        ranked_applicants = []
        
        for app in applications:
            # Extract CV text (simplified - in production, parse PDF)
            cv_text = f"CV URL: {app['cv_url']}"
            cover_letter = app.get("cover_letter", "")
            application_id = app.get("id") or app.get("application_id") or app.get("applicant_id")
            application_id = str(application_id)

            applicant_user = app.get("applicant") or {}
            applicant_email = applicant_user.get("email")
            display_name = (
                app.get("applicant_name")
                or applicant_user.get("full_name")
                or (applicant_email.split("@")[0] if applicant_email else "Candidate")
            )
            
            # Use LLM to score and analyze applicant
            from agent.prompts.loader import format_prompt
            prompt = format_prompt(
                "ats_analysis.md",
                job_title=job['title'],
                job_requirements=job['requirements'],
                job_description=job['description'],
                cv_text=cv_text,
                cover_letter=cover_letter
            )
            
            try:
                response = llm.invoke(prompt)
                content = response.content
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback if JSON parsing fails
                    result = {
                        "score": 50,
                        "summary": "Unable to fully analyze application",
                        "skills": []
                    }
                
                skills = result.get("skills", [])
                if isinstance(skills, str):
                    skills = [skill.strip() for skill in skills.split(",") if skill.strip()]

                ranked_applicants.append(RankedApplicant(
                    application_id=application_id,
                    applicant_id=app["applicant_id"],
                    name=display_name,
                    email=applicant_email or "unknown@candidate",
                    score=float(result.get("score", 50)),
                    summary=result.get("summary", ""),
                    cv_url=app["cv_url"],
                    skills=skills if isinstance(skills, list) else []
                ))
            except Exception as e:
                # If analysis fails for one applicant, continue with others
                ranked_applicants.append(RankedApplicant(
                    application_id=application_id,
                    applicant_id=app["applicant_id"],
                    name=display_name,
                    email=applicant_email or "unknown@candidate",
                    score=0,
                    summary=f"Error analyzing: {str(e)}",
                    cv_url=app["cv_url"],
                    skills=[]
                ))
        
        # Sort by score descending
        ranked_applicants.sort(key=lambda x: x.score, reverse=True)
        
        return ATSRankingResponse(
            job_id=job_id,
            job_title=job["title"],
            applicants=ranked_applicants
        )
    
    except Exception as e:
        raise Exception(f"Error ranking applicants: {str(e)}")

