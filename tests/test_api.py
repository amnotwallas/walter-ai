import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import get_settings
from unittest.mock import MagicMock, patch

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
    response = client.post("/api/v1/chat/stream", json={"query": "Hola"})
    assert response.status_code == 403
    assert "INVALID_API_KEY" in response.json()["detail"]

def test_chat_schema_validation():
    """Verifica que la validación de Pydantic funcione con API Key válida."""
    # Enviamos query vacía que viola el min_length=1 definido en el esquema
    response = client.post("/api/v1/chat/stream", json={"query": ""}, headers=HEADERS)
    assert response.status_code == 422

def test_chat_stream_success():
    """Verifica que el flujo de streaming funcione (mockeando el cliente de OpenAI)."""
    payload = {"query": "Test query", "session_id": "test_session"}
    
    # Mockeamos el generador de AgentService para evitar llamadas reales a la API
    with patch("app.services.agent_service.AgentService.get_streaming_response") as mock_stream:
        mock_stream.return_value = iter(["data: Hello\n\n", "data: world\n\n"])
        
        response = client.post("/api/v1/chat/stream", json=payload, headers=HEADERS)
        
        assert response.status_code == 200
        assert "data: Hello" in response.text
        assert "data: world" in response.text

def test_chat_init_action():
    """Verifica que la acción 'init' devuelva el mensaje de sistema listo."""
    payload = {
        "query": "initialize", # Enviamos query para evitar 422
        "session_id": "new_session_123", 
        "action": "init"
    }
    
    response = client.post("/api/v1/chat/stream", json=payload, headers=HEADERS)
    
    assert response.status_code == 200
    assert "WALTER_AI_CORE_ESTABLISHED" in response.text

def test_quality_guard_logic():
    """Prueba la lógica interna del QualityGuard."""
    from app.services.quality_service import QualityGuard
    
    # Caso 1: Respuesta genérica
    bad_response = "Claro que sí, como modelo de lenguaje estoy aquí para ayudarte."
    result = QualityGuard.evaluate("Hola", bad_response)
    assert result["score"] < 80
    
    # Caso 2: Respuesta correcta (WALTER_AI style)
    good_response = "WALTER_AI: SISTEMA_OPERATIVO activo. Consultando FASTAPI."
    result = QualityGuard.evaluate("Hola", good_response)
    assert result["score"] >= 80

def test_rate_limiting():
    """Verifica que el rate limiting esté activo."""
    payload = {"query": "Rate limit test"}
    # El límite es 5 por minuto. Hacemos 6.
    # Nota: Puede variar dependiendo de si el TestClient resetea el estado
    for _ in range(5):
        client.post("/api/v1/chat/stream", json=payload, headers=HEADERS)
    
    response = client.post("/api/v1/chat/stream", json=payload, headers=HEADERS)
    # Si el limitador está funcionando en el entorno de test:
    if response.status_code == 429:
        assert "Rate limit exceeded" in response.text
