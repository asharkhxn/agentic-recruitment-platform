from typing import Dict, List, Any, Optional
from core.config import get_supabase_client, Config
from core.models import RankedApplicant, ATSRankingResponse
from langchain_groq import ChatGroq
import json
import re


llm = ChatGroq(api_key=Config.GROQ_API_KEY, model="llama-3.3-70b-versatile")
async def run_sql_query(query: str) -> List[Dict[str, Any]]:
    """Execute SQL SELECT query against Supabase database."""
    try:
        # Only allow SELECT queries for safety
        query_upper = query.upper().strip()
        if not query_upper.startswith('SELECT'):
            return {"error": "Only SELECT queries are allowed. Use the create_job tool to create jobs."}
        
        supabase = get_supabase_client()
        
        # Parse table name from query
        table_match = re.search(r'from\s+(\w+)', query.lower())
        if not table_match:
            return {"error": "Could not parse table name"}
        
        table_name = table_match.group(1)
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}


async def create_job(title: str, description: str, requirements: str, location: str, salary: Optional[str], user_id: str) -> Dict[str, Any]:
    """Create a new job posting."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("jobs").insert({
            "title": title,
            "description": description,
            "requirements": requirements,
            "location": location,
            "salary": salary,
            "created_by": user_id
        }).execute()
        return response.data[0]
    except Exception as e:
        return {"error": str(e)}


async def search_jobs(keywords: Optional[str] = None, location: Optional[str] = None, salary: Optional[str] = None) -> List[Dict[str, Any]] | Dict[str, Any]:
    """Search jobs by keyword, location, or salary phrase."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("jobs").select("*").order("created_at", desc=True)

        # Apply filters dynamically
        if keywords:
            keywords = keywords.strip()
            if keywords:
                query = query.or_(
                    f"title.ilike.%{keywords}%,description.ilike.%{keywords}%,requirements.ilike.%{keywords}%"
                )

        if location:
            location = location.strip()
            if location:
                query = query.ilike("location", f"%{location}%")

        if salary:
            salary = salary.strip()
            if salary:
                query = query.ilike("salary", f"%{salary}%")

        response = query.execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}


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


async def summarize_cv(cv_text: str) -> str:
    """Summarize CV using LLM."""
    try:
        prompt = f"""Summarize the following CV in 2-3 sentences, highlighting key skills and experience:

{cv_text}

Summary:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error summarizing CV: {str(e)}"


async def generate_job_description(title: str, key_requirements: str) -> str:
    """Generate a job description using LLM."""
    try:
        prompt = f"""Generate a professional job description for the following position:

Title: {title}
Key Requirements: {key_requirements}

Create a compelling job description including:
- Role overview
- Key responsibilities
- Required qualifications
- Desired skills

Job Description:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error generating job description: {str(e)}"


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
            prompt = f"""You are an ATS (Applicant Tracking System). Analyze this applicant for the job.

Job Title: {job['title']}
Job Requirements: {job['requirements']}
Job Description: {job['description']}

Applicant CV: {cv_text}
Cover Letter: {cover_letter}

Provide:
1. A score from 0-100 indicating fit for the role
2. A brief summary (2-3 sentences)
3. Key skills identified (comma-separated list)

Format your response as JSON:
{{
  "score": <number>,
  "summary": "<text>",
  "skills": ["skill1", "skill2", ...]
}}
"""
            
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
                
                applicant_user = app.get("applicant") or {}
                applicant_email = applicant_user.get("email")
                display_name = (
                    app.get("applicant_name")
                    or applicant_user.get("full_name")
                    or (applicant_email.split("@")[0] if applicant_email else "Candidate")
                )

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


# Tool definitions for LangGraph
TOOLS = {
    "run_sql_query": run_sql_query,
    "create_job": create_job,
    "get_applicants": get_applicants,
    "summarize_cv": summarize_cv,
    "generate_job_description": generate_job_description,
    "rank_applicants_for_job": rank_applicants_for_job,
    "search_jobs": search_jobs
}
