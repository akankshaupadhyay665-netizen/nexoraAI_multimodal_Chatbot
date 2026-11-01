"""
Nexora AI - Backend API Tests
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify health endpoint responds with online status"""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["platform"] == "NEXORA AI"
    assert "database" in data

def test_get_models():
    """Verify models catalog endpoint lists integrated models"""
    res = client.get("/api/models")
    assert res.status_code == 200
    models = res.json()
    assert isinstance(models, list)
    assert len(models) >= 4
    model_ids = [m["id"] for m in models]
    assert "gemini-flash-lite-latest" in model_ids
    assert "pollinations-flux" in model_ids

def test_conversations_crud():
    """Verify full CRUD lifecycle for conversations"""
    # 1. Create
    res = client.post("/api/conversations", json={"title": "Test Thread", "model_used": "gemini-2.5-flash"})
    assert res.status_code == 200
    conv = res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Test Thread"

    # 2. List
    res = client.get("/api/conversations")
    assert res.status_code == 200
    items = res.json()
    assert any(c["id"] == conv_id for c in items)

    # 3. Retrieve
    res = client.get(f"/api/conversations/{conv_id}")
    assert res.status_code == 200
    assert res.json()["id"] == conv_id

    # 4. Update
    res = client.put(f"/api/conversations/{conv_id}", json={"title": "Updated Title"})
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"

    # 5. Delete
    res = client.delete(f"/api/conversations/{conv_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

def test_chat_endpoint_fallback():
    """Verify chat endpoint returns intelligent response even without API key"""
    res = client.post("/api/chat", json={
        "message": "Hello Nexora, explain your platform architecture.",
        "model": "gemini-2.5-flash"
    })
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert "user_message" in data
    assert "assistant_message" in data
    assert len(data["assistant_message"]["content"]) > 20

def test_settings_endpoints():
    """Verify settings retrieval and updates"""
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "gemini_configured" in data
    assert "model_list" in data


def test_reports_endpoints():
    """Verify live reports data and CSV export"""
    res = client.get("/api/reports")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "total_conversations" in data["metrics"]
    assert "models_breakdown" in data
    assert "recent_activity" in data

    csv_res = client.get("/api/reports/export-csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "Timestamp,Activity Category,Description" in csv_res.text
