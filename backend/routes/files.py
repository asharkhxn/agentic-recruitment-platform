from fastapi import APIRouter, HTTPException, Depends
from core.config import get_supabase_client
from core.auth import verify_recruiter, User
from typing import Optional

router = APIRouter()


def _derive_cv_path(cv_url: Optional[str]) -> Optional[str]:
    if not cv_url:
        return None
    marker = "/object/public/cv-uploads/"
    if marker in cv_url:
        return cv_url.split(marker, 1)[-1]
    marker_alt = "cv-uploads/"
    if marker_alt in cv_url:
        return cv_url.split(marker_alt, 1)[-1]
    return None


@router.get("/signed-url/{file_path:path}")
async def get_signed_url(file_path: str, user: User = Depends(verify_recruiter)):
    """Get signed URL for CV access (recruiter only)."""
    try:
        supabase = get_supabase_client()
        
        # Generate signed URL valid for 1 hour
        signed_url = supabase.storage.from_("cv-uploads").create_signed_url(
            file_path,
            60 * 60  # 1 hour
        )
        
        return {"signed_url": signed_url["signedURL"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}/preview")
async def get_application_cv_preview(application_id: str, user: User = Depends(verify_recruiter)):
    """Generate a temporary signed URL for viewing an applicant's CV."""
    try:
        supabase = get_supabase_client()
        record = (
            supabase
            .table("applications")
            .select("cv_url")
            .eq("id", application_id)
            .single()
            .execute()
        )

        if not record.data:
            raise HTTPException(status_code=404, detail="Application not found")

        cv_url = record.data.get("cv_url")
        if not cv_url:
            raise HTTPException(status_code=400, detail="CV URL unavailable for this application")

        cv_path = _derive_cv_path(cv_url)

        if cv_path:
            try:
                signed = supabase.storage.from_("cv-uploads").create_signed_url(cv_path, 600)
                return {"signed_url": signed["signedURL"]}
            except Exception:
                # Fall back to returning the public URL if signing fails
                return {"signed_url": cv_url}

        return {"signed_url": cv_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
