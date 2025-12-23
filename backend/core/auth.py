import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

from .config import get_supabase_client
from .models import User

security = HTTPBearer()


async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Verify Supabase JWT token and return user information."""
    try:
        token = credentials.credentials
        
        # Use Supabase client configured with the token
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        # Create a client with the user's token
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Supabase configuration missing")

        supabase: Client = create_client(supabase_url, supabase_key)
        supabase.postgrest.auth(token)
        
        # Get user from Supabase using the token
        response = supabase.auth.get_user(token)
        
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_data = response.user
        role = user_data.user_metadata.get("role", "applicant")
        
        # Get user from database to ensure they exist
        db_user = supabase.table("users").select("*").eq("id", user_data.id).execute()
        
        if not db_user.data:
            # Automatically provision user record if missing
            service_client = get_supabase_client()
            service_client.table("users").upsert({
                "id": user_data.id,
                "email": user_data.email,
                "role": role,
                "full_name": user_data.user_metadata.get("full_name")
            }).execute()
            db_user = service_client.table("users").select("*").eq("id", user_data.id).execute()
            if not db_user.data:
                raise HTTPException(status_code=401, detail="User not found in database")
        
        user_record = db_user.data[0] if isinstance(db_user.data, list) else db_user.data
        return User(
            id=user_data.id,
            email=user_data.email,
            role=user_record.get("role", role),
            full_name=user_record.get("full_name") or user_data.user_metadata.get("full_name")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {str(e)}")  # Debug logging
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def require_role(required_role: str):
    """Decorator to require specific role."""
    async def decorator(user: User = Security(verify_jwt)) -> User:
        if user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role}"
            )
        return user
    return decorator


async def verify_recruiter(user: User = Security(verify_jwt)) -> User:
    """Verify user is a recruiter."""
    if user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return user
