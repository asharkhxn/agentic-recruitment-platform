import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agent.tools import (
    create_job,
    get_applicants,
    summarize_cv,
    generate_job_description,
    rank_applicants_for_job
)


@pytest.mark.asyncio
async def test_create_job():
    """Test create_job tool."""
    with patch("agent.tools.get_supabase_client") as mock_supabase:
        mock_response = MagicMock()
        mock_response.data = [{
            "id": "job1",
            "title": "AI Engineer",
            "description": "Build AI",
            "requirements": "Python, ML",
            "location": "London",
            "salary": "150k"
        }]
        
        mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = mock_response
        
        result = await create_job(
            title="AI Engineer",
            description="Build AI",
            requirements="Python, ML",
            location="London",
            salary="150k",
            user_id="user1"
        )
        
        assert result["title"] == "AI Engineer"
        assert "error" not in result


@pytest.mark.asyncio
async def test_get_applicants():
    """Test get_applicants tool."""
    with patch("agent.tools.get_supabase_client") as mock_supabase:
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "app1",
                "applicant_id": "user1",
                "job_id": "job1",
                "applicant": {"email": "one@example.com"}
            }
        ]
        
        mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_response
        
        result = await get_applicants()
        
        assert len(result) == 1
        assert result[0]["id"] == "app1"


@pytest.mark.asyncio
async def test_get_applicants_filtered():
    """Test get_applicants tool with job filter."""
    with patch("agent.tools.get_supabase_client") as mock_supabase:
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "app1",
                "job_id": "job1",
                "applicant": {"email": "one@example.com"}
            }
        ]
        
        mock_query = mock_supabase.return_value.table.return_value.select.return_value
        mock_query.eq.return_value.execute.return_value = mock_response
        
        result = await get_applicants(job_id="job1")
        
        assert len(result) == 1


@pytest.mark.asyncio
async def test_summarize_cv():
    """Test CV summarization."""
    with patch("agent.tools.llm") as mock_llm:
        mock_response = MagicMock()
        mock_response.content = "Experienced developer with 5 years in Python and AI."
        mock_llm.invoke.return_value = mock_response
        
        result = await summarize_cv("Long CV text here...")
        
        assert "developer" in result.lower()
        assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_job_description():
    """Test job description generation."""
    with patch("agent.tools.llm") as mock_llm:
        mock_response = MagicMock()
        mock_response.content = "We are seeking a talented Backend Developer..."
        mock_llm.invoke.return_value = mock_response
        
        result = await generate_job_description(
            title="Backend Developer",
            key_requirements="Python, FastAPI, PostgreSQL"
        )
        
        assert "Backend Developer" in result
        assert len(result) > 0


@pytest.mark.asyncio
async def test_rank_applicants_for_job():
    """Test ATS ranking functionality."""
    with patch("agent.tools.get_supabase_client") as mock_supabase, \
         patch("agent.tools.llm") as mock_llm:
        
        # Mock job data
        mock_job_response = MagicMock()
        mock_job_response.data = {
            "id": "job1",
            "title": "Python Developer",
            "description": "Backend role",
            "requirements": "Python, FastAPI"
        }
        
        # Mock applications data
        mock_apps_response = MagicMock()
        mock_apps_response.data = [
            {
                "id": "application1",
                "applicant_id": "user1",
                "job_id": "job1",
                "cv_url": "https://example.com/cv1.pdf",
                "cover_letter": "I love Python",
                "applicant_name": "John Doe",
                "applicant": {"email": "john@example.com", "full_name": "Johnathan Doe"}
            },
            {
                "id": "application2",
                "applicant_id": "user2",
                "job_id": "job1",
                "cv_url": "https://example.com/cv2.pdf",
                "cover_letter": "FastAPI expert",
                "applicant": {"email": "jane@example.com"}
            }
        ]
        
        # Mock LLM responses
        mock_llm_response1 = MagicMock()
        mock_llm_response1.content = '{"score": 85, "summary": "Strong Python skills", "skills": ["Python", "Django"]}'
        
        mock_llm_response2 = MagicMock()
        mock_llm_response2.content = '{"score": 92, "summary": "FastAPI expert", "skills": ["Python", "FastAPI", "PostgreSQL"]}'
        
        mock_llm.invoke.side_effect = [mock_llm_response1, mock_llm_response2]
        
        # Setup mock chain
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        
        mock_supabase.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value.execute.return_value = mock_job_response
        mock_eq.execute.return_value = mock_apps_response
        
        result = await rank_applicants_for_job("job1")
        
        assert result.job_id == "job1"
        assert result.job_title == "Python Developer"
        assert len(result.applicants) == 2
        # Should be sorted by score descending
        assert result.applicants[0].score >= result.applicants[1].score
        assert result.applicants[0].score == 92
