import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock, AsyncMock

from core.auth import verify_recruiter
from core.models import User


client = TestClient(app)


def test_get_jobs():
    """Test getting all jobs."""
    with patch("routes.jobs.get_supabase_client") as mock_supabase:
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "job1",
                "title": "Software Engineer",
                "description": "Great job",
                "requirements": "Python, FastAPI",
                "salary": "100k",
                "created_by": "user1",
                "created_at": "2024-01-01"
            }
        ]
        
        mock_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        response = client.get("/jobs")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Software Engineer"


def test_get_job_by_id():
    """Test getting a specific job."""
    with patch("routes.jobs.get_supabase_client") as mock_supabase:
        mock_response = MagicMock()
        mock_response.data = {
            "id": "job1",
            "title": "Software Engineer",
            "description": "Great job",
            "requirements": "Python, FastAPI",
            "salary": "100k",
            "created_by": "user1",
            "created_at": "2024-01-01"
        }
        
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        response = client.get("/jobs/job1")
        
        assert response.status_code == 200
        assert response.json()["title"] == "Software Engineer"


def test_create_job():
    """Test creating a job as recruiter."""
    with patch("routes.jobs.get_supabase_client") as mock_supabase:
        
        async def recruiter_override():
            return User(id="recruiter1", email="recruiter@example.com", role="recruiter")

        app.dependency_overrides[verify_recruiter] = recruiter_override
        
        mock_response = MagicMock()
        mock_response.data = [{
            "id": "job1",
            "title": "Backend Developer",
            "description": "Build APIs",
            "requirements": "Python",
            "salary": "120k",
            "created_by": "recruiter1"
        }]
        
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = mock_response
        
        job_data = {
            "title": "Backend Developer",
            "description": "Build APIs",
            "requirements": "Python",
            "salary": "120k"
        }
        
        response = client.post(
            "/jobs",
            json=job_data,
            headers={"Authorization": "Bearer mock_token"}
        )
        app.dependency_overrides.pop(verify_recruiter, None)
        
        assert response.status_code == 200
        assert response.json()["title"] == "Backend Developer"


def test_delete_job_unauthorized():
    """Test deleting a job by non-owner."""
    with patch("routes.jobs.get_supabase_client") as mock_supabase:
        
        async def recruiter_override():
            return User(id="recruiter2", email="recruiter2@example.com", role="recruiter")

        app.dependency_overrides[verify_recruiter] = recruiter_override
        
        mock_response = MagicMock()
        mock_response.data = {"created_by": "recruiter1"}
        
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        response = client.delete(
            "/jobs/job1",
            headers={"Authorization": "Bearer mock_token"}
        )
        app.dependency_overrides.pop(verify_recruiter, None)
        
        assert response.status_code == 403
