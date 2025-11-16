"""
Tests for FastAPI backend
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from api import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "Code Assistant" in data["service"]


def test_list_sessions():
    """Test list sessions endpoint"""
    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "count" in data


def test_invalid_session_query():
    """Test query with invalid session"""
    response = client.post(
        "/query",
        json={
            "session_id": "invalid-session-id",
            "query": "test query"
        }
    )
    assert response.status_code == 404


def test_invalid_github_url():
    """Test upload with invalid GitHub URL"""
    response = client.post(
        "/upload/github",
        json={"repo_url": "not-a-valid-url"}
    )
    # Should fail to clone
    assert response.status_code in [400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
