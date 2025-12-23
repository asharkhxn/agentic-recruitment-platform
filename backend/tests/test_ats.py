import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock, AsyncMock

from main import app
from core.auth import verify_recruiter
from core.models import User


client = TestClient(app)


def test_rank_endpoint():
    """Test ATS ranking endpoint."""

    async def recruiter_override():
        return User(id="recruiter1", email="recruiter@example.com", role="recruiter")

    app.dependency_overrides[verify_recruiter] = recruiter_override
    try:
        with patch("agent.tools.rank_applicants_for_job", new_callable=AsyncMock) as mock_rank:
            mock_rank.return_value = MagicMock(
                job_id="job1",
                job_title="Software Engineer",
                applicants=[
                    MagicMock(
                        applicant_id="user1",
                        application_id="app1",
                        name="John Doe",
                        email="john@example.com",
                        score=85.0,
                        summary="Great fit",
                        cv_url="https://example.com/cv.pdf",
                        cv_path="user1/job1/cv.pdf",
                        skills=["Python", "FastAPI"]
                    )
                ]
            )

            response = client.post(
                "/ats/rank",
                json={"job_id": "job1"},
                headers={"Authorization": "Bearer mock_token"}
            )
    finally:
        app.dependency_overrides.pop(verify_recruiter, None)

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job1"
    assert len(data["applicants"]) == 1


def test_rank_endpoint_unauthorized():
    """Test ATS ranking endpoint requires recruiter role."""

    async def recruiter_override():
        raise HTTPException(status_code=403, detail="Recruiter access required")

    app.dependency_overrides[verify_recruiter] = recruiter_override
    try:
        response = client.post(
            "/ats/rank",
            json={"job_id": "job1"},
            headers={"Authorization": "Bearer mock_token"}
        )
    finally:
        app.dependency_overrides.pop(verify_recruiter, None)

    # Should fail because user is not a recruiter
    assert response.status_code == 403
