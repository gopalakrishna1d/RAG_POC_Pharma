from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint():
    response = client.post("/api/chat", json={"question": "How many open deviations are there?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "answer" in payload
    assert payload["intent"]["entity"] == "deviation"
