from unittest.mock import patch
import pytest

with patch("app.core.telemetry.OTLPSpanExporter"):
    from main import app

from fastapi.testclient import TestClient

client = TestClient(app)

def test_trace_correlation():
    # Trigger a request and verify response status
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200


