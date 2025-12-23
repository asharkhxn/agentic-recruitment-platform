from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from core.config import get_supabase_client
from core.models import Application
from core.auth import verify_jwt, User
import uuid

router = APIRouter()


@router.get("", response_model=List[Application])
async def get_applications(job_id: Optional[str] = None, user: User = Depends(verify_jwt)):
    """Get applications. Recruiters see all, applicants see only their own."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("applications").select("*")
        
        if user.role == "applicant":
            query = query.eq("applicant_id", user.id)
        else:
            query = query.eq("recruiter_id", user.id)
        
        if job_id:
            query = query.eq("job_id", job_id)
        
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{application_id}", response_model=Application)
async def get_application(application_id: str, user: User = Depends(verify_jwt)):
    """Get a specific application."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("applications").select("*").eq("id", application_id).single().execute()
        
        # Check authorization
        if user.role == "applicant" and response.data["applicant_id"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if user.role == "recruiter" and response.data.get("recruiter_id") != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail="Application not found")


@router.post("", response_model=Application)
async def create_application(
    job_id: str = Form(...),
    cover_letter: Optional[str] = Form(None),
    motivation: str = Form(...),
    proud_project: str = Form(...),
    cv_file: UploadFile = File(...),
    user: User = Depends(verify_jwt)
):
    """Create a new application with CV upload."""
    try:
        if user.role != "applicant":
            raise HTTPException(status_code=403, detail="Only applicants can apply")

        # Check if job exists
        supabase = get_supabase_client()
        job = supabase.table("jobs").select("id", "created_by").eq("id", job_id).single().execute()
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        recruiter_id = job.data.get("created_by")
        if not recruiter_id:
            raise HTTPException(status_code=400, detail="Job is missing recruiter information")
        
        # Upload CV to Supabase Storage
        file_extension = cv_file.filename.split(".")[-1]
        file_name = f"{user.id}/{job_id}/{uuid.uuid4()}.{file_extension}"
        
        file_bytes = await cv_file.read()
        storage_response = supabase.storage.from_("cv-uploads").upload(
            file_name,
            file_bytes,
            {"content-type": cv_file.content_type}
        )
        
        # Get public URL
        cv_url = supabase.storage.from_("cv-uploads").get_public_url(file_name)
        
        # Create application record
        applicant_name = user.full_name or user.email
        response = supabase.table("applications").insert({
            "applicant_id": user.id,
            "job_id": job_id,
            "cv_url": cv_url,
            "cover_letter": cover_letter,
            "recruiter_id": recruiter_id,
            "applicant_name": applicant_name,
            "motivation": motivation,
            "proud_project": proud_project
        }).execute()
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{application_id}")
async def delete_application(application_id: str, user: User = Depends(verify_jwt)):
    """Delete an application (applicant only, own applications)."""
    try:
        supabase = get_supabase_client()
        
        # Verify ownership
        existing = supabase.table("applications").select("applicant_id").eq("id", application_id).single().execute()
        if existing.data["applicant_id"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        supabase.table("applications").delete().eq("id", application_id).execute()
        return {"message": "Application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
