from unittest.mock import patch
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from app.core.telemetry import init_telemetry

@patch("app.core.telemetry.OTLPSpanExporter")
def test_telemetry_initialization(mock_exporter):
    init_telemetry("test-service")
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)
    assert provider.resource.attributes["service.name"] == "test-service"

