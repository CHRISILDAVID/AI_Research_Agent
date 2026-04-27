"""Basic tests for the AI Research Agent backend."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check():
    """Verify the health check endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ai-research-agent"}

def test_root_endpoint():
    """Verify the root endpoint returns basic service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Research Agent"
    assert data["status"] == "running"
