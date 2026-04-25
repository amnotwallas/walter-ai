import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()

# Headers comunes
HEADERS = {"X-API-KEY": settings.API_KEY}

def test_root_endpoint():
    """Verifica que la ruta raíz responda correctamente."""
    response = client.get("/")
    assert response.status_code == 200
    assert "WALTER_AI_NEURAL_CORE_ONLINE" in response.json()["message"]

def test_health_check():
    """Verifica que el endpoint de salud responda correctamente."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_chat_auth_failure():
    """Verifica que el acceso sea denegado sin API Key válida."""
    response = client.post("/api/v1/chat", json={"query": "Hola"})
    assert response.status_code == 403
    assert "INVALID_API_KEY" in response.json()["detail"]

def test_chat_schema_validation():
    """Verifica que la validación de Pydantic funcione con API Key válida."""
    # Enviamos un body vacío para forzar error 422
    response = client.post("/api/v1/chat", json={}, headers=HEADERS)
    assert response.status_code == 422

def test_chat_success_mock(mocker):
    """Prueba un flujo exitoso de chat usando un mock del servicio."""
    # Mockeamos el método get_response del AgentService
    mock_response = "SISTEMA_OPERATIVO: HOLA_MUNDO. SOY_WALTER_AI."
    mocker.patch(
        "app.services.agent_service.AgentService.get_response", 
        return_value=mock_response
    )
    
    payload = {"query": "Quién eres?"}
    response = client.post("/api/v1/chat", json=payload, headers=HEADERS)
    
    assert response.status_code == 200
    assert response.json()["response"] == mock_response

def test_rate_limiting():
    """Verifica que el sistema bloquee tras exceder el límite de 5 peticiones."""
    # Realizamos 5 peticiones exitosas (mockeadas)
    payload = {"query": "Test"}
    for _ in range(5):
        response = client.post("/api/v1/chat", json=payload, headers=HEADERS)
        assert response.status_code == 200
    
    # La 6ta petición debe fallar con 429 Too Many Requests
    response = client.post("/api/v1/chat", json=payload, headers=HEADERS)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text
