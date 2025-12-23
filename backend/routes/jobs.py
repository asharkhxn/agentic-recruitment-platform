from fastapi import APIRouter, HTTPException, Depends
from typing import List
from core.config import get_supabase_client
from core.models import Job, JobCreate
from core.auth import verify_jwt, verify_recruiter, User

router = APIRouter()


@router.get("", response_model=List[Job])
async def get_jobs():
    """Get all jobs (public)."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """Get a specific job (public)."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("", response_model=Job)
async def create_job(job: JobCreate, user: User = Depends(verify_recruiter)):
    """Create a new job (recruiter only)."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("jobs").insert({
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "location": job.location,
            "salary": job.salary,
            "created_by": user.id
        }).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}", response_model=Job)
async def update_job(job_id: str, job: JobCreate, user: User = Depends(verify_recruiter)):
    """Update a job (recruiter only, own jobs)."""
    try:
        supabase = get_supabase_client()
        
        # Verify ownership
        existing = supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
        if existing.data["created_by"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this job")
        
        response = supabase.table("jobs").update({
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "location": job.location,
            "salary": job.salary
        }).eq("id", job_id).execute()
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(job_id: str, user: User = Depends(verify_recruiter)):
    """Delete a job (recruiter only, own jobs)."""
    try:
        supabase = get_supabase_client()
        
        # Verify ownership
        existing = supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
        if existing.data["created_by"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this job")
        
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
