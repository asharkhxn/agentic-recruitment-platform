
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List
from core.config import get_supabase_client
from core.models import Job, JobCreate
from core.auth import verify_jwt, verify_recruiter, User
# sanitizer removed by request — inputs are minimally normalized below

router = APIRouter()


@router.post("/close/{job_id}")
async def close_job(job_id: str, user: User = Depends(verify_recruiter)):
    """Mark a job as closed (recruiter only, own jobs)."""
    try:
        supabase = get_supabase_client()

        # Verify ownership
        existing = supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Job not found")
        if existing.data["created_by"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to close this job")

        # Ensure status column exists in DB; update to 'closed'
        response = supabase.table("jobs").update({"status": "closed"}).eq("id", job_id).execute()
        return {"message": "Job closed successfully", "job": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-recruiter/{recruiter_id}", response_model=List[Job])
async def get_jobs_by_recruiter(recruiter_id: str, user: User = Depends(verify_recruiter)):
    """Get all jobs created by a specific recruiter (recruiter only)."""
    try:
        if user.id != recruiter_id:
            raise HTTPException(status_code=403, detail="Not authorized to view these jobs")
        supabase = get_supabase_client()
        response = supabase.table("jobs").select("*").eq("created_by", recruiter_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
async def create_job(job: dict = Body(...), user: User = Depends(verify_recruiter)):
    """Create a new job (recruiter only).

    This endpoint validates required fields and returns a friendly message
    listing any missing details so the caller can provide them.
    """
    try:
        # Required fields for creating a job (location is optional)
        required = ["title", "description", "requirements"]
        missing = [f for f in required if not job.get(f) or str(job.get(f)).strip() == ""]
        if missing:
            # Return a helpful 400 with the missing field names
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing required fields",
                    "missing_fields": missing,
                    "message": f"Please provide the following fields: {', '.join(missing)}"
                }
            )

        # Build a JobCreate for further validation and reuse existing pydantic rules
        job_payload = JobCreate(**{k: job.get(k) for k in job})

        # Minimal normalization (trim strings)
        title = str(job_payload.title).strip()
        description = str(job_payload.description).strip()
        requirements = str(job_payload.requirements).strip()
        location = str(job_payload.location).strip() if job_payload.location else None
        salary = str(job_payload.salary).strip() if job_payload.salary else None

        supabase = get_supabase_client()
        response = supabase.table("jobs").insert({
            "title": title,
            "description": description,
            "requirements": requirements,
            "location": location,
            "salary": salary,
            "created_by": user.id
        }).execute()
        return response.data[0]
    except HTTPException:
        # re-raise friendly validation HTTPException
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}", response_model=Job)
async def update_job(job_id: str, job: JobCreate, user: User = Depends(verify_recruiter)):
    """Update a job (recruiter only, own jobs)."""
    try:
        # Minimal normalization (trim strings)
        title = str(job.title).strip()
        description = str(job.description).strip()
        requirements = str(job.requirements).strip()
        location = str(job.location).strip() if job.location else None
        salary = str(job.salary).strip() if job.salary else None

        supabase = get_supabase_client()
        
        # Verify ownership
        existing = supabase.table("jobs").select("created_by").eq("id", job_id).single().execute()
        if existing.data["created_by"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this job")
        
        response = supabase.table("jobs").update({
            "title": title,
            "description": description,
            "requirements": requirements,
            "location": location,
            "salary": salary
        }).eq("id", job_id).execute()
        
        return response.data[0]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
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
