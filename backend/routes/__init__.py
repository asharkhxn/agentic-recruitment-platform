from fastapi import APIRouter

# This file imports and exports all routers
from .auth import router as auth_router
from .jobs import router as jobs_router
from .applications import router as applications_router
from .agent import router as agent_router
from .files import router as files_router
from .ats import router as ats_router

__all__ = [
    "auth_router",
    "jobs_router", 
    "applications_router",
    "agent_router",
    "files_router",
    "ats_router"
]
