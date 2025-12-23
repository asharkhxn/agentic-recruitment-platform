from fastapi import APIRouter, HTTPException, Depends
from core.models import ATSRankingRequest, ATSRankingResponse
from core.auth import verify_recruiter, User
from agent.tools import rank_applicants_for_job

router = APIRouter()


@router.post("/rank", response_model=ATSRankingResponse)
async def rank_applicants(request: ATSRankingRequest, user: User = Depends(verify_recruiter)):
    """Rank applicants for a job using AI (recruiter only)."""
    try:
        result = await rank_applicants_for_job(request.job_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
