import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    with patch("core.config.get_supabase_client") as mock:
        yield mock


@pytest.fixture
def mock_supabase_anon():
    with patch("core.config.get_supabase_anon_client") as mock:
        yield mock


@pytest.fixture
def recruiter_token():
    """Mock JWT token for recruiter."""
    return "mock_recruiter_token"


@pytest.fixture
def applicant_token():
    """Mock JWT token for applicant."""
    return "mock_applicant_token"


@pytest.fixture
def mock_verify_jwt_recruiter():
    with patch("core.auth.verify_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = MagicMock(
            id="user123",
            email="recruiter@example.com",
            role="recruiter"
        )
        yield mock


@pytest.fixture
def mock_verify_jwt_applicant():
    with patch("core.auth.verify_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = MagicMock(
            id="applicant123",
            email="applicant@example.com",
            role="applicant"
        )
        yield mock
