from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
import re

from core.config import get_supabase_anon_client, get_supabase_client

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str 
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    role: str  # 'applicant' or 'recruiter'


class AuthResponse(BaseModel):
    access_token: str
    user: dict


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    try:
        supabase = get_supabase_anon_client()
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        
        service_client = get_supabase_client()
        user_record = service_client.table("users").select("*").eq("id", response.user.id).execute()
        if not user_record.data:
            service_client.table("users").upsert({
                "id": response.user.id,
                "email": response.user.email,
                "role": response.user.user_metadata.get("role", "applicant"),
                "full_name": response.user.user_metadata.get("full_name")
            }).execute()
            user_record = service_client.table("users").select("*").eq("id", response.user.id).execute()

        user_row = user_record.data[0] if user_record.data else {}
        role = user_row.get("role", response.user.user_metadata.get("role", "applicant"))
        full_name = user_row.get("full_name") or response.user.user_metadata.get("full_name")

        return AuthResponse(
            access_token=response.session.access_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "role": role,
                "full_name": full_name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """Sign up with email, password and role."""
    try:
        # Enhanced password validation: at least 8 chars, upper, lower, digit, special char
        pwd = request.password
        if (
            len(pwd) < 8
            or not re.search(r"[A-Z]", pwd)
            or not re.search(r"[a-z]", pwd)
            or not re.search(r"[0-9]", pwd)
            or not re.search(r"[^A-Za-z0-9]", pwd)
        ):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters and include upper, lower, numeric, and special characters."
            )

        if request.role not in {"applicant", "recruiter"}:
            raise HTTPException(status_code=400, detail="Role must be either 'applicant' or 'recruiter'")

        supabase = get_supabase_anon_client()
        
        full_name = f"{request.first_name} {request.last_name}"
        
        # Sign up with metadata
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "role": request.role,
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "full_name": full_name
                }
            }
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Signup failed")
        
        # Create user record in users table using service role (bypasses RLS)
        supabase_service = get_supabase_client()
        supabase_service.table("users").upsert({
            "id": response.user.id,
            "email": request.email,
            "role": request.role,
            "full_name": full_name
        }).execute()
        
        return AuthResponse(
            access_token=response.session.access_token if response.session else "pending_confirmation",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "role": request.role,
                "full_name": full_name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout():
    """Logout (handled client-side with Supabase)."""
    return {"message": "Logout successful"}
