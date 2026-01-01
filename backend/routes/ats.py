from fastapi import APIRouter, HTTPException, Depends
from core.models import ATSRankingRequest, ATSRankingResponse
from core.auth import verify_recruiter, User
from core.config import get_supabase_client
from agent.tools.applicant_tools import rank_applicants_for_job

router = APIRouter()


@router.post("/rank", response_model=ATSRankingResponse)
async def rank_applicants(request: ATSRankingRequest, user: User = Depends(verify_recruiter)):
    """Rank applicants for a job using AI (recruiter only)."""
    try:
        # Verify the job exists and that the requesting recruiter owns it
        supabase = get_supabase_client()
        existing = supabase.table("jobs").select("created_by, title").eq("id", request.job_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Job not found")
        if existing.data.get("created_by") != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to rank applicants for this job")

        result = await rank_applicants_for_job(request.job_id)
        # attach job_title from DB for convenience (response model includes job_title)
        result.job_title = existing.data.get("title")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
