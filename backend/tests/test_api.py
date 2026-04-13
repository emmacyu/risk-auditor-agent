import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os
from pathlib import Path

# Add backend directory to sys.path so 'app.main' can be resolved
backend_dir = Path(os.path.abspath(__file__)).parent.parent
sys.path.append(str(backend_dir))

from app.main import app
from fastapi.testclient import TestClient

def test_chat_endpoint():
    """Test the /chat API endpoint to ensure it accepts requests and returns a valid answer."""
    with TestClient(app) as client:
        payload = {
            "message": "How are you?",
            "user_id": "fastapi_api_tester_02"
        }
        
        response = client.post("/chat", json=payload)
        assert response.status_code == 200, "API failed to return 200 OK"
        
        data = response.json()
        assert "answer" in data, "API response missing 'answer' field"
        assert len(data["answer"]) > 0, "API returned an empty answer"
