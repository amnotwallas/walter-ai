import pytest
from app.core.telemetry import init_telemetry
from opentelemetry import trace

def test_telemetry_initialization():
    init_telemetry("test-service")
    provider = trace.get_tracer_provider()
    assert provider is not None
