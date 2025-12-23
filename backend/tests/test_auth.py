import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from core.auth import verify_jwt


def _setup_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")


@pytest.mark.asyncio
async def test_verify_jwt_valid_token(monkeypatch):
    """Verify that a valid token returns the expected user."""
    _setup_env(monkeypatch)
    mock_supabase = MagicMock()
    mock_service = MagicMock()

    mock_user = MagicMock()
    mock_user.id = "user123"
    mock_user.email = "test@example.com"
    mock_user.user_metadata = {"role": "recruiter", "full_name": "Test User"}

    mock_auth_response = MagicMock()
    mock_auth_response.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_auth_response

    db_response = MagicMock()
    db_response.data = [{"role": "recruiter", "full_name": "Test User"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = db_response
    mock_service.table.return_value.select.return_value.eq.return_value.execute.return_value = db_response

    with patch("core.auth.create_client", return_value=mock_supabase), \
         patch("core.auth.get_supabase_client", return_value=mock_service):
        credentials = MagicMock()
        credentials.credentials = "valid_token"

        user = await verify_jwt(credentials)

    assert user.id == "user123"
    assert user.email == "test@example.com"
    assert user.role == "recruiter"
    assert user.full_name == "Test User"


@pytest.mark.asyncio
async def test_verify_jwt_provisions_missing_user(monkeypatch):
    """User without DB record should be provisioned via service client."""
    _setup_env(monkeypatch)
    mock_supabase = MagicMock()

    mock_user = MagicMock()
    mock_user.id = "user456"
    mock_user.email = "new@example.com"
    mock_user.user_metadata = {"role": "applicant", "full_name": "New User"}

    mock_auth_response = MagicMock(user=mock_user)
    mock_supabase.auth.get_user.return_value = mock_auth_response

    empty_response = MagicMock()
    empty_response.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = empty_response

    service_client = MagicMock()
    service_select = service_client.table.return_value.select.return_value.eq.return_value
    service_select.execute.return_value = MagicMock(data=[{"role": "applicant", "full_name": "New User"}])

    with patch("core.auth.create_client", return_value=mock_supabase), \
         patch("core.auth.get_supabase_client", return_value=service_client):
        credentials = MagicMock()
        credentials.credentials = "new_token"

        user = await verify_jwt(credentials)

    service_client.table.return_value.upsert.return_value.execute.assert_called_once()
    assert user.id == "user456"
    assert user.role == "applicant"


@pytest.mark.asyncio
async def test_verify_jwt_invalid_token(monkeypatch):
    """Invalid token should raise HTTPException 401."""
    _setup_env(monkeypatch)
    mock_supabase = MagicMock()
    mock_service = MagicMock()

    mock_supabase.auth.get_user.return_value = MagicMock(user=None)

    with patch("core.auth.create_client", return_value=mock_supabase), \
         patch("core.auth.get_supabase_client", return_value=mock_service):
        credentials = MagicMock()
        credentials.credentials = "bad_token"

        with pytest.raises(HTTPException) as exc_info:
            await verify_jwt(credentials)

    assert exc_info.value.status_code == 401
    assert "invalid token" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_verify_jwt_missing_configuration(monkeypatch):
    """Missing Supabase configuration should raise a 500 error."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    credentials = MagicMock()
    credentials.credentials = "token"

    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt(credentials)

    assert exc_info.value.status_code == 500
    assert "configuration" in exc_info.value.detail.lower()
