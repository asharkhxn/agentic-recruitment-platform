import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env from project root directory (parent of backend)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    JWT_SECRET = os.getenv("JWT_SECRET")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def get_supabase_client() -> Client:
    """Get Supabase client with service role key for backend operations."""
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key for user operations."""
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
