from fastapi.testclient import TestClient

def test_get_models(client: TestClient):
    """Test the /api/models endpoint."""
    response = client.get("/api/models")
    assert response.status_code == 200
    
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0
    assert "gemini-1.5-flash" in data["models"]

def test_get_sessions(client: TestClient):
    """Test the /api/sessions endpoint."""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
