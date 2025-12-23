import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
from io import BytesIO

from core.auth import verify_jwt
from core.models import User


client = TestClient(app)


def test_get_applications_as_applicant():
    """Test getting applications as applicant."""
    with patch("routes.applications.get_supabase_client") as mock_supabase:
        
        async def applicant_override():
            return User(id="applicant1", email="applicant@example.com", role="applicant", full_name="Test Applicant")

        app.dependency_overrides[verify_jwt] = applicant_override

        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "app1",
                "applicant_id": "applicant1",
                "job_id": "job1",
                "cv_url": "https://example.com/cv.pdf",
                "cover_letter": "I'm great!",
                "applicant_name": "Test Applicant",
                "motivation": "I love the mission",
                "proud_project": "Built an AI agent"
            }
        ]
        
        mock_query = mock_supabase.return_value.table.return_value.select.return_value
        mock_query.eq.return_value.order.return_value.execute.return_value = mock_response
        try:
            response = client.get(
                "/applications",
                headers={"Authorization": "Bearer mock_token"}
            )
        finally:
            app.dependency_overrides.pop(verify_jwt, None)
        
        assert response.status_code == 200
        assert len(response.json()) == 1


def test_create_application():
    """Test creating an application with CV upload."""
    with patch("routes.applications.get_supabase_client") as mock_supabase:
        
        async def applicant_override():
            return User(id="applicant1", email="applicant@example.com", role="applicant", full_name="Test Applicant")

        app.dependency_overrides[verify_jwt] = applicant_override

        # Mock job check
        mock_job_response = MagicMock()
        mock_job_response.data = {"id": "job1", "created_by": "recruiter1"}
        
        # Mock storage upload
        mock_storage = MagicMock()
        mock_storage.upload.return_value = {"path": "applicant1/job1/cv.pdf"}
        mock_storage.get_public_url.return_value = "https://example.com/cv.pdf"
        
        # Mock application insert
        mock_app_response = MagicMock()
        mock_app_response.data = [{
            "id": "app1",
            "applicant_id": "applicant1",
            "job_id": "job1",
            "cv_url": "https://example.com/cv.pdf",
            "recruiter_id": "recruiter1",
            "applicant_name": "Test Applicant",
            "motivation": "I love your mission",
            "proud_project": "Built an AI agent"
        }]
        
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_job_response
        mock_supabase.return_value.storage.from_.return_value = mock_storage
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = mock_app_response
        
        # Create fake file
        file_content = b"fake pdf content"
        files = {"cv_file": ("cv.pdf", BytesIO(file_content), "application/pdf")}
        data = {
            "job_id": "job1",
            "cover_letter": "Hire me!",
            "motivation": "I love your mission",
            "proud_project": "Built an AI agent"
        }
        
        try:
            response = client.post(
                "/applications",
                data=data,
                files=files,
                headers={"Authorization": "Bearer mock_token"}
            )
        finally:
            app.dependency_overrides.pop(verify_jwt, None)
        
        assert response.status_code == 200
        assert response.json()["cv_url"] == "https://example.com/cv.pdf"


def test_create_application_as_recruiter_fails():
    """Test that recruiters cannot create applications."""
    async def recruiter_override():
        return User(id="recruiter1", email="recruiter@example.com", role="recruiter")

    app.dependency_overrides[verify_jwt] = recruiter_override

    file_content = b"fake pdf"
    files = {"cv_file": ("cv.pdf", BytesIO(file_content), "application/pdf")}
    data = {
        "job_id": "job1",
        "motivation": "Just testing",
        "proud_project": "Automation work"
    }

    try:
        response = client.post(
            "/applications",
            data=data,
            files=files,
            headers={"Authorization": "Bearer mock_token"}
        )
    finally:
        app.dependency_overrides.pop(verify_jwt, None)

    assert response.status_code == 403
