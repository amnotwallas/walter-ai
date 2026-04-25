from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Verifica que el endpoint de salud responda correctamente."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_chat_schema_validation():
    """Verifica que la validación de Pydantic funcione."""
    response = client.post("/api/v1/chat", json={"query": ""})
    assert response.status_code == 422 
