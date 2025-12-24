from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime


# Small normalized base model for lightweight input normalization
class NormalizedBaseModel(BaseModel):
    """Base model that trims string fields (before validation) and
    ensures created_at timestamps are set when missing.

    Uses pydantic v2 model_validator hooks.
    """

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    def _strip_strings(cls, values):
        # values may be a dict or other mapping
        if isinstance(values, dict):
            out = {}
            for k, v in values.items():
                if isinstance(v, str):
                    out[k] = v.strip()
                else:
                    out[k] = v
            return out
        return values

    @model_validator(mode="after")
    def _set_defaults(self):
        # Set created_at to utcnow() if the model has the attribute and it's None
        if hasattr(self, "created_at") and getattr(self, "created_at") is None:
            object.__setattr__(self, "created_at", datetime.utcnow())
        return self


class User(NormalizedBaseModel):
    id: str
    email: str
    role: str  # 'applicant' or 'recruiter'
    full_name: Optional[str] = None


class Job(NormalizedBaseModel):
    id: Optional[str] = None
    title: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = Field(default=None)


class JobCreate(NormalizedBaseModel):
    title: str
    description: str
    requirements: str
    location: str
    salary: Optional[str] = None


class Application(NormalizedBaseModel):
    id: Optional[str] = None
    applicant_id: str
    job_id: str
    cv_url: str
    cover_letter: Optional[str] = None
    recruiter_id: Optional[str] = None
    applicant_name: Optional[str] = None
    motivation: Optional[str] = None
    proud_project: Optional[str] = None
    created_at: Optional[datetime] = Field(default=None)


class ApplicationCreate(NormalizedBaseModel):
    job_id: str
    cover_letter: Optional[str] = None


class ChatMessage(NormalizedBaseModel):
    message: str
    user_id: str  # ID of the user sending the message
    conversation_id: Optional[str] = None


class ChatResponse(NormalizedBaseModel):
    response: str
    conversation_id: str


class RankedApplicant(NormalizedBaseModel):
    applicant_id: str
    name: str
    email: str
    score: float
    summary: str
    cv_url: str
    application_id: str
    skills: list[str]


class ATSRankingRequest(NormalizedBaseModel):
    job_id: str


class ATSRankingResponse(NormalizedBaseModel):
    job_id: str
    job_title: str
    applicants: list[RankedApplicant]
