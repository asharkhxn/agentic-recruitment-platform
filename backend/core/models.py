from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: str
    email: str
    role: str  # 'applicant' or 'recruiter'
    full_name: Optional[str] = None


class Job(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = None


class JobCreate(BaseModel):
    title: str
    description: str
    requirements: str
    location: str
    salary: Optional[str] = None


class Application(BaseModel):
    id: Optional[str] = None
    applicant_id: str
    job_id: str
    cv_url: str
    cover_letter: Optional[str] = None
    recruiter_id: Optional[str] = None
    applicant_name: Optional[str] = None
    motivation: Optional[str] = None
    proud_project: Optional[str] = None
    created_at: Optional[datetime] = None


class ApplicationCreate(BaseModel):
    job_id: str
    cover_letter: Optional[str] = None


class ChatMessage(BaseModel):
    message: str
    user_id: str  # ID of the user sending the message
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sql_generated: Optional[str] = None


class RankedApplicant(BaseModel):
    applicant_id: str
    name: str
    email: str
    score: float
    summary: str
    cv_url: str
    application_id: str
    skills: list[str]


class ATSRankingRequest(BaseModel):
    job_id: str


class ATSRankingResponse(BaseModel):
    job_id: str
    job_title: str
    applicants: list[RankedApplicant]
