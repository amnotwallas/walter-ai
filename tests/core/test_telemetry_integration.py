import io
import json
import logging
import re
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.core.logger import JsonFormatter

@patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter")
def test_trace_correlation(mock_exporter):
    from main import app

    log_output = io.StringIO()
    handler = logging.StreamHandler(log_output)
    handler.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(handler)

    try:
        with TestClient(app) as test_client:
            response = test_client.get("/health")
            assert response.status_code == 200
    finally:
        logging.getLogger().removeHandler(handler)

    raw_logs = log_output.getvalue().strip().split("\n")
    logs = [json.loads(line) for line in raw_logs if line.strip()]
    assert len(logs) > 0

    request_logs = [log for log in logs if log.get("path") == "/health"]
    assert len(request_logs) > 0

    hex_32_pattern = re.compile(r"^[0-9a-fA-F]{32}$")
    for log in request_logs:
        trace_id = log.get("trace_id")
        assert trace_id is not None
        assert trace_id != "N/A"
        assert len(trace_id) == 32
        assert hex_32_pattern.match(trace_id)




